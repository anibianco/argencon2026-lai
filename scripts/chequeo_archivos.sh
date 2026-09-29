#!/bin/bash
# ============================================================
# Inspección rápida de estructura de archivos antes de correr
# calc_sensitivity_index_S.py
#
# Uso: ajustar las rutas abajo y correr en mendieta:
#   bash chequeo_archivos.sh
# ============================================================

echo "##############################################"
echo "# 1. ISOP - salida de mgn2mech (las 4 corridas)"
echo "# OJO: hay UN ARCHIVO POR DÍA en Output/FINAL/, no uno por semana"
echo "##############################################"
for run_dir in \
    "/home/abianco/MEGAN_verano2023/MEGAN" \
    "/home/abianco/MEGAN_verano2023_LAIdefault/MEGAN" \
    "/home/abianco/MEGAN_invierno2023/MEGAN" \
    "/home/abianco/MEGAN_invierno2023_LAIdefault/MEGAN"
do
    echo ""
    echo "--- $run_dir/Output/FINAL/ ---"
    if [ -d "$run_dir/Output/FINAL" ]; then
        ls -la "$run_dir/Output/FINAL/" | head -10
        # Chequeamos estructura de UN archivo de ejemplo
        ejemplo=$(ls "$run_dir/Output/FINAL/"*.ncf 2>/dev/null | head -1)
        if [ -n "$ejemplo" ]; then
            echo "  Estructura de $ejemplo:"
            ncdump -h "$ejemplo" | grep -E "ISOP|TSTEP|ROW|COL|LAY|float|double"
        fi
    else
        echo "  >>> CARPETA NO ENCONTRADA, ajustar ruta <<<"
    fi
done

echo ""
echo "##############################################"
echo "# 2. LAI usado por megcan (dentro de cada corrida)"
echo "##############################################"
for run_dir in \
    "/home/abianco/MEGAN_verano2023/MEGAN" \
    "/home/abianco/MEGAN_verano2023_LAIdefault/MEGAN" \
    "/home/abianco/MEGAN_invierno2023/MEGAN" \
    "/home/abianco/MEGAN_invierno2023_LAIdefault/MEGAN"
do
    f="$run_dir/Input/MAP/LAI3_ARG_30km.ncf"
    echo ""
    echo "--- $f ---"
    if [ -f "$f" ]; then
        echo "Cantidad de variables LAI##:"
        ncdump -h "$f" | grep -cE "LAI[0-9][0-9]"
        echo "Valores no-cero en LAI01, LAI02, LAI27, LAI28 (si existen, para confirmar cuáles tienen datos reales):"
        python3 -c "
import xarray as xr
ds = xr.open_dataset('$f')
for v in ['LAI01','LAI02','LAI27','LAI28']:
    if v in ds:
        arr = ds[v].values
        print(f'  {v}: min={arr.min():.2f} max={arr.max():.2f} mean={arr.mean():.2f}')
    else:
        print(f'  {v}: NO EXISTE en este archivo')
" 2>&1
    else
        echo "  >>> ARCHIVO NO ENCONTRADO, ajustar ruta <<<"
    fi
done

echo ""
echo "##############################################"
echo "# 4. Tabla celda -> ecoregión"
echo "##############################################"
f="/home/abianco/MEGANv3.21/Input/MAP/grid_to_ecoregion.csv"
echo "--- $f ---"
if [ -f "$f" ]; then
    echo "Encabezado (nombres de columna reales):"
    head -1 "$f"
    echo ""
    echo "Primeras filas:"
    head -5 "$f"
else
    echo "  >>> ARCHIVO NO ENCONTRADO, ajustar ruta <<<"
fi
