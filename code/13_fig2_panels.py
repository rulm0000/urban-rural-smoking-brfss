"""Step 13. Fig 2: predicted probability of current smoking by urban-rural status,
2018-2025 (Model 3b), with unadjusted prevalence, nationwide and for each state whose
urban-rural x year interaction is significant after false discovery rate adjustment.

Draws the values that step 12 (Stata) estimated. Panels follow the Table 2 order in two
columns, with the legend in the next free cell. The label in each panel is the
Benjamini-Hochberg q value of the interaction (the unadjusted P for the nationwide panel,
which is not in an FDR family), with the letter q or P in italics.

Inputs : output/models/fig2_plotted_values.csv  (step 12)
         output/models/fig2_entities.do         (step 9: panel order and q labels)
Output : output/figures/Fig2.tif (300 dpi, LZW, 7.5 in wide) and Fig2.png
"""
import os
import re

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from PIL import Image

from common import FIGURES_DIR, MODELS_DIR, YEARS, ensure_dirs

URBAN, RURAL = "#1A476F", "#FF0000"          # Stata s2color navy and red
DASH = (0, (6, 3))
NCOL = 2


def has_font(name):
    try:
        fm.findfont(name, fallback_to_default=False)
        return True
    except ValueError:
        return False


def panels():
    """Panel names and q labels, in Table 2 order, from fig2_entities.do."""
    text = open(os.path.join(MODELS_DIR, "fig2_entities.do"), encoding="utf-8").read()
    names = re.findall(r'"([^"]+)"', re.search(r"local entity_names `\"(.*)\"'", text).group(1))
    labels = [re.search(r'local s%d "([^"]*)"' % (i + 1), text).group(1) for i in range(len(names))]
    return names, labels


def main():
    ensure_dirs()
    vals = pd.read_csv(os.path.join(MODELS_DIR, "fig2_plotted_values.csv"))
    names, labels = panels()
    n = len(names)
    nrow = -(-(n + 1) // NCOL)

    font = next((f for f in ("Arial", "Liberation Sans") if has_font(f)), "DejaVu Sans")
    # the statistic letter (q or P) in each panel label is set in italics
    plt.rcParams.update({"font.family": font, "font.size": 9, "mathtext.fontset": "custom",
                         "mathtext.rm": font, "mathtext.it": font + ":italic",
                         "mathtext.bf": font + ":bold", "mathtext.sf": font, "mathtext.cal": font})
    fig, axes = plt.subplots(nrow, NCOL, figsize=(7.5, 2.05 * nrow + 0.45), squeeze=False)
    fig.subplots_adjust(left=0.11, right=0.985, top=0.975, bottom=0.075, wspace=0.07, hspace=0.42)

    for i, name in enumerate(names):
        ax = axes[i // NCOL][i % NCOL]
        d = vals[vals.entity == name]
        series = [(0, URBAN, "-"), (1, RURAL, DASH)]
        for u, col, _ in series:
            s = d[d.urru == u].sort_values("year")
            ax.fill_between(s.year, s.lo, s.hi, color=col, alpha=0.18, lw=0, zorder=1)
        for u, col, ls in series:
            s = d[d.urru == u].sort_values("year")
            ax.plot(s.year, s.pred, color=col, lw=1.3, ls=ls, zorder=3)
        for u, col, _ in series:
            s = d[d.urru == u].sort_values("year")
            ax.scatter(s.year, s.prev, s=22, color=col, zorder=4, linewidths=0)

        ax.set_title(name, fontsize=10, pad=3)
        label = r"$\mathit{%s}$%s" % (labels[i][0], labels[i][1:])   # e.g. q = .023, P < .001
        ax.text(0.985, 0.04, label, transform=ax.transAxes, ha="right", va="bottom", fontsize=8.5)
        ax.set_ylim(0, 0.30)
        ax.set_xlim(YEARS[0] - 0.4, YEARS[-1] + 0.4)
        ax.set_yticks([0, .05, .10, .15, .20, .25, .30])
        ax.set_xticks(YEARS)
        ax.grid(axis="y", color="#E6ECEF", lw=0.8, zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_linewidth(0.8)
        ax.tick_params(length=3, width=0.8, labelsize=7.5)
        if i % NCOL == 0:
            ax.set_yticklabels(["%.2f" % v for v in ax.get_yticks()])
        else:
            ax.set_yticklabels([])
        # year labels only where no panel sits below (the bottom of each column)
        if i + NCOL >= n:
            ax.set_xticklabels([str(y) for y in YEARS], rotation=45, ha="right", rotation_mode="anchor")
        else:
            ax.set_xticklabels([])

    for k in range(n, nrow * NCOL):
        axes[k // NCOL][k % NCOL].axis("off")
    legend_ax = axes[n // NCOL][n % NCOL]
    handles = [Line2D([], [], color=URBAN, lw=1.6, ls="-"),
               Line2D([], [], color=RURAL, lw=1.6, ls=DASH),
               Patch(facecolor=URBAN, alpha=0.18, lw=0),
               Patch(facecolor=RURAL, alpha=0.18, lw=0),
               Line2D([], [], color=URBAN, marker="o", ls="none", ms=5.5),
               Line2D([], [], color=RURAL, marker="o", ls="none", ms=5.5)]
    texts = ["Urban, predicted probability", "Rural, predicted probability", "Urban, 95% CI",
             "Rural, 95% CI", "Urban, unadjusted prevalence", "Rural, unadjusted prevalence"]
    legend_ax.legend(handles, texts, loc="center", frameon=False, fontsize=9.5, handlelength=2.6,
                     labelspacing=0.75, borderaxespad=0)

    fig.supylabel("Predicted Probability", fontsize=11, x=0.015)
    fig.supxlabel("Year", fontsize=11, y=0.008)

    png = os.path.join(FIGURES_DIR, "Fig2.png")
    fig.savefig(png, dpi=300)
    plt.close(fig)
    im = Image.open(png).convert("RGB")
    w = 2250
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(os.path.join(FIGURES_DIR, "Fig2.tif"), compression="tiff_lzw", dpi=(300, 300))
    print("Fig 2:", im.size, "->", FIGURES_DIR)


if __name__ == "__main__":
    main()
