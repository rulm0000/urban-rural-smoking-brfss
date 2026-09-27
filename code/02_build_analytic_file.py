"""Step 2. Build the pooled 2018-2025 analytic file from the raw CDC BRFSS files.

Input : LLCP2018.XPT ... LLCP2025.XPT (raw folder; see step 1)
Output: data/derived/brfss_2018_2025_analytic.csv  (one row per respondent, all years)

With --from-archive, the raw files are not needed: the same file is unpacked from the
compressed copy kept in this repository (data/brfss_2018_2025_analytic.csv.xz).
With --make-archive, that compressed copy is (re)created from the built file.

The same derivation is applied to every survey year:

  currentsmoker  _RFSMOK3: 1 -> 0 (not a current smoker), 2 -> 1 (current smoker), 9 -> missing
  URRU           _URBSTAT: 1 -> 0 (urban), 2 -> 1 (rural); NCHS Urban-Rural Classification Scheme
  METRO          _METSTAT: 1 -> 0 (metropolitan), 2 -> 1 (nonmetropolitan); not used in the models
  SEXVAR         SEXVAR (2019 onward) or SEX1 (2018): 1 male, 2 female; other codes -> missing
  _RACEGR3       _RACEGR3, or _RACEGR4 where _RACEGR3 is absent (same five categories); 9 -> missing
  _EDUCAG        1-4; 9 -> missing
  _AGE_G         six age groups as provided by CDC
  year_centered  survey year - 2020, assigned per file. The interview year (IYEAR) is not used
                 because interviews for a survey year can continue into the next calendar year.

Models use _LLCPWT, _STSTR and _PSU exactly as provided by CDC.
"""
import hashlib
import lzma
import os
import shutil
import sys

import pandas as pd
import pyreadstat

from common import ANALYTIC_CSV, CHECKSUMS, MODEL_VARS, RAW_DIR, ROOT, YEARS, ensure_dirs

ARCHIVE = os.path.join(ROOT, "data", "brfss_2018_2025_analytic.csv.xz")
FINAL = ["_STATE", "_PSU", "SEXVAR", "_STSTR", "_LLCPWT", "_RACEGR3", "_AGE_G", "_EDUCAG",
         "year_centered", "URRU", "currentsmoker", "METRO"]
INTEGER = ["_STATE", "_PSU", "SEXVAR", "_STSTR", "_RACEGR3", "_AGE_G", "_EDUCAG",
           "year_centered", "URRU", "currentsmoker", "METRO"]


def load_year(y):
    path = os.path.join(RAW_DIR, "LLCP%d.XPT" % y)
    _, meta = pyreadstat.read_xport(path, metadataonly=True, encoding="LATIN1")
    have = set(meta.column_names)
    sexv = "SEXVAR" if "SEXVAR" in have else "SEX1"
    racev = "_RACEGR3" if "_RACEGR3" in have else "_RACEGR4"
    use = ["_STATE", "_PSU", "_STSTR", "_LLCPWT", sexv, racev, "_AGE_G", "_EDUCAG",
           "_URBSTAT", "_METSTAT", "_RFSMOK3"]
    df, _ = pyreadstat.read_xport(path, usecols=use, encoding="LATIN1")
    out = pd.DataFrame({
        "_STATE": df["_STATE"], "_PSU": df["_PSU"], "_STSTR": df["_STSTR"], "_LLCPWT": df["_LLCPWT"],
        "SEXVAR": df[sexv].where(df[sexv].isin([1, 2])),
        "_RACEGR3": df[racev].where(df[racev].isin([1, 2, 3, 4, 5])),
        "_AGE_G": df["_AGE_G"],
        "_EDUCAG": df["_EDUCAG"].where(df["_EDUCAG"].isin([1, 2, 3, 4])),
        "year_centered": float(y - 2020),
        "URRU": df["_URBSTAT"].map({1.0: 0.0, 2.0: 1.0}),
        "currentsmoker": df["_RFSMOK3"].map({1.0: 0.0, 2.0: 1.0}),
        "METRO": df["_METSTAT"].map({1.0: 0.0, 2.0: 1.0}),
    })
    print("  %d: %7d records (sex from %s, race/ethnicity from %s)" % (y, len(out), sexv, racev))
    return out[FINAL]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def expected_sha256():
    with open(CHECKSUMS) as f:
        for line in f:
            if line.strip().endswith(os.path.basename(ANALYTIC_CSV)):
                return line.split()[0].lower()


def check(path):
    got, want = sha256(path), expected_sha256()
    status = "matches the published analytic file" if got == want else "DOES NOT MATCH the published file"
    print("SHA-256 %s: %s" % (got, status))


def from_archive():
    print("Unpacking", ARCHIVE)
    with lzma.open(ARCHIVE, "rb") as src, open(ANALYTIC_CSV, "wb") as dst:
        shutil.copyfileobj(src, dst, 1 << 22)
    print("wrote", ANALYTIC_CSV)
    check(ANALYTIC_CSV)


def make_archive():
    print("Compressing", ANALYTIC_CSV, "(takes several minutes)")
    with open(ANALYTIC_CSV, "rb") as src, lzma.open(ARCHIVE, "wb", preset=9 | lzma.PRESET_EXTREME) as dst:
        shutil.copyfileobj(src, dst, 1 << 22)
    print("wrote %s (%.1f MB)" % (ARCHIVE, os.path.getsize(ARCHIVE) / 1e6))


def main():
    ensure_dirs()
    if "--from-archive" in sys.argv:
        return from_archive()
    if "--make-archive" in sys.argv:
        return make_archive()
    print("Reading raw BRFSS files from", RAW_DIR)
    df = pd.concat([load_year(y) for y in YEARS], ignore_index=True)
    for c in INTEGER:                      # write 1 rather than 1.0 (smaller file, same values)
        df[c] = df[c].astype("Int64")
    df.to_csv(ANALYTIC_CSV, index=False)
    cc = df[MODEL_VARS].notna().all(axis=1)
    print("records: %d  complete cases: %d (%.1f%%)" % (len(df), cc.sum(), 100 * cc.mean()))
    print("wrote", ANALYTIC_CSV)
    check(ANALYTIC_CSV)


if __name__ == "__main__":
    main()
