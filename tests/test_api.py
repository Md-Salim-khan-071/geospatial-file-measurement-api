
import io
import zipfile

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


SAMPLE_KML = b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Test Polygon</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              77.590,12.970,0
              77.600,12.970,0
              77.600,12.980,0
              77.590,12.980,0
              77.590,12.970,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>
"""


def test_root():
    response = client.get("/")
    assert response.status_code == 200


def test_upload_rejects_invalid_extension():
    response = client.post(
        "/api/files/",
        files={"file": ("test.txt", b"invalid", "text/plain")}
    )
    assert response.status_code == 400


def test_file_not_found():
    response = client.get("/api/files/nonexistent-id/")
    assert response.status_code == 404


def test_measurements_file_not_found():
    response = client.get("/api/files/nonexistent-id/measurements/")
    assert response.status_code == 404


def test_upload_invalid_zip():
    response = client.post(
        "/api/files/",
        files={"file": ("invalid.zip", b"not a zip", "application/zip")}
    )
    assert response.status_code == 400


def test_upload_zip_without_shapefile():
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("readme.txt", "Not a shapefile")

    response = client.post(
        "/api/files/",
        files={"file": ("no_shapefile.zip", buffer.getvalue(), "application/zip")}
    )
    assert response.status_code == 400


def test_successful_kml_upload():
    response = client.post(
        "/api/files/",
        files={"file": ("test.kml", SAMPLE_KML, "application/vnd.google-earth.kml+xml")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.kml"
    assert data["feature_count"] >= 1
    assert data["status"] == "COMPLETED"
    assert data["features"][0]["measurement"]["type"] == "area"


def test_uploaded_file_metadata_persists():
    upload = client.post(
        "/api/files/",
        files={"file": ("persist.kml", SAMPLE_KML, "application/vnd.google-earth.kml+xml")}
    )
    assert upload.status_code == 200
    file_id = upload.json()["id"]

    response = client.get(f"/api/files/{file_id}/")
    assert response.status_code == 200
    assert response.json()["id"] == file_id
    assert response.json()["filename"] == "persist.kml"


def test_measurements_persist_after_upload():
    upload = client.post(
        "/api/files/",
        files={"file": ("measure.kml", SAMPLE_KML, "application/vnd.google-earth.kml+xml")}
    )
    assert upload.status_code == 200
    file_id = upload.json()["id"]

    response = client.get(f"/api/files/{file_id}/measurements/")
    assert response.status_code == 200

    data = response.json()
    assert data["file_id"] == file_id
    assert len(data["features"]) >= 1
    assert data["features"][0]["measurement"]["value"] > 0
