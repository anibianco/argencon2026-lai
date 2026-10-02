#!/usr/bin/env python
"""
Genera las figuras del paper ARGENCON #327 a partir de data/raw/.

    python scripts/make_figures.py                 # version del paper (Default verano original)
    python scripts/make_figures.py --summer rerun  # Default verano re-corrido el 26/06 22:26

Salida: figures/fig*.pdf (vectorial, fuentes embebidas).
Estilo: el de las figuras originales del manuscrito (lat/lon), con norte, escala,
leyendas mas grandes y contornos de ecorregiones pedidos por los revisores.

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
from matplotlib.patches import Patch, Rectangle
from shapely import contains_xy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
FIG = os.path.join(ROOT, "figures")

# ------------------------------------------------------------------ estilo
# Estilo de las figuras originales (matplotlib por defecto, mapas en lat/lon), con los
# agregados pedidos por los revisores: norte, escala, leyendas mas grandes y contornos
# de ecorregiones en los mapas de sesgo.
COL_W, PAGE_W = 3.5, 7.16          # ancho de columna / de pagina IEEE (in)
mpl.rcParams.update({
    # figuras generadas al tamano final del paper: estos tamanos son los que se imprimen
    "font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "pdf.fonttype": 42, "savefig.dpi": 600,
})
C_DEFAULT, C_MODIS = "steelblue", "firebrick"
ECO_COLORS = {                      # colores de la figura original
    "Dry Chaco": "#8B4513", "Humid Chaco": "#228B22", "Humid Pampas": "#FFD700",
    "Espinal": "#FF8C00", "Patagonian steppe": "#4682B4",
}
ECO_LABEL = {"Patagonian steppe": "Patagonian Steppe"}
OTHER_C = "lightgray"

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



# coordenadas geograficas de bordes y centros de celda
XE, YE = np.meshgrid(xe, ye)
LONE, LATE = TO_LL.transform(XE, YE)            # (NY+1, NX+1)
LONC, LATC = TO_LL.transform(XC, YC)            # (NY, NX)
ARG_LL = gpd.GeoSeries([ARG_GEOM], crs=CRS).to_crs("EPSG:4326").simplify(0.01)

EXT_DOMAIN = (-84.5, -41.5, -62, -17.5)         # dominio completo (Fig. 1 y LAI)
EXT_ARG = (-74, -53.3, -55.5, -21.3)            # Argentina (mapas de sesgo y ecorregiones)


# ------------------------------------------------------------------ helpers de mapa
def setup_map(ax, extent, xlabel=True, ylabel=True, step=5):
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
    ax.set_aspect(1 / np.cos(np.deg2rad(0.5 * (extent[2] + extent[3]))))
    ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(step))
    ax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(5))
    ax.set_xlabel("Longitude" if xlabel else "")
    ax.set_ylabel("Latitude" if ylabel else "")


def outline(ax, lw=0.7, color="black"):
    ARG_LL.boundary.plot(ax=ax, color=color, lw=lw, zorder=5)


def north_arrow(ax, fx=0.88, fy=0.88, size=0.08):
    ax.annotate("N", xy=(fx, fy + size), xytext=(fx, fy), xycoords="axes fraction",
                ha="center", va="top", fontsize=7.5, fontweight="bold", zorder=10,
                arrowprops=dict(facecolor="black", edgecolor="black", width=1.4,
                                headwidth=5, headlength=5))


def scale_bar(ax, km=500, fx=0.06, fy=0.05):
    """Barra de escala en km, correcta a la latitud donde se dibuja."""
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    lon, lat = x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)
    dlon = km / (111.32 * np.cos(np.deg2rad(lat)))
    H = 0.012 * (y1 - y0)
    for i in range(2):
        ax.add_patch(Rectangle((lon + i * dlon / 2, lat), dlon / 2, H,
                               fc="black" if i == 0 else "white", ec="black", lw=0.6, zorder=10))
    ax.text(lon + dlon / 2, lat + 1.8 * H, f"{km} km", ha="center", va="bottom",
            fontsize=6.5, zorder=10)


def field(ax, Z, cmap, norm, mask=None):
    Z = np.array(Z, dtype=float)
    if mask is not None:
        Z = np.where(mask, Z, np.nan)
    return ax.pcolormesh(LONE, LATE, np.ma.masked_invalid(Z), cmap=cmap, norm=norm,
                         shading="flat", rasterized=True, zorder=2)


def dots(ax, Z, cmap, norm, s=2.6):
    """Celdas como puntos (estilo de las Figs. 4 y 5 originales)."""
    ok = MASK & np.isfinite(Z)
    return ax.scatter(LONC[ok], LATC[ok], c=Z[ok], cmap=cmap, norm=norm, s=s,
                      marker="o", linewidths=0, rasterized=True, zorder=3)


def eco_contours(ax, color="0.15", lw=0.45):
    """Limites entre ecorregiones (las 5 principales + 'otras') sobre la grilla."""
    from matplotlib.collections import LineCollection
    code = np.full((NY, NX), -1)
    for k, n in enumerate(ECO_COLORS):
        code[(ECO == n) & MASK] = k
    code[MASK & (code < 0)] = 99
    segs = []
    for j in range(NY):
        for i in range(NX - 1):
            if code[j, i] != code[j, i + 1] and min(code[j, i], code[j, i + 1]) >= 0:
                segs.append([(LONE[j, i + 1], LATE[j, i + 1]), (LONE[j + 1, i + 1], LATE[j + 1, i + 1])])
    for j in range(NY - 1):
        for i in range(NX):
            if code[j, i] != code[j + 1, i] and min(code[j, i], code[j + 1, i]) >= 0:
                segs.append([(LONE[j + 1, i], LATE[j + 1, i]), (LONE[j + 1, i + 1], LATE[j + 1, i + 1])])
    ax.add_collection(LineCollection(segs, colors=color, linewidths=lw, zorder=4,
                                     linestyles=(0, (3, 1.5))))


def save(fig, name):
    os.makedirs(FIG, exist_ok=True)
    p = os.path.join(FIG, name + ".pdf")
    fig.savefig(p, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print("  ", os.path.relpath(p, ROOT))


# ------------------------------------------------------------------ figuras
def fig1_domain():
    fig, ax = plt.subplots(figsize=(2.6, 2.8))
    ax.scatter(LONC.ravel(), LATC.ravel(), s=0.5, c="lightgray", lw=0, rasterized=True,
               label=f"MEGAN domain ({NX}×{NY}, trimmed from WRF)", zorder=1)
    ax.scatter(LONC[MASK], LATC[MASK], s=1.3, c="steelblue", lw=0, rasterized=True,
               label="Argentina continental mask", zorder=2)
    # borde del dominio WRF crudo (una celda mas por lado)
    xw = np.r_[xe[0] - DX, xe[-1] + DX]; yw = np.r_[ye[0] - DX, ye[-1] + DX]
    t = np.linspace(0, 1, 100)
    bx = np.r_[xw[0] + t * (xw[1] - xw[0]), np.full(100, xw[1]), xw[1] - t * (xw[1] - xw[0]), np.full(100, xw[0])]
    by = np.r_[np.full(100, yw[0]), yw[0] + t * (yw[1] - yw[0]), np.full(100, yw[1]), yw[1] - t * (yw[1] - yw[0])]
    blon, blat = TO_LL.transform(bx, by)
    ax.plot(blon, blat, "r--", lw=1.0, label=f"Raw WRF domain boundary ({NX + 2}×{NY + 2})", zorder=4)
    lon0, lon1, lat0, lat1 = -78.6, -50.5, -57.7, -20.4    # extension de descarga MODIS
    ax.plot([lon0, lon1, lon1, lon0, lon0], [lat0, lat0, lat1, lat1, lat0], color="green", lw=1.0,
            label="MODIS MCD15A2H download extent", zorder=4)
    setup_map(ax, (-87, -40, -63.5, -16), step=10)
    north_arrow(ax, fx=0.92, fy=0.86); scale_bar(ax, 1000, fx=0.58, fy=0.27)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), fontsize=6.5, markerscale=4,
              frameon=False, handlelength=2.2)
    save(fig, "fig1_domain")


def fig2_lai():
    panels = [
        D["npy_default_2003_regrillado_python"] / 10.0,
        D["npy_lai_2003_reprocesado_verano"] / 10.0,
        D["lai_modis2023_summer"],
        D["npy_default_2003_invierno_regrillado_python"] / 10.0,
        D["npy_lai_2003_reprocesado_invierno"] / 10.0,
        D["lai_modis2023_winter"],
    ]
    cols = ["Default\n(MEGAN clim. ~2003)", "MODIS v6.1 2003\n(new algorithm)",
            "MODIS v6.1 2023\n(new algorithm)"]
    rows = ["Summer (4–10 Jan 2023)", "Winter (1–7 Aug 2023)"]
    fig, axs = plt.subplots(2, 3, figsize=(5.4, 5.0),
                            gridspec_kw=dict(wspace=0.06, hspace=0.06))
    norm = mpl.colors.Normalize(0, 6.5)
    for k, (ax, Z) in enumerate(zip(axs.flat, panels)):
        r, c = divmod(k, 3)
        Z = np.where(Z < 0, np.nan, Z)
        pm = field(ax, Z, "YlGn", norm)
        outline(ax, 0.45)
        setup_map(ax, EXT_DOMAIN, xlabel=(r == 1), ylabel=False, step=10)
        if r == 0:
            ax.set_title(cols[c])
        if c == 0:
            ax.set_ylabel(f"{rows[r]}\nLatitude")
        else:
            ax.tick_params(labelleft=False)
        if r == 0:
            ax.tick_params(labelbottom=False)
    north_arrow(axs[0, 0], fx=0.88, fy=0.30); scale_bar(axs[0, 0], 500, fx=0.62, fy=0.08)
    cb = fig.colorbar(pm, ax=axs, orientation="vertical", fraction=0.025, pad=0.02, shrink=0.8)
    cb.set_label("LAI (m$^2$ m$^{-2}$)")
    save(fig, "fig2_lai")


def fig3_ecoregions():
    names = list(ECO_COLORS)
    code = np.full((NY, NX), np.nan)
    for k, n in enumerate(names):
        code[(ECO == n) & MASK] = k
    code[MASK & np.isnan(code)] = len(names)
    cmap = ListedColormap([ECO_COLORS[n] for n in names] + [OTHER_C])
    norm = BoundaryNorm(np.arange(len(names) + 2) - 0.5, cmap.N)
    fig, ax = plt.subplots(figsize=(2.6, 2.4))
    field(ax, code, cmap, norm)
    outline(ax, 0.5)
    setup_map(ax, EXT_ARG)
    north_arrow(ax, fx=0.13, fy=0.84); scale_bar(ax, 500, fx=0.58, fy=0.015)
    handles = [Patch(fc=ECO_COLORS[n], ec="black", lw=0.4, label=ECO_LABEL.get(n, n)) for n in names]
    handles.append(Patch(fc=OTHER_C, ec="black", lw=0.4, label="Other ecoregions"))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2,
              fontsize=6.5, frameon=False, handlelength=1.3, columnspacing=0.8, labelspacing=0.3)
    save(fig, "fig3_ecoregions")


def _bias_maps(values, cmap, norm, cblabel, name, extend):
    fig, axs = plt.subplots(1, 2, figsize=(3.3, 2.75), sharey=True,
                            gridspec_kw=dict(wspace=0.06))
    for i, (ax, (title, Z)) in enumerate(zip(axs, values)):
        pm = dots(ax, Z, cmap, norm)
        eco_contours(ax)
        outline(ax, 0.5, "0.4")
        setup_map(ax, EXT_ARG, ylabel=(i == 0))
        ax.set_title(title)
    north_arrow(axs[0], fx=0.88, fy=0.86); scale_bar(axs[0], 500, fx=0.58, fy=0.015)
    cb = fig.colorbar(pm, ax=axs, orientation="vertical", fraction=0.04, pad=0.02, extend=extend)
    cb.set_label(cblabel)
    save(fig, name)


def fig4_fig5(summer_version):
    dE, dP = {}, {}
    for s in ["summer", "winter"]:
        Dd, Mm = weekly(s, "default", summer_version), weekly(s, "modis", summer_version)
        dE[s] = Mm - Dd
        with np.errstate(divide="ignore", invalid="ignore"):
            dP[s] = np.where(Dd > 1e-6, 100 * (Mm - Dd) / Dd, np.nan)
    _bias_maps([("(a) Summer", dP["summer"]), ("(b) Winter", dP["winter"])], "RdBu_r",
               mpl.colors.Normalize(-60, 60), r"$\Delta$E (%)", "fig4_rel_bias", "both")
    v = np.nanpercentile(np.abs(dE["summer"][MASK]), 99)
    v = float(np.ceil(v / 100) * 100)
    _bias_maps([("(a) Summer", dE["summer"]), ("(b) Winter", dE["winter"])], "RdBu_r",
               mpl.colors.Normalize(-v, v), r"$\Delta$E (kmol)", "fig5_abs_bias", "both")
    return dE, dP


def fig6_temporal(summer_version):
    R = D["npy_daily_hourly_results"].item()
    if summer_version == "rerun":
        c = D["isop_hourly_summer_default"].astype("f8")[:, :, MASK].sum(axis=2)
        R["Summer"]["hourly_D"] = c
        R["Summer"]["daily_D"] = c.sum(axis=1)
    fig, axs = plt.subplots(4, 1, figsize=(2.2, 5.6), gridspec_kw=dict(hspace=0.95))
    x = np.arange(1, 8); hr = np.arange(24)
    for j, S in enumerate(["Summer", "Winter"]):
        ax = axs[j]
        dD = R[S]["daily_D"] * 3.6 / 1e3; dM = R[S]["daily_M"] * 3.6 / 1e3   # 10^3 kmol/day
        ax.fill_between(x, dM, dD, color="gray", alpha=0.3, label="ΔE gap")
        ax.plot(x, dD, "-o", color=C_DEFAULT, lw=1.1, ms=3, label="Default")
        ax.plot(x, dM, "-s", color=C_MODIS, lw=1.1, ms=3, label="MODIS")
        ax.set_title(f"({'ab'[j]}) Daily totals — {S}")
        ax.set_xlabel("Day of simulated week"); ax.set_ylabel("ISOP (×10³ kmol/day)")
        ax.set_xticks(x)
        ax.legend(loc="upper left" if j == 0 else "upper center", fontsize=6, handlelength=1.5,
                  borderpad=0.3, labelspacing=0.25)
        ax = axs[2 + j]
        for arr, col, lab in [(R[S]["hourly_D"] / 1e3, C_DEFAULT, "Default (mean)"),
                              (R[S]["hourly_M"] / 1e3, C_MODIS, "MODIS (mean)")]:
            mu, sd = arr.mean(0), arr.std(0)
            ax.fill_between(hr, mu - sd, mu + sd, color=col, alpha=0.2)
            ax.plot(hr, mu, color=col, lw=1.1, label=lab)
        ax.set_title(f"({'cd'[j]}) Mean diurnal cycle — {S}")
        ax.set_xlabel("Hour of day (UTC)"); ax.set_ylabel("ISOP (kmol/s)")
        ax.set_xticks([0, 4, 8, 12, 16, 20]); ax.set_ylim(bottom=0)
        ax.legend(loc="upper left", fontsize=6, handlelength=1.5, borderpad=0.3, labelspacing=0.25)
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
