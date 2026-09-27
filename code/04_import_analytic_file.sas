/*==========================================================================
  Step 4. Import the analytic CSV into a SAS dataset once, for steps 5-8.
  Input : data\derived\brfss_2018_2025_analytic.csv   (step 2)
  Output: data\derived\brfss.sas7bdat
==========================================================================*/
options nosource nonotes;

/* Set the working folder to the repository root (the parent of this program's code\ folder),
   so every path below is relative. Done in a DATA step so folder names containing quotes or
   spaces need no special handling. */
data _null_;
    length p $1024;
    p = getoption('sysin');
    p = substr(p, 1, find(p, '\code\', 'i', -length(p)) - 1);
    rc = dlgcdir(p);
    put 'NOTE: working folder ' p;
run;
libname der "data\derived";

proc import datafile="data\derived\brfss_2018_2025_analytic.csv" out=der.brfss dbms=csv replace;
    getnames=yes; guessingrows=5000;
run;

proc contents data=der.brfss short; run;
