/* NATIONWIDE GEE logistic regression via PROC GENMOD (cluster-robust SEs)
   — from nationwide_genmod_gee_analysis.sas, Models 1, 2, 3a, 3b.
   The four PROC GENMOD GEE models (repeated subject=_state, type=exch) and the
   data-prep/PROC MEANS summary are unchanged from the source; only the PROC IMPORT
   of data/combinedbrfss_18_24v10.csv was replaced with an inline DATA step building
   the same work.brfss_raw from a synthetic BRFSS-shaped sample (not real CDC data). */

data work.brfss_raw;
    input _STATE _PSU _STSTR _LLCPWT year_centered IYEAR SEXVAR _AGE_G _RACEGR3 _EDUCAG URRU currentsmoker Quit;
    datalines;
    4 1010 101 460.65 -1 2019 2 5 4 2 1 0 0
    4 1010 101 473.36 -2 2018 2 1 3 2 0 0 0
    4 1010 101 625.33 -2 2018 1 4 1 1 1 1 0
    4 1010 101 262.37 2 2022 2 4 4 2 0 1 0
    4 1010 101 600.93 1 2021 1 6 4 3 0 0 0
    4 1010 101 146.84 -2 2018 1 3 3 1 1 0 1
    4 1010 101 644.37 -1 2019 1 4 1 1 1 1 0
    4 1010 101 247.26 2 2022 2 4 4 1 1 0 0
    4 1011 101 518.35 4 2024 2 3 1 4 0 0 1
    4 1011 101 198.22 3 2023 2 1 4 2 0 0 0
    4 1011 101 615.89 1 2021 2 4 1 4 0 0 1
    4 1011 101 106.11 4 2024 1 1 2 4 1 0 0
    4 1011 101 319.43 4 2024 2 2 3 1 0 0 0
    4 1011 101 158.88 2 2022 1 1 2 1 0 0 0
    4 1011 101 643.22 3 2023 1 5 4 2 1 1 0
    4 1011 101 454.19 3 2023 1 6 2 2 0 0 0
    4 1012 101 516.84 2 2022 1 1 1 1 1 0 1
    4 1012 101 377.17 3 2023 2 4 3 2 1 0 1
    4 1012 101 356.34 -2 2018 1 3 2 1 0 1 0
    4 1012 101 304.53 2 2022 1 1 3 3 0 0 1
    4 1012 101 676.92 1 2021 1 3 1 1 1 0 0
    4 1012 101 164.7 3 2023 1 5 4 1 0 1 0
    4 1012 101 677.3 3 2023 2 1 3 1 0 0 1
    4 1012 101 98.77 4 2024 1 3 4 1 1 0 0
    4 1020 102 124.79 2 2022 1 5 4 4 1 1 0
    4 1020 102 659.24 3 2023 1 6 3 4 0 1 0
    4 1020 102 222.74 0 2020 2 4 1 1 1 0 0
    4 1020 102 500.44 0 2020 2 4 3 1 0 1 0
    4 1020 102 492.86 1 2021 1 5 3 4 0 0 0
    4 1020 102 650.9 1 2021 2 6 2 2 0 1 0
    4 1020 102 119.77 4 2024 1 2 4 3 0 0 1
    4 1020 102 317.18 0 2020 1 2 4 4 1 0 0
    4 1021 102 456.68 -2 2018 2 6 4 3 1 0 1
    4 1021 102 362.0 3 2023 2 5 3 1 1 1 0
    4 1021 102 147.59 3 2023 1 3 2 1 0 1 0
    4 1021 102 86.68 0 2020 1 1 2 4 1 1 0
    4 1021 102 667.03 0 2020 1 5 2 2 1 0 0
    4 1021 102 202.06 3 2023 1 4 1 4 0 0 0
    4 1021 102 617.02 3 2023 2 4 4 3 0 0 1
    4 1021 102 278.64 0 2020 1 2 4 1 0 0 0
    4 1022 102 382.22 0 2020 1 3 1 4 0 0 0
    4 1022 102 647.92 -1 2019 1 2 4 1 0 0 0
    4 1022 102 406.53 4 2024 2 2 4 1 1 1 0
    4 1022 102 604.06 3 2023 1 6 3 3 1 1 0
    4 1022 102 83.06 -1 2019 1 3 3 4 0 0 1
    4 1022 102 183.4 1 2021 1 1 4 1 1 1 0
    4 1022 102 638.55 1 2021 2 4 3 2 1 0 0
    4 1022 102 160.27 1 2021 2 5 1 2 1 0 0
    5 2010 201 300.32 -2 2018 1 1 2 2 0 0 0
    5 2010 201 408.82 3 2023 2 1 1 3 1 1 0
    5 2010 201 471.42 2 2022 2 1 4 2 1 1 0
    5 2010 201 192.3 3 2023 1 5 2 2 0 0 0
    5 2010 201 134.65 -1 2019 1 2 2 1 1 0 1
    5 2010 201 504.83 -1 2019 2 1 4 2 1 1 0
    5 2010 201 292.97 -2 2018 1 1 3 3 0 0 0
    5 2010 201 641.16 -2 2018 2 1 1 1 0 0 0
    5 2011 201 177.98 -1 2019 1 2 2 1 1 1 0
    5 2011 201 554.13 3 2023 1 6 1 2 1 1 0
    5 2011 201 311.36 1 2021 2 4 4 3 1 1 0
    5 2011 201 200.98 0 2020 1 2 4 4 0 0 0
    5 2011 201 643.42 4 2024 1 1 3 1 0 0 0
    5 2011 201 562.35 0 2020 1 5 3 3 1 0 0
    5 2011 201 208.23 4 2024 2 2 3 4 1 1 0
    5 2011 201 300.5 -2 2018 2 1 3 4 0 1 0
    5 2012 201 410.51 -1 2019 2 2 3 3 0 0 0
    5 2012 201 436.45 4 2024 2 5 2 1 1 1 0
    5 2012 201 201.18 1 2021 1 5 2 3 0 0 1
    5 2012 201 394.85 0 2020 1 1 3 3 1 0 0
    5 2012 201 372.49 1 2021 2 6 1 1 0 0 1
    5 2012 201 327.11 1 2021 1 4 4 4 0 1 0
    5 2012 201 543.6 2 2022 2 3 4 3 1 0 0
    5 2012 201 636.48 1 2021 1 1 1 2 0 0 0
    5 2020 202 548.41 1 2021 2 1 1 2 1 0 1
    5 2020 202 517.97 4 2024 1 5 4 2 0 1 0
    5 2020 202 175.93 -1 2019 2 5 4 1 0 0 0
    5 2020 202 440.99 2 2022 1 4 4 4 1 1 0
    5 2020 202 271.33 -1 2019 1 3 3 2 1 0 0
    5 2020 202 670.18 4 2024 2 3 2 3 1 1 0
    5 2020 202 96.68 0 2020 1 6 1 1 0 1 0
    5 2020 202 499.29 4 2024 1 1 3 1 0 1 0
    5 2021 202 293.09 0 2020 2 6 4 4 0 1 0
    5 2021 202 582.12 1 2021 1 1 4 2 0 0 1
    5 2021 202 366.45 1 2021 2 2 3 2 1 0 0
    5 2021 202 560.81 4 2024 1 1 4 4 1 0 1
    5 2021 202 255.41 1 2021 1 3 1 3 0 0 0
    5 2021 202 353.41 -2 2018 2 2 3 3 0 1 0
    5 2021 202 659.49 -1 2019 2 4 4 3 1 1 0
    5 2021 202 573.6 0 2020 2 1 3 1 0 0 0
    5 2022 202 254.5 -2 2018 1 4 2 2 1 0 0
    5 2022 202 119.72 -2 2018 1 2 2 3 0 0 0
    5 2022 202 132.51 0 2020 1 5 3 1 1 0 0
    5 2022 202 554.12 1 2021 2 1 2 2 0 0 0
    5 2022 202 124.93 1 2021 2 3 3 2 1 0 0
    5 2022 202 368.09 4 2024 2 4 1 4 0 1 0
    5 2022 202 232.35 1 2021 2 5 1 1 0 0 0
    5 2022 202 408.02 -1 2019 2 6 2 3 0 1 0
;
run;

data work.brfss_clean;
    set work.brfss_raw;
    if cmiss(currentsmoker, urru, year_centered, _age_g, sexvar, _racegr3, _educag, _state) > 0 then delete;
    year = year_centered + 2020;
    label currentsmoker = "Current Smoker"
          urru = "Urban-Rural Status"
          year_centered = "Year (Centered at 2020)"
          _state = "State FIPS Code";
run;

proc sort data=work.brfss_clean;
    by _state;
run;

title "Data Summary";
proc means data=work.brfss_clean n mean;
    var currentsmoker urru year_centered;
run;

* STEP 2: MODEL 1 - URRU + YEAR_CENTERED with GEE
******************************************************************************/

title "MODEL 1: GEE Logistic Regression with State Clustering";
title2 "DV: Current Smoker | IVs: urru, year_centered | Clustering: State";

proc genmod data=work.brfss_clean descending;
    class _state urru;
    model currentsmoker = urru year_centered / dist=binomial link=logit type3;
    repeated subject=_state / type=exch covb corrw;
    estimate 'Rural vs Urban' urru 1 -1 / exp;
    ods output GEEEmpPEst=model1_params
               GEERCov=model1_rcov
               Type3=model1_type3;
    store work.model1_gee;
run;

/******************************************************************************
* STEP 3: MODEL 2 - MODEL 1 + AGE + SEX + RACE with GEE
******************************************************************************/

title "MODEL 2: GEE Logistic Regression with State Clustering";
title2 "DV: Current Smoker | IVs: urru, year_centered, age, sex, race | Clustering: State";

proc genmod data=work.brfss_clean descending;
    class _state urru _age_g sexvar _racegr3;
    model currentsmoker = urru year_centered _age_g sexvar _racegr3 / dist=binomial link=logit type3;
    repeated subject=_state / type=exch covb corrw;
    estimate 'Rural vs Urban' urru 1 -1 / exp;
    ods output GEEEmpPEst=model2_params
               GEERCov=model2_rcov
               Type3=model2_type3;
    store work.model2_gee;
run;

/******************************************************************************
* STEP 4: MODEL 3a - MODEL 2 + EDUCATION with GEE
******************************************************************************/

title "MODEL 3a: GEE Logistic Regression with State Clustering";
title2 "DV: Current Smoker | IVs: urru, year_centered, age, sex, race, education | Clustering: State";

proc genmod data=work.brfss_clean descending;
    class _state urru _age_g sexvar _racegr3 _educag;
    model currentsmoker = urru year_centered _age_g sexvar _racegr3 _educag / dist=binomial link=logit type3;
    repeated subject=_state / type=exch covb corrw;
    estimate 'Rural vs Urban' urru 1 -1 / exp;
    ods output GEEEmpPEst=model3a_params
               GEERCov=model3a_rcov
               Type3=model3a_type3;
    store work.model3a_gee;
run;

/******************************************************************************
* STEP 5: MODEL 3b - MODEL 3a + URRU*YEAR_CENTERED INTERACTION with GEE
******************************************************************************/

title "MODEL 3b: GEE Logistic Regression WITH INTERACTION and State Clustering";
title2 "DV: Current Smoker | IVs: urru*year_centered, age, sex, race, education | Clustering: State";

proc genmod data=work.brfss_clean descending;
    class _state urru _age_g sexvar _racegr3 _educag;
    model currentsmoker = urru | year_centered _age_g sexvar _racegr3 _educag / dist=binomial link=logit type3;
    repeated subject=_state / type=exch covb corrw;
    estimate 'Rural vs Urban at Year=0' urru 1 -1 / exp;
    estimate 'Interaction Effect' urru*year_centered 1 / exp;
    ods output GEEEmpPEst=model3b_params
               GEERCov=model3b_rcov
               Type3=model3b_type3;
    store work.model3b_gee;
run;

%put ================================================================;
%put GEE MODELS 1, 2, 3a, 3b COMPLETE;
%put ================================================================;
