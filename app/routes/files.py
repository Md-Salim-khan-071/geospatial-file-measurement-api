from pathlib import Path, PurePosixPath
import io
import uuid
import zipfile

import geopandas as gpd
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.database import SessionLocal
from app.models import GeospatialFile
from app.services.measurements import calculate_measurement


router = APIRouter(prefix="/api/files", tags=["Files"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_ZIP_FILES = 100
MAX_UNCOMPRESSED_SIZE = 50 * 1024 * 1024  # 50 MB


def validate_shapefile_zip(content: bytes) -> None:
    """Validate ZIP integrity and required Shapefile components."""
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            infos = archive.infolist()

            if len(infos) > MAX_ZIP_FILES:
                raise HTTPException(
                    status_code=400,
                    detail="ZIP contains too many files"
                )

            total_size = sum(info.file_size for info in infos)

            if total_size > MAX_UNCOMPRESSED_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail="Uncompressed ZIP contents exceed 50 MB"
                )

            shapefiles = {}

            for info in infos:
                # Reject absolute paths and directory traversal.
                path = PurePosixPath(info.filename.replace("\\", "/"))

                if (
                    path.is_absolute()
                    or ".." in path.parts
                    or (path.parts and ":" in path.parts[0])
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="ZIP contains an unsafe file path"
                    )

                if info.is_dir():
                    continue

                suffix = path.suffix.lower()

                if suffix in {".shp", ".shx", ".dbf"}:
                    # Components must share the same directory and basename.
                    key = (
                        str(path.parent).lower(),
                        path.stem.lower()
                    )
                    shapefiles.setdefault(key, set()).add(suffix)

            required = {".shp", ".shx", ".dbf"}

            if not any(required.issubset(parts) for parts in shapefiles.values()):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "ZIP must contain a matching .shp, .shx, "
                        "and .dbf file for at least one Shapefile"
                    )
                )

            bad_file = archive.testzip()

            if bad_file is not None:
                raise HTTPException(
                    status_code=400,
                    detail="ZIP archive is corrupted"
                )

    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=400,
            detail="Invalid ZIP archive"
        )


def json_safe_value(value):
    """Convert missing and non-native scalar values into JSON-safe values."""
    if value is None or value is pd.NA:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(value, "item"):
        value = value.item()

    return value


def extract_features(gdf):
    """Extract feature information and calculate measurements."""
    features = []

    for index, row in gdf.iterrows():
        geometry = row.geometry

        measurement = (
            calculate_measurement(geometry, gdf.crs)
            if geometry is not None
            else None
        )

        properties = {
            key: json_safe_value(value)
            for key, value in row.items()
            if key != "geometry"
        }

        features.append({
            "feature_id": (
                int(index) if isinstance(index, int) else str(index)
            ),
            "geometry_type": (
                geometry.geom_type if geometry is not None else None
            ),
            "geometry": (
                geometry.__geo_interface__
                if geometry is not None else None
            ),
            "properties": properties,
            "measurement": measurement
        })

    return features


@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    # Use only the basename; never use a client-supplied path for storage.
    original_name = Path(file.filename.replace("\\", "/")).name
    extension = Path(original_name).suffix.lower()

    if extension not in {".kml", ".zip"}:
        raise HTTPException(
            status_code=400,
            detail="Only KML or ZIP files are supported"
        )

    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{extension}"

    try:
        # Read at most the limit plus one byte.
        content = await file.read(MAX_FILE_SIZE + 1)

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds the 10 MB size limit"
            )

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )

        if extension == ".zip":
            validate_shapefile_zip(content)

        file_path.write_bytes(content)

        # Parse the uploaded geospatial file.
        if extension == ".kml":
            gdf = gpd.read_file(file_path, driver="KML")
        else:
            gdf = gpd.read_file(file_path)

        if gdf.empty:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file contains no features"
            )

        # Measurement calculations require a known CRS for measurable geometry.
        features = extract_features(gdf)

        db = SessionLocal()

        try:
            record = GeospatialFile(
                id=file_id,
                filename=original_name,
                file_path=str(file_path),
                crs=str(gdf.crs) if gdf.crs else None,
                feature_count=len(gdf),
                status="COMPLETED",
                measurements=features
            )

            db.add(record)
            db.commit()

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

        return {
            "id": file_id,
            "filename": original_name,
            "feature_count": len(gdf),
            "crs": str(gdf.crs) if gdf.crs else None,
            "status": "COMPLETED",
            "features": features
        }

    except HTTPException:
        file_path.unlink(missing_ok=True)
        raise

    except Exception as exc:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=f"Unable to process geospatial file: {str(exc)}"
        )

    finally:
        await file.close()


@router.get("/{file_id}/")
def get_file_info(file_id: str):
    db = SessionLocal()

    try:
        record = db.query(GeospatialFile).filter(
            GeospatialFile.id == file_id
        ).first()

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )

        return {
            "id": record.id,
            "filename": record.filename,
            "feature_count": record.feature_count,
            "crs": record.crs,
            "status": record.status
        }

    finally:
        db.close()


@router.get("/{file_id}/measurements/")
def get_file_measurements(file_id: str):
    db = SessionLocal()

    try:
        record = db.query(GeospatialFile).filter(
            GeospatialFile.id == file_id
        ).first()

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )

        # Measurements were calculated and saved during upload.
        return {
            "file_id": record.id,
            "filename": record.filename,
            "feature_count": record.feature_count,
            "features": record.measurements or []
        }

    finally:
        db.close()