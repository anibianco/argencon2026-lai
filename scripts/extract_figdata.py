#!/usr/bin/env python
"""
Extrae de las corridas MEGAN en mendieta todo lo necesario para regenerar
las figuras del paper ARGENCON #327, en un unico archivo comprimido.

Uso (en mendieta):
    python extract_figdata.py
Salida:
    ~/ARGENCON_figuras/figdata_argencon.npz   (~20-40 MB)

Solo requiere numpy y netCDF4.
"""
import os
import numpy as np
import netCDF4 as nc

H = os.path.expanduser("~")
R = os.path.join(H, "MEGAN2023")   # carpeta que contiene las 4 corridas
OUT = os.path.join(H, "ARGENCON_figuras", "figdata_argencon.npz")

RUNS = {
    "summer_modis":   "MEGAN_verano2023",
    "summer_default": "MEGAN_verano2023_LAIdefault",
    "winter_modis":   "MEGAN_invierno2023",
    "winter_default": "MEGAN_invierno2023_LAIdefault",
}
DOYS = {"summer": range(4, 11), "winter": range(213, 220)}   # semanas simuladas
LAIVAR = {"summer": "LAI01", "winter": "LAI27"}             # composites MODIS usados

out, log = {}, []
hdr_done = False

# ---------------- ISOP horario (mol/s) ----------------
for key, rundir in RUNS.items():
    season = key.split("_")[0]
    cube = []
    for doy in DOYS[season]:
        f = f"{R}/{rundir}/MEGAN/Output/FINAL/MEGANv32.ARG_30km.CB6X.2023{doy:03d}.BDSNP.ncf"
        with nc.Dataset(f) as ds:
            v = ds.variables["ISOP"]
            x = np.array(v[:, 0, :, :], dtype="f8")          # (TSTEP, ROW, COL)
            if x.shape[0] > 24:
                log.append(f"{os.path.basename(f)}: {x.shape[0]} pasos, uso los primeros 24")
                x = x[:24]
            cube.append(x.astype("f4"))
            if not hdr_done:
                for a in ["P_ALP", "P_BET", "P_GAM", "XCENT", "YCENT", "XORIG", "YORIG",
                          "XCELL", "YCELL", "NCOLS", "NROWS", "GDTYP"]:
                    out["hdr_" + a] = np.array(getattr(ds, a))
                out["isop_units"] = np.array(getattr(v, "units", "").strip())
                hdr_done = True
    cube = np.stack(cube)                                   # (7, 24, ROW, COL)
    out[f"isop_hourly_{key}"] = cube
    wk = cube.astype("f8").sum(axis=(0, 1)) * 3600.0 / 1000.0   # kmol/semana por celda
    out[f"isop_weekly_kmol_{key}"] = wk
    log.append(f"{key}: cubo {cube.shape}, total dominio = {wk.sum():,.0f} kmol")

# ---------------- LAI ----------------
def read_lai(path, var, scale=1.0):
    with nc.Dataset(path) as ds:
        return np.array(ds.variables[var][0, 0, :, :], dtype="f4") * scale

for season, tag in [("summer", "verano"), ("winter", "invierno")]:
    var = LAIVAR[season]
    p_def = f"{R}/MEGAN_{tag}2023_LAIdefault/MEGAN/Input/MAP/LAI3_ARG_30km_PYTHONREGRID.ncf"
    p_m23 = f"{R}/MEGAN_{tag}2023/LAI/processed/LAI3_ARG_30km_{tag}2023.ncf"
    for name, p, sc in [("default_laiv", p_def, 0.1), ("modis2023", p_m23, 1.0)]:
        try:
            out[f"lai_{name}_{season}"] = read_lai(p, var, sc)
            log.append(f"LAI {name} {season}: OK ({var})")
        except Exception as e:
            log.append(f"LAI {name} {season}: FALLO -> {e}")

# arrays ya procesados para la figura de LAI (los mismos que usa la Fig. 2 actual)
fw = f"{H}/ARGENCON_figuras/FINAL_weekmean"
for fn in ["default_2003_regrillado_python.npy", "default_2003_invierno_regrillado_python.npy",
           "lai_2003_reprocesado_verano.npy", "lai_2003_reprocesado_invierno.npy",
           "daily_hourly_results.npy"]:
    try:
        out["npy_" + fn[:-4]] = np.load(os.path.join(fw, fn), allow_pickle=True)
        log.append(f"{fn}: OK")
    except Exception as e:
        log.append(f"{fn}: FALLO -> {e}")

np.savez_compressed(OUT, **out)
print("\n".join(log))
print(f"\nGuardado: {OUT}  ({os.path.getsize(OUT)/1e6:.1f} MB)")
print("Tabla I del paper: Default verano 7894248 / invierno 1462273 kmol (solo Argentina;"
      " los totales de arriba son del dominio completo, deben ser MAYORES).")
