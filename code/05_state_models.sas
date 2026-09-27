/*==========================================================================
  Step 5. Survey logistic regression models, nationwide and for each of the 43 states.

  Design: BRFSS final weight (_LLCPWT), stratum (_STSTR) and primary sampling unit (_PSU),
  Taylor-series linearization (PROC SURVEYLOGISTIC).

    Model 1   urban-rural status + survey year
    Model 2   Model 1 + age, sex, race/ethnicity
    Model 3   Model 2 + education                          ("Model 3a" in the manuscript)
    Model 3b  Model 3 + urban-rural x survey year interaction,
              with the annual change in the odds of smoking for urban and rural residents

  Outputs (output\models\):
    state_params.csv   URRU, year_centered and year_centered*URRU estimates, entity x model
    simple_slopes.csv  ESTIMATE statements for the urban and rural annual change (Model 3b)
==========================================================================*/
options nosource nonotes;
ods listing close; ods results off;

data _null_;
    length p $1024;
    p = getoption('sysin');
    p = substr(p, 1, find(p, '\code\', 'i', -length(p)) - 1);
    rc = dlgcdir(p);
    put 'NOTE: working folder ' p;
run;
libname der "data\derived";

data d;
    set der.brfss;
    keep _STATE _PSU _STSTR _LLCPWT year_centered SEXVAR _AGE_G _RACEGR3 _EDUCAG URRU currentsmoker;
    if nmiss(_AGE_G, SEXVAR, _RACEGR3, URRU, currentsmoker, _EDUCAG,
             _STATE, _LLCPWT, _STSTR, _PSU, year_centered) > 0 then delete;
run;

/* 0 = nationwide, then the 43 states with rural respondents (FIPS codes) */
%let ENTITIES = 0 1 2 4 5 6 8 12 13 16 17 18 19 20 21 22 23 24 26 27 28 29 30 31 32
                35 36 37 38 39 40 41 42 45 46 47 48 49 50 51 53 54 55 56;

%macro fit(ent=, mnum=, cls=, model=, slopes=0);
    proc surveylogistic data=d;
        %if &ent ne 0 %then %do; where _STATE = &ent; %end;
        class URRU (ref='0') &cls / param=GLM;
        model currentsmoker (event='1') = &model;
        weight _LLCPWT; strata _STSTR; cluster _PSU;
        %if &slopes %then %do;
            estimate "Year slope URRU=0" year_centered 1 / exp cl;
            estimate "Year slope URRU=1" year_centered 1 year_centered*URRU 1 / exp cl;
            ods output Estimates=est;
        %end;
        ods output ParameterEstimates=pe;
    run;
    data pe_&ent._&mnum;
        length Model $3 Variable $32;
        set pe;
        State_Code = &ent; Model = "&mnum";
        if Variable in ("URRU", "year_centered", "year_centered*URRU") and Estimate ne 0;
        OR = exp(Estimate); LowerCL_OR = exp(Estimate - 1.96*StdErr); UpperCL_OR = exp(Estimate + 1.96*StdErr);
        keep State_Code Model Variable Estimate StdErr OR LowerCL_OR UpperCL_OR ProbChiSq;
    run;
    proc datasets lib=work nolist; delete pe; quit;
    %if &slopes %then %do;
        data es_&ent;
            length Label $40;
            set est;
            State_Code = &ent;
            keep State_Code Label Estimate StdErr ExpEstimate LowerExp UpperExp ProbChiSq;
        run;
        proc datasets lib=work nolist; delete est; quit;
    %end;
%mend;

%macro runall;
    %local i e;
    %do i = 1 %to %sysfunc(countw(&ENTITIES));
        %let e = %scan(&ENTITIES, &i);
        %put NOTE: entity &e;
        %fit(ent=&e, mnum=1,  cls=,                                 model=URRU year_centered);
        %fit(ent=&e, mnum=2,  cls=_AGE_G SEXVAR _RACEGR3,           model=URRU year_centered _AGE_G SEXVAR _RACEGR3);
        %fit(ent=&e, mnum=3,  cls=_AGE_G SEXVAR _RACEGR3 _EDUCAG,   model=URRU year_centered _AGE_G SEXVAR _RACEGR3 _EDUCAG);
        %fit(ent=&e, mnum=3b, cls=_AGE_G SEXVAR _RACEGR3 _EDUCAG,
             model=year_centered URRU year_centered*URRU _AGE_G SEXVAR _RACEGR3 _EDUCAG, slopes=1);
    %end;
    data params;
        set %do i = 1 %to %sysfunc(countw(&ENTITIES)); %let e = %scan(&ENTITIES, &i);
                pe_&e._1 pe_&e._2 pe_&e._3 pe_&e._3b %end; ;
    run;
    data slopes;
        set %do i = 1 %to %sysfunc(countw(&ENTITIES)); %let e = %scan(&ENTITIES, &i); es_&e %end; ;
    run;
%mend;
%runall;

proc export data=params outfile="output\models\state_params.csv"  dbms=csv replace; run;
proc export data=slopes outfile="output\models\simple_slopes.csv" dbms=csv replace; run;
