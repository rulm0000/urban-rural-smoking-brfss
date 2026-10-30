"""Step 11. S1 Fig: current smoking prevalence by state, rural and urban residents, 2018 and 2025.

Same geographic map as Fig 1, with Alaska and Hawaii drawn as insets below the southwestern
states. Weighted prevalence on the complete-case analytic sample. Estimates with an
unweighted n < 50 or a relative standard error > 30% (Kish effective sample size) are shown
as not available (grey), as are states with no data for that year. Puerto Rico is in the
boundary file but not in the analysis, so it is not drawn.

Inputs : data/derived/brfss_2018_2025_analytic.csv  (step 2)
         resources/cb_2023_us_state_20m.shp (+ .dbf, .shx, .prj)
                                                      (US Census Bureau 2023 cartographic
                                                      boundary file, states, 1:20,000,000)
Outputs: output/figures/S1_Fig.tif (300 dpi, LZW, 7.5 in wide) and S1_Fig.png
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
import matplotlib.ticker as mticker
from matplotlib.colors import Normalize, to_hex
from matplotlib.patches import Patch
from PIL import Image

from common import ABBR, ANALYTIC_CSV, FIGURES_DIR, RESOURCES_DIR, analytic_sample, ensure_dirs

VMIN, VMAX, CMAP = 0.05, 0.30, plt.get_cmap("RdYlGn_r")
NOT_SHOWN = "#d9d9d9"
BOUNDARIES = "cb_2023_us_state_20m.shp"
EDGE, EDGE_LW = "0.8", 0.35
FIG_W, LABEL_W, MAP_GAP = 7.5, 0.32, 0.15     # inches


def has_font(name):
    try:
        fm.findfont(name, fallback_to_default=False)
        return True
    except ValueError:
        return False


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


def state_shapes():
    """State shapes in plotting coordinates, as in step 10. Each region (the lower 48 states
    and DC, Alaska, Hawaii) is drawn in longitude and latitude with the x axis scaled by the
    cosine of its middle latitude, as a geopandas map of each region would look. Alaska and
    Hawaii are then scaled and moved below the southwestern states."""
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
    df = analytic_sample(pd.read_csv(ANALYTIC_CSV))
    df["year"] = df["year_centered"].map({-2: 2018, 5: 2025})
    df = df[df["year"].isin([2018, 2025])]
    m = df.groupby(["_STATE", "year", "URRU"]).apply(metrics, include_groups=False).reset_index()
    m.loc[(m["n"] < 50) | (m["rse"] > 30), "prevalence"] = np.nan
    m["fips"] = m["_STATE"].astype(int)
    m = m[m["fips"].isin(ABBR)]

    g = state_shapes()
    bx0, by0, bx1, by1 = g.total_bounds
    pad = 0.005 * (bx1 - bx0)
    xlim, ylim = (bx0 - pad, bx1 + pad), (by0 - pad, by1 + pad)
    map_w = (FIG_W - LABEL_W - MAP_GAP - 0.03) / 2
    map_h = map_w * (ylim[1] - ylim[0]) / (xlim[1] - xlim[0])

    font = next((f for f in ("Arial", "Liberation Sans") if has_font(f)), "DejaVu Sans")
    plt.rcParams.update({"font.family": font})
    title_h, row_gap, legend_h = 0.30, 0.10, 0.62
    fig_h = title_h + 2 * map_h + row_gap + legend_h
    fig = plt.figure(figsize=(FIG_W, fig_h))
    norm = Normalize(VMIN, VMAX)

    panels = [((0, 0), 2018, 1), ((0, 1), 2025, 1), ((1, 0), 2018, 0), ((1, 1), 2025, 0)]
    for (r, c), yr, urru in panels:
        left = LABEL_W + c * (map_w + MAP_GAP)
        base = legend_h + (1 - r) * (map_h + row_gap)
        ax = fig.add_axes([left / FIG_W, base / fig_h, map_w / FIG_W, map_h / fig_h])
        vals = m[(m.year == yr) & (m.URRU == urru)].set_index("fips")["prevalence"]
        fill = [NOT_SHOWN if pd.isna(vals.get(f, np.nan)) else to_hex(CMAP(norm(vals[f])))
                for f in g["fips"]]
        # Alaska and Hawaii are outlined in their own color so that small islands keep it
        edge = [col if f in (2, 15) else EDGE for f, col in zip(g["fips"], fill)]
        g.plot(ax=ax, color=fill, edgecolor=edge, linewidth=EDGE_LW)
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_aspect("equal")
        ax.set_axis_off()
        if r == 0:
            ax.set_title(str(yr), fontsize=11, pad=6)
        if c == 0:
            fig.text(0.5 * LABEL_W / FIG_W, (base + 0.5 * map_h) / fig_h,
                     "Rural" if urru == 1 else "Urban", rotation=90, ha="center", va="center",
                     fontsize=11)

    # legend: colour scale, centred under the maps, plus the grey "not available" key
    cb_w, cb_h = 3.3, 0.13
    cb_left = LABEL_W + (2 * map_w + MAP_GAP - cb_w) / 2
    cb_base = legend_h - 0.10 - cb_h
    cax = fig.add_axes([cb_left / FIG_W, cb_base / fig_h, cb_w / FIG_W, cb_h / fig_h])
    cb = fig.colorbar(plt.cm.ScalarMappable(cmap=CMAP, norm=norm), cax=cax, orientation="horizontal")
    cb.set_label("Current smoking prevalence", fontsize=9, labelpad=3)
    cb.ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0, decimals=0))
    cb.ax.tick_params(labelsize=8, length=3)
    cb.outline.set_edgecolor("lightgrey")
    fig.legend(handles=[Patch(facecolor=NOT_SHOWN, edgecolor="none", label="Not available")],
               loc="center left", frameon=False, fontsize=9, handlelength=1.6, borderaxespad=0,
               bbox_to_anchor=((cb_left + cb_w + 0.3) / FIG_W, (cb_base + cb_h / 2) / fig_h))

    png = os.path.join(FIGURES_DIR, "S1_Fig.png")
    fig.savefig(png, dpi=300)
    plt.close(fig)
    im = Image.open(png).convert("RGB")
    im.save(os.path.join(FIGURES_DIR, "S1_Fig.tif"), compression="tiff_lzw", dpi=(300, 300))
    print("S1 Fig:", im.size, "->", FIGURES_DIR)


if __name__ == "__main__":
    main()
