/*==========================================================================
  Step 7. Sensitivity analysis: specification of survey year, nationwide Model 3b
  (S4 Table, Panel A). Survey design as in step 5.

    LINEAR       survey year as a linear term (primary analysis)
    QUADRATIC    adds year squared and rural x year squared; joint Wald test of both
    CATEGORICAL  survey year as a categorical variable; Type 3 test of rural x year

  Outputs (output\models\):
    year_spec.csv    parameter estimates, all three specifications
    year_fit.csv     fit statistics
    year_test.csv    Wald tests of the quadratic terms
    year_type3.csv   Type 3 tests, categorical-year model
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
    year           = year_centered + 2020;
run;

%let COV = _AGE_G SEXVAR _RACEGR3 _EDUCAG;

/* 1. LINEAR */
proc surveylogistic data=d;
    class &COV / param=GLM;
    model currentsmoker (event='1') = URRU year_centered rural_x_year &COV;
    weight _LLCPWT; strata _STSTR; cluster _PSU;
    ods output ParameterEstimates=pe1 FitStatistics=fit1;
run;

/* 2. QUADRATIC */
proc surveylogistic data=d;
    class &COV / param=GLM;
    model currentsmoker (event='1') = URRU year_centered year_sq rural_x_year rural_x_yearsq &COV;
    weight _LLCPWT; strata _STSTR; cluster _PSU;
    quad_joint:  test year_sq = 0, rural_x_yearsq = 0;
    quad_gap:    test rural_x_yearsq = 0;
    ods output ParameterEstimates=pe2 FitStatistics=fit2 TestStmts=test2;
run;

/* 3. CATEGORICAL year */
proc surveylogistic data=d;
    class URRU (ref='0') year (ref='2018') &COV / param=GLM;
    model currentsmoker (event='1') = URRU year URRU*year &COV;
    weight _LLCPWT; strata _STSTR; cluster _PSU;
    ods output ParameterEstimates=pe3 FitStatistics=fit3 Type3=type3_3;
run;

data allpe;
    length Spec $12 Variable $32 ClassVal0 $12 ClassVal1 $12;
    set pe1 (in=a) pe2 (in=b) pe3 (in=c);
    if a then Spec="LINEAR"; else if b then Spec="QUADRATIC"; else Spec="CATEGORICAL";
    if Estimate ne 0;
    OR  = exp(Estimate);
    LCL = exp(Estimate - 1.96*StdErr);
    UCL = exp(Estimate + 1.96*StdErr);
run;
data allfit;
    length Spec $12;
    set fit1 (in=a) fit2 (in=b) fit3 (in=c);
    if a then Spec="LINEAR"; else if b then Spec="QUADRATIC"; else Spec="CATEGORICAL";
run;

proc export data=allpe   outfile="output\models\year_spec.csv"  dbms=csv replace; run;
proc export data=allfit  outfile="output\models\year_fit.csv"   dbms=csv replace; run;
proc export data=test2   outfile="output\models\year_test.csv"  dbms=csv replace; run;
proc export data=type3_3 outfile="output\models\year_type3.csv" dbms=csv replace; run;
