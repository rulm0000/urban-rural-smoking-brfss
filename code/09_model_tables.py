"""Step 9. Turn the SAS model output into the manuscript and supplement tables.

Inputs (output/models/, from steps 5-8):
  state_params.csv, simple_slopes.csv, nationwide_gee.csv, year_spec.csv, year_test.csv,
  state_quadratic.csv

Outputs (output/tables/):
  Table2_trends_and_interaction.csv   Table 2: urban and rural annual ORs and the urban-rural x
                                      year interaction (nationwide and states with P < .05),
                                      with Benjamini-Hochberg q values
  S1_Table_urban_rural_ORs.csv        S1 Table: urban-rural OR, Models 1, 2 and 3a
  interaction_all_states.csv          interaction OR, P and q for all 43 states
  S4_Table_A_year_specification.csv   S4 Table, Panel A
  S4_Table_B_state_quadratic.csv      S4 Table, Panel B
  results_counts.txt                  the "X of 43 states" counts quoted in the Results
Outputs (output/models/):
  state_or_summary.csv                input for Fig 1
  fig2_entities.do                    panels and P/q labels for Fig 2 (read by step 12)

Multiple testing: q values use the Benjamini-Hochberg false discovery rate procedure across
the 43 state-specific tests. The nationwide model is a single test and is not in that family.
"""
import os

import numpy as np
import pandas as pd
from scipy.stats import chi2, norm
from statsmodels.stats.multitest import multipletests

from common import FIPS, MODELS_DIR, TABLES_DIR, ensure_dirs, fmt_p, num, stars

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


def s1_table(pe):
    """Urban-rural OR by state for Models 1, 2, 3a; nationwide row from the GEE models."""
    urru = pe[pe.Variable == "URRU"]
    s1 = urru.pivot_table(index=["State_Code", "State"], columns="Model",
                          values=["OR", "LowerCL_OR", "UpperCL_OR", "ProbChiSq"], aggfunc="first")
    s1.columns = [a + "_M" + b for a, b in s1.columns]
    s1 = s1.reset_index().sort_values("State_Code")

    g = pd.read_csv(os.path.join(MODELS_DIR, "nationwide_gee.csv"))
    g["Variable"] = g["Variable"].astype(str).str.strip()
    g["Model"] = g["Model"].astype(str).str.strip()
    g["P"] = num(g["ProbZ"]).values
    gu = g[g.Variable.str.upper() == "URRU"].set_index("Model")

    rows = []
    r = {"State": "Nationwide"}
    for m, lab in (("1", "Model 1"), ("2", "Model 2"), ("3", "Model 3a")):
        x = gu.loc[m]
        r[lab + " OR"] = "%.2f%s" % (x.OR, stars(x.P))
        r[lab + " 95% CI"] = ci(x.LowerCL_OR, x.UpperCL_OR)
    rows.append(r)
    for _, x in s1[s1.State_Code != 0].iterrows():
        r = {"State": x.State}
        for m, lab in (("1", "Model 1"), ("2", "Model 2"), ("3", "Model 3a")):
            r[lab + " OR"] = "%.2f%s" % (x["OR_M" + m], stars(x["ProbChiSq_M" + m]))
            r[lab + " 95% CI"] = ci(x["LowerCL_OR_M" + m], x["UpperCL_OR_M" + m])
        rows.append(r)
    pd.DataFrame(rows).to_csv(os.path.join(TABLES_DIR, "S1_Table_urban_rural_ORs.csv"), index=False)
    return s1


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
    keep = it[(it.State_Code == 0) | it.sig_raw].sort_values("State_Code")
    rows = []
    for _, x in keep.iterrows():
        s = sl.loc[x.State_Code]
        rows.append({
            "State": x.State,
            "Urban OR": "%.2f" % s.Urban_OR, "Urban 95% CI": ci(s.Urban_LCL, s.Urban_UCL),
            "Rural OR": "%.2f" % s.Rural_OR, "Rural 95% CI": ci(s.Rural_LCL, s.Rural_UCL),
            "Interaction OR": "%.3f" % x.OR, "Interaction 95% CI": ci(x.LowerCL_OR, x.UpperCL_OR, 3),
            "P": fmt_p(x.ProbChiSq), "q": "–" if pd.isna(x.q_BH) else fmt_p(x.q_BH),
            "Significant after FDR adjustment": "" if pd.isna(x.q_BH) else ("Yes" if x.sig_BH else "No"),
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
    chor["OR_Model3b_interaction"] = chor.State_Code.map(ib.OR)
    chor["PValue_Model3b_interaction"] = chor.State_Code.map(ib.ProbChiSq)
    chor.to_csv(os.path.join(MODELS_DIR, "state_or_summary.csv"), index=False)

    # Fig 2 panels: nationwide + every state with an interaction P < .05, with P and q labels.
    # Bold label = still significant after FDR adjustment (same rule as Table 2).
    def pq(v, sym):
        return "%s < .001" % sym if v < .001 else "%s = %s" % (sym, ("%.3f" % v).lstrip("0"))
    fips, names, labels = [], [], []
    for _, x in keep.iterrows():
        fips.append(str(int(x.State_Code)))
        names.append('"%s"' % x.State)
        lab = pq(x.ProbChiSq, "P") if pd.isna(x.q_BH) else pq(x.ProbChiSq, "P") + ", " + pq(x.q_BH, "q")
        labels.append("{bf:%s}" % lab if bool(x.sig_BH) else lab)
    lines = ["* Written by 09_model_tables.py from the model output. Do not edit by hand.",
             'local entity_fips "%s"' % " ".join(fips),
             "local entity_names `\" %s \"'" % " ".join(names)]
    lines += ['local s%d "%s"' % (i + 1, l) for i, l in enumerate(labels)]
    open(os.path.join(MODELS_DIR, "fig2_entities.do"), "w").write("\n".join(lines) + "\n")


def s4_tables():
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
    pd.DataFrame(a).to_csv(os.path.join(TABLES_DIR, "S4_Table_A_year_specification.csv"),
                           index=False, encoding="utf-8-sig")

    q = pd.read_csv(os.path.join(MODELS_DIR, "state_quadratic.csv"))
    q["Label"] = q["Label"].astype(str).str.strip()
    q["p"] = num(q["ProbChiSq"]).values
    b = []
    for lab, test in (("quad_gap", "Rural × year² (curvature in the urban-rural difference)"),
                      ("quad_joint", "Joint test: year² and rural × year²")):
        x = q[q.Label == lab].copy()
        x["q"] = multipletests(x.p.values, alpha=0.05, method="fdr_bh")[1]
        n = len(x)
        b.append({"Test": test, "States with P < .05": "%d/%d" % ((x.p < .05).sum(), n),
                  "States with q < .05": "%d/%d" % ((x.q < .05).sum(), n)})
    pd.DataFrame(b).to_csv(os.path.join(TABLES_DIR, "S4_Table_B_state_quadratic.csv"),
                           index=False, encoding="utf-8-sig")


def counts(s1, it, sl):
    body = s1[s1.State_Code != 0]
    n = len(body)
    L = ["estimable states: %d" % n]
    for m, lab in (("1", "1"), ("2", "2"), ("3", "3a")):
        pc, oc = "ProbChiSq_M" + m, "OR_M" + m
        sig = body[body[pc] < .05]
        hi, lo = sig[sig[oc] > 1], sig[sig[oc] < 1]
        L.append("Model %s: significant %d/%d; rural higher %d (OR %.2f-%.2f); rural lower %d [%s]"
                 % (lab, len(sig), n, len(hi), hi[oc].min(), hi[oc].max(), len(lo),
                    "; ".join("%s %.2f" % (a, b) for a, b in zip(lo.State, lo[oc])) or "none"))
    st = it[it.State_Code != 0]
    sr, sb = st[st.sig_raw].sort_values("State"), st[st.sig_BH].sort_values("State")
    L.append("Interaction P < .05: %d/%d: %s" % (len(sr), n, ", ".join(sr.State)))
    L.append("Interaction q < .05: %d/%d: %s" % (len(sb), n, ", ".join(sb.State)))
    L.append("Significant interactions with OR < 1 (narrowing gap): %s"
             % (", ".join(sr.loc[sr.OR < 1, "State"]) or "none"))
    nr = it[it.State_Code == 0].iloc[0]
    L.append("Nationwide interaction: OR %.3f (%.3f, %.3f), P %s"
             % (nr.OR, nr.LowerCL_OR, nr.UpperCL_OR, fmt_p(nr.ProbChiSq)))
    ns = sl.loc[0]
    L.append("Nationwide annual OR: urban %.2f %s, rural %.2f %s"
             % (ns.Urban_OR, ci(ns.Urban_LCL, ns.Urban_UCL), ns.Rural_OR, ci(ns.Rural_LCL, ns.Rural_UCL)))
    txt = "\n".join(L)
    open(os.path.join(TABLES_DIR, "results_counts.txt"), "w", encoding="utf-8").write(txt + "\n")
    print(txt)


def main():
    ensure_dirs()
    pe = read_params()
    s1 = s1_table(pe)
    it = interaction_table(pe)
    sl = simple_slopes(pe, it)
    keep = table2(it, sl)
    fig_inputs(s1, it, keep)
    s4_tables()
    counts(s1, it, sl)
    print("wrote tables to", TABLES_DIR)


if __name__ == "__main__":
    main()
