# Urban-rural differences in cigarette smoking by state, BRFSS 2018-2025

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23018447.svg)](https://doi.org/10.5281/zenodo.23018447)

Analysis code for:

> Ulm CR, et al. State-level trends in urban-rural differences in cigarette smoking in the United States. *PLOS ONE* (under review, PONE-D-26-32210).

The code runs the full analysis, from the raw CDC files to every table and figure in the paper, with one command.

## Quick start (Windows)

Requirements: SAS 9.4 (steps 4-8), Stata 19 or later (steps 6 and 12; any edition, BE is enough), Python 3.10 or later, about 10 GB of free disk space, and an internet connection for the first run.

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
| 3 | `code/03_descriptives.py` | Table 1, S2 Table, sample flow and state-by-year counts (`sample_flow.csv`, `state_by_year.csv`) |
| 4 | `code/04_import_analytic_file.sas` | SAS copy of the analytic file |
| 5 | `code/05_state_models.sas` | Survey logistic models for the 43 states (Models 1, 2, 3a, 3b); the nationwide fit is not reported (every nationwide result comes from step 6) |
| 6 | `code/06_nationwide_gee.sas`, then `code/06b_nationwide_gee.do` | Nationwide survey-weighted GEE models, clustered by state, for every nationwide result. First SAS: Models 1, 2, 3a and 3b (S3 Table). Then Stata: the urban and rural annual ORs and the interaction from Model 3b (Table 2), Model 3b + year squared + rural x year squared (S1 Table, panel 1a) and the nationwide predicted probabilities for Fig 2 (`nationwide_gee_slopes.csv`, `nationwide_gee_quadratic.csv`, `fig2_nationwide_gee.csv`) |
| 7 | `code/07_year_specification.sas` | Linear, quadratic and categorical survey year, nationwide survey logistic models (not reported; step 9 checks that the GEE quadratic model of step 6 has the same estimates) |
| 8 | `code/08_state_quadratic.sas` | Quadratic trend within each state (S1 Table, panel 1b) |
| 9 | `code/09_model_tables.py` | Table 2, S1 Table, S3 Table, the counts quoted in the Results (`results_counts.txt`), the table and figure captions (`table_captions.md`), the Fig 1 input (`state_or_summary.csv`) and the list of Fig 2 panels (`fig2_entities.do`) |
| 10 | `code/10_fig1_map.py` | Fig 1: US state map of the urban-rural odds ratios (Models 1, 2 and 3a), with Alaska and Hawaii as insets |
| 11 | `code/11_s1_fig_map.py` | S1 Fig: US state maps of smoking prevalence, rural and urban, 2018 and 2025 |
| 12 | `code/12_fig2_predictions.do` | Predicted probabilities and 95% CIs for Fig 2 (survey-weighted `svy` models for the state panels; the nationwide panel is copied from step 6), plus unadjusted prevalence for reference (`fig2_plotted_values.csv`) |
| 13 | `code/13_fig2_panels.py` | Fig 2 (2 columns, legend in the last cell): predicted probability lines with 95% CI bands, drawn from the step 12 values |

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
resources/             US state boundaries for Fig 1 and S1 Fig (US Census Bureau shapefile)
```

The outputs from the published run are in `output/` so results can be checked without re-running. A new run overwrites them, and `git diff` shows any difference.

## Methods in brief

- **Data:** BRFSS combined landline and cell phone public-use files, 2018-2025.
- **Outcome:** current cigarette smoking (`_RFSMOK3`).
- **Exposure:** urban vs rural county of residence (`_URBSTAT`, NCHS Urban-Rural Classification Scheme for Counties).
- **Covariates:** age group, sex, race/ethnicity and education.
- **Analytic sample:** complete cases (`output/tables/sample_flow.csv`).
- **Survey design:** every model uses the BRFSS final weight (`_LLCPWT`).
  - State models: `PROC SURVEYLOGISTIC` with the stratum (`_STSTR`) and primary sampling unit (`_PSU`) provided by CDC for each survey year (Taylor-series linearization). The Fig 2 state panels use the same design in Stata (`svy`).
  - Nationwide models, for every nationwide result (S3 Table, Table 2, S1 Table panel 1a and Fig 2): survey-weighted generalized estimating equations with an independence working correlation and empirical standard errors clustered by state (`PROC GENMOD`; in Stata, `glm` with `vce(cluster _state)`, its variance multiplied by (G-1)/G, G = 51 states, so that it equals GENMOD's empirical variance).
- **Multiple testing:** Benjamini-Hochberg (BH) adjusted p-values control the false discovery rate across the 43 state-specific tests, separately for each family: the urban-rural odds ratio in Models 1, 2 and 3a, and the urban-rural x year interaction in Model 3b. A state-specific result is significant when its BH-adjusted p-value is < .05.

## Archived copy

Version 1.2.0 of this repository, including the analytic data file, is archived at UNC Dataverse: https://doi.org/10.15139/S3/E6VVVL. Since that version, the changes in presentation are these: the supplementary tables are renumbered in order of first citation in the paper (the old S3 Table is now S1 Table, the old S1 Table is now S2 Table, and the old S2 Table is now S3 Table, with their CSV files renamed to match); Fig 1 and S1 Fig are geographic state maps drawn on the US Census Bureau boundary file; Fig 2 is simpler (two columns, drawn in Python from the Stata estimates, showing only the predicted probabilities and their 95% CIs); Table 2 and S1 Table (the quadratic year sensitivity analysis) have a new layout; and the tables and captions call the false discovery rate-adjusted value the BH-adjusted p-value. One change affects the results: the nationwide results in Table 2 (the urban and rural annual ORs and the interaction), S1 Table panel 1a and Fig 2 now come from the nationwide GEE models clustered by state, as the Methods describe, instead of the nationwide survey logistic models: the estimates are the same, and the 95% CIs and p-values are those of the GEE models. Every other estimate is the same. Version 1.0.0 is also archived on Zenodo: https://doi.org/10.5281/zenodo.23018447

## Data

BRFSS data are collected by the Centers for Disease Control and Prevention (CDC) and are publicly available at <https://www.cdc.gov/brfss/annual_data/annual_data.htm>. See [data/README.md](data/README.md) for file details, variable definitions and terms of use.

Source: Centers for Disease Control and Prevention (CDC). Behavioral Risk Factor Surveillance System Survey Data. Atlanta, Georgia: U.S. Department of Health and Human Services, Centers for Disease Control and Prevention, 2018-2025.

Use of these data does not imply endorsement by CDC.

State boundaries in Fig 1 and S1 Fig: US Census Bureau, 2023 Cartographic Boundary File, States, 1:20,000,000 (`cb_2023_us_state_20m`), <https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_20m.zip>. The unzipped files are kept unchanged in `resources/`. They are a work of the US government and in the public domain.

## License

Code: MIT License (see `LICENSE`). BRFSS data: see [data/README.md](data/README.md).
