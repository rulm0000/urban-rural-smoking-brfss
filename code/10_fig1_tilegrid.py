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

from common import FIGURES_DIR, MODELS_DIR, ensure_dirs

ABBR = {1: "AL", 2: "AK", 4: "AZ", 5: "AR", 6: "CA", 8: "CO", 9: "CT", 10: "DE", 11: "DC", 12: "FL",
        13: "GA", 15: "HI", 16: "ID", 17: "IL", 18: "IN", 19: "IA", 20: "KS", 21: "KY", 22: "LA",
        23: "ME", 24: "MD", 25: "MA", 26: "MI", 27: "MN", 28: "MS", 29: "MO", 30: "MT", 31: "NE",
        32: "NV", 33: "NH", 34: "NJ", 35: "NM", 36: "NY", 37: "NC", 38: "ND", 39: "OH", 40: "OK",
        41: "OR", 42: "PA", 44: "RI", 45: "SC", 46: "SD", 47: "TN", 48: "TX", 49: "UT", 50: "VT",
        51: "VA", 53: "WA", 54: "WV", 55: "WI", 56: "WY"}
# (row, column) tile positions; row 0 at the top
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
