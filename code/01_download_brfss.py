"""Step 1. Download the BRFSS public-use files (2018-2025) from CDC and verify them.

For each year this script
  1. skips the download if LLCP<year>.XPT is already in the raw folder with the expected SHA-256,
  2. otherwise downloads https://www.cdc.gov/brfss/annual_data/<year>/files/LLCP<year>XPT.zip,
  3. extracts the .XPT file (some CDC zip members carry a trailing space in the name), and
  4. checks the SHA-256 against data/SHA256SUMS.

The files are about 1 GB each (about 8 GB in total). If you already have them, point the
pipeline at that folder instead (run_all.ps1 -RawDir <folder>) and nothing is downloaded.
"""
import hashlib
import os
import shutil
import sys
import urllib.request
import zipfile

from common import CHECKSUMS, RAW_DIR, YEARS

URL = "https://www.cdc.gov/brfss/annual_data/{y}/files/LLCP{y}XPT.zip"


def sha256(path, block=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(block), b""):
            h.update(chunk)
    return h.hexdigest()


def expected_hashes():
    out = {}
    with open(CHECKSUMS) as f:
        for line in f:
            if line.strip():
                digest, name = line.split(None, 1)
                out[name.strip()] = digest.lower()
    return out


def fetch(year, dest_xpt):
    zpath = dest_xpt[:-4] + "XPT.zip"
    print("  downloading", URL.format(y=year))
    with urllib.request.urlopen(URL.format(y=year)) as r, open(zpath, "wb") as f:
        shutil.copyfileobj(r, f, length=1 << 20)
    with zipfile.ZipFile(zpath) as z:
        member = [m for m in z.namelist() if m.strip().upper().endswith(".XPT")][0]
        with z.open(member) as src, open(dest_xpt, "wb") as dst:
            shutil.copyfileobj(src, dst, length=1 << 20)
    os.remove(zpath)


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    want = expected_hashes()
    bad = []
    for y in YEARS:
        name = "LLCP%d.XPT" % y
        path = os.path.join(RAW_DIR, name)
        if os.path.exists(path) and sha256(path) == want[name]:
            print("%s: present, checksum OK" % name)
            continue
        fetch(y, path)
        ok = sha256(path) == want[name]
        print("%s: downloaded, checksum %s" % (name, "OK" if ok else "MISMATCH"))
        if not ok:
            bad.append(name)
    if bad:
        sys.exit("Checksum mismatch for %s. CDC may have re-released these files; results may differ "
                 "slightly from the published analysis." % ", ".join(bad))
    print("All %d BRFSS files verified in %s" % (len(YEARS), RAW_DIR))


if __name__ == "__main__":
    main()
