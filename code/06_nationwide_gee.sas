/*==========================================================================
  Step 6. Nationwide models: survey-weighted generalized estimating equations
  (weight _LLCPWT) with robust standard errors clustered by state
  (REPEATED SUBJECT=_STATE, independence working correlation).
  Models 1, 2, 3 (3a) and 3b as defined in step 5. Nationwide row of S1 Table.

  Outputs (output\models\):
    nationwide_gee.csv        URRU, year and interaction terms
    nationwide_gee_full.csv   every parameter
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
    if cmiss(currentsmoker, URRU, year_centered, _AGE_G, SEXVAR, _RACEGR3, _EDUCAG, _STATE, _LLCPWT) > 0 then delete;
run;
proc sort data=d; by _STATE; run;

%macro gee(mnum=, cls=, model=);
    proc genmod data=d descending;
        class _STATE URRU(ref='0') &cls;
        model currentsmoker = &model / dist=binomial link=logit;
        weight _LLCPWT;
        repeated subject=_STATE / type=ind;
        ods output GEEEmpPEst=ge;
    run;
    data full_&mnum; length Model $3; set ge; Model="&mnum"; run;
    data r_&mnum;
        length Model $3 Variable $32;
        set ge;
        Model = "&mnum"; Variable = strip(Parm);
        if (upcase(Variable) = "URRU" or upcase(Variable) = "YEAR_CENTERED"
            or index(upcase(Variable), "URRU*YEAR") > 0 or index(upcase(Variable), "YEAR_CENTERED*URRU") > 0)
           and Estimate ne 0;
        OR = exp(Estimate); LowerCL_OR = exp(Estimate - 1.96*StdErr); UpperCL_OR = exp(Estimate + 1.96*StdErr);
        keep Model Variable Level1 Estimate StdErr OR LowerCL_OR UpperCL_OR ProbZ;
    run;
    proc datasets lib=work nolist; delete ge; quit;
%mend;

%gee(mnum=1,  cls=,                                                          model=URRU year_centered);
%gee(mnum=2,  cls=_AGE_G(ref='1') SEXVAR(ref='1') _RACEGR3(ref='1'),         model=URRU year_centered _AGE_G SEXVAR _RACEGR3);
%gee(mnum=3,  cls=_AGE_G(ref='1') SEXVAR(ref='1') _RACEGR3(ref='1') _EDUCAG(ref='1'),
              model=URRU year_centered _AGE_G SEXVAR _RACEGR3 _EDUCAG);
%gee(mnum=3b, cls=_AGE_G(ref='1') SEXVAR(ref='1') _RACEGR3(ref='1') _EDUCAG(ref='1'),
              model=URRU year_centered _AGE_G SEXVAR _RACEGR3 _EDUCAG URRU*year_centered);

data all;  set r_1 r_2 r_3 r_3b; run;
data fall; set full_1 full_2 full_3 full_3b; run;
proc export data=all  outfile="output\models\nationwide_gee.csv"      dbms=csv replace; run;
proc export data=fall outfile="output\models\nationwide_gee_full.csv" dbms=csv replace; run;
