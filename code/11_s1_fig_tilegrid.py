"""Step 11. S1 Fig: current smoking prevalence by state, rural and urban residents, 2018 and 2025.

Same tile-grid layout as Fig 1: each state is an equal-size square in its approximate
geographic position. Weighted prevalence on the complete-case analytic sample. Estimates
with an unweighted n < 50 or a relative standard error > 30% (Kish effective sample size)
are shown as not available (grey), as are states with no data for that year.

Input : data/derived/brfss_2018_2025_analytic.csv
Output: output/figures/S1_Fig.tif (300 dpi, LZW, 7.5 in wide) and S1_Fig.png
"""
import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import Normalize
from matplotlib.patches import Patch, Rectangle
from PIL import Image

from common import ABBR, ANALYTIC_CSV, FIGURES_DIR, GRID, analytic_sample, ensure_dirs

VMIN, VMAX, CMAP = 0.05, 0.30, plt.get_cmap("RdYlGn_r")
NOT_SHOWN = "#d9d9d9"


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


def text_color(rgba):
    lum = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
    return "white" if lum < 0.45 else "black"


def main():
    ensure_dirs()
    df = analytic_sample(pd.read_csv(ANALYTIC_CSV))
    df["year"] = df["year_centered"].map({-2: 2018, 5: 2025})
    df = df[df["year"].isin([2018, 2025])]
    m = df.groupby(["_STATE", "year", "URRU"]).apply(metrics, include_groups=False).reset_index()
    m.loc[(m["n"] < 50) | (m["rse"] > 30), "prevalence"] = np.nan
    m["abbr"] = m["_STATE"].astype(int).map(ABBR)
    m = m.dropna(subset=["abbr"])

    norm = Normalize(VMIN, VMAX)
    fig = plt.figure(figsize=(7.5, 6.0))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.09], hspace=0.06, wspace=0.04,
                          left=0.06, right=0.99, top=0.95, bottom=0.10)
    panels = [((0, 0), 2018, 1), ((0, 1), 2025, 1), ((1, 0), 2018, 0), ((1, 1), 2025, 0)]
    for (r, c), yr, urru in panels:
        ax = fig.add_subplot(gs[r, c])
        vals = m[(m.year == yr) & (m.URRU == urru)].set_index("abbr")["prevalence"]
        for ab, (gr, gc) in GRID.items():
            v = vals.get(ab, np.nan)
            color = NOT_SHOWN if pd.isna(v) else CMAP(norm(v))
            ax.add_patch(Rectangle((gc, -gr), 0.92, 0.92, facecolor=color, edgecolor="white", linewidth=0.6))
            ax.text(gc + 0.46, -gr + 0.46, ab, ha="center", va="center", fontsize=6.5,
                    color="black" if pd.isna(v) else text_color(CMAP(norm(v))))
        ax.set_xlim(-0.2, 12.1)
        ax.set_ylim(-7.2, 1.1)
        ax.set_aspect("equal")
        ax.axis("off")
        if r == 0:
            ax.set_title(str(yr), fontsize=11)
        if c == 0:
            ax.text(-0.6, -3.05, "Rural" if urru == 1 else "Urban", rotation=90,
                    ha="center", va="center", fontsize=11)

    # legend: colour scale plus the grey "not shown" key
    lg = gs[2, :].subgridspec(1, 3, width_ratios=[0.2, 0.55, 0.25], wspace=0.06)
    cax = fig.add_subplot(lg[0, 1])
    sm = plt.cm.ScalarMappable(cmap=CMAP, norm=norm)
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.set_label("Current smoking prevalence", fontsize=9, labelpad=2)
    cb.ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0, decimals=0))
    cb.ax.tick_params(labelsize=8)
    cb.outline.set_edgecolor("lightgrey")
    kax = fig.add_subplot(lg[0, 2])
    kax.axis("off")
    kax.legend(handles=[Patch(facecolor=NOT_SHOWN, label="Not available")],
               loc="center left", frameon=False, fontsize=9, handlelength=1.4)

    png = os.path.join(FIGURES_DIR, "S1_Fig.png")
    fig.savefig(png, dpi=300)
    im = Image.open(png).convert("RGB")
    im.save(os.path.join(FIGURES_DIR, "S1_Fig.tif"), compression="tiff_lzw", dpi=(300, 300))
    print("S1 Fig:", im.size, "->", FIGURES_DIR)


if __name__ == "__main__":
    main()
