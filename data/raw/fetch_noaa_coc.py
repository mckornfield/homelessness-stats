"""
Map NOAA 1991-2020 climate normals (January average temperature) to CoC centroids.

Source: NOAA Climate Normals
URL: https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals

Steps:
1. Download monthly normals: https://www.ncei.noaa.gov/data/normals-monthly/1991-2020/archive/
2. Filter for month=01, variable=MLY-TAVG-NORMAL (mean temp, tenths of °F)
3. Load station metadata (lat/lon) from station list
4. For each CoC, compute centroid (from HUD CoC shapefiles or a CoC→lat/lon table)
5. Assign nearest station's January temp to each CoC

CoC centroid reference (manually curated for major CoCs):
  CA-600: (34.05, -118.24)  — Los Angeles
  NY-600: (40.71, -74.01)   — New York City
  WA-500: (47.61, -122.33)  — Seattle
  (etc.)

Alternatively, use state-level January averages as a proxy (embedded in src/county_data.py).
"""
