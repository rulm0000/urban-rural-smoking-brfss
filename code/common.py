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


ABBR = {1: "AL", 2: "AK", 4: "AZ", 5: "AR", 6: "CA", 8: "CO", 9: "CT", 10: "DE", 11: "DC", 12: "FL",
        13: "GA", 15: "HI", 16: "ID", 17: "IL", 18: "IN", 19: "IA", 20: "KS", 21: "KY", 22: "LA",
        23: "ME", 24: "MD", 25: "MA", 26: "MI", 27: "MN", 28: "MS", 29: "MO", 30: "MT", 31: "NE",
        32: "NV", 33: "NH", 34: "NJ", 35: "NM", 36: "NY", 37: "NC", 38: "ND", 39: "OH", 40: "OK",
        41: "OR", 42: "PA", 44: "RI", 45: "SC", 46: "SD", 47: "TN", 48: "TX", 49: "UT", 50: "VT",
        51: "VA", 53: "WA", 54: "WV", 55: "WI", 56: "WY"}
# Tile-grid map used by Fig 1 and S1 Fig: every state is an equal-size square placed at its
# approximate geographic position. (row, column) positions; row 0 at the top.
GRID = {"AK": (0, 0), "ME": (0, 11), "VT": (1, 10), "NH": (1, 11),
        "WA": (2, 1), "ID": (2, 2), "MT": (2, 3), "ND": (2, 4), "MN": (2, 5), "IL": (2, 6), "WI": (2, 7),
        "MI": (2, 8), "NY": (2, 9), "RI": (2, 10), "MA": (2, 11),
        "OR": (3, 1), "NV": (3, 2), "WY": (3, 3), "SD": (3, 4), "IA": (3, 5), "IN": (3, 6), "OH": (3, 7),
        "PA": (3, 8), "NJ": (3, 9), "CT": (3, 10),
        "CA": (4, 1), "UT": (4, 2), "CO": (4, 3), "NE": (4, 4), "MO": (4, 5), "KY": (4, 6), "WV": (4, 7),
        "VA": (4, 8), "MD": (4, 9), "DE": (4, 10),
        "AZ": (5, 2), "NM": (5, 3), "KS": (5, 4), "AR": (5, 5), "TN": (5, 6), "NC": (5, 7), "SC": (5, 8),
        "DC": (5, 9),
        "OK": (6, 4), "LA": (6, 5), "MS": (6, 6), "AL": (6, 7), "GA": (6, 8),
        "HI": (7, 0), "TX": (7, 4), "FL": (7, 9)}
assert len(GRID) == 51 and len(set(GRID.values())) == 51 and set(GRID) == set(ABBR.values())


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
