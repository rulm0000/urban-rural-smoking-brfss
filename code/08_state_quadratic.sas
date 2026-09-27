/*==========================================================================
  Step 8. Sensitivity analysis: quadratic time trend within each of the 43 states
  (S4 Table, Panel B). Model 3b plus year squared and rural x year squared, with Wald
  tests of the quadratic terms. Survey design as in step 5.

  Output: output\models\state_quadratic.csv
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
    if nmiss(_AGE_G, SEXVAR, _RACEGR3, URRU, currentsmoker, _EDUCAG,
             _STATE, _LLCPWT, _STSTR, _PSU, year_centered) > 0 then delete;
    year_sq        = year_centered * year_centered;
    rural_x_year   = URRU * year_centered;
    rural_x_yearsq = URRU * year_sq;
run;

%let STATES = 1 2 4 5 6 8 12 13 16 17 18 19 20 21 22 23 24 26 27 28 29 30 31 32
              35 36 37 38 39 40 41 42 45 46 47 48 49 50 51 53 54 55 56;

%macro runq;
    %local i st;
    %do i = 1 %to %sysfunc(countw(&STATES));
        %let st = %scan(&STATES, &i);
        proc surveylogistic data=d;
            where _STATE = &st;
            class _AGE_G SEXVAR _RACEGR3 _EDUCAG / param=GLM;
            model currentsmoker (event='1') = URRU year_centered year_sq rural_x_year rural_x_yearsq
                                              _AGE_G SEXVAR _RACEGR3 _EDUCAG;
            weight _LLCPWT; strata _STSTR; cluster _PSU;
            quad_joint: test year_sq = 0, rural_x_yearsq = 0;
            quad_gap:   test rural_x_yearsq = 0;
            ods output TestStmts=ts;
        run;
        data ts_&st; set ts; State_Code = &st; run;
        proc datasets lib=work nolist; delete ts; quit;
    %end;
    data allq;
        set %do i = 1 %to %sysfunc(countw(&STATES)); %let st = %scan(&STATES, &i); ts_&st %end; ;
    run;
%mend;
%runq;

proc export data=allq outfile="output\models\state_quadratic.csv" dbms=csv replace; run;
