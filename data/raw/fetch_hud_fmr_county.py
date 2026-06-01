"""
Fetch HUD Fair Market Rents 2023 by county.

Source: HUD USER FMR data
URL: https://www.huduser.gov/portal/datasets/fmr.html

Steps:
1. Download 'FY2023_4050_FMRs_revised.xlsx' from the FMR page
2. Key columns: fips2000 (county FIPS), fmr_1 (1BR FMR)

Example:
  import pandas as pd
  df = pd.read_excel("FY2023_4050_FMRs_revised.xlsx")
  df["county_fips"] = df["fips2000"].astype(str).str.zfill(5)
  df = df[["county_fips", "fmr_1", "countyname", "State"]].rename(
      columns={"fmr_1": "median_1br_fmr"}
  )
  df.to_csv("hud_fmr_county_2023.csv", index=False)
"""
