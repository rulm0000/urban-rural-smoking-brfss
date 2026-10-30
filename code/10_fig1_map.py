"""Step 10. Fig 1: urban-rural odds ratios by state, Models 1, 2 and 3a.

Geographic map of the US states, with Alaska and Hawaii drawn as insets below the
southwestern states. A state is colored by its rural to urban odds ratio only when the odds
ratio is significant after Benjamini-Hochberg false discovery rate adjustment across the
43 state-specific tests for that model (BH-adjusted p-value < .05); otherwise it is light grey
("Non-significant"). The jurisdictions with no rural respondents, which are not in the
state-specific models, are dark grey ("Rural sample size: n < 50"). Puerto Rico is in the
boundary file but not in the analysis, so it is not drawn.

Inputs : output/models/state_or_summary.csv          (step 9)
         resources/cb_2023_us_state_20m.shp (+ .dbf, .shx, .prj)
                                                      (US Census Bureau 2023 cartographic
                                                      boundary file, states, 1:20,000,000)
Outputs: output/figures/Fig1.tif (300 dpi, LZW, 7.5 in wide) and Fig1.png
"""
import os

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import shapely

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from PIL import Image

from common import ABBR, FIGURES_DIR, MODELS_DIR, RESOURCES_DIR, ensure_dirs

# legend order, top to bottom
COLORS = {"OR ≥ 1.50": "#034e7b", "1.25 < OR < 1.50": "#3690c0", "1.00 < OR ≤ 1.25": "#a6bddb",
          "OR < 1.00": "#fee090", "Non-significant": "#d9d9d9", "Rural sample size: n < 50": "#969696"}
BOUNDARIES = "cb_2023_us_state_20m.shp"
EDGE, EDGE_LW = "0.8", 0.35
FIG_W, MAP_W, GAP = 7.5, 3.6, 0.2      # inches


def has_font(name):
    try:
        fm.findfont(name, fallback_to_default=False)
        return True
    except ValueError:
        return False


def category(orv, q, present):
    """Legend category of one state. The bins use the unrounded odds ratio."""
    if not present:
        return "Rural sample size: n < 50"
    if pd.isna(orv) or pd.isna(q) or q >= 0.05:
        return "Non-significant"
    if orv < 1.0:
        return "OR < 1.00"
    if 1.0 < orv <= 1.25:
        return "1.00 < OR ≤ 1.25"
    if 1.25 < orv < 1.5:
        return "1.25 < OR < 1.50"
    if orv >= 1.5:
        return "OR ≥ 1.50"
    raise ValueError("significant odds ratio of exactly 1.00 has no legend category")


def state_shapes():
    """State shapes in plotting coordinates. Each region (the lower 48 states and DC, Alaska,
    Hawaii) is drawn in longitude and latitude with the x axis scaled by the cosine of its
    middle latitude, as a geopandas map of each region would look. Alaska and Hawaii are then
    scaled and moved below the southwestern states, Alaska on the left as in the original
    figure."""
    g = gpd.read_file(os.path.join(RESOURCES_DIR, BOUNDARIES))
    g["fips"] = g["STATEFP"].astype(int)
    g = g[g["fips"].isin(ABBR)].copy()          # the 50 states and DC; drops Puerto Rico

    def unwrap(xy):                             # Aleutian islands west of 180 degrees
        xy = xy.copy()
        xy[xy[:, 0] > 0, 0] -= 360
        return xy

    g["geometry"] = [shapely.transform(geom, unwrap) for geom in g.geometry]

    def equirect(geoms):
        lat0 = (geoms.total_bounds[1] + geoms.total_bounds[3]) / 2
        return geoms.scale(xfact=np.cos(np.radians(lat0)), yfact=1.0, origin=(0, 0))

    ak, hi = g["fips"] == 2, g["fips"] == 15
    conus = equirect(g.geometry[~ak & ~hi])
    x0, y0, x1, _ = conus.total_bounds
    width = x1 - x0

    def inset(geoms, left, bottom, size):
        """Place a region with its lower-left corner at (left, bottom) and its width equal to
        size, all as fractions of the width of the lower 48 states."""
        geoms = equirect(geoms)
        bx0, by0, bx1, _ = geoms.total_bounds
        s = size * width / (bx1 - bx0)
        return geoms.scale(s, s, origin=(bx0, by0)).translate(x0 + left * width - bx0,
                                                              y0 + bottom * width - by0)

    g["geometry"] = pd.concat([conus, inset(g.geometry[ak], 0.0, -0.035, 0.24),
                               inset(g.geometry[hi], 0.25, -0.01, 0.14)])
    return gpd.GeoDataFrame(g, geometry="geometry")


def main():
    ensure_dirs()
    df = pd.read_csv(os.path.join(MODELS_DIR, "state_or_summary.csv"))
    res = df[df.State_Code != 0].assign(fips=lambda d: d.State_Code.astype(int)).set_index("fips")
    models = [("Model 1", "OR_Model1", "QValue_Model1"), ("Model 2", "OR_Model2", "QValue_Model2"),
              ("Model 3a", "OR_Model3", "QValue_Model3")]

    g = state_shapes()
    bx0, by0, bx1, by1 = g.total_bounds
    pad = 0.005 * (bx1 - bx0)
    xlim, ylim = (bx0 - pad, bx1 + pad), (by0 - pad, by1 + pad)
    map_h = MAP_W * (ylim[1] - ylim[0]) / (xlim[1] - xlim[0])

    font = next((f for f in ("Arial", "Liberation Sans") if has_font(f)), "DejaVu Sans")
    plt.rcParams.update({"font.family": font})
    title_h, top, row_gap, bottom = 0.28, 0.04, 0.10, 0.04
    fig_h = top + 2 * (title_h + map_h) + row_gap + bottom
    fig = plt.figure(figsize=(FIG_W, fig_h))

    def add_map(left, base):
        return fig.add_axes([left / FIG_W, base / fig_h, MAP_W / FIG_W, map_h / fig_h])

    side = (FIG_W - 2 * MAP_W - GAP) / 2
    base_bottom = bottom
    base_top = bottom + map_h + title_h + row_gap
    axes = [add_map(side, base_top), add_map(side + MAP_W + GAP, base_top), add_map(0, base_bottom)]

    for ax, (title, orc, qc) in zip(axes, models):
        present = g["fips"].isin(res.index)
        cats = [category(res.at[f, orc] if p else np.nan, res.at[f, qc] if p else np.nan, p)
                for f, p in zip(g["fips"], present)]
        fill = [COLORS[c] for c in cats]
        # Alaska and Hawaii have no neighbours in their insets: outline them in their own
        # color so that the small islands keep the state's color
        edge = [c if f in (2, 15) else EDGE for f, c in zip(g["fips"], fill)]
        g.plot(ax=ax, color=fill, edgecolor=edge, linewidth=EDGE_LW)
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_aspect("equal")
        ax.set_axis_off()
        ax.set_title(title, fontsize=11, pad=4)
        counts = pd.Series(cats).value_counts()
        print(title + ":", ", ".join(f"{k} {counts.get(k, 0)}" for k in COLORS))

    # bottom row: Model 3a and the legend, centred together as in the original figure
    leg = fig.legend(handles=[Patch(facecolor=v, edgecolor="none", label=k) for k, v in COLORS.items()],
                     loc="center left", frameon=True, fontsize=9, handlelength=2.0, borderpad=0.7,
                     labelspacing=0.55, edgecolor="0.8", fancybox=False)
    fig.canvas.draw()
    leg_w = leg.get_window_extent().width / fig.dpi
    left3 = (FIG_W - (MAP_W + GAP + leg_w)) / 2
    axes[2].set_position([left3 / FIG_W, base_bottom / fig_h, MAP_W / FIG_W, map_h / fig_h])
    leg.set_bbox_to_anchor(((left3 + MAP_W + GAP) / FIG_W, (base_bottom + 0.42 * map_h) / fig_h),
                           transform=fig.transFigure)

    png = os.path.join(FIGURES_DIR, "Fig1.png")
    fig.savefig(png, dpi=300)
    plt.close(fig)
    im = Image.open(png).convert("RGB")
    im.save(os.path.join(FIGURES_DIR, "Fig1.tif"), compression="tiff_lzw", dpi=(300, 300))
    print("Fig 1:", im.size, "->", FIGURES_DIR)


if __name__ == "__main__":
    main()
