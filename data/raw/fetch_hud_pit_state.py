"""
Fetch HUD Point-in-Time (PIT) count data aggregated to state level.

Source: HUD Exchange AHAR downloads
URL: https://www.hudexchange.info/resource/3031/pit-and-hic-data-since-2007/

The page offers Excel/CSV downloads by year. For 2023:
1. Visit https://www.hudexchange.info/resource/3031/pit-and-hic-data-since-2007/
2. Download '2007-2023-PIT-Counts-by-CoC.xlsx'
3. Sheet: '2023' contains CoC-level counts
4. Aggregate to state by summing total_homeless, sheltered_es, sheltered_th,
   sheltered_sh, unsheltered, and veteran columns grouped by state code.

No API key required. Data is publicly available for download.
"""

# Example aggregation after downloading:
#
# import pandas as pd
#
# df = pd.read_excel(
#     "2007-2023-PIT-Counts-by-CoC.xlsx",
#     sheet_name="2023",
# )
# state_df = df.groupby("State").agg(
#     total_homeless=("Overall Homeless, 2023", "sum"),
#     sheltered=("Sheltered Total Homeless, 2023", "sum"),
#     unsheltered=("Unsheltered Homeless, 2023", "sum"),
#     veteran=("Overall Homeless Veterans, 2023", "sum"),
# ).reset_index()
# state_df.to_csv("hud_pit_state_2023.csv", index=False)
