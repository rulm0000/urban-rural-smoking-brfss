# Data

## Source files

The analysis uses the BRFSS combined landline and cell phone (LLCP) public-use files for 2018-2025, in SAS transport format. They are published by CDC at:

`https://www.cdc.gov/brfss/annual_data/<YEAR>/files/LLCP<YEAR>XPT.zip`

Step 1 of the pipeline (`code/01_download_brfss.py`) downloads and unzips them into `data/raw/`. It then checks each file against `SHA256SUMS`:

| Year | File | Size (bytes) |
|---|---|---|
| 2018 | LLCP2018.XPT | 961,961,120 |
| 2019 | LLCP2019.XPT | 1,136,901,120 |
| 2020 | LLCP2020.XPT | 889,974,880 |
| 2021 | LLCP2021.XPT | 1,055,538,560 |
| 2022 | LLCP2022.XPT | 1,152,938,320 |
| 2023 | LLCP2023.XPT | 1,205,554,400 |
| 2024 | LLCP2024.XPT | 1,093,874,240 |
| 2025 | LLCP2025.XPT | 799,971,280 |

If CDC re-releases a file, the checksum will not match and the step stops with a message.

## Analytic file

Step 2 builds `data/derived/brfss_2018_2025_analytic.csv`, which has one row per respondent (3,388,638 records) and 12 variables. A compressed copy is kept in this repository as `data/brfss_2018_2025_analytic.csv.xz`, so the analysis can be reproduced without downloading the raw files (`run_all.ps1 -UseArchivedData`).

| Variable | Definition |
|---|---|
| `_STATE` | State FIPS code |
| `_STSTR`, `_PSU`, `_LLCPWT` | Survey stratum, primary sampling unit and final weight, as provided by CDC |
| `currentsmoker` | 1 = current smoker, 0 = not a current smoker (`_RFSMOK3`); don't know/refused = missing |
| `URRU` | 1 = rural, 0 = urban county (`_URBSTAT`) |
| `METRO` | 1 = nonmetropolitan, 0 = metropolitan county (`_METSTAT`); not used in the models |
| `_AGE_G` | Age group (six categories) |
| `SEXVAR` | 1 = male, 2 = female (`SEX1` in 2018) |
| `_RACEGR3` | Race/ethnicity, five categories (`_RACEGR4` where `_RACEGR3` is absent) |
| `_EDUCAG` | Education, four categories |
| `year_centered` | Survey year minus 2020 |

## Urban-rural classification

For 2018-2024, `_URBSTAT` is based on the 2013 NCHS Urban-Rural Classification Scheme for Counties. For 2025, it is based on the 2023 scheme. The rural cut point is the same in both.

## Jurisdictions and years

Eight jurisdictions had no rural respondents in 2018-2024 and are excluded from the state-specific models:

- Connecticut
- Delaware
- District of Columbia
- Hawaii
- Massachusetts
- New Hampshire
- New Jersey
- Rhode Island

US territories are not classified by NCHS.

Some states are missing a survey year in the public-use files. For example, California, Mississippi and Nevada have no 2025 data, and Tennessee has no 2024 data. S3 Table, Panel B lists the sample size by state and year.

## Terms of use

BRFSS public-use data are produced by a U.S. federal agency. They are in the public domain and may be reproduced without permission ([BRFSS FAQ](https://www.cdc.gov/brfss/about/brfss_faq.htm); [CDC use of agency materials](https://www.cdc.gov/other/agencymaterials.html)). CDC asks that:

- published material acknowledge CDC's BRFSS as the original source;
- users not change the substantive content of the materials, and derived files be described as derived;
- use of the data not be presented as implying endorsement by CDC, HHS or the U.S. government.

The files are de-identified public-use data and contain no direct identifiers.
