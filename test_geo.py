import geopandas as gpd

gdf = gpd.read_file("sample.kml", driver="KML")

print(gdf)
print("\nCRS:", gdf.crs)
print("\nGeometry:", gdf.geometry.iloc[0].geom_type)
print("\nProperties:")
print(gdf.iloc[0].drop("geometry"))