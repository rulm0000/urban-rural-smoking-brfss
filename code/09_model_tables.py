"""Step 9. Turn the SAS model output into the manuscript and supplement tables.

Inputs (output/models/, from steps 5-8):
  state_params.csv, simple_slopes.csv, nationwide_gee.csv, year_spec.csv, year_test.csv,
  state_quadratic.csv
  and, to check the numbers quoted in table_captions.md, the step 3 tables
  Table1_header_numbers.txt, Table1_sample_characteristics_values.csv and state_by_year.csv

Outputs (output/tables/):
  Table2_trends_and_interaction.csv   Table 2: urban and rural annual ORs and the urban-rural x
                                      year interaction (Model 3b), with P and Benjamini-Hochberg
                                      q; rows = nationwide + states with interaction q < .05
  S2_Table_urban_rural_ORs.csv        S2 Table: urban-rural OR and 95% CI, Models 1, 2 and 3a;
                                      the "Model N q < .05" Yes/No columns mark the states
                                      printed in bold (significant after FDR adjustment)
  interaction_all_states.csv          interaction OR, P and q for all 43 states
  S3_Table_A_year_specification.csv   S3 Table, Panel A (nationwide year specification)
  S3_Table_B_state_quadratic.csv      S3 Table, Panel B (state quadratic tests: year² alone,
                                      rural x year², joint): states with P < .05 and q < .05
  results_counts.txt                  the "X of 43 states" counts quoted in the Results
  table_captions.md                   titles, notes and captions of Tables 1-2, S1-S3 Tables,
                                      Fig 1, Fig 2 and S1 Fig as they read in the manuscript
Outputs (output/models/):
  state_or_summary.csv                input for Fig 1 (OR, P and q per model and state)
  fig2_entities.do                    panels and q labels for Fig 2 (read by step 12):
                                      nationwide + states with interaction q < .05

Multiple testing: q values use the Benjamini-Hochberg false discovery rate procedure across
the 43 state-specific tests, applied separately to each family of tests: the urban-rural odds
ratio in Model 1, in Model 2 and in Model 3a, and the urban-rural x year interaction in Model 3b
(in S3 Table Panel B, each quadratic test is also its own family). A state-specific result is
significant when q < .05. The nationwide model is a single test, is not in any family, and is
judged by its unadjusted P.
"""
import os

import numpy as np
import pandas as pd
from scipy.stats import chi2, norm
from statsmodels.stats.multitest import multipletests

from common import FIPS, MODELS_DIR, TABLES_DIR, ensure_dirs, fmt_p, num

NAMES = dict(FIPS)
NAMES[0] = "Nationwide"


def read_params():
    pe = pd.read_csv(os.path.join(MODELS_DIR, "state_params.csv"))
    pe["Variable"] = pe["Variable"].astype(str).str.strip()
    pe["Model"] = pe["Model"].astype(str).str.strip()
    for c in ("Estimate", "StdErr", "OR", "LowerCL_OR", "UpperCL_OR", "ProbChiSq"):
        pe[c] = num(pe[c]).values
    pe["State"] = pe["State_Code"].map(NAMES)
    return pe


def ci(lo, hi, d=2):
    return "(%.*f, %.*f)" % (d, lo, d, hi)


def s2_table(pe):
    """Urban-rural OR by state for Models 1, 2, 3a; nationwide row from the GEE models.
    The "q < .05" columns flag the cells printed in bold in S2 Table."""
    urru = pe[pe.Variable == "URRU"]
    s1 = urru.pivot_table(index=["State_Code", "State"], columns="Model",
                          values=["OR", "LowerCL_OR", "UpperCL_OR", "ProbChiSq"], aggfunc="first")
    s1.columns = [a + "_M" + b for a, b in s1.columns]
    s1 = s1.reset_index().sort_values("State_Code")
    # Benjamini-Hochberg q values across the 43 state-specific tests, separately for each model
    # (the same family definition as the interaction tests). The nationwide row is not in a family.
    states = s1.State_Code != 0
    for m in ("1", "2", "3"):
        s1["q_M" + m] = np.nan
        s1.loc[states, "q_M" + m] = multipletests(s1.loc[states, "ProbChiSq_M" + m].values,
                                                  alpha=0.05, method="fdr_bh")[1]

    g = pd.read_csv(os.path.join(MODELS_DIR, "nationwide_gee.csv"))
    g["Variable"] = g["Variable"].astype(str).str.strip()
    g["Model"] = g["Model"].astype(str).str.strip()
    g["P"] = num(g["ProbZ"]).values
    gu = g[g.Variable.str.upper() == "URRU"].set_index("Model")
    # the S2 Table note states "All nationwide P < .001"
    assert (gu.loc[["1", "2", "3"], "P"] < .001).all(), "a nationwide urban-rural P is >= .001"

    models = (("1", "Model 1"), ("2", "Model 2"), ("3", "Model 3a"))
    rows = []
    r = {"State": "Nationwide"}
    for m, lab in models:
        x = gu.loc[m]
        r[lab + " OR"] = "%.2f" % x.OR
        r[lab + " 95% CI"] = ci(x.LowerCL_OR, x.UpperCL_OR)
    for m, lab in models:
        r[lab + " q < .05"] = "–"          # not in an FDR family
    rows.append(r)
    for _, x in s1[s1.State_Code != 0].iterrows():
        r = {"State": x.State}
        for m, lab in models:
            r[lab + " OR"] = "%.2f" % x["OR_M" + m]
            r[lab + " 95% CI"] = ci(x["LowerCL_OR_M" + m], x["UpperCL_OR_M" + m])
        for m, lab in models:
            r[lab + " q < .05"] = "Yes" if x["q_M" + m] < .05 else "No"
        rows.append(r)
    pd.DataFrame(rows).to_csv(os.path.join(TABLES_DIR, "S2_Table_urban_rural_ORs.csv"), index=False,
                              encoding="utf-8-sig")
    return s1, gu


def interaction_table(pe):
    ib = pe[(pe.Variable == "year_centered*URRU") & (pe.Model == "3b")].copy()
    st = ib[ib.State_Code != 0].copy()
    st["q_BH"] = multipletests(st.ProbChiSq.values, alpha=0.05, method="fdr_bh")[1]
    nat = ib[ib.State_Code == 0].copy()
    nat["q_BH"] = np.nan
    it = pd.concat([nat, st]).sort_values("State_Code")
    it["sig_raw"] = it.ProbChiSq < .05
    it["sig_BH"] = it.q_BH < .05
    out = it[["State_Code", "State", "Estimate", "StdErr", "OR", "LowerCL_OR", "UpperCL_OR",
              "ProbChiSq", "q_BH", "sig_raw", "sig_BH"]]
    out.to_csv(os.path.join(TABLES_DIR, "interaction_all_states.csv"), index=False)
    return it


def simple_slopes(pe, it):
    """Urban slope = year_centered coefficient of Model 3b (urban is the reference level).
    Rural slope = ESTIMATE 'URRU=1' (year + interaction), checked against the coefficients."""
    yc = pe[(pe.Variable == "year_centered") & (pe.Model == "3b")].set_index("State_Code")
    ib = it.set_index("State_Code")
    sl = pd.read_csv(os.path.join(MODELS_DIR, "simple_slopes.csv"))
    for c in ("Estimate", "StdErr"):
        sl[c] = num(sl[c]).values
    rur = sl[sl.Label.astype(str).str.contains("URRU=1")].set_index("State_Code")
    diff = (rur.Estimate - (yc.Estimate + ib.Estimate)).abs().max()
    assert diff < 2e-3, "rural slope does not equal year + interaction (max diff %g)" % diff

    t = pd.DataFrame({"State_Code": yc.index})
    for g, est, se in (("Urban", yc.Estimate, yc.StdErr), ("Rural", rur.Estimate, rur.StdErr)):
        e, s = t.State_Code.map(est), t.State_Code.map(se)
        t[g + "_OR"] = np.exp(e).values
        t[g + "_LCL"] = np.exp(e - 1.96 * s).values
        t[g + "_UCL"] = np.exp(e + 1.96 * s).values
        t[g + "_P"] = 2 * (1 - norm.cdf(np.abs((e / s).values)))
    return t.set_index("State_Code")


def table2(it, sl):
    """Rows: nationwide + the states whose interaction is significant after FDR adjustment."""
    keep = it[(it.State_Code == 0) | it.sig_BH].sort_values("State_Code")
    rows = []
    for _, x in keep.iterrows():
        s = sl.loc[x.State_Code]
        rows.append({
            "State": x.State,
            "Urban OR": "%.2f" % s.Urban_OR, "Urban 95% CI": ci(s.Urban_LCL, s.Urban_UCL),
            "Rural OR": "%.2f" % s.Rural_OR, "Rural 95% CI": ci(s.Rural_LCL, s.Rural_UCL),
            "Interaction OR": "%.3f" % x.OR, "Interaction 95% CI": ci(x.LowerCL_OR, x.UpperCL_OR, 3),
            "P": fmt_p(x.ProbChiSq), "q": "–" if pd.isna(x.q_BH) else fmt_p(x.q_BH),
        })
    pd.DataFrame(rows).to_csv(os.path.join(TABLES_DIR, "Table2_trends_and_interaction.csv"),
                              index=False, encoding="utf-8-sig")
    return keep


def fig_inputs(s1, it, keep):
    ib = it.set_index("State_Code")
    chor = pd.DataFrame({"State_Code": s1.State_Code.values, "State": s1.State.values})
    for m in ("1", "2", "3"):
        chor["OR_Model" + m] = s1["OR_M" + m].values
        chor["PValue_Model" + m] = s1["ProbChiSq_M" + m].values
        chor["QValue_Model" + m] = s1["q_M" + m].values
    chor["OR_Model3b_interaction"] = chor.State_Code.map(ib.OR)
    chor["PValue_Model3b_interaction"] = chor.State_Code.map(ib.ProbChiSq)
    chor.to_csv(os.path.join(MODELS_DIR, "state_or_summary.csv"), index=False)

    # Fig 2 panels: the Table 2 rows (nationwide + states with an interaction q < .05).
    # Label: q for the states; unadjusted P for the nationwide model (not in an FDR family).
    def pq(v, sym):
        return "%s < .001" % sym if v < .001 else "%s = %s" % (sym, ("%.3f" % v).lstrip("0"))
    fips, names, labels = [], [], []
    for _, x in keep.iterrows():
        fips.append(str(int(x.State_Code)))
        names.append('"%s"' % x.State)
        labels.append(pq(x.ProbChiSq, "P") if pd.isna(x.q_BH) else pq(x.q_BH, "q"))
    lines = ["* Written by 09_model_tables.py from the model output. Do not edit by hand.",
             'local entity_fips "%s"' % " ".join(fips),
             "local entity_names `\" %s \"'" % " ".join(names)]
    lines += ['local s%d "%s"' % (i + 1, l) for i, l in enumerate(labels)]
    open(os.path.join(MODELS_DIR, "fig2_entities.do"), "w").write("\n".join(lines) + "\n")


def s3_tables():
    # P values from the Wald chi-square itself: SAS rounds ProbChiSq to four decimals, which can
    # flip the third decimal (e.g. .7875 printed for P = .78753)
    ys = pd.read_csv(os.path.join(MODELS_DIR, "year_spec.csv"))
    ys["Variable"] = ys["Variable"].astype(str).str.strip()
    ys["p"] = chi2.sf(num(ys["WaldChiSq"]).values, 1)
    tst = pd.read_csv(os.path.join(MODELS_DIR, "year_test.csv"))
    tst["p"] = chi2.sf(num(tst["WaldChiSq"]).values, num(tst["NumDF"] if "NumDF" in tst else tst["DF"]).values)

    def row(spec, var, label, term):
        x = ys[(ys.Spec.str.strip() == spec) & (ys.Variable == var)].iloc[0]
        return {"Specification": label, "Term": term, "OR": "%.3f" % x.OR,
                "95% CI": ci(x.LCL, x.UCL, 3), "P": fmt_p(x.p)}
    a = [row("LINEAR", "rural_x_year", "Linear year (primary)", "Rural × year"),
         row("QUADRATIC", "rural_x_year", "Quadratic year", "Rural × year"),
         row("QUADRATIC", "rural_x_yearsq", "", "Rural × year²"),
         row("QUADRATIC", "year_sq", "", "Year²"),
         {"Specification": "", "Term": "Joint test: year² and rural × year²", "OR": "", "95% CI": "",
          "P": fmt_p(tst[tst.Label.str.strip() == "quad_joint"].p.iloc[0])}]
    pd.DataFrame(a).to_csv(os.path.join(TABLES_DIR, "S3_Table_A_year_specification.csv"),
                           index=False, encoding="utf-8-sig")

    q = pd.read_csv(os.path.join(MODELS_DIR, "state_quadratic.csv"))
    q["Label"] = q["Label"].astype(str).str.strip()
    q["p"] = num(q["ProbChiSq"]).values
    q["State"] = q["State_Code"].map(NAMES)
    # quad_year: Model 3b + year² only. quad_gap, quad_joint: Model 3b + year² + rural x year².
    # Each test is its own family of 43 state-specific tests.
    b, quad = [], {}
    for lab, test in (("quad_year", "Year² (curvature of the time trend; Model 3b plus year²)"),
                      ("quad_gap", "Rural × year² (curvature in the urban-rural difference)"),
                      ("quad_joint", "Joint test: year² and rural × year²")):
        x = q[q.Label == lab].copy()
        assert len(x) == 43, "%s: %d states" % (lab, len(x))
        x["q"] = multipletests(x.p.values, alpha=0.05, method="fdr_bh")[1]
        n = len(x)
        b.append({"Test": test, "States with P < .05": "%d/%d" % ((x.p < .05).sum(), n),
                  "States with q < .05": "%d/%d" % ((x.q < .05).sum(), n)})
        quad[lab] = x
    pd.DataFrame(b).to_csv(os.path.join(TABLES_DIR, "S3_Table_B_state_quadratic.csv"),
                           index=False, encoding="utf-8-sig")
    return quad


def counts(s1, gu, it, sl, quad):
    body = s1[s1.State_Code != 0]
    n = len(body)
    L = ["estimable states: %d" % n]
    L.append("Nationwide urban-rural OR (GEE): " + "; ".join(
        "Model %s %.2f %s, P %s" % (lab, gu.loc[m].OR, ci(gu.loc[m].LowerCL_OR, gu.loc[m].UpperCL_OR),
                                    fmt_p(gu.loc[m].P))
        for m, lab in (("1", "1"), ("2", "2"), ("3", "3a"))))
    for m, lab in (("1", "1"), ("2", "2"), ("3", "3a")):
        pc, oc = "ProbChiSq_M" + m, "OR_M" + m
        sig = body[body[pc] < .05]
        hi, lo = sig[sig[oc] > 1], sig[sig[oc] < 1]
        L.append("Model %s: significant %d/%d; rural higher %d (OR %.2f-%.2f); rural lower %d [%s]"
                 % (lab, len(sig), n, len(hi), hi[oc].min(), hi[oc].max(), len(lo),
                    "; ".join("%s %.2f" % (a, b) for a, b in zip(lo.State, lo[oc])) or "none"))
        qc = "q_M" + m
        qsig = body[body[qc] < .05]
        qhi, qlo = qsig[qsig[oc] > 1], qsig[qsig[oc] < 1]
        lost = sig[sig[qc] >= .05].sort_values("State")
        L.append("Model %s after FDR adjustment (q < .05): significant %d/%d; rural higher %d (OR %.2f-%.2f); "
                 "rural lower %d; no longer significant: %s"
                 % (lab, len(qsig), n, len(qhi), qhi[oc].min(), qhi[oc].max(), len(qlo),
                    ", ".join("%s (P %s, q %s)" % (a, fmt_p(b), fmt_p(c))
                              for a, b, c in zip(lost.State, lost[pc], lost[qc])) or "none"))
        L.append("Model %s after FDR adjustment, out of %d: rural higher %d/%d (%.1f%%; OR %.2f-%.2f); "
                 "rural lower %d (%s); not significant %d/%d (%.1f%%)"
                 % (lab, n, len(qhi), n, 100 * len(qhi) / n, qhi[oc].min(), qhi[oc].max(), len(qlo),
                    "; ".join("%s: OR %.2f, 95%% CI %s, q %s" % (a, b, ci(c, d), fmt_p(e))
                              for a, b, c, d, e in zip(qlo.State, qlo[oc], qlo["LowerCL_OR_M" + m],
                                                       qlo["UpperCL_OR_M" + m], qlo[qc])) or "none",
                    n - len(qsig), n, 100 * (n - len(qsig)) / n))
    st = it[it.State_Code != 0]
    sr, sb = st[st.sig_raw].sort_values("State"), st[st.sig_BH].sort_values("State")
    L.append("Interaction P < .05: %d/%d: %s" % (len(sr), n, ", ".join(sr.State)))
    L.append("Interaction q < .05: %d/%d: %s" % (len(sb), n, ", ".join(sb.State)))
    L.append("Interaction after FDR adjustment, out of %d: significant (q < .05; Table 2 rows and Fig 2 "
             "panels) %d/%d (%.1f%%); not significant (q >= .05) %d/%d (%.1f%%)"
             % (n, len(sb), n, 100 * len(sb) / n, n - len(sb), n, 100 * (n - len(sb)) / n))
    L.append("Significant interactions with OR < 1 (narrowing gap): %s"
             % (", ".join(sr.loc[sr.OR < 1, "State"]) or "none"))
    nr = it[it.State_Code == 0].iloc[0]
    L.append("Nationwide interaction: OR %.3f (%.3f, %.3f), P %s"
             % (nr.OR, nr.LowerCL_OR, nr.UpperCL_OR, fmt_p(nr.ProbChiSq)))
    ns = sl.loc[0]
    L.append("Nationwide annual OR: urban %.2f %s, rural %.2f %s"
             % (ns.Urban_OR, ci(ns.Urban_LCL, ns.Urban_UCL), ns.Rural_OR, ci(ns.Rural_LCL, ns.Rural_UCL)))
    for lab, test in (("quad_year", "year² alone (Model 3b + year²)"),
                      ("quad_gap", "rural × year² (Model 3b + year² + rural × year²)"),
                      ("quad_joint", "joint test of year² and rural × year² (same model)")):
        x = quad[lab].sort_values("State")
        sp, sq = x[x.p < .05], x[x.q < .05]
        L.append("State quadratic, %s: P < .05 %d/%d [%s]; q < .05 %d/%d [%s]"
                 % (test, len(sp), len(x), ", ".join(sp.State) or "none",
                    len(sq), len(x), ", ".join(sq.State) or "none"))
    txt = "\n".join(L)
    open(os.path.join(TABLES_DIR, "results_counts.txt"), "w", encoding="utf-8").write(txt + "\n")
    print(txt)


# Titles, notes and captions as they read in the revised manuscript and its supplement
# (written to output/tables/table_captions.md). One string per paragraph; "#" starts a heading.
CAPTIONS = [
    "# Table and figure captions",
    ("Titles, notes and captions of the tables and figures as they read in the revised "
     "manuscript and its supplement. Bold type in a Word table is shown in the CSV file as a "
     "Yes/No column. Written by `code/09_model_tables.py`, which checks the numbers quoted "
     "here against the analysis output."),
    "## Table 1",
    "Table body: `Table1_sample_characteristics.csv`",
    "Table 1. Sample demographic characteristics (N = 3,054,432), BRFSS 2018-2025",
    ("Note. We present only the complete-case analytic sample in this table. Sample sizes are "
     "unweighted. Percentages (%) and smoking prevalences are weighted. The unweighted sample "
     "sizes across the 43 states included in state-specific analyses ranged from 18,294 "
     "(Nevada) to 176,783 (New York) respondents. Within states, the rural sample sizes ranged "
     "from 546 (Nevada) to 45,875 (Maine) respondents, and urban sample sizes ranged from "
     "17,748 (Nevada) to 161,879 (New York) respondents. “Smoking prevalence” is the "
     "percentage of current cigarette smokers within the total sample for each subgroup. For "
     "example, 6.4% of the total weighted sample lived in rural counties, and 18.6% of adults "
     "in those counties were current smokers."),
    "## Fig 1",
    "Figure: `output/figures/Fig1.tif`",
    ("Fig 1. Differences in urban-rural cigarette smoking in US states, 2018-2025. Each state "
     "is shown as a square of equal size in its approximate geographic position."),
    ("Notes. OR = Odds Ratio. Odds of smoking were higher among rural residents in "
     "darker-colored states. States with non-significant rural to urban odds ratios (q ≥ .05 "
     "after false discovery rate adjustment across the 43 state-specific tests for each model) "
     "or insufficient rural sample sizes (n < 50) for analysis are in light and dark grey, "
     "respectively."),
    "## Table 2",
    "Table body: `Table2_trends_and_interaction.csv`",
    ("Table 2. Linear time trends in current smoking among urban and rural groups, and the "
     "urban-rural by year interaction (Model 3b)"),
    ("Note. OR = Odds Ratio, CI = Confidence Interval. Urban and rural odds ratios are the "
     "annual change in the odds of current smoking from Model 3b. The odds ratio for the "
     "interaction term (urban-rural × year) is from Model 3b and indicates the yearly rural "
     "odds ratio divided by the yearly urban odds ratio; when values are above 1, this "
     "indicates that the odds of smoking declined more slowly among rural than urban "
     "residents. P = unadjusted p-value for the interaction. q = Benjamini-Hochberg false "
     "discovery rate adjusted p-value across the 43 state-specific interaction tests. Example "
     "interpretation: In Washington, the odds of smoking decreased by 7% each year (OR = 0.93, "
     "95% CI: 0.92, 0.94) among urban residents, but did not decrease significantly (OR = "
     "1.01, 95% CI: 0.97, 1.06) for rural residents. The interaction OR of 1.091 (95% CI: "
     "1.040, 1.145) demonstrates that the yearly rural odds ratio was 9% higher than the "
     "yearly urban odds ratio. States shown are those with a significant interaction after "
     "false discovery rate adjustment (q < .05)."),
    "## Fig 2",
    "Figure: `output/figures/Fig2.tif`",
    ("Fig 2. Predicted probabilities (lines) from logistic regression Model 3b and unadjusted "
     "prevalences (dots) of current smoking in rural (red) and urban (blue) counties "
     "nationwide and in states with significant interaction terms after false discovery rate "
     "adjustment (q < .05), 2018-2025. Shaded bands are 95% CIs. The Benjamini-Hochberg false "
     "discovery rate adjusted p-value (q) for the urban-rural × year interaction (unadjusted P "
     "for the nationwide model) is shown in the lower right of each panel."),
    "## S1 Table",
    ("Table body: `S1_Table_state_prevalence.csv` (in the Word table the Nationwide row is "
     "bold)"),
    "In the supplement file:",
    ("S1 Table. State-level smoking prevalence estimates in rural and urban counties, 2018 and "
     "2025."),
    ("Note. Weighted prevalence of current cigarette smoking among the complete-case analytic "
     "sample; respondents with missing smoking status are excluded from both numerator and "
     "denominator. CI = confidence interval. A dash indicates that the estimate was suppressed "
     "because the unweighted sample size was less than 50 or the relative standard error "
     "exceeded 30%, or that the state did not contribute data in that year. California, "
     "Mississippi, and Nevada are not included in the 2025 BRFSS data."),
    "In the manuscript's Supporting information list:",
    ("S1 Table. State-level smoking prevalence estimates in rural and urban counties, 2018 and "
     "2025. A dash indicates that the estimate was suppressed because the relative standard "
     "error was greater than 30% or the unweighted sample size was less than 50, or that the "
     "state did not contribute data in that year."),
    "## S1 Fig",
    "Figure: `output/figures/S1_Fig.tif`",
    "In the manuscript's Supporting information list:",
    ("S1 Fig. State-level smoking prevalence estimates in rural and urban counties. The maps "
     "show smoking prevalence estimates for 2018 (left panels) and 2025 (right panels) in "
     "rural (top panels) and urban (bottom panels) counties. Higher prevalence is indicated by "
     "red and lower prevalence by green. State estimates are excluded (grey) if the unweighted "
     "sample size was less than 50, the relative standard error was greater than 30%, or the "
     "state was not included in the BRFSS data for that year."),
    "## S2 Table",
    ("Table body: `S2_Table_urban_rural_ORs.csv` (an OR and its 95% CI are bold when the "
     "matching \"Model N q < .05\" column is Yes)"),
    "In the supplement file:",
    ("S2 Table. Odds ratios for the urban-rural variable in the nationwide and state-specific "
     "logistic regression models, 2018-2025"),
    ("Note. For nationwide analyses, we used generalized estimating equations with state-level "
     "cluster-robust standard errors to account for clustering of observations within states. "
     "All nationwide P < .001. Bold indicates that the state-specific odds ratio was "
     "significant after Benjamini-Hochberg false discovery rate adjustment (q < .05) across "
     "the 43 state-specific tests for that model."),
    "In the manuscript's Supporting information list:",
    ("S2 Table. Odds ratios for the urban-rural variable in the nationwide and state-specific "
     "logistic regression models."),
    "## S3 Table",
    "In the supplement file:",
    ("S3 Table. Sensitivity analyses: quadratic specification of survey year, nationwide "
     "(Panel A) and within states (Panel B)."),
    "Panel A. Specification of survey year, nationwide Model 3b",
    "Table body: `S3_Table_A_year_specification.csv`",
    ("Note. Rural × year and rural × year² are ratios of the rural-to-urban odds ratio per "
     "year and per year². Values greater than 1 suggest a wider urban-rural difference. Year² "
     "indicates the curvature of the time trend. The joint test assesses both year² and rural "
     "× year² together. Models adjust for age, sex, race/ethnicity, and education and use "
     "BRFSS complex survey design (survey weights, strata, primary sampling units)."),
    "Panel B. Quadratic time trends within states (Model 3b plus quadratic terms)",
    "Table body: `S3_Table_B_state_quadratic.csv`",
    ("Note. q-values are Benjamini-Hochberg false discovery rate adjusted for the 43 "
     "state-specific analyses. The year² row is from Model 3b plus year² only; the other two "
     "rows are from Model 3b plus year² and rural × year²."),
    "In the manuscript's Supporting information list:",
    ("S3 Table. Sensitivity analyses: quadratic specification of survey year, nationwide and "
     "within states."),
]


def captions(it, sl):
    """Write table_captions.md after checking every number it quotes against the analysis
    output (the Table 1 numbers against the step 3 tables)."""
    text = "\n\n".join(CAPTIONS)
    hdr = {}
    for line in open(os.path.join(TABLES_DIR, "Table1_header_numbers.txt"), encoding="utf-8"):
        if ":" in line:
            k, v = line.split(":", 1)
            hdr[k.strip()] = v.strip()
    t1 = pd.read_csv(os.path.join(TABLES_DIR, "Table1_sample_characteristics_values.csv"))
    rural = t1[(t1.Variable == "County") & (t1.Category == "Rural")].iloc[0]
    yrs = pd.read_csv(os.path.join(TABLES_DIR, "state_by_year.csv"), index_col="State")
    no2025 = list(yrs.index[yrs["2025"] == 0])
    wa, wi = sl.loc[53], it.set_index("State_Code").loc[53]    # Table 2 example: Washington
    assert wi.sig_BH and wa.Rural_LCL < 1 < wa.Rural_UCL
    expect = [
        "(N = %s)" % hdr["analytic sample (complete)"].split()[0],
        "state-specific analyses ranged from %s respondents" % hdr["state n range"],
        "rural sample sizes ranged from %s respondents" % hdr["rural n range"],
        "urban sample sizes ranged from %s respondents" % hdr["urban n range"],
        "%.1f%% of the total weighted sample lived in rural counties, and %.1f%% of adults"
        % (rural.Percentage, rural["Smoking prevalence"]),
        "decreased by %.0f%% each year (OR = %.2f, 95%% CI: %.2f, %.2f)"
        % (100 * (1 - wa.Urban_OR), wa.Urban_OR, wa.Urban_LCL, wa.Urban_UCL),
        "did not decrease significantly (OR = %.2f, 95%% CI: %.2f, %.2f)"
        % (wa.Rural_OR, wa.Rural_LCL, wa.Rural_UCL),
        "interaction OR of %.3f (95%% CI: %.3f, %.3f)" % (wi.OR, wi.LowerCL_OR, wi.UpperCL_OR),
        "was %.0f%% higher" % (100 * (wi.OR - 1)),
        "%s, and %s are not included in the 2025 BRFSS data" % (", ".join(no2025[:-1]), no2025[-1]),
    ]
    missing = [e for e in expect if e not in text]
    assert not missing, "table_captions.md quotes numbers that differ from the output: %s" % missing
    open(os.path.join(TABLES_DIR, "table_captions.md"), "w", encoding="utf-8").write(text + "\n")


def main():
    ensure_dirs()
    pe = read_params()
    s1, gu = s2_table(pe)
    it = interaction_table(pe)
    sl = simple_slopes(pe, it)
    keep = table2(it, sl)
    fig_inputs(s1, it, keep)
    quad = s3_tables()
    counts(s1, gu, it, sl, quad)
    captions(it, sl)
    print("wrote tables to", TABLES_DIR)


if __name__ == "__main__":
    main()
