"""Step 11. S1 Fig: current smoking prevalence by state, rural and urban residents, 2018 and 2025.

Weighted prevalence on the complete-case analytic sample. Estimates with an unweighted
n < 50 or a relative standard error > 30% (Kish effective sample size) are shown in grey.

Inputs : data/derived/brfss_2018_2025_analytic.csv, resources/us-states.json
Outputs: output/figures/S1_Fig.png and S1_Fig.tif
"""
import os

import geopandas as gpd
import matplotlib
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

from common import ANALYTIC_CSV, FIGURES_DIR, FIPS, RESOURCES_DIR, analytic_sample, ensure_dirs


def metrics(group):
    n = len(group)
    tw = group["_LLCPWT"].sum()
    if tw == 0 or n == 0:
        return pd.Series({"prevalence": np.nan, "n": n, "rse": np.nan})
    p = (group["currentsmoker"] * group["_LLCPWT"]).sum() / tw
    sw2 = (group["_LLCPWT"] ** 2).sum()
    neff = tw ** 2 / sw2 if sw2 > 0 else 0
    rse = np.nan if (neff == 0 or p <= 0 or p >= 1) else 100 * np.sqrt(p * (1 - p) / neff) / p
    return pd.Series({"prevalence": p, "n": int(n), "rse": rse})


def main():
    ensure_dirs()
    df = analytic_sample(pd.read_csv(ANALYTIC_CSV))
    df["year"] = df["year_centered"].map({-2: 2018, 5: 2025})
    df = df[df["year"].isin([2018, 2025])]
    m = df.groupby(["_STATE", "year", "URRU"]).apply(metrics, include_groups=False).reset_index()
    m.loc[(m["n"] < 50) | (m["rse"] > 30), "prevalence"] = np.nan
    m["State"] = m["_STATE"].map(FIPS)

    gdf = gpd.read_file(os.path.join(RESOURCES_DIR, "us-states.json")).rename(columns={"name": "State"})
    fig, axes = plt.subplots(2, 2, figsize=(20, 12), sharex=True, sharey=True)
    panels = {(0, 0): (2018, 1), (0, 1): (2025, 1), (1, 0): (2018, 0), (1, 1): (2025, 0)}
    vmin, vmax, cmap = 0.05, 0.30, "RdYlGn_r"
    for (r, c), (yr, urru) in panels.items():
        ax = axes[r, c]
        g = gdf.merge(m[(m.year == yr) & (m.URRU == urru)], on="State", how="left")
        kw = dict(column="prevalence", cmap=cmap, vmin=vmin, vmax=vmax, missing_kwds={"color": "lightgrey"})
        g[~g.State.isin(["Alaska", "Hawaii"])].plot(ax=ax, linewidth=0.8, edgecolor="0.8", **kw)
        ax.set_axis_off()
        ak = ax.inset_axes([0.05, 0.0, 0.25, 0.25])
        g[g.State == "Alaska"].plot(ax=ak, **kw)
        ak.set_axis_off()
        hi = ax.inset_axes([0.3, 0.0, 0.2, 0.2])
        g[g.State == "Hawaii"].plot(ax=hi, **kw)
        hi.set_axis_off()

    axes[0, 0].set_title("2018", fontsize=30, pad=20)
    axes[0, 1].set_title("2025", fontsize=30, pad=20)
    fig.text(0.08, 0.7, "Rural", va="center", rotation="vertical", fontsize=30)
    fig.text(0.08, 0.3, "Urban", va="center", rotation="vertical", fontsize=30)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    sm.set_array([])
    cax = fig.add_axes([0.25, 0.06, 0.5, 0.03])
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.set_label("Current smoking prevalence", size=20, labelpad=15)
    cb.ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0, decimals=0))
    cb.ax.tick_params(labelsize=16)
    cb.outline.set_edgecolor("lightgrey")
    cb.outline.set_linewidth(1)
    fig.tight_layout(rect=[0.05, 0.1, 0.95, 1])

    png = os.path.join(FIGURES_DIR, "S1_Fig.png")
    plt.savefig(png, dpi=300, bbox_inches="tight")
    im = Image.open(png).convert("RGB")
    w = 2250                                   # 7.5 in at 300 dpi
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(os.path.join(FIGURES_DIR, "S1_Fig.tif"), compression="tiff_lzw", dpi=(300, 300))
    print("S1 Fig ->", FIGURES_DIR)


if __name__ == "__main__":
    main()
