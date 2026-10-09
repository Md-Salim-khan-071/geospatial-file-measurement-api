from shapely.geometry import Polygon, LineString, Point
from app.services.measurements import calculate_measurement


def test_polygon_area():
    polygon = Polygon([
        (77.59, 12.97),
        (77.60, 12.97),
        (77.60, 12.98),
        (77.59, 12.98),
        (77.59, 12.97)
    ])

    result = calculate_measurement(polygon, "EPSG:4326")

    assert result["type"] == "area"
    assert result["unit"] == "m²"
    assert result["value"] > 0


def test_linestring_length():
    line = LineString([
        (77.59, 12.97),
        (77.60, 12.98)
    ])

    result = calculate_measurement(line, "EPSG:4326")

    assert result["type"] == "length"
    assert result["unit"] == "m"
    assert result["value"] > 0


def test_point_has_no_measurement():
    point = Point(77.59, 12.97)

    result = calculate_measurement(point, "EPSG:4326")

    assert result is None