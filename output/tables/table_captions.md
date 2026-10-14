# Table and figure captions

Titles, notes and captions of the tables and figures as they read in the revised manuscript and its supplement. Bold type in a Word table is shown in the CSV file as a Yes/No column. Written by `code/09_model_tables.py`, which checks the numbers quoted here against the analysis output.

## Table 1

Table body: `Table1_sample_characteristics.csv`

Table 1. Sample demographic characteristics (N = 3,054,432), BRFSS 2018-2025

Note. We present only the complete-case analytic sample in this table. Sample sizes are unweighted. Percentages (%) and smoking prevalences are weighted. The unweighted sample sizes across the 43 states included in state-specific analyses ranged from 18,294 (Nevada) to 176,783 (New York) respondents. Within states, the rural sample sizes ranged from 546 (Nevada) to 45,875 (Maine) respondents, and urban sample sizes ranged from 17,748 (Nevada) to 161,879 (New York) respondents. “Smoking prevalence” is the percentage of current cigarette smokers within the total sample for each subgroup. For example, 6.4% of the total weighted sample lived in rural counties, and 18.6% of adults in those counties were current smokers.

## Fig 1

Figure: `output/figures/Fig1.tif`

Fig 1. Differences in urban-rural cigarette smoking in US states, 2018-2025. Each state is shown as a square of equal size in its approximate geographic position.

Notes. OR = Odds Ratio. Odds of smoking were higher among rural residents in darker-colored states. States with non-significant rural to urban odds ratios (q ≥ .05 after false discovery rate adjustment across the 43 state-specific tests for each model) or insufficient rural sample sizes (n < 50) for analysis are in light and dark grey, respectively.

## Table 2

Table body: `Table2_trends_and_interaction.csv`

Table 2. Linear time trends in current smoking among urban and rural groups, and the urban-rural by year interaction (Model 3b)

Note. OR = Odds Ratio, CI = Confidence Interval. Urban and rural odds ratios are the annual change in the odds of current smoking from Model 3b. The odds ratio for the interaction term (urban-rural × year) is from Model 3b and indicates the yearly rural odds ratio divided by the yearly urban odds ratio; when values are above 1, this indicates that the odds of smoking declined more slowly among rural than urban residents. P = unadjusted p-value for the interaction. q = Benjamini-Hochberg false discovery rate adjusted p-value across the 43 state-specific interaction tests. Example interpretation: In Washington, the odds of smoking decreased by 7% each year (OR = 0.93, 95% CI: 0.92, 0.94) among urban residents, but did not decrease significantly (OR = 1.01, 95% CI: 0.97, 1.06) for rural residents. The interaction OR of 1.091 (95% CI: 1.040, 1.145) demonstrates that the yearly rural odds ratio was 9% higher than the yearly urban odds ratio. States shown are those with a significant interaction after false discovery rate adjustment (q < .05).

## Fig 2

Figure: `output/figures/Fig2.tif`

Fig 2. Predicted probabilities (lines) from logistic regression Model 3b and unadjusted prevalences (dots) of current smoking in rural (red) and urban (blue) counties nationwide and in states with significant interaction terms after false discovery rate adjustment (q < .05), 2018-2025. Shaded bands are 95% CIs. The Benjamini-Hochberg false discovery rate adjusted p-value (q) for the urban-rural × year interaction (unadjusted P for the nationwide model) is shown in the lower right of each panel.

## S1 Table

Table body: `S1_Table_state_prevalence.csv` (in the Word table the Nationwide row is bold)

In the supplement file:

S1 Table. State-level smoking prevalence estimates in rural and urban counties, 2018 and 2025.

Note. Weighted prevalence of current cigarette smoking among the complete-case analytic sample; respondents with missing smoking status are excluded from both numerator and denominator. CI = confidence interval. A dash indicates that the estimate was suppressed because the unweighted sample size was less than 50 or the relative standard error exceeded 30%, or that the state did not contribute data in that year. California, Mississippi, and Nevada are not included in the 2025 BRFSS data.

In the manuscript's Supporting information list:

S1 Table. State-level smoking prevalence estimates in rural and urban counties, 2018 and 2025. A dash indicates that the estimate was suppressed because the relative standard error was greater than 30% or the unweighted sample size was less than 50, or that the state did not contribute data in that year.

## S1 Fig

Figure: `output/figures/S1_Fig.tif`

In the manuscript's Supporting information list:

S1 Fig. State-level smoking prevalence estimates in rural and urban counties. The maps show smoking prevalence estimates for 2018 (left panels) and 2025 (right panels) in rural (top panels) and urban (bottom panels) counties. Higher prevalence is indicated by red and lower prevalence by green. State estimates are excluded (grey) if the unweighted sample size was less than 50, the relative standard error was greater than 30%, or the state was not included in the BRFSS data for that year.

## S2 Table

Table body: `S2_Table_urban_rural_ORs.csv` (an OR and its 95% CI are bold when the matching "Model N q < .05" column is Yes)

In the supplement file:

S2 Table. Odds ratios for the urban-rural variable in the nationwide and state-specific logistic regression models, 2018-2025

Note. For nationwide analyses, we used generalized estimating equations with state-level cluster-robust standard errors to account for clustering of observations within states. All nationwide P < .001. Bold indicates that the state-specific odds ratio was significant after Benjamini-Hochberg false discovery rate adjustment (q < .05) across the 43 state-specific tests for that model.

In the manuscript's Supporting information list:

S2 Table. Odds ratios for the urban-rural variable in the nationwide and state-specific logistic regression models.

## S3 Table

In the supplement file:

S3 Table. Sensitivity analyses: quadratic specification of survey year, nationwide (Panel A) and within states (Panel B).

Panel A. Specification of survey year, nationwide Model 3b

Table body: `S3_Table_A_year_specification.csv`

Note. Rural × year and rural × year² are ratios of the rural-to-urban odds ratio per year and per year². Values greater than 1 suggest a wider urban-rural difference. Year² indicates the curvature of the time trend. The joint test assesses both year² and rural × year² together. Models adjust for age, sex, race/ethnicity, and education and use BRFSS complex survey design (survey weights, strata, primary sampling units).

Panel B. Quadratic time trends within states (Model 3b plus quadratic terms)

Table body: `S3_Table_B_state_quadratic.csv`

Note. q-values are Benjamini-Hochberg false discovery rate adjusted for the 43 state-specific analyses. The year² row is from Model 3b plus year² only; the other two rows are from Model 3b plus year² and rural × year².

In the manuscript's Supporting information list:

S3 Table. Sensitivity analyses: quadratic specification of survey year, nationwide and within states.
