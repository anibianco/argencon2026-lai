#!/usr/bin/env python
"""
Genera las figuras del paper ARGENCON #327 a partir de data/raw/.

    python scripts/make_figures.py                 # version del paper (Default verano original)
    python scripts/make_figures.py --summer rerun  # Default verano re-corrido el 26/06 22:26

Salida: figures/fig*.pdf (vectorial, fuentes embebidas, tamano final IEEE).

Datos de entrada (data/raw/):
  figdata_argencon.npz                     extraido con scripts/extract_figdata.py (mendieta)
  FINAL_weekmean/isop_*_weekmean.npy       campos usados en las tablas del paper
  Argentina_cont.shp/                      limite IGN (continental + Malvinas)
  grid_to_ecoregion.csv                    celda -> ecorregion WWF/Olson

Convencion de grilla: IOAPI, fila 0 = sur.
"""
import argparse
import os

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyproj
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import FancyArrow, Patch, Rectangle
from shapely import contains_xy
from shapely.geometry import LineString, box

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
FIG = os.path.join(ROOT, "figures")

# ------------------------------------------------------------------ estilo
COL_W, PAGE_W = 3.5, 7.16          # ancho de columna / de pagina IEEE (in)
mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["TeX Gyre Termes", "Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "lines.linewidth": 1.2, "pdf.fonttype": 42, "savefig.dpi": 600,
    "axes.spines.top": False, "axes.spines.right": False,
})
C_DEFAULT, C_MODIS = "#2a78d6", "#eb6834"      # series 1 y 2
INK, MUTED = "#1f1f1f", "#6b6b6b"
ECO_COLORS = {                                  # validado (pares adyacentes en el mapa)
    "Dry Chaco": "#2a78d6", "Humid Chaco": "#1baf7a", "Espinal": "#eda100",
    "Humid Pampas": "#e87ba4", "Patagonian steppe": "#eb6834",
}
ECO_LABEL = {"Patagonian steppe": "Patagonian Steppe"}

# ------------------------------------------------------------------ datos
D = np.load(os.path.join(RAW, "figdata_argencon.npz"), allow_pickle=True)
h = lambda k: float(D["hdr_" + k])
NX, NY, DX = int(D["hdr_NCOLS"]), int(D["hdr_NROWS"]), h("XCELL")
CRS = pyproj.CRS.from_proj4(
    f"+proj=lcc +lat_1={h('P_ALP')} +lat_2={h('P_BET')} +lon_0={h('P_GAM')} "
    f"+lat_0={h('YCENT')} +x_0=0 +y_0=0 +a=6370000 +b=6370000 +units=m +no_defs")
TO_LL = pyproj.Transformer.from_crs(CRS, "EPSG:4326", always_xy=True)
TO_XY = pyproj.Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
xe = h("XORIG") + np.arange(NX + 1) * DX           # bordes de celda
ye = h("YORIG") + np.arange(NY + 1) * DX
xc, yc = 0.5 * (xe[1:] + xe[:-1]), 0.5 * (ye[1:] + ye[:-1])
XC, YC = np.meshgrid(xc, yc)

ARG = gpd.read_file(os.path.join(RAW, "Argentina_cont.shp",
                                 "Argentina_continental_malvinas.shp")).to_crs(CRS)
ARG_GEOM = ARG.union_all()
MASK = contains_xy(ARG_GEOM, XC, YC)                 # 3050 celdas (reproduce Tabla I)
ARG_LINE = gpd.GeoSeries([ARG_GEOM.simplify(2000)], crs=CRS)

iy, ix = np.where(MASK)
PAD = 1.5 * DX
EXT = (xe[ix.min()] - PAD, xe[ix.max() + 1] + PAD, ye[iy.min()] - PAD, ye[iy.max() + 1] + PAD)

ECO = np.full((NY, NX), "", dtype=object)
_e = pd.read_csv(os.path.join(RAW, "grid_to_ecoregion.csv"))
ECO[_e.row.values, _e.col.values] = _e.ECO_NAME.fillna("").values

KMOL_PER_WEEKMEAN = 7 * 3600 / 1000                  # weekmean.npy -> kmol/semana


def weekly(season, run, summer_version):
    """Emision semanal por celda (kmol)."""
    if season == "summer" and run == "default" and summer_version == "paper":
        f = os.path.join(RAW, "FINAL_weekmean", "isop_default_summer_weekmean.npy")
        return np.load(f) * KMOL_PER_WEEKMEAN
    return D[f"isop_weekly_kmol_{season}_{run}"]


# ------------------------------------------------------------------ helpers de mapa
def setup_map(ax, extent=EXT, grat=True, left=True, bottom=True, lon_lab_step=10):
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True); s.set_linewidth(0.6); s.set_color(INK)
    if grat:
        graticule(ax, extent, left, bottom, lon_lab_step=lon_lab_step)


def graticule(ax, extent, left=True, bottom=True, dlon=10, dlat=10, lon_lab_step=10):
    x0, x1, y0, y1 = extent
    frame = box(x0, y0, x1, y1)
    kw = dict(color="#bdbdbd", lw=0.35, zorder=1)
    for lat in range(-90, 1, dlat):
        lons = np.linspace(-110, -20, 400)
        x, y = TO_XY.transform(lons, np.full_like(lons, lat))
        line = LineString(np.c_[x, y]).intersection(frame)
        if line.is_empty:
            continue
        ax.plot(x, y, **kw)
        if left:
            lx = LineString([(x0, y0), (x0, y1)]).intersection(LineString(np.c_[x, y]))
            if not lx.is_empty and lx.geom_type == "Point":
                ax.text(x0 - 0.015 * (x1 - x0), lx.y, f"{abs(lat)}°S", ha="right", va="center",
                        fontsize=6.5, color=MUTED, clip_on=False)
    for lon in range(-100, -29, dlon):
        lats = np.linspace(-70, 0, 400)
        x, y = TO_XY.transform(np.full_like(lats, lon), lats)
        line = LineString(np.c_[x, y]).intersection(frame)
        if line.is_empty:
            continue
        ax.plot(x, y, **kw)
        if bottom and lon % lon_lab_step == 0:
            bx = LineString([(x0, y0), (x1, y0)]).intersection(LineString(np.c_[x, y]))
            if not bx.is_empty and bx.geom_type == "Point":
                ax.text(bx.x, y0 - 0.012 * (y1 - y0), f"{abs(lon)}°W", ha="center", va="top",
                        fontsize=6.5, color=MUTED, clip_on=False)


def outline(ax, lw=0.5, color=INK):
    ARG_LINE.boundary.plot(ax=ax, color=color, lw=lw, zorder=5)
    ax.set_xlabel(""); ax.set_ylabel("")


def north_arrow(ax, fx=0.86, fy=0.90, size=0.07):
    """Flecha al norte geografico (rotada segun la convergencia de meridianos)."""
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    px, py = x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)
    lon, lat = TO_LL.transform(px, py)
    qx, qy = TO_XY.transform(lon, lat + 0.5)
    ang = np.arctan2(qx - px, qy - py)
    L = size * (y1 - y0)
    dx, dy = L * np.sin(ang), L * np.cos(ang)
    ax.add_patch(FancyArrow(px - dx / 2, py - dy / 2, dx, dy, width=L * 0.08,
                            head_width=L * 0.38, head_length=L * 0.38,
                            length_includes_head=True, color=INK, zorder=10))
    ax.text(px + dx / 2 + 0.03 * L * np.sin(ang), py + dy / 2 + 0.12 * L, "N",
            ha="center", va="bottom", fontsize=7, fontweight="bold", color=INK, zorder=10)


def scale_bar(ax, km=500, fx=0.06, fy=0.04):
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    px, py = x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)
    L, H = km * 1000, 0.009 * (y1 - y0)
    for i in range(2):
        ax.add_patch(Rectangle((px + i * L / 2, py), L / 2, H, fc=INK if i == 0 else "white",
                               ec=INK, lw=0.5, zorder=10))
    ax.text(px + L / 2, py + 1.8 * H, f"{km} km", ha="center", va="bottom", fontsize=6,
            color=INK, zorder=10)


def eco_contours(ax, color="#3a3a3a", lw=0.45):
    """Limites entre ecorregiones (las 5 principales + 'otras') trazados sobre la grilla."""
    from matplotlib.collections import LineCollection
    code = np.full((NY, NX), -1)
    for k, n in enumerate(ECO_COLORS):
        code[(ECO == n) & MASK] = k
    code[MASK & (code < 0)] = 99
    segs = []
    for j in range(NY):
        for i in range(NX - 1):
            a, b = code[j, i], code[j, i + 1]
            if a != b and a >= 0 and b >= 0:
                segs.append([(xe[i + 1], ye[j]), (xe[i + 1], ye[j + 1])])
    for j in range(NY - 1):
        for i in range(NX):
            a, b = code[j, i], code[j + 1, i]
            if a != b and a >= 0 and b >= 0:
                segs.append([(xe[i], ye[j + 1]), (xe[i + 1], ye[j + 1])])
    ax.add_collection(LineCollection(segs, colors=color, linewidths=lw, zorder=4,
                                     linestyles=(0, (2.5, 1.2))))


def field(ax, Z, cmap, norm, mask=None):
    Z = np.array(Z, dtype=float)
    if mask is not None:
        Z = np.where(mask, Z, np.nan)
    return ax.pcolormesh(xe, ye, np.ma.masked_invalid(Z), cmap=cmap, norm=norm,
                         shading="flat", rasterized=True, zorder=2)


def save(fig, name):
    os.makedirs(FIG, exist_ok=True)
    p = os.path.join(FIG, name + ".pdf")
    fig.savefig(p, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("  ", os.path.relpath(p, ROOT))


# ------------------------------------------------------------------ figuras
def fig1_domain():
    fig, ax = plt.subplots(figsize=(COL_W, 4.2))
    wrf = (xe[0] - DX, xe[-1] + DX, ye[0] - DX, ye[-1] + DX)
    m = 0.06 * (wrf[1] - wrf[0])
    ext = (wrf[0] - m, wrf[1] + m, wrf[2] - m, wrf[3] + m)
    setup_map(ax, ext)
    ax.add_patch(Rectangle((xe[0], ye[0]), xe[-1] - xe[0], ye[-1] - ye[0],
                           fc="#ececec", ec=MUTED, lw=0.6, zorder=1.5,
                           label=f"MEGAN domain ({NX}×{NY}, 30 km)"))
    ax.add_patch(Rectangle((wrf[0], wrf[2]), wrf[1] - wrf[0], wrf[3] - wrf[2], fc="none",
                           ec="#c0392b", lw=0.9, ls=(0, (4, 2)), zorder=6,
                           label=f"WRF domain ({NX + 2}×{NY + 2})"))
    field(ax, np.ones((NY, NX)), ListedColormap([C_DEFAULT]), None, MASK)
    outline(ax, 0.45)
    # extension de descarga MODIS (aprox., leida de la figura original)
    lon0, lon1, lat0, lat1 = -78.6, -50.5, -57.7, -20.4
    lo = np.r_[np.linspace(lon0, lon1, 50), np.full(50, lon1), np.linspace(lon1, lon0, 50), np.full(50, lon0)]
    la = np.r_[np.full(50, lat0), np.linspace(lat0, lat1, 50), np.full(50, lat1), np.linspace(lat1, lat0, 50)]
    mx, my = TO_XY.transform(lo, la)
    ax.plot(mx, my, color="#1b7f3b", lw=0.9, zorder=6, label="MODIS MCD15A2H extent")
    h_ = ax.get_legend_handles_labels()[0]
    h_.insert(1, Patch(fc=C_DEFAULT, label=f"Argentina mask ({MASK.sum()} cells)"))
    ax.legend(handles=h_, loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=2, frameon=False,
              fontsize=6.5, handlelength=1.6, columnspacing=1.0)
    north_arrow(ax, fx=0.87, fy=0.70, size=0.06); scale_bar(ax, 1000, fx=0.10, fy=0.055)
    save(fig, "fig1_domain")


def fig2_lai():
    panels = [
        ("summer", "Default", D["npy_default_2003_regrillado_python"] / 10.0),
        ("summer", "MODIS v6.1 2003", D["npy_lai_2003_reprocesado_verano"] / 10.0),
        ("summer", "MODIS v6.1 2023", D["lai_modis2023_summer"]),
        ("winter", "Default", D["npy_default_2003_invierno_regrillado_python"] / 10.0),
        ("winter", "MODIS v6.1 2003", D["npy_lai_2003_reprocesado_invierno"] / 10.0),
        ("winter", "MODIS v6.1 2023", D["lai_modis2023_winter"]),
    ]
    cmap = mpl.colormaps["Greens"]; norm = mpl.colors.Normalize(0, 6)
    fig, axs = plt.subplots(1, 6, figsize=(PAGE_W, 2.75), gridspec_kw=dict(wspace=0.04))
    for i, (ax, (season, name, Z)) in enumerate(zip(axs, panels)):
        Z = np.where(Z < 0, np.nan, Z)
        setup_map(ax, left=(i == 0), bottom=True, lon_lab_step=20)
        pm = field(ax, Z, cmap, norm)
        outline(ax, 0.4)
        ax.set_title(f"({'abcdef'[i]}) {name}", fontsize=7, pad=2)
    fig.subplots_adjust(top=0.80)
    yh = axs[0].get_position().y1 + 0.075
    axs[0].figure.text(0.5 * (axs[0].get_position().x0 + axs[2].get_position().x1), yh,
                       "Summer (4–10 Jan 2023)", ha="center", va="bottom", fontsize=8, weight="bold")
    axs[0].figure.text(0.5 * (axs[3].get_position().x0 + axs[5].get_position().x1), yh,
                       "Winter (1–7 Aug 2023)", ha="center", va="bottom", fontsize=8, weight="bold")
    north_arrow(axs[0], fx=0.80, fy=0.88, size=0.08); scale_bar(axs[0], 500, fx=0.08, fy=0.03)
    cb = fig.colorbar(pm, ax=axs, orientation="vertical", fraction=0.015, pad=0.012, extend="max")
    cb.set_label("LAI (m$^2$ m$^{-2}$)"); cb.outline.set_linewidth(0.5)
    save(fig, "fig2_lai")


def fig3_ecoregions():
    names = list(ECO_COLORS)
    code = np.full((NY, NX), np.nan)
    for k, n in enumerate(names):
        code[(ECO == n) & MASK] = k
    code[MASK & np.isnan(code)] = len(names)
    cmap = ListedColormap([ECO_COLORS[n] for n in names] + ["#d9d9d9"])
    norm = BoundaryNorm(np.arange(len(names) + 2) - 0.5, cmap.N)
    fig, ax = plt.subplots(figsize=(COL_W, 3.6))
    setup_map(ax)
    field(ax, code, cmap, norm)
    outline(ax, 0.5)
    north_arrow(ax, fx=0.86, fy=0.90); scale_bar(ax, 500, fx=0.06, fy=0.03)
    counts = {n: int(((ECO == n) & MASK).sum()) for n in names}
    other = int(((ECO != "") & MASK).sum() - sum(counts.values()))   # 4 celdas sin ecorregion no se cuentan
    handles = [Patch(fc=ECO_COLORS[n], ec="white", lw=0.5,
                     label=f"{ECO_LABEL.get(n, n)} ({counts[n]})") for n in names]
    handles.append(Patch(fc="#d9d9d9", ec="white", lw=0.5, label=f"Other ecoregions ({other})"))
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False,
              title="Ecoregion (N cells)", title_fontsize=7, fontsize=7, handlelength=1.2,
              handleheight=1.0, labelspacing=0.5, alignment="left")
    save(fig, "fig3_ecoregions")


def _bias_maps(values, cmap, norm, cblabel, name, extend):
    fig, axs = plt.subplots(1, 2, figsize=(COL_W, 3.55), gridspec_kw=dict(wspace=0.05))
    for i, (ax, (title, Z)) in enumerate(zip(axs, values)):
        setup_map(ax, left=(i == 0))
        ax.add_patch(Rectangle((EXT[0], EXT[2]), EXT[1] - EXT[0], EXT[3] - EXT[2],
                               fc="#f4f4f4", ec="none", zorder=0))
        field(ax, np.ones((NY, NX)), ListedColormap(["#c8c8c8"]), None, MASK)   # sin emision Default
        pm = field(ax, Z, cmap, norm, MASK)
        eco_contours(ax)
        outline(ax, 0.45)
        ax.set_title(title, fontsize=8, pad=2)
    north_arrow(axs[0], fx=0.84, fy=0.90, size=0.075); scale_bar(axs[0], 500, fx=0.07, fy=0.03)
    cb = fig.colorbar(pm, ax=axs, orientation="horizontal", fraction=0.045, pad=0.07,
                      aspect=30, extend=extend)
    cb.set_label(cblabel); cb.outline.set_linewidth(0.5)
    save(fig, name)


def fig4_fig5(summer_version):
    dE, dP = {}, {}
    for s in ["summer", "winter"]:
        Dd, Mm = weekly(s, "default", summer_version), weekly(s, "modis", summer_version)
        dE[s] = Mm - Dd
        with np.errstate(divide="ignore", invalid="ignore"):
            dP[s] = np.where(Dd > 1e-6, 100 * (Mm - Dd) / Dd, np.nan)
    rb = mpl.colormaps["RdBu_r"]
    _bias_maps([("(a) Summer", dP["summer"]), ("(b) Winter", dP["winter"])], rb,
               mpl.colors.Normalize(-60, 60), r"$\Delta E$ (%)", "fig4_rel_bias", "both")
    v = np.nanpercentile(np.abs(dE["summer"][MASK]), 99)
    v = float(np.ceil(v / 100) * 100)
    _bias_maps([("(a) Summer", dE["summer"]), ("(b) Winter", dE["winter"])], rb,
               mpl.colors.Normalize(-v, v), r"$\Delta E$ (kmol week$^{-1}$)", "fig5_abs_bias", "both")
    return dE, dP


def fig6_temporal(summer_version):
    R = D["npy_daily_hourly_results"].item()
    if summer_version == "rerun":                       # recalcula con la corrida nueva
        c = D["isop_hourly_summer_default"].astype("f8")[:, :, MASK].sum(axis=2)
        R["Summer"]["hourly_D"] = c
        R["Summer"]["daily_D"] = c.sum(axis=1)
    fig, axs = plt.subplots(2, 2, figsize=(COL_W, 3.3), gridspec_kw=dict(hspace=0.55, wspace=0.42))
    dates = {"Summer": [f"{d}" for d in range(4, 11)], "Winter": [f"{d}" for d in range(1, 8)]}
    month = {"Summer": "January 2023", "Winter": "August 2023"}
    for j, S in enumerate(["Summer", "Winter"]):
        ax = axs[0, j]
        dD = R[S]["daily_D"] * 3.6 / 1e3; dM = R[S]["daily_M"] * 3.6 / 1e3   # 10^3 kmol/day
        x = np.arange(1, 8)
        ax.fill_between(x, dM, dD, color="#bdbdbd", alpha=0.6, lw=0, label=r"$\Delta E$")
        ax.plot(x, dD, "-o", color=C_DEFAULT, ms=3, label="Default")
        ax.plot(x, dM, "-s", color=C_MODIS, ms=3, label="MODIS 2023")
        ax.set_xticks(x); ax.set_xticklabels(dates[S]); ax.set_xlabel(f"Day ({month[S]})")
        ax.set_title(f"({'ab'[j]}) {S}, daily", loc="left", pad=3)
        ax = axs[1, j]
        hD = R[S]["hourly_D"] / 1e3; hM = R[S]["hourly_M"] / 1e3                   # kmol/s
        hr = np.arange(24)
        for arr, col, lab in [(hD, C_DEFAULT, "Default"), (hM, C_MODIS, "MODIS 2023")]:
            mu, sd = arr.mean(0), arr.std(0)
            ax.fill_between(hr, mu - sd, mu + sd, color=col, alpha=0.18, lw=0)
            ax.plot(hr, mu, color=col, label=lab)
        ax.set_xticks([0, 6, 12, 18, 24]); ax.set_xlim(0, 23); ax.set_xlabel("Hour (UTC)")
        ax.set_title(f"({'cd'[j]}) {S}, diurnal", loc="left", pad=3)
    axs[0, 0].set_ylabel(r"ISOP ($10^3$ kmol day$^{-1}$)")
    axs[1, 0].set_ylabel(r"ISOP (kmol s$^{-1}$)")
    for ax in axs.flat:
        ax.grid(axis="y", color="#e5e5e5", lw=0.5); ax.set_axisbelow(True)
        ax.set_ylim(bottom=0 if ax in axs[1] else None)
    h1, l1 = axs[0, 0].get_legend_handles_labels()
    fig.legend(h1, l1, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.03))
    save(fig, "fig6_temporal")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--summer", choices=["paper", "rerun"], default="paper",
                    help="corrida Default de verano: la del paper o la re-corrida del 26/06")
    ap.add_argument("--out", default=FIG, help="carpeta de salida (por defecto figures/)")
    a = ap.parse_args()
    FIG = os.path.abspath(a.out)
    print(f"Mascara Argentina: {MASK.sum()} celdas | Default verano: {a.summer}")
    fig1_domain(); fig2_lai(); fig3_ecoregions()
    dE, dP = fig4_fig5(a.summer); fig6_temporal(a.summer)
    for s in ["summer", "winter"]:
        print(f"  {s}: dE min/max celda = {np.nanmin(dE[s][MASK]):.0f} / {np.nanmax(dE[s][MASK]):.0f} kmol;"
              f" dE% mediana Patagonian steppe = "
              f"{np.nanmedian(dP[s][(ECO == 'Patagonian steppe') & MASK]):.1f} %")
