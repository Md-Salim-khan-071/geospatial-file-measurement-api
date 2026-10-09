import geopandas as gpd


def calculate_measurement(geometry, crs):
    if geometry is None or geometry.is_empty:
        return None

    geometry_type = geometry.geom_type

    if geometry_type == "Point":
        return None

    if crs is None:
        raise ValueError("CRS is missing")

    projected_crs = gpd.GeoSeries([geometry], crs=crs).estimate_utm_crs()

    projected_geometry = gpd.GeoSeries(
        [geometry],
        crs=crs
    ).to_crs(projected_crs).iloc[0]

    if geometry_type == "Polygon":
        return {
            "value": projected_geometry.area,
            "unit": "m²",
            "type": "area"
        }

    if geometry_type == "LineString":
        return {
            "value": projected_geometry.length,
            "unit": "m",
            "type": "length"
        }

    return None