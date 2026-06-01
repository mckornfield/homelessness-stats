"""
Fetch NOAA 1991-2020 Climate Normals — average January temperature by state.

Source: NOAA Climate Normals
URL: https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals

Method:
1. Download the 1991-2020 Normals station data (monthly normals CSV):
   https://www.ncei.noaa.gov/data/normals-monthly/1991-2020/archive/

2. Filter for month=01 (January), variable=MLY-TAVG-NORMAL (mean temp, tenths °F)

3. Geocode stations to states using station metadata (latitude/longitude → state FIPS)

4. Average station values within each state

No API key required for bulk downloads. NOAA Climate Data Online also offers
API access (free registration required): https://www.ncdc.noaa.gov/cdo-web/api/v2/

Example:
  curl -o normals_monthly.csv \\
    "https://www.ncei.noaa.gov/data/normals-monthly/1991-2020/archive/mly-normal-all.csv"
"""

# Example processing:
#
# import pandas as pd
#
# df = pd.read_csv("mly-normal-all.csv")
# jan = df[df["month"] == 1][["station", "state", "MLY-TAVG-NORMAL"]]
# jan["jan_temp_f"] = jan["MLY-TAVG-NORMAL"] / 10.0  # tenths of °F → °F
# state_temps = jan.groupby("state")["jan_temp_f"].mean().reset_index()
# state_temps.to_csv("noaa_jan_temp_state.csv", index=False)
