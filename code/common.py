"""Shared paths and constants for the Python steps of the pipeline.

All paths are relative to the repository root, so the pipeline runs from any folder.
The raw BRFSS folder can be moved elsewhere by setting the BRFSS_RAW_DIR environment
variable (run_all.ps1 does this when you pass -RawDir).
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DIR = os.environ.get("BRFSS_RAW_DIR") or os.path.join(ROOT, "data", "raw")
DERIVED_DIR = os.path.join(ROOT, "data", "derived")
ANALYTIC_CSV = os.path.join(DERIVED_DIR, "brfss_2018_2025_analytic.csv")
CHECKSUMS = os.path.join(ROOT, "data", "SHA256SUMS")

MODELS_DIR = os.path.join(ROOT, "output", "models")    # raw SAS / Stata estimates
TABLES_DIR = os.path.join(ROOT, "output", "tables")    # manuscript and supplement tables
FIGURES_DIR = os.path.join(ROOT, "output", "figures")  # Fig 1, Fig 2, S1 Fig
RESOURCES_DIR = os.path.join(ROOT, "resources")

YEARS = list(range(2018, 2026))

# Variables that define the complete-case analytic sample used by every model, table and figure
MODEL_VARS = ["currentsmoker", "URRU", "_AGE_G", "SEXVAR", "_RACEGR3", "_EDUCAG",
              "_LLCPWT", "_STSTR", "_PSU"]

FIPS = {1: "Alabama", 2: "Alaska", 4: "Arizona", 5: "Arkansas", 6: "California", 8: "Colorado",
        9: "Connecticut", 10: "Delaware", 11: "District of Columbia", 12: "Florida", 13: "Georgia",
        15: "Hawaii", 16: "Idaho", 17: "Illinois", 18: "Indiana", 19: "Iowa", 20: "Kansas",
        21: "Kentucky", 22: "Louisiana", 23: "Maine", 24: "Maryland", 25: "Massachusetts",
        26: "Michigan", 27: "Minnesota", 28: "Mississippi", 29: "Missouri", 30: "Montana",
        31: "Nebraska", 32: "Nevada", 33: "New Hampshire", 34: "New Jersey", 35: "New Mexico",
        36: "New York", 37: "North Carolina", 38: "North Dakota", 39: "Ohio", 40: "Oklahoma",
        41: "Oregon", 42: "Pennsylvania", 44: "Rhode Island", 45: "South Carolina",
        46: "South Dakota", 47: "Tennessee", 48: "Texas", 49: "Utah", 50: "Vermont",
        51: "Virginia", 53: "Washington", 54: "West Virginia", 55: "Wisconsin", 56: "Wyoming"}

# Jurisdictions with no rural respondents in 2018-2024; excluded from state-specific analyses
ZERO_RURAL = {9, 10, 11, 15, 25, 33, 34, 44}
TERRITORIES = {66, 72, 78}


def ensure_dirs():
    for d in (DERIVED_DIR, MODELS_DIR, TABLES_DIR, FIGURES_DIR):
        os.makedirs(d, exist_ok=True)


def analytic_sample(df):
    """Complete cases on every model variable."""
    return df[df[MODEL_VARS].notna().all(axis=1)].copy()


def num(s):
    """Parse SAS-exported numbers. SAS writes very small p-values as '<.0001'; that is an
    upper bound, so it is mapped to half the bound."""
    import pandas as pd
    s = pd.Series(s).astype(str).str.strip()
    lt = s.str.startswith("<")
    v = pd.to_numeric(s.str.replace("<", "", regex=False), errors="coerce")
    return v.where(~lt, v / 2)


def fmt_p(p):
    """APA-style P value: '<.001' or three decimals without a leading zero."""
    import pandas as pd
    if pd.isna(p):
        return ""
    return "<.001" if p < .001 else ("%.3f" % p).lstrip("0")


def stars(p):
    """Significance stars used in S1 Table (*P<.05, **P<.01, ***P<.001)."""
    import pandas as pd
    if pd.isna(p):
        return ""
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""
