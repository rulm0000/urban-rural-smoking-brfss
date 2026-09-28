"""Step 10. Fig 1: urban-rural odds ratios by state, Models 1, 2 and 3a.

Each state is drawn as an equal-size square in its approximate geographic position, so
small states are as visible as large ones.

Input : output/models/state_or_summary.csv  (step 9)
Output: output/figures/Fig1.tif (300 dpi, LZW, 7.5 in wide) and Fig1.png
"""
import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from PIL import Image

from common import ABBR, FIGURES_DIR, GRID, MODELS_DIR, ensure_dirs

COLORS = {"OR ≥ 1.50": "#034e7b", "1.25 < OR < 1.50": "#3690c0", "OR ≤ 1.25": "#a6bddb",
          "OR < 1.0": "#fee090", "Non-significant": "#d9d9d9", "Rural sample size: n < 50": "#969696"}
DARK = {"OR ≥ 1.50", "1.25 < OR < 1.50"}


def category(orv, p, present):
    if not present:
        return "Rural sample size: n < 50"
    if pd.isna(orv) or pd.isna(p) or p >= 0.05:
        return "Non-significant"
    if orv < 1.0:
        return "OR < 1.0"
    if orv <= 1.25:
        return "OR ≤ 1.25"
    if orv < 1.5:
        return "1.25 < OR < 1.50"
    return "OR ≥ 1.50"


def main():
    ensure_dirs()
    df = pd.read_csv(os.path.join(MODELS_DIR, "state_or_summary.csv"))
    df = df[df.State_Code != 0]
    res = df.assign(abbr=df.State_Code.astype(int).map(ABBR)).set_index("abbr")
    models = [("Model 1", "OR_Model1", "PValue_Model1"), ("Model 2", "OR_Model2", "PValue_Model2"),
              ("Model 3a", "OR_Model3", "PValue_Model3")]

    fig, axs = plt.subplots(2, 2, figsize=(7.5, 5.6))
    axs = axs.ravel()
    for ax, (title, orc, pc) in zip(axs, models):
        for ab, (r, c) in GRID.items():
            present = ab in res.index
            cat = category(res.at[ab, orc] if present else np.nan,
                           res.at[ab, pc] if present else np.nan, present)
            ax.add_patch(Rectangle((c, -r), 0.92, 0.92, facecolor=COLORS[cat], edgecolor="white", linewidth=0.6))
            ax.text(c + 0.46, -r + 0.46, ab, ha="center", va="center", fontsize=6.5,
                    color="white" if cat in DARK else "black")
        ax.set_xlim(-0.2, 12.1)
        ax.set_ylim(-7.2, 1.1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=11)
    axs[3].axis("off")
    axs[3].legend(handles=[Patch(color=v, label=k) for k, v in COLORS.items()],
                  loc="center", frameon=False, fontsize=9)
    plt.tight_layout(pad=0.4, w_pad=0.6, h_pad=0.8)
    png = os.path.join(FIGURES_DIR, "Fig1.png")
    fig.savefig(png, dpi=300)
    im = Image.open(png).convert("RGB")
    im.save(os.path.join(FIGURES_DIR, "Fig1.tif"), compression="tiff_lzw", dpi=(300, 300))
    print("Fig 1:", im.size, "->", FIGURES_DIR)


if __name__ == "__main__":
    main()
