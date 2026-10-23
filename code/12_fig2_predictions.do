* ==============================================================================
* Step 12. Fig 2 values: predicted probability of current smoking by urban-rural
* status, 2018-2025 (Model 3b), with unadjusted prevalence, nationwide and for each
* state whose urban-rural x year interaction is significant after Benjamini-Hochberg
* false discovery rate adjustment (q < .05; the Table 2 rows). Step 13 draws Fig 2
* from the values written here.
*
* Run from the repository root (run_all.ps1 does this).
* Inputs : data/derived/brfss_2018_2025_analytic.csv   (step 2)
*          output/models/fig2_entities.do              (step 9: panels and q labels)
* Output : output/models/fig2_plotted_values.csv       (every plotted value)
*
* Notes
*   - Survey design: svyset _psu [pweight=_llcpwt], strata(_ststr). Single-PSU strata are
*     treated as certainty units, matching PROC SURVEYLOGISTIC in the SAS models.
*   - Prevalence dots and fitted lines use the same complete-case analytic sample.
*   - Fitted values are kept only for the years a state contributes data.
* ==============================================================================
clear all
set more off

include "output/models/fig2_entities.do"
local n_entities : word count `entity_fips'
di "Panels: `n_entities'"

* ---- import once, restrict to the analytic sample, cache ------------------------
import delimited "data/derived/brfss_2018_2025_analytic.csv", clear
egen _nm = rowmiss(currentsmoker urru year_centered _age_g sexvar _racegr3 _educag _llcpwt _ststr _psu _state)
keep if _nm == 0
drop _nm
di "Analytic sample N = " _N
compress
tempfile cc
save `cc'

* ---- estimate: predicted probabilities and prevalence for each panel -------------
tempname pf
tempfile plotted
postfile `pf' str30 entity int fips int year byte urru double pred double lo double hi double prev ///
    using `plotted', replace

local row = 1
foreach fips of local entity_fips {
    local entity_name : word `row' of `entity_names'
    di _n "{hline 70}" _n "`row'/`n_entities': `entity_name' (FIPS `fips')" _n "{hline 70}"

    use `cc', clear
    if `fips' != 0 keep if _state == `fips'
    svyset _psu [pweight=_llcpwt], strata(_ststr) singleunit(certainty)

    preserve
    collapse (mean) prev=currentsmoker [pw=_llcpwt], by(year_centered urru)
    tempfile prevalence
    save `prevalence'
    restore

    qui summarize year_centered
    local ymin = r(min)
    local ymax = r(max)

    svy: logistic currentsmoker i.urru##c.year_centered i._age_g i.sexvar i._racegr3 i._educag
    margins urru, at(year_centered=(-2(1)5))
    matrix pred_mat = r(table)

    clear
    set obs 16
    gen year_centered = .
    gen urru = .
    gen pred_prob = .
    gen ci_lower = .
    gen ci_upper = .
    local obs = 1
    forvalues yr = -2/5 {
        forvalues u = 0/1 {
            replace year_centered = `yr' in `obs'
            replace urru = `u' in `obs'
            replace pred_prob = pred_mat[1, `obs'] in `obs'
            replace ci_lower  = pred_mat[5, `obs'] in `obs'
            replace ci_upper  = pred_mat[6, `obs'] in `obs'
            local obs = `obs' + 1
        }
    }
    merge 1:1 year_centered urru using `prevalence', nogenerate
    foreach v in pred_prob ci_lower ci_upper {
        replace `v' = . if year_centered < `ymin' | year_centered > `ymax'
    }
    forvalues i = 1/`=_N' {
        post `pf' ("`entity_name'") (`fips') (`=year_centered[`i'] + 2020') (`=urru[`i']') ///
            (`=pred_prob[`i']') (`=ci_lower[`i']') (`=ci_upper[`i']') (`=prev[`i']')
    }
    local row = `row' + 1
}
postclose `pf'

use `plotted', clear
export delimited "output/models/fig2_plotted_values.csv", replace
di "FIG 2 VALUES DONE"
