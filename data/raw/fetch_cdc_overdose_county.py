"""
Fetch CDC WONDER drug overdose death rates by county.

Source: CDC WONDER Multiple Cause of Death database
URL: https://wonder.cdc.gov/mcd.html

CDC WONDER uses a web query interface (not a REST API) that exports tab-separated text.

Steps to reproduce the query:
1. Go to https://wonder.cdc.gov/mcd-icd10-expanded.html
2. Group by: State, County
3. Year: 2020-2022 (3-year aggregate for stability)
4. ICD-10 codes: X40-X44, X60-X64, X85, Y10-Y14 (drug overdose deaths)
5. Export as tab-delimited text
6. Save as data/raw/cdc_overdose_county.txt

The exported file contains columns: State, County, FIPS, Deaths, Population, Crude Rate
Suppressed values (< 10 deaths) are marked as 'Suppressed' — treat as NA.

Example processing:
  import pandas as pd
  df = pd.read_csv("cdc_overdose_county.txt", sep="\\t", na_values=["Suppressed", "Missing"])
  df["county_fips"] = df["County Code"].astype(str).str.zfill(5)
  df["overdose_rate_per_100k"] = pd.to_numeric(df["Crude Rate"], errors="coerce")
  df = df[["county_fips", "overdose_rate_per_100k"]].dropna()
  df.to_csv("cdc_overdose_county.csv", index=False)
"""
