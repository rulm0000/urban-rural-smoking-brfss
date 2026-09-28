# Urban-rural differences in cigarette smoking by state, BRFSS 2018-2025

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23018447.svg)](https://doi.org/10.5281/zenodo.23018447)

Analysis code for:

> Ulm CR, et al. State-level trends in urban-rural differences in cigarette smoking in the United States. *PLOS ONE* (under review, PONE-D-26-32210).

The code runs the full analysis, from the raw CDC files to every table and figure in the paper, with one command.

## Quick start (Windows)

Requirements: SAS 9.4, Stata 17 or later, Python 3.10 or later, about 10 GB of free disk space, and an internet connection for the first run.

```powershell
git clone https://github.com/rulm0000/urban-rural-smoking-brfss.git
cd urban-rural-smoking-brfss
python -m pip install -r requirements.txt
.\run_all.ps1
```

You can also double-click `run_all.bat`.

The first step downloads the eight BRFSS files from CDC (about 8 GB) and checks each one against the SHA-256 checksums in `data/SHA256SUMS`. There are two ways to skip the download:

```powershell
.\run_all.ps1 -RawDir "D:\BRFSS"     # use BRFSS files you already have
.\run_all.ps1 -UseArchivedData        # use the analytic file kept in this repository
```

Other options:

- `-From 9` resumes from a later step.
- `-SasExe` and `-StataExe` set the program paths if they are not found automatically.

A full run takes about 20 minutes on a laptop, mostly the SAS models.

## What each step does

| Step | Script | Produces |
|---|---|---|
| 1 | `code/01_download_brfss.py` | BRFSS 2018-2025 files, verified by checksum |
| 2 | `code/02_build_analytic_file.py` | `data/derived/brfss_2018_2025_analytic.csv` (or unpacks it from the archived copy) |
| 3 | `code/03_descriptives.py` | Table 1, S2 Table, S3 Table (sample flow and state-by-year counts) |
| 4 | `code/04_import_analytic_file.sas` | SAS copy of the analytic file |
| 5 | `code/05_state_models.sas` | Survey logistic models, nationwide and 43 states (Models 1, 2, 3a, 3b) |
| 6 | `code/06_nationwide_gee.sas` | Nationwide survey-weighted GEE models, clustered by state |
| 7 | `code/07_year_specification.sas` | Linear, quadratic and categorical survey year (S4 Table, Panel A) |
| 8 | `code/08_state_quadratic.sas` | Quadratic trend within each state (S4 Table, Panel B) |
| 9 | `code/09_model_tables.py` | Table 2, S1 Table, S4 Table, and the counts quoted in the Results |
| 10 | `code/10_fig1_tilegrid.py` | Fig 1 |
| 11 | `code/11_s1_fig_tilegrid.py` | S1 Fig |
| 12 | `code/12_fig2_panels.do` | Fig 2 |
| 13 | `code/13_fig2_tiff.py` | Fig 2 as a 300 dpi TIFF |

## Repository layout

```
run_all.ps1            one-command run (run_all.bat for double-click)
code/                  analysis steps, numbered in run order; common.py holds shared paths
data/SHA256SUMS        checksums of the CDC source files
data/brfss_2018_2025_analytic.csv.xz   compressed analytic file (all 8 years)
data/raw/              BRFSS files (downloaded; not tracked)
data/derived/          analytic file (built; not tracked)
output/tables/         manuscript and supplement tables (CSV)
output/figures/        Fig 1, Fig 2, S1 Fig (PNG and TIFF)
output/models/         model estimates from SAS and Stata
output/logs/           run logs (not tracked)
```

The outputs from the published run are in `output/` so results can be checked without re-running. A new run overwrites them, and `git diff` shows any difference.

## Methods in brief

- **Data:** BRFSS combined landline and cell phone public-use files, 2018-2025.
- **Outcome:** current cigarette smoking (`_RFSMOK3`).
- **Exposure:** urban vs rural county of residence (`_URBSTAT`, NCHS Urban-Rural Classification Scheme for Counties).
- **Covariates:** age group, sex, race/ethnicity and education.
- **Analytic sample:** complete cases (S3 Table).
- **Survey design:** every model uses the BRFSS final weight (`_LLCPWT`), stratum (`_STSTR`) and primary sampling unit (`_PSU`) as provided by CDC for each survey year.
  - State models: `PROC SURVEYLOGISTIC` (Taylor-series linearization).
  - Nationwide models: survey-weighted generalized estimating equations with standard errors clustered by state (`PROC GENMOD`).
- **Multiple testing:** q values control the false discovery rate across the 43 state-specific interaction tests (Benjamini-Hochberg).

## Archived copy

Version 1.0.0 of this repository, including the analytic data file, is archived on Zenodo: https://doi.org/10.5281/zenodo.23018447

## Data

BRFSS data are collected by the Centers for Disease Control and Prevention (CDC) and are publicly available at <https://www.cdc.gov/brfss/annual_data/annual_data.htm>. See [data/README.md](data/README.md) for file details, variable definitions and terms of use.

Source: Centers for Disease Control and Prevention (CDC). Behavioral Risk Factor Surveillance System Survey Data. Atlanta, Georgia: U.S. Department of Health and Human Services, Centers for Disease Control and Prevention, 2018-2025.

Use of these data does not imply endorsement by CDC.

## License

Code: MIT License (see `LICENSE`). BRFSS data: see [data/README.md](data/README.md).
