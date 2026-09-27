* ==============================================================================
* Step 12. Fig 2: predicted probability of current smoking by urban-rural status,
* 2018-2025 (Model 3b), with unadjusted prevalence, nationwide and for each state
* with an urban-rural x year interaction P < .05.
*
* Run from the repository root (run_all.ps1 does this).
* Inputs : data/derived/brfss_2018_2025_analytic.csv   (step 2)
*          output/models/fig2_entities.do              (step 9: panels and P/q labels)
* Outputs: output/figures/Fig2.png
*          output/models/fig2_plotted_values.csv       (every plotted value)
*
* Notes
*   - Survey design: svyset _psu [pweight=_llcpwt], strata(_ststr). Single-PSU strata are
*     treated as certainty units, matching PROC SURVEYLOGISTIC in the SAS models.
*   - Prevalence dots and fitted lines use the same complete-case analytic sample.
*   - Fitted lines are drawn only over the years a state contributes data.
*   - The label in each panel gives the interaction P value and the Benjamini-Hochberg
*     q value; bold = still significant after false discovery rate adjustment.
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
gen year_centered = year - 2020
rename pred pred_prob
rename lo ci_lower
rename hi ci_upper
tempfile all
save `all'

* ---- draw the panels -------------------------------------------------------------
local row = 1
local graphs ""
foreach fips of local entity_fips {
    local entity_name : word `row' of `entity_names'
    use `all', clear
    keep if fips == `fips'

    local show_ylabel = mod(`row' - 1, 3) == 0
    if `show_ylabel' local ylabel_opt "ylabel(0(0.05)0.30, angle(0) format(%4.2f) labsize(vsmall))"
    else             local ylabel_opt "ylabel(0(0.05)0.30, nolabels noticks)"
    * year labels only on the bottom panel of each column; the other panels keep the label
    * space (labels drawn in white) so every plot region is the same size and rows line up
    local is_bottom = (`row' + 3 > `n_entities')
    if `is_bottom' local xlabel_opt `"xlabel(-2 "2018" -1 "2019" 0 "2020" 1 "2021" 2 "2022" 3 "2023" 4 "2024" 5 "2025", labsize(vsmall) angle(45))"'
    else           local xlabel_opt `"xlabel(-2 "2018" -1 "2019" 0 "2020" 1 "2021" 2 "2022" 3 "2023" 4 "2024" 5 "2025", labsize(vsmall) angle(45) labcolor(white))"'

    twoway ///
        (rarea ci_lower ci_upper year_centered if urru==0, fcolor(navy%20) lwidth(none)) ///
        (rarea ci_lower ci_upper year_centered if urru==1, fcolor(red%20)  lwidth(none)) ///
        (line pred_prob year_centered if urru==0, lcolor(navy) lwidth(medium) lpattern(solid)) ///
        (line pred_prob year_centered if urru==1, lcolor(red)  lwidth(medium) lpattern(dash)) ///
        (scatter prev year_centered if urru==0, mcolor(navy) msize(medium) msymbol(O)) ///
        (scatter prev year_centered if urru==1, mcolor(red)  msize(medium) msymbol(O)), ///
        title("`entity_name'", size(medsmall) color(black)) ///
        note("`s`row''", ring(0) position(4) size(small) color(black)) ///
        xtitle("") ytitle("") `ylabel_opt' `xlabel_opt' ///
        yscale(range(0 0.30)) xscale(range(-2.3 5.3)) ///
        legend(off) scheme(s2color) ///
        graphregion(color(white) margin(tiny)) plotregion(margin(small)) ///
        name(graph`row', replace)

    local graphs "`graphs' graph`row'"
    local row = `row' + 1
}

* ---- legend in the empty cell: invisible plots (if 0) carry the panel styles --------
clear
set obs 2
gen x = _n
gen y = _n
twoway ///
    (rarea y y x if 0, fcolor(navy%20) lwidth(none)) ///
    (rarea y y x if 0, fcolor(red%20)  lwidth(none)) ///
    (line y x if 0, lcolor(navy) lwidth(medium) lpattern(solid)) ///
    (line y x if 0, lcolor(red)  lwidth(medium) lpattern(dash)) ///
    (scatter y x if 0, mcolor(navy) msize(medium) msymbol(O)) ///
    (scatter y x if 0, mcolor(red)  msize(medium) msymbol(O)) ///
    (scatter y x, msymbol(none)), ///
    legend(order(3 "Urban, predicted probability" 4 "Rural, predicted probability" ///
                 1 "Urban, 95% CI" 2 "Rural, 95% CI" ///
                 5 "Urban, unadjusted prevalence" 6 "Rural, unadjusted prevalence") ///
           cols(1) ring(0) position(0) size(medsmall) symxsize(10) keygap(2) rowgap(1.5) region(lcolor(none))) ///
    xscale(off) yscale(off) ylabel(none) xlabel(none) xtitle("") ytitle("") ///
    title(" ", size(medsmall)) plotregion(style(none)) ///
    graphregion(color(white) margin(tiny)) name(graphleg, replace)
local graphs "`graphs' graphleg"

local nrows = ceil((`n_entities' + 1) / 3)
local ysz = max(4, 2.2 * `nrows')
graph combine `graphs', cols(3) ///
    l1title("Predicted Probability", size(small)) b1title("Year", size(small)) ///
    graphregion(color(white) margin(medium)) imargin(0.2 0.2 0.2 0.2) iscale(*0.75) ///
    ysize(`ysz') xsize(8) name(final_panel, replace)

graph export "output/figures/Fig2.png", replace width(2400)
di "FIG 2 DONE"
