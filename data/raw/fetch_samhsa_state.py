"""
Fetch SAMHSA NSDUH state-level substance use and mental health estimates.

Source: SAMHSA National Survey on Drug Use and Health (NSDUH)
URL: https://www.samhsa.gov/data/nsduh/state-reports-NSDUH

For 2021-2022 combined estimates:
1. Visit https://www.samhsa.gov/data/nsduh/state-reports-NSDUH
2. Download the 2021-2022 NSDUH State-Level Excel tables
3. Key tables:
   - Table 47: Any Mental Illness (AMI) past year, adults 18+, percent by state
   - Table 16: Illicit drug use disorder past year, adults 18+, percent by state
   - Table 21: Alcohol use disorder past year, adults 18+, percent by state

No API key required. Data is publicly available for download.

Column mapping from downloaded tables:
  ami_pct                -> Table 47, '18+' row, state column
  drug_disorder_pct      -> Table 16, '18+' row, state column
"""

# Example extraction after downloading NSDUH Excel:
#
# import pandas as pd
#
# xls = pd.ExcelFile("NSDUHsaeTotals2022.xlsx")
# ami = pd.read_excel(xls, sheet_name="Table 47", header=4)
# # Reshape and clean as needed; column names vary by year
# ami.to_csv("samhsa_ami_state_2022.csv", index=False)
