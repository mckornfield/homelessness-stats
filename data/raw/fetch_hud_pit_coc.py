"""
Fetch HUD 2023 PIT counts at the CoC level.

Source: HUD Exchange AHAR downloads
URL: https://www.hudexchange.info/resource/3031/pit-and-hic-data-since-2007/

CDC WONDER uses a web query interface (not a REST API) that exports tab-separated text.

Steps:
1. Download '2007-2023-PIT-Counts-by-CoC.xlsx'
2. Read sheet '2023'
3. Key columns: 'CoC Number', 'CoC Name', 'CoC Category',
   'Overall Homeless, 2023', 'Sheltered Total Homeless, 2023',
   'Unsheltered Homeless, 2023', 'Overall Homeless Veterans, 2023'

Example:
  import pandas as pd
  df = pd.read_excel("2007-2023-PIT-Counts-by-CoC.xlsx", sheet_name="2023")
  df = df.rename(columns={
      "CoC Number": "coc_code",
      "CoC Name": "coc_name",
      "Overall Homeless, 2023": "total_homeless",
      "Sheltered Total Homeless, 2023": "sheltered_homeless",
      "Unsheltered Homeless, 2023": "unsheltered_homeless",
      "Overall Homeless Veterans, 2023": "veteran_homeless",
  })
  df["state_postal"] = df["coc_code"].str[:2]
  df.to_csv("hud_pit_coc_2023.csv", index=False)
"""
