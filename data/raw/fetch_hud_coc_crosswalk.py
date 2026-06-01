"""
Fetch the HUD CoC-to-county crosswalk and CoC centroid coordinates.

Source 1: HUD CoC GIS Shapefiles
URL: https://www.hudexchange.info/programs/coc/gis-tools/

The shapefile contains CoC boundaries as polygons. Use geopandas to compute centroids:
  import geopandas as gpd
  gdf = gpd.read_file("CoC_GIS_NatlTerrDC_Shapefile_2023.zip")
  gdf["centroid"] = gdf.geometry.centroid
  gdf["lat"] = gdf["centroid"].y
  gdf["lon"] = gdf["centroid"].x
  gdf[["COCNUM", "COCNAME", "lat", "lon"]].to_csv("coc_centroids.csv", index=False)

Source 2: HUD CoC-to-county crosswalk
URL: https://www.hudexchange.info/resource/6000/

Download 'FY2023_CoC_to_County_crosswalk.xlsx'
This file maps each CoC code to all counties it overlaps, with population weights.
Use the highest-weight county as the primary county FIPS for choropleth mapping.
"""
