# Geospatial File Measurement API

A REST API built with FastAPI to upload and process geospatial files in KML and zipped Shapefile formats. It extracts feature information and calculates polygon areas and line lengths using CRS-aware coordinate transformations.

## Features

- Upload KML and zipped Shapefile files.
- Extract feature geometry, properties, and coordinate reference system (CRS).
- Calculate polygon area in square metres and line length in metres.
- Transform geographic coordinates into a suitable projected CRS before measuring.
- Store file metadata and measurement results in SQLite.
- Retrieve file information and calculated measurements through REST endpoints.
- Validate file formats and handle invalid uploads.
- Automated tests using Pytest.

## Tech Stack

- **Language:** Python
- **API:** FastAPI, Uvicorn
- **Geospatial processing:** GeoPandas, Shapely, PyProj
- **Database:** SQLite, SQLAlchemy
- **Testing:** Pytest, HTTPX

## Setup

Clone the repository and navigate into the project directory.

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --reload
```

Open the interactive API documentation at:

`http://127.0.0.1:8000/docs`

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Check API availability |
| POST | `/api/files/` | Upload and process a geospatial file |
| GET | `/api/files/{file_id}/` | Retrieve file metadata |
| GET | `/api/files/{file_id}/measurements/` | Retrieve stored feature measurements |

### Upload a file

Use the interactive documentation at `/docs` or send a multipart file upload to `POST /api/files/`.

Supported formats: `.kml` and `.zip` containing a Shapefile.

### Measurement response

Each feature includes its geometry type, geometry, properties, and measurement when supported.

Example measurement:

```json
{
  "type": "area",
  "value": 1201683.92,
  "unit": "m²"
}
```

The value above is illustrative; actual measurements depend on the uploaded geometry.

## Coordinate Reference Systems

Geographic coordinates expressed in degrees cannot be used directly for area or length measurements. The API projects supported geometries into a suitable projected CRS before calculating measurements in metres.

Files without a usable CRS may not be measurable.

## Run Tests

```bash
pytest -v
```

The project includes automated tests for API availability, invalid uploads, successful KML processing, metadata persistence, measurement retrieval, and geometry measurements.

## Future Improvements

- Support MultiPolygon and MultiLineString measurements.
- Add database migrations and configurable storage.
- Improve handling of large uploads and background processing.
- Add authentication, deployment configuration, and broader integration tests.

## Author

Mohammed Salim Usman Khan