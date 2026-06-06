"""
Fetch presidential election results for state and county-level analysis.

=== State-level: 2024 presidential results ===

Source: AP / state election boards (certified results)
The embedded _ELECTION_2024 dict in src/state_data.py contains Harris 2-party
vote % for all 50 states + DC. To refresh with official certified results:

  https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/
  https://en.wikipedia.org/wiki/2024_United_States_presidential_election

2-party vote % = candidate_votes / (dem_votes + rep_votes) * 100
Margin = 2 * dem_pct - 100  (positive = Democratic lean, negative = Republican)

=== County-level: 2020 presidential results ===

Source: MIT Election Data and Science Lab
  Title: U.S. President 1976–2020
  DOI: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VOQCHQ
  Direct download (free, no account needed):
  https://dataverse.harvard.edu/api/access/datafile/:persistentId?persistentId=doi:10.7910/DVN/VOQCHQ/NT5UXP

Alternative (processed CSV, no login):
  https://raw.githubusercontent.com/tonmcg/US_County_Level_Election_Results_08-20/master/2020_US_County_Level_Presidential_Results.csv

Example processing after download:
  import pandas as pd

  df = pd.read_csv("2020_US_County_Level_Presidential_Results.csv")
  df["county_fips"] = df["county_fips"].astype(str).str.zfill(5)
  df["biden_pct_2020"] = df["per_dem"] * 100       # already as fraction 0-1
  df["dem_margin_2020"] = df["diff"]                # or compute: biden_pct*2 - 100

  # Filter to counties in our CoC dataset and save
  coc_fips = [...]  # list of county FIPS from _COC_DATA
  subset = df[df["county_fips"].isin(coc_fips)][["county_fips", "biden_pct_2020"]]
  subset.to_csv("election_county_2020.csv", index=False)

Note: The embedded _ELECTION_COUNTY_2020 in src/county_data.py covers all
~100 primary county FIPS codes used by our CoC dataset.
"""
