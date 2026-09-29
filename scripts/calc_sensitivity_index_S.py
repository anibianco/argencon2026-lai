"""
Calcula el índice de sensibilidad normalizado S entre LAI e ISOP, píxel a píxel,
para las 4 corridas MEGAN v3.21 (MODIS/Default x verano/invierno) del dominio ARG_30km.

    S = (ΔE / E_default) / (ΔLAI / LAI_default)

Interpretación:
    S ≈ 0  -> ISOP casi insensible al cambio de LAI en ese píxel
    S ≈ 1  -> respuesta proporcional (1% de cambio en LAI = 1% de cambio en ISOP)
    S > 1  -> alta sensibilidad (amplifica el cambio de LAI)
    S < 0  -> respuesta inversa (raro, revisar si aparece - puede indicar saturación
              de luz/temperatura dominando sobre el efecto de área foliar)

Requiere: xarray, numpy, pandas, netCDF4 (backend de xarray)
    pip install xarray pandas netCDF4 --break-system-packages   (si falta alguno)

Autor: script generado para Ani (ARGENCON paper, sensibilidad ISOP)
"""

import numpy as np
import pandas as pd
import xarray as xr

# =====================================================================
# 1. CONFIGURACIÓN — AJUSTAR ESTAS RUTAS A TU ESTRUCTURA REAL EN MENDIETA
# =====================================================================

BASE = "/home/abianco/MEGANv3.21"

# Carpetas reales de las 4 corridas (confirmadas en sesiones anteriores).
# OJO: cada corrida vive en su propia carpeta autocontenida, NO todas bajo
# MEGANv3.21/Output/ como supuse al principio.
RUN_DIRS = {
    ("modis",   "verano"):   "/home/abianco/MEGAN_verano2023/MEGAN",
    ("default", "verano"):   "/home/abianco/MEGAN_verano2023_LAIdefault/MEGAN",
    ("modis",   "invierno"): "/home/abianco/MEGAN_invierno2023/MEGAN",
    ("default", "invierno"): "/home/abianco/MEGAN_invierno2023_LAIdefault/MEGAN",
}

# mgn2mech (step7) escribe UN ARCHIVO POR DÍA en Output/FINAL/, con el patrón:
#   MEGANv32.ARG_30km.CB6X.<DOY 7 dígitos AAAADDD>.BDSNP.ncf
# Confirmado en log real: .../Output/FINAL/MEGANv32.ARG_30km.CB6X.2023004.BDSNP.ncf
# Por eso ISOP_FILES ahora es una LISTA de archivos diarios por corrida, no un
# archivo único con 7 días concatenados (ese supuesto era incorrecto).
DOY_RANGES = {
    "verano":   range(4, 11),    # DOY 004-010
    "invierno": range(213, 220),  # DOY 213-219
}

def _isop_daily_files(modis_o_default, season):
    run_dir = RUN_DIRS[(modis_o_default, season)]
    return [
        f"{run_dir}/Output/FINAL/MEGANv32.ARG_30km.CB6X.2023{doy:03d}.BDSNP.ncf"
        for doy in DOY_RANGES[season]
    ]

ISOP_FILES = {
    ("modis",   "verano"):   _isop_daily_files("modis", "verano"),
    ("default", "verano"):   _isop_daily_files("default", "verano"),
    ("modis",   "invierno"): _isop_daily_files("modis", "invierno"),
    ("default", "invierno"): _isop_daily_files("default", "invierno"),
}

# LAI que efectivamente usó megcan en cada corrida: vive DENTRO de la carpeta
# de cada corrida (Input/MAP/LAI3_ARG_30km.ncf), no en una carpeta global
# compartida. Tiene 46 variables LAI01..LAI46 en formato IOAPI (confirmado).
LAI_FILES = {
    key: f"{run_dir}/Input/MAP/LAI3_ARG_30km.ncf"
    for key, run_dir in RUN_DIRS.items()
}

# Tanto el LAI default como el LAI MODIS quedaron reconstruidos en el MISMO
# formato IOAPI de 46 variables LAI01..LAI46 (el MODIS se armó usando el
# default como template estructural). Por eso aplicamos el MISMO promedio
# ponderado por período a los dos, no un nombre de variable único para MODIS.
# OJO: para MODIS hay que confirmar con chequeo_archivos.sh si los períodos
# fuera de la semana de estudio están vacíos/repetidos o tienen datos reales
# de otras fechas (no debería importar para este cálculo, pero conviene saber).
LAI_PERIODS = {
    "verano":   [("LAI01", 5 / 7), ("LAI02", 2 / 7)],
    "invierno": [("LAI27", 4 / 7), ("LAI28", 3 / 7)],
}

# Variable ISOP dentro del archivo de salida de mgn2mech
ISOP_VAR = "ISOP"

# Tabla celda -> ecoregión (la que ya armaste con el spatial join Olson 2001)
ECOREGION_CSV = f"{BASE}/Input/MAP/grid_to_ecoregion.csv"
# Ajustar nombres de columna reales:
COL_ROW = "ROW"
COL_COL = "COL"
COL_ECOREGION = "ecoregion"

# Umbral mínimo de celdas para que una ecoregión entre en la tabla principal
MIN_CELDAS = 20

OUTPUT_DIR = f"{BASE}/../ARGENCON_figuras"  # ajustar si tu carpeta de salida es otra


# =====================================================================
# 2. FUNCIONES DE CARGA
# =====================================================================

def load_isop_daily_total(file_list, varname=ISOP_VAR):
    """
    Carga los archivos diarios de salida de mgn2mech (uno por DOY) y devuelve
    el TOTAL DIARIO PROMEDIO de la semana, sumando los 24 timesteps horarios
    de CADA archivo (recordá el bug de timestep: sumar solo el timestep 0 da
    prácticamente cero) y promediando esos totales diarios entre los 7 días.

    file_list: lista de paths, uno por día (ej. DOY004..DOY010 para verano).

    Trabajamos siempre en UTC: el TSTEP del archivo IOAPI/CMAQ está en UTC por
    convención (TSTEP=0 NO es medianoche hora local de Argentina, es la hora
    de referencia SDATE/STIME del archivo, típicamente UTC). No corregimos ese
    desfasaje horario en ningún punto del cálculo, según decisión explícita.

    Devuelve un array 2D (ROW, COL).
    """
    daily_totals = []
    for path in file_list:
        ds = xr.open_dataset(path)
        data = ds[varname]  # dims esperadas: (TSTEP, LAY, ROW, COL) o (TSTEP, ROW, COL)

        if "LAY" in data.dims:
            data = data.isel(LAY=0)

        n_tstep = data.sizes["TSTEP"]
        if n_tstep != 24:
            raise ValueError(
                f"{path}: TSTEP={n_tstep}, se esperaban 24 (un archivo por día). "
                f"Revisar si este archivo en realidad contiene más de un día."
            )

        daily_totals.append(data.sum(dim="TSTEP"))

    weekly_mean_daily_total = xr.concat(daily_totals, dim="day").mean(dim="day")
    return weekly_mean_daily_total.values  # (ROW, COL)


def load_lai(path, varname):
    """Carga una variable LAI 2D (ROW, COL) de un archivo IOAPI/netCDF."""
    ds = xr.open_dataset(path)
    data = ds[varname]
    # Si tiene dimensión temporal residual, tomamos el primer/único timestep
    for extra_dim in ("TSTEP", "LAY", "time"):
        if extra_dim in data.dims and data.sizes[extra_dim] == 1:
            data = data.isel({extra_dim: 0})
    return data.values  # (ROW, COL)


def load_lai_weighted(path, periods):
    """
    Carga el LAI default como promedio PONDERADO de dos (o más) períodos de
    8 días, cuando la semana de estudio cae repartida entre ellos.

    periods: lista de tuplas (nombre_variable, peso), donde los pesos suman 1.
             Ej: [("LAI01", 5/7), ("LAI02", 2/7)]

    Esto evita el sesgo de "quedarte con el período que tiene mayoría de días",
    que sería arbitrario cuando el reparto es parejo (p.ej. 4 días vs 3 días).
    """
    pesos = [w for _, w in periods]
    assert abs(sum(pesos) - 1.0) < 1e-6, f"Los pesos no suman 1: {pesos}"

    acumulado = None
    for varname, peso in periods:
        capa = load_lai(path, varname)
        acumulado = capa * peso if acumulado is None else acumulado + capa * peso

    return acumulado


# =====================================================================
# 3. CÁLCULO DEL ÍNDICE S PÍXEL A PÍXEL
# =====================================================================

def calc_sensitivity_index(E_default, E_modis, LAI_default, LAI_modis):
    """
    Calcula ΔE%, ΔLAI% y S = (ΔE/E_default) / (ΔLAI/LAI_default), píxel a píxel.

    Enmascara (NaN) los píxeles donde:
      - E_default == 0  (no se puede calcular ΔE/E_default)
      - LAI_default == 0 (no se puede calcular ΔLAI/LAI_default, división por cero)
      - ΔLAI ≈ 0 (S no está definido / sería ±infinito; sin cambio de LAI no hay
        forma de medir sensibilidad en ese píxel, aunque ΔE también sea ~0)
    """
    dE = E_modis - E_default
    dLAI = LAI_modis - LAI_default

    with np.errstate(divide="ignore", invalid="ignore"):
        dE_pct = np.where(E_default != 0, dE / E_default, np.nan)
        dLAI_pct = np.where(LAI_default != 0, dLAI / LAI_default, np.nan)

        # Umbral pequeño para evitar división por valores casi-cero que disparan
        # S a valores absurdos (p.ej. ΔLAI=0.001 con ΔE moderado da S=500)
        eps = 1e-6
        S = np.where(np.abs(dLAI_pct) > eps, dE_pct / dLAI_pct, np.nan)

    return dE, dE_pct, dLAI, dLAI_pct, S


# =====================================================================
# 4. AGREGACIÓN POR ECOREGIÓN
# =====================================================================

def aggregate_by_ecoregion(S, dE_pct, dLAI_pct, ecoregion_csv, min_celdas=MIN_CELDAS):
    """
    Aplana las matrices 2D a una tabla por celda, las une con la clasificación
    de ecoregión (el mismo grid_to_ecoregion.csv usado en el modelo), y calcula
    media/mediana de S y ΔE% por ecoregión. Filtra por N mínimo de celdas.
    """
    eco = pd.read_csv(ecoregion_csv)

    nrows, ncols = S.shape
    rows, cols = np.meshgrid(np.arange(nrows), np.arange(ncols), indexing="ij")

    df = pd.DataFrame({
        COL_ROW: rows.ravel(),
        COL_COL: cols.ravel(),
        "S": S.ravel(),
        "dE_pct": dE_pct.ravel() * 100,
        "dLAI_pct": dLAI_pct.ravel() * 100,
    })

    merged = df.merge(eco[[COL_ROW, COL_COL, COL_ECOREGION]], on=[COL_ROW, COL_COL], how="left")

    summary = (
        merged.dropna(subset=["S"])
        .groupby(COL_ECOREGION)
        .agg(
            N=("S", "size"),
            S_media=("S", "mean"),
            S_mediana=("S", "median"),
            dE_pct_media=("dE_pct", "mean"),
            dLAI_pct_media=("dLAI_pct", "mean"),
        )
        .reset_index()
        .sort_values("N", ascending=False)
    )

    summary["incluida_en_tabla_principal"] = summary["N"] >= min_celdas
    return merged, summary


# =====================================================================
# 5. EJECUCIÓN PRINCIPAL
# =====================================================================

def run_for_season(season):
    print(f"\n=== Procesando temporada: {season} ===")

    E_default = load_isop_daily_total(ISOP_FILES[("default", season)])
    E_modis = load_isop_daily_total(ISOP_FILES[("modis", season)])

    LAI_default = load_lai_weighted(LAI_FILES[("default", season)], LAI_PERIODS[season])
    LAI_modis = load_lai_weighted(LAI_FILES[("modis", season)], LAI_PERIODS[season])

    # Chequeo rápido de dimensiones consistentes (77x157 esperado)
    assert E_default.shape == E_modis.shape == LAI_default.shape == LAI_modis.shape, (
        f"Dimensiones inconsistentes: E_default={E_default.shape}, "
        f"E_modis={E_modis.shape}, LAI_default={LAI_default.shape}, "
        f"LAI_modis={LAI_modis.shape}"
    )

    dE, dE_pct, dLAI, dLAI_pct, S = calc_sensitivity_index(
        E_default, E_modis, LAI_default, LAI_modis
    )

    print(f"  S nacional (media, excluyendo NaN): {np.nanmean(S):.3f}")
    print(f"  S nacional (mediana): {np.nanmedian(S):.3f}")
    print(f"  Píxeles con S definido: {np.sum(~np.isnan(S))} de {S.size}")

    merged, summary = aggregate_by_ecoregion(S, dE_pct, dLAI_pct, ECOREGION_CSV)

    out_csv = f"{OUTPUT_DIR}/sensitivity_S_{season}.csv"
    summary.to_csv(out_csv, index=False)
    print(f"  Tabla por ecoregión guardada en: {out_csv}")

    # Guardamos también el mapa S píxel a píxel en netCDF para graficar después
    out_nc = f"{OUTPUT_DIR}/sensitivity_S_{season}.nc"
    xr.Dataset({"S": (["ROW", "COL"], S), "dE_pct": (["ROW", "COL"], dE_pct * 100)}).to_netcdf(out_nc)
    print(f"  Mapa S (netCDF) guardado en: {out_nc}")

    return summary


if __name__ == "__main__":
    resumen_verano = run_for_season("verano")
    resumen_invierno = run_for_season("invierno")

    print("\n=== Resumen verano (top 10 por N) ===")
    print(resumen_verano.head(10).to_string(index=False))

    print("\n=== Resumen invierno (top 10 por N) ===")
    print(resumen_invierno.head(10).to_string(index=False))
