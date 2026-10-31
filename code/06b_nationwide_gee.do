* ==============================================================================
* Step 6, second part (Stata). Nationwide survey-weighted generalized estimating
* equations (GEE) with standard errors clustered by state: the nationwide results
* that need more than the parameter table of 06_nationwide_gee.sas.
*
* Run from the repository root (run_all.ps1 does this, after 06_nationwide_gee.sas).
* Input  : data/derived/brfss_2018_2025_analytic.csv   (step 2)
* Outputs (output/models/):
*   nationwide_gee_slopes.csv     Model 3b: the urban annual change (year), the rural
*                                 annual change (year + urban-rural x year, by lincom)
*                                 and the urban-rural x year interaction, plus the
*                                 urban-rural term, each as log odds, SE, z, P, OR and
*                                 95% CI (Table 2, nationwide row; step 9)
*   nationwide_gee_quadratic.csv  Model 3b + year^2 + rural x year^2, the QUADRATIC
*                                 specification of step 7: year^2 and rural x year^2
*                                 (S1 Table, panel 1a; step 9), plus the other
*                                 urban-rural and year terms
*   fig2_nationwide_gee.csv       Fig 2, nationwide panel: predicted probability of
*                                 current smoking by year and urban-rural status from
*                                 Model 3b, with 95% CIs, and the unadjusted prevalence
*                                 (step 12 copies these rows into fig2_plotted_values.csv)
*
* Estimator. The same as 06_nationwide_gee.sas: PROC GENMOD with WEIGHT _LLCPWT,
* REPEATED SUBJECT=_STATE / TYPE=IND and empirical ("robust") standard errors.
*   - With an independence working correlation the GEE estimating equations are the
*     weighted logistic score equations, sum_i w_i x_i (y_i - mu_i) = 0, so
*         glm ... [pweight=_llcpwt], family(binomial) link(logit) vce(cluster _state)
*     gives the GENMOD point estimates (which are also those of the survey logistic
*     models of steps 5 and 7, fit with the same weights).
*   - Both programs use the cluster sandwich variance
*         V = c * inv(B) * (sum_g u_g u_g') * inv(B),
*         B   = sum_i w_i mu_i (1 - mu_i) x_i x_i'
*         u_g = sum over the respondents i in state g of w_i (y_i - mu_i) x_i
*     GENMOD's empirical variance has no small-sample factor (c = 1). Stata's
*     vce(cluster) uses c = G/(G-1), with G the number of clusters (51 here, so its
*     standard errors are about 1% larger). The program gee_rescale multiplies e(V)
*     by (G-1)/G and reposts it, so _se[], lincom and margins all use GENMOD's
*     empirical variance.
*   - The program gee_check recomputes the c = 1 sandwich directly from the data in
*     Mata and stops the run (r(9)) if any standard error differs from the rescaled
*     e(V) by more than 1e-5 (relative). Step 9 also checks the Model 3b estimates and
*     standard errors against 06_nationwide_gee.sas.
*   - States are the clusters; the BRFSS strata and PSUs are not used (as in GENMOD).
*     The weights enter only through w_i, so their scale does not matter.
*   - 95% CIs are estimate +/- 1.96 SE on the log-odds scale, as in the SAS steps;
*     P values are from the normal distribution.
*   - Fig 2 uses the same margins command as step 12 does for the state panels
*     (margins urru, at(year_centered=(-2(1)5)), predictive margins averaged over the
*     weighted estimation sample, delta-method SEs). The predicted probabilities are
*     the same as those from the svy fit; only their CIs change.
* ==============================================================================
clear all
set more off
set type double

* ---- programs -------------------------------------------------------------------
* Multiply e(V) by (G-1)/G: from Stata's vce(cluster) variance to GENMOD's
* empirical variance (see the header).
program define gee_rescale, eclass
    tempname V
    local G = e(N_clust)
    matrix `V' = e(V) * ((`G' - 1) / `G')
    ereturn repost V = `V'
    ereturn scalar gee_vfactor = (`G' - 1) / `G'
    di as txt "e(V) multiplied by (G-1)/G = " as res %8.6f e(gee_vfactor) as txt ", G = " as res `G'
end

* Recompute GENMOD's empirical variance (c = 1) in Mata and compare its standard
* errors with _se[] after gee_rescale.
*   xvars() : the model's columns as explicit variables, the constant last
*   bnames(): the matching coefficient names in e(b)
program define gee_check
    syntax, xvars(string) bnames(string)
    tempvar touse mu r a
    quietly {
        gen byte `touse' = e(sample)
        predict double `mu' if `touse', mu
        gen double `r' = _llcpwt * (currentsmoker - `mu') if `touse'
        gen double `a' = _llcpwt * `mu' * (1 - `mu') if `touse'
    }
    if `: word count `xvars'' != `: word count `bnames'' {
        di as err "gee_check: xvars() and bnames() differ in length"
        exit 198
    }
    mata: gee_sandwich("`xvars'", "`r'", "`a'", "_state", "`touse'")
    di as txt _n "Check: SE after gee_rescale vs SE from the sandwich computed in Mata (" ///
        as res GEE_G as txt " clusters)"
    local k = 0
    local worst = 0
    foreach b of local bnames {
        local ++k
        local s0 = sqrt(el(GEE_V0, `k', `k'))
        local rel = abs(_se[`b'] / `s0' - 1)
        local worst = max(`worst', `rel')
        di as txt %-26s "`b'" as res %14.8f _se[`b'] %14.8f `s0'
    }
    di as txt "largest relative difference: " as res %9.2e `worst'
    if missing(`worst') | `worst' > 1e-5 {
        di as err "the rescaled e(V) does not equal the GENMOD empirical variance"
        exit 9
    }
end

* Post one linear combination of the coefficients to the results file.
program define post_term
    args pf term expr
    tempname b se
    quietly lincom `expr'
    scalar `b' = r(estimate)
    scalar `se' = r(se)
    post `pf' ("`term'") ("`expr'") (`b') (`se') (`b' / `se') (2 * normal(-abs(`b' / `se'))) ///
        (exp(`b')) (exp(`b' - 1.96 * `se')) (exp(`b' + 1.96 * `se')) (e(N)) (e(N_clust)) (e(gee_vfactor))
end

mata:
void gee_sandwich(string scalar xvars, string scalar rv, string scalar av, string scalar gv, string scalar touse)
{
    real matrix X, r, a, g, info, U, Binv
    real scalar j

    st_view(X, ., tokens(xvars), touse)
    st_view(r, ., rv, touse)
    st_view(a, ., av, touse)
    st_view(g, ., gv, touse)
    info = panelsetup(g, 1)
    U = J(rows(info), cols(X), 0)
    for (j = 1; j <= rows(info); j++) {
        U[j, .] = cross(panelsubmatrix(r, j, info), panelsubmatrix(X, j, info))
    }
    Binv = invsym(cross(X, a, X))
    st_matrix("GEE_V0", Binv * cross(U, U) * Binv)
    st_numscalar("GEE_G", rows(info))
}
end

* ---- analytic sample: complete cases, as in step 12 and the SAS steps --------------
import delimited "data/derived/brfss_2018_2025_analytic.csv", clear asdouble
egen _nm = rowmiss(currentsmoker urru year_centered _age_g sexvar _racegr3 _educag _llcpwt _ststr _psu _state)
keep if _nm == 0
drop _nm
di "Analytic sample N = " _N
* gee_sandwich needs the respondents of each state together
sort _state, stable

* unadjusted prevalence for fig2_nationwide_gee.csv, as in step 12
preserve
collapse (mean) prev=currentsmoker [pw=_llcpwt], by(year_centered urru)
tempfile prevalence
save `prevalence'
restore

qui summarize year_centered
local ymin = r(min)
local ymax = r(max)

* explicit columns for gee_check (the factor-variable models drop the lowest level)
gen byte _one = 1
gen double _rxy = urru * year_centered
gen double year_sq = year_centered^2
gen double rural_x_yearsq = urru * year_sq
local xcov ""
local bcov ""
foreach v in _age_g sexvar _racegr3 _educag {
    quietly levelsof `v', local(levs)
    gettoken base levs : levs
    foreach l of local levs {
        gen byte _d`v'`l' = (`v' == `l')
        local xcov "`xcov' _d`v'`l'"
        local bcov "`bcov' `l'.`v'"
    }
}
local cov i._age_g i.sexvar i._racegr3 i._educag

tempname pf
tempfile slopes quadratic

* ---- Model 3b ----------------------------------------------------------------------
di _n "{hline 70}" _n "Model 3b, nationwide GEE" _n "{hline 70}"
glm currentsmoker i.urru##c.year_centered `cov' [pweight=_llcpwt], ///
    family(binomial) link(logit) vce(cluster _state)
gee_rescale
ereturn display
gee_check, xvars(urru year_centered _rxy `xcov' _one) ///
    bnames(1.urru year_centered 1.urru#c.year_centered `bcov' _cons)

postfile `pf' str16 term str40 expression double estimate double se double z double p ///
    double or double lcl double ucl long n long n_clust double vfactor using `slopes', replace
post_term `pf' urru_x_year "1.urru#c.year_centered"
post_term `pf' urban_year  "year_centered"
post_term `pf' rural_year  "year_centered + 1.urru#c.year_centered"
post_term `pf' urru        "1.urru"
postclose `pf'

* Fig 2, nationwide panel (the same margins command as step 12)
margins urru, at(year_centered=(-2(1)5))
matrix pred_mat = r(table)

* ---- Model 3b + year^2 + rural x year^2 ----------------------------------------------
di _n "{hline 70}" _n "Model 3b + year^2 + rural x year^2, nationwide GEE" _n "{hline 70}"
glm currentsmoker i.urru##c.year_centered year_sq rural_x_yearsq `cov' [pweight=_llcpwt], ///
    family(binomial) link(logit) vce(cluster _state)
gee_rescale
ereturn display
gee_check, xvars(urru year_centered _rxy year_sq rural_x_yearsq `xcov' _one) ///
    bnames(1.urru year_centered 1.urru#c.year_centered year_sq rural_x_yearsq `bcov' _cons)
test year_sq rural_x_yearsq

postfile `pf' str16 term str40 expression double estimate double se double z double p ///
    double or double lcl double ucl long n long n_clust double vfactor using `quadratic', replace
post_term `pf' year_sq        "year_sq"
post_term `pf' rural_x_yearsq "rural_x_yearsq"
post_term `pf' year_centered  "year_centered"
post_term `pf' rural_x_year   "1.urru#c.year_centered"
post_term `pf' urru           "1.urru"
postclose `pf'

* ---- write the results ---------------------------------------------------------------
use `slopes', clear
list term estimate se p or lcl ucl, noobs abbreviate(12)
export delimited "output/models/nationwide_gee_slopes.csv", replace

use `quadratic', clear
list term estimate se p or lcl ucl, noobs abbreviate(12)
export delimited "output/models/nationwide_gee_quadratic.csv", replace

* Fig 2 values, laid out as in step 12 (rows: year, then urban and rural)
clear
set obs 16
gen str30 entity = "Nationwide"
gen int fips = 0
gen int year_centered = .
gen byte urru = .
gen double pred = .
gen double lo = .
gen double hi = .
local obs = 1
forvalues yr = -2/5 {
    forvalues u = 0/1 {
        replace year_centered = `yr' in `obs'
        replace urru = `u' in `obs'
        replace pred = pred_mat[1, `obs'] in `obs'
        replace lo   = pred_mat[5, `obs'] in `obs'
        replace hi   = pred_mat[6, `obs'] in `obs'
        local obs = `obs' + 1
    }
}
merge 1:1 year_centered urru using `prevalence', nogenerate
foreach v in pred lo hi {
    replace `v' = . if year_centered < `ymin' | year_centered > `ymax'
}
gen int year = year_centered + 2020
order entity fips year urru pred lo hi prev
keep entity fips year urru pred lo hi prev
sort year urru
list, noobs
export delimited "output/models/fig2_nationwide_gee.csv", replace
di "NATIONWIDE GEE DONE"
