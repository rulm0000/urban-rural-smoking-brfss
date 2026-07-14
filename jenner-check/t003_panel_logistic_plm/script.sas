/* Predicted-probability panel (Model 3b, URRU x year_centered interaction) via
   PROC LOGISTIC with STORE, PROC PLM scoring (score ... / ilink), a PROC SQL join of
   predictions to weighted prevalence, and a PROC SGPANEL panel — from sas_panel_final.sas.
   The per-entity PROC LOGISTIC/STORE/PLM blocks, the weighted-means scoring grid, the
   prevalence PROC MEANS, the SQL merge and the SGPANEL are unchanged from the source.
   Adaptations for a self-contained run: the PROC IMPORT of data/combinedbrfss_18_24v10.csv
   is replaced with an inline DATA step building the same brfss dataset from a synthetic
   BRFSS-shaped sample (not real CDC data), and the entity list is limited to the states
   present in that sample (Nationwide + Arizona + Arkansas). */

%let outdir = .;
ods graphics on / width=1200px height=900px imagename="sas_panel_entities" imagefmt=png;

data brfss;
    input _STATE _PSU _STSTR _LLCPWT year_centered IYEAR SEXVAR _AGE_G _RACEGR3 _EDUCAG URRU currentsmoker Quit;
    datalines;
    4 411 41 199.04 1 2021 1 1 3 4 1 0 1
    4 411 41 520.21 -2 2018 1 1 4 1 1 1 0
    4 411 41 487.91 -1 2019 2 1 3 1 1 0 0
    4 411 41 584.85 3 2023 2 6 3 3 0 0 0
    4 411 41 497.49 -1 2019 2 6 4 2 0 0 0
    4 411 41 250.85 1 2021 1 5 1 1 0 1 0
    4 411 41 361.93 0 2020 2 5 1 3 1 0 0
    4 411 41 283.52 3 2023 1 3 1 1 0 0 0
    4 411 41 338.06 1 2021 1 6 4 2 0 0 1
    4 411 41 665.68 4 2024 1 2 1 2 0 0 1
    4 411 41 199.85 4 2024 1 6 3 1 1 1 0
    4 411 41 144.17 0 2020 2 3 2 4 0 1 0
    4 412 41 87.3 1 2021 1 6 3 1 0 1 0
    4 412 41 476.5 -2 2018 2 6 2 4 1 0 0
    4 412 41 420.96 0 2020 2 5 4 4 0 0 0
    4 412 41 182.5 2 2022 1 1 2 3 1 0 0
    4 412 41 82.44 4 2024 1 3 2 4 0 0 0
    4 412 41 358.58 4 2024 1 1 4 2 1 0 1
    4 412 41 424.64 2 2022 2 1 3 4 1 0 0
    4 412 41 91.07 4 2024 1 3 2 1 1 0 0
    4 412 41 267.35 1 2021 2 5 3 3 1 1 0
    4 412 41 627.7 4 2024 2 2 1 4 1 0 0
    4 412 41 310.05 0 2020 1 6 4 2 1 0 1
    4 412 41 565.34 4 2024 2 1 4 1 1 1 0
    4 421 42 204.26 4 2024 2 2 1 4 0 1 0
    4 421 42 128.53 2 2022 1 5 2 4 0 0 1
    4 421 42 533.77 -1 2019 1 1 2 1 0 0 1
    4 421 42 98.18 2 2022 2 6 1 1 1 0 1
    4 421 42 217.94 1 2021 1 1 2 2 1 0 0
    4 421 42 689.07 1 2021 2 6 2 3 1 0 0
    4 421 42 550.13 1 2021 2 3 3 1 0 0 0
    4 421 42 536.28 -2 2018 2 2 4 4 0 1 0
    4 421 42 263.67 0 2020 2 2 3 2 1 1 0
    4 421 42 584.56 2 2022 2 4 4 1 0 0 0
    4 421 42 317.12 1 2021 1 4 4 1 0 0 0
    4 421 42 519.46 0 2020 1 6 4 4 0 0 0
    4 422 42 416.35 4 2024 1 6 2 1 1 0 0
    4 422 42 90.99 3 2023 2 1 4 2 0 0 1
    4 422 42 645.59 0 2020 1 5 3 3 0 0 0
    4 422 42 493.57 -2 2018 1 3 2 2 1 0 0
    4 422 42 676.43 4 2024 2 6 3 1 0 0 0
    4 422 42 473.8 0 2020 2 6 1 3 0 0 0
    4 422 42 117.95 4 2024 1 2 2 2 0 1 0
    4 422 42 108.4 2 2022 1 3 4 1 0 0 0
    4 422 42 640.5 3 2023 1 2 1 3 0 0 0
    4 422 42 525.22 0 2020 2 1 1 4 1 1 0
    4 422 42 588.53 -1 2019 1 2 3 1 0 1 0
    4 422 42 452.38 2 2022 2 5 2 2 0 0 0
    5 511 51 207.18 -2 2018 2 1 1 2 0 0 0
    5 511 51 214.6 0 2020 1 3 2 2 1 0 0
    5 511 51 311.09 3 2023 1 3 1 2 0 0 1
    5 511 51 517.65 0 2020 2 1 1 2 0 0 1
    5 511 51 493.2 4 2024 1 3 4 4 1 0 0
    5 511 51 654.71 -2 2018 1 6 2 1 1 1 0
    5 511 51 169.15 1 2021 1 6 1 3 1 0 0
    5 511 51 529.53 2 2022 2 2 4 2 1 1 0
    5 511 51 113.81 1 2021 2 1 3 1 0 0 0
    5 511 51 458.72 -2 2018 1 6 3 2 1 1 0
    5 511 51 212.61 0 2020 1 4 1 3 1 0 1
    5 511 51 309.5 3 2023 1 5 4 3 0 0 0
    5 512 51 120.31 0 2020 2 5 1 4 0 0 0
    5 512 51 142.71 0 2020 1 1 1 4 0 0 0
    5 512 51 451.22 4 2024 2 3 4 2 1 0 0
    5 512 51 484.43 4 2024 1 5 2 1 1 0 0
    5 512 51 629.05 4 2024 1 4 3 4 0 1 0
    5 512 51 381.45 -2 2018 1 6 3 2 0 1 0
    5 512 51 341.15 -1 2019 2 3 4 4 0 0 0
    5 512 51 616.75 4 2024 1 1 4 1 0 0 0
    5 512 51 204.78 -2 2018 1 3 2 2 0 0 1
    5 512 51 124.14 -2 2018 2 2 2 2 0 0 0
    5 512 51 513.7 3 2023 1 1 3 1 0 0 0
    5 512 51 138.17 -2 2018 1 6 2 3 1 0 1
    5 521 52 608.16 4 2024 1 1 2 2 0 1 0
    5 521 52 393.53 2 2022 2 4 1 1 1 0 1
    5 521 52 547.5 2 2022 2 1 2 3 1 0 1
    5 521 52 653.36 4 2024 2 4 1 2 0 1 0
    5 521 52 641.25 1 2021 2 6 3 2 1 1 0
    5 521 52 439.57 3 2023 2 1 4 4 0 0 0
    5 521 52 431.84 2 2022 1 2 4 1 0 1 0
    5 521 52 579.46 4 2024 2 4 1 4 0 1 0
    5 521 52 401.52 -2 2018 2 1 2 4 0 0 0
    5 521 52 310.99 4 2024 2 2 2 2 0 0 0
    5 521 52 433.87 -1 2019 2 2 1 1 1 0 0
    5 521 52 592.32 -1 2019 2 2 1 4 1 1 0
    5 522 52 573.23 1 2021 2 5 1 1 1 1 0
    5 522 52 621.61 -1 2019 1 3 2 3 1 0 0
    5 522 52 452.12 -1 2019 2 3 3 2 0 1 0
    5 522 52 317.12 2 2022 1 3 2 1 0 1 0
    5 522 52 233.16 -1 2019 1 3 3 1 0 0 1
    5 522 52 226.74 0 2020 2 2 3 1 1 0 0
    5 522 52 566.13 3 2023 2 5 2 2 1 0 0
    5 522 52 507.69 1 2021 1 3 4 1 1 1 0
    5 522 52 348.38 4 2024 1 5 1 3 0 0 1
    5 522 52 293.17 3 2023 2 6 4 3 1 0 0
    5 522 52 318.66 -1 2019 2 3 2 4 1 0 0
    5 522 52 401.78 -2 2018 2 1 2 3 0 0 0
;
run;

data brfss;
    set brfss;
    if nmiss(_AGE_G, SEXVAR, _RACEGR3, URRU, currentsmoker, _EDUCAG, _STATE, _LLCPWT, _PSU, _STSTR, year_centered) = 0;
run;

* Get weighted means;
proc means data=brfss noprint;
    var _AGE_G SEXVAR _RACEGR3 _EDUCAG;
    weight _LLCPWT;
    output out=means mean=;
run;

* Create scoring dataset;
data score;
    set means(keep=_AGE_G SEXVAR _RACEGR3 _EDUCAG);
    _AGE_G = round(_AGE_G);
    SEXVAR = round(SEXVAR);
    _RACEGR3 = round(_RACEGR3);
    _EDUCAG = round(_EDUCAG);
    do URRU = 0, 1;
        do year_centered = -2 to 4;
            output;
        end;
    end;
run;

* Nationwide - create initial preds dataset;
data temp; set brfss; run;
proc logistic data=temp noprint;
    class URRU (ref='0') _AGE_G SEXVAR _RACEGR3 _EDUCAG / param=glm;
    model currentsmoker (event='1') = URRU year_centered _AGE_G SEXVAR _RACEGR3 _EDUCAG URRU*year_centered;
    weight _LLCPWT;
    store model_store;
run;
proc plm restore=model_store noinfo;
    score data=score out=s / ilink;
run;
data s; set s; rename Predicted=P_1 Lower=Lower_1 Upper=Upper_1; run;
data preds; length entity $30; set s; entity= "Nationwide" ; row=1; run;

* Arizona;
data temp; set brfss; where _STATE=4; run;
proc logistic data=temp noprint;
    class URRU (ref='0') _AGE_G SEXVAR _RACEGR3 _EDUCAG / param=glm;
    model currentsmoker (event='1') = URRU year_centered _AGE_G SEXVAR _RACEGR3 _EDUCAG URRU*year_centered;
    weight _LLCPWT;
    store model_store;
run;
proc plm restore=model_store noinfo;
    score data=score out=s / ilink alpha=0.05;
run;
data s; set s; rename Predicted=P_1 LowerCLMean=Lower_1 UpperCLMean=Upper_1; entity= "Arizona" ; row=2; run;
proc append base=preds data=s; run;

* Arkansas;
data temp; set brfss; where _STATE=5; run;
proc logistic data=temp noprint;
    class URRU (ref='0') _AGE_G SEXVAR _RACEGR3 _EDUCAG / param=glm;
    model currentsmoker (event='1') = URRU year_centered _AGE_G SEXVAR _RACEGR3 _EDUCAG URRU*year_centered;
    weight _LLCPWT;
    store model_store;
run;
proc plm restore=model_store noinfo;
    score data=score out=s / ilink alpha=0.05;
run;
data s; set s; rename Predicted=P_1 LowerCLMean=Lower_1 UpperCLMean=Upper_1; entity= "Arkansas" ; row=3; run;
proc append base=preds data=s; run;

/* Unadjusted weighted prevalence for the sampled states */
proc means data=brfss noprint;
    class _STATE year_centered URRU;
    where _STATE in (4,5);
    var currentsmoker;
    weight _LLCPWT;
    types _STATE*year_centered*URRU;
    output out=prevalence mean=prev;
run;

data prevalence;
    set prevalence;
    year = 2020 + year_centered;
    if _STATE = 4 then entity = "Arizona";
    else if _STATE = 5 then entity = "Arkansas";
    else delete;
    if URRU = 0 then location = "Urban"; else location = "Rural";
    keep entity year location prev;
run;

* Get nationwide prevalence;
proc means data=brfss noprint;
    class year_centered URRU;
    var currentsmoker;
    weight _LLCPWT;
    types year_centered*URRU;
    output out=prev_nation mean=prev;
run;

data prev_nation;
    set prev_nation;
    year = 2020 + year_centered;
    entity = "Nationwide";
    if URRU = 0 then location =  "Urban" ;
    else location =  "Rural" ;
    keep entity year location prev;
run;

* Combine prevalence data;
data prevalence;
    set prev_nation prevalence;
run;

* Prepare predicted probabilities for plotting;
data plot_pred;
    set preds;
    year = 2020 + year_centered;
    pred = P_1;
    if URRU = 0 then location =  "Urban" ;
    else location =  "Rural" ;
    keep entity row year location pred;
run;

* Merge predictions with prevalence;
proc sql;
    create table plot as
    select a.*, b.prev
    from plot_pred as a
    left join prevalence as b
    on a.entity = b.entity and a.year = b.year and a.location = b.location;
quit;

proc sgpanel data=plot;
    panelby entity / columns=3 rows=1 novarname spacing=5 headerattrs=(size=12pt weight=bold) sort=data;
    scatter x=year y=prev / group=location markerattrs=(size=8 symbol=circlefilled);
    series x=year y=pred / group=location lineattrs=(thickness=2) name='series';
    rowaxis min=0 max=0.35 values=(0 to 0.35 by 0.05)
            label="Predicted Probability" labelattrs=(size=14pt weight=bold);
    colaxis min=2018 max=2024 values=(2018 to 2024)
            label="Year" labelattrs=(size=14pt weight=bold);
    styleattrs datacontrastcolors=(navy red) datalinepatterns=(solid dot);
    keylegend 'series' / position=bottom valueattrs=(size=12pt);
run;

ods graphics off;
%put =================================================================;
%put ANALYSIS COMPLETE;
%put =================================================================;
