"""Step 3. Descriptive tables, computed directly from the analytic file.

Outputs (output/tables/):
  Table1_sample_characteristics.csv  Table 1: weighted percentages and smoking prevalence,
                                     complete-case analytic sample
  Table1_header_numbers.txt          sample sizes and state ranges quoted in the text
  S2_Table_state_prevalence.csv      S2 Table: rural and urban smoking prevalence by state,
                                     2018 and 2025, with 95% CIs and rural/urban ratios
  S3_Table_A_sample_flow.csv         S3 Table, Panel A: exclusion steps (flow diagram)
  S3_Table_B_state_by_year.csv       S3 Table, Panel B: analytic-sample size by state and year

Prevalence estimates exclude respondents with missing smoking status from numerator and
denominator. Weighted counts in Table 1 use _LLCPWT / 8, so they describe an average annual
population. S2 Table CIs use the Kish effective sample size; estimates are suppressed when
the unweighted n < 50 or the relative standard error > 30%.
"""
import os

import numpy as np
import pandas as pd

from common import (ANALYTIC_CSV, FIPS, TABLES_DIR, TERRITORIES, ZERO_RURAL, YEARS,
                    analytic_sample, ensure_dirs)


# --------------------------------------------------------------------------- Table 1
def table1(cc, n_all):
    df = cc.copy()
    df["w"] = df["_LLCPWT"] / len(YEARS)       # average annual population (8 survey years pooled)
    W = df["w"].sum()
    df["County"] = df["URRU"].map({0: "Urban", 1: "Rural"})
    df["Age in years"] = df["_AGE_G"].map({1: "18-24", 2: "25-34", 3: "35-44", 4: "45-54",
                                           5: "55-64", 6: "65 or older"})
    df["Sex"] = df["SEXVAR"].map({1: "Male", 2: "Female"})
    df["Race/ethnicity"] = df["_RACEGR3"].map({1: "Non-Hispanic White", 2: "Non-Hispanic Black",
                                               3: "Non-Hispanic Other", 4: "Non-Hispanic Multiracial",
                                               5: "Hispanic"})
    df["Education"] = df["_EDUCAG"].map({1: "Did not graduate high school", 2: "Graduated high school",
                                         3: "Attended college or technical school",
                                         4: "Graduated from college or technical school"})
    df["Survey year"] = (df["year_centered"] + 2020).astype(int).astype(str)
    order = {
        "County": ["Urban", "Rural"],
        "Age in years": ["18-24", "25-34", "35-44", "45-54", "55-64", "65 or older"],
        "Sex": ["Female", "Male"],
        "Race/ethnicity": ["Non-Hispanic White", "Non-Hispanic Black", "Non-Hispanic Other",
                           "Non-Hispanic Multiracial", "Hispanic"],
        "Education": ["Did not graduate high school", "Graduated high school",
                      "Attended college or technical school", "Graduated from college or technical school"],
        "Survey year": [str(y) for y in YEARS],
    }
    rows = []
    for var, levels in order.items():
        for lv in levels:
            g = df[df[var] == lv]
            wsum = g["w"].sum()
            rows.append({"Variable": var, "Category": lv, "Unweighted n": len(g),
                         "Weighted n (avg annual)": round(wsum),
                         "Percentage": 100 * wsum / W,
                         "Smoking prevalence": 100 * (g["w"] * g["currentsmoker"]).sum() / wsum})
    t = pd.DataFrame(rows).round({"Percentage": 4, "Smoking prevalence": 4})
    t.to_csv(os.path.join(TABLES_DIR, "Table1_sample_characteristics.csv"), index=False)

    states = df[~df["_STATE"].isin(ZERO_RURAL)]
    per = states.groupby("_STATE").agg(n=("URRU", "size"),
                                       rural=("URRU", lambda s: int((s == 1).sum())),
                                       urban=("URRU", lambda s: int((s == 0).sum())))
    per["name"] = per.index.map(lambda f: FIPS[int(f)])
    lines = [
        f"records in pooled file      : {n_all:,}",
        f"analytic sample (complete)  : {len(df):,}  ({100 * len(df) / n_all:.1f}%)",
        f"43-state analytic sample    : {len(states):,}",
        f"weighted N (sum of _LLCPWT) : {df['_LLCPWT'].sum():,.0f}",
        f"weighted N (avg annual, /8) : {W:,.0f}",
        f"overall smoking prevalence  : {100 * (df['w'] * df['currentsmoker']).sum() / W:.1f}%",
        "",
        f"state n range   : {per.n.min():,} ({per.loc[per.n.idxmin(), 'name']}) to "
        f"{per.n.max():,} ({per.loc[per.n.idxmax(), 'name']})",
        f"rural n range   : {per.rural.min():,} ({per.loc[per.rural.idxmin(), 'name']}) to "
        f"{per.rural.max():,} ({per.loc[per.rural.idxmax(), 'name']})",
        f"urban n range   : {per.urban.min():,} ({per.loc[per.urban.idxmin(), 'name']}) to "
        f"{per.urban.max():,} ({per.loc[per.urban.idxmax(), 'name']})",
    ]
    open(os.path.join(TABLES_DIR, "Table1_header_numbers.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


# --------------------------------------------------------------------------- S3 Panel A
def sample_flow(df):
    steps = [
        ("Current smoking status missing, don't know, or refused", df.currentsmoker.notna()),
        ("Urban-rural status unavailable: US territories (not classified by NCHS)",
         ~(df.URRU.isna() & df._STATE.isin(TERRITORIES))),
        ("Urban-rural status unavailable: other", df.URRU.notna()),
        ("Race/ethnicity missing, don't know, or refused", df._RACEGR3.notna()),
        ("Education missing, don't know, or refused", df._EDUCAG.notna()),
        ("Sex missing, don't know, or refused", df.SEXVAR.notna()),
    ]
    rows = [{"Step": "BRFSS respondents, 2018-2025", "Excluded": "", "Remaining": len(df)}]
    keep = pd.Series(True, index=df.index)
    for lab, cond in steps:
        before = int(keep.sum())
        keep &= cond
        rows.append({"Step": "Excluded: " + lab, "Excluded": before - int(keep.sum()),
                     "Remaining": int(keep.sum())})
    rows.append({"Step": "Nationwide analytic sample (complete cases)", "Excluded": "",
                 "Remaining": int(keep.sum())})
    cc = df[keep]
    z = cc[cc._STATE.isin(ZERO_RURAL)]
    rows.append({"Step": "Excluded from state-specific analyses: 8 jurisdictions with no rural "
                         "respondents in 2018-2024", "Excluded": len(z), "Remaining": len(cc) - len(z)})
    rows.append({"Step": "State-specific analytic sample (43 states)", "Excluded": "",
                 "Remaining": len(cc) - len(z)})
    t = pd.DataFrame(rows)
    t["Percent of initial"] = (100 * t.Remaining / len(df)).round(1)
    t.to_csv(os.path.join(TABLES_DIR, "S3_Table_A_sample_flow.csv"), index=False)
    print(t.to_string(index=False))


# --------------------------------------------------------------------------- S2 Table
def prev_ci(g):
    w, y, n = g["_LLCPWT"], g["currentsmoker"], len(g)
    if n == 0 or w.sum() == 0:
        return pd.Series(dict(prev=np.nan, lo=np.nan, hi=np.nan, n=n, rse=np.nan, suppressed=True))
    p = (w * y).sum() / w.sum()
    neff = w.sum() ** 2 / (w ** 2).sum()
    se = np.sqrt(p * (1 - p) / neff) if neff > 0 else np.nan
    rse = 100 * se / p if p > 0 else np.inf
    lo, hi = max(0, p - 1.96 * se), min(1, p + 1.96 * se)
    return pd.Series(dict(prev=100 * p, lo=100 * lo, hi=100 * hi, n=n, rse=rse,
                          suppressed=(n < 50) or (rse > 30)))


def s2_and_availability(cc):
    df = cc.copy()
    df["year"] = (df["year_centered"] + 2020).astype(int)
    df = df[~df["_STATE"].isin(ZERO_RURAL)]

    grid = df.groupby(["_STATE", "year"]).size().unstack(fill_value=0)
    grid.index = [FIPS[int(i)] for i in grid.index]
    grid.index.name = "State"
    grid.to_csv(os.path.join(TABLES_DIR, "S3_Table_B_state_by_year.csv"))

    sub = df[df["year"].isin([2018, 2025])]
    res = sub.groupby(["_STATE", "year", "URRU"]).apply(prev_ci, include_groups=False).reset_index()
    rows = []
    for st in sorted(res["_STATE"].unique()):
        r = {"State": FIPS[int(st)]}
        for yr in (2018, 2025):
            for urru, lab in ((1, "Rural"), (0, "Urban")):
                x = res[(res._STATE == st) & (res.year == yr) & (res.URRU == urru)]
                if len(x) and not x.iloc[0].suppressed:
                    x = x.iloc[0]
                    r[f"{lab} {yr}"] = f"{x.prev:.1f} ({x.lo:.1f}, {x.hi:.1f})"
                    r[f"_{lab}_{yr}"] = x.prev
                else:
                    r[f"{lab} {yr}"] = "—"
                    r[f"_{lab}_{yr}"] = np.nan
            ru, ur = r[f"_Rural_{yr}"], r[f"_Urban_{yr}"]
            ok = pd.notna(ru) and pd.notna(ur) and ur > 0
            r[f"Ratio {yr}"] = f"{ru / ur:.2f}" if ok else "—"
            r[f"_ratio_{yr}"] = ru / ur if ok else np.nan
        d = r["_ratio_2025"] - r["_ratio_2018"]
        r["Change in ratio"] = f"{d:+.2f}" if pd.notna(d) else "—"
        yrs = grid.loc[FIPS[int(st)]]
        present = [y for y in yrs.index if yrs[y] > 0]
        r["Years available"] = f"{min(present)}-{max(present)}" + \
            ("" if len(present) == len(YEARS) else f" ({len(present)} of {len(YEARS)})")
        rows.append(r)

    nat = {"State": "Nationwide (43 states)"}
    for yr in (2018, 2025):
        for urru, lab in ((1, "Rural"), (0, "Urban")):
            x = prev_ci(sub[(sub.year == yr) & (sub.URRU == urru)])
            nat[f"{lab} {yr}"] = f"{x.prev:.1f} ({x.lo:.1f}, {x.hi:.1f})"
            nat[f"_{lab}_{yr}"] = x.prev
        nat[f"_ratio_{yr}"] = nat[f"_Rural_{yr}"] / nat[f"_Urban_{yr}"]
        nat[f"Ratio {yr}"] = f"{nat[f'_ratio_{yr}']:.2f}"
    nat["Change in ratio"] = f"{nat['_ratio_2025'] - nat['_ratio_2018']:+.2f}"
    nat["Years available"] = "2018-2025"
    rows.insert(0, nat)

    t = pd.DataFrame(rows)
    show = ["State", "Rural 2018", "Urban 2018", "Ratio 2018", "Rural 2025", "Urban 2025",
            "Ratio 2025", "Change in ratio", "Years available"]
    t[show].to_csv(os.path.join(TABLES_DIR, "S2_Table_state_prevalence.csv"), index=False,
                   encoding="utf-8-sig")
    print(t[show].head(5).to_string(index=False))


def main():
    ensure_dirs()
    df = pd.read_csv(ANALYTIC_CSV)
    cc = analytic_sample(df)
    table1(cc, len(df))
    sample_flow(df)
    s2_and_availability(cc)
    print("wrote tables to", TABLES_DIR)


if __name__ == "__main__":
    main()
