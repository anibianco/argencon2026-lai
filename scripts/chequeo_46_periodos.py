"""
Diagnóstico definitivo: ¿qué períodos del LAI MODIS (verano/invierno) tienen
dato real vs relleno/placeholder?

Lógica: imprimimos la media nacional (excluyendo ceros) de las 46 variables
LAI01..LAI46 de cada archivo. Si hay cobertura MODIS real para todo el año,
vamos a ver una curva estacional gradual (subiendo y bajando suavemente).
Si en cambio hay relleno, vamos a ver BLOQUES de valores IDÉNTICOS (la misma
media exacta repetida en varios períodos consecutivos o no consecutivos),
que es la huella digital de un placeholder copiado.

Uso:
    python3 chequeo_46_periodos.py /ruta/al/archivo.ncf
"""

import sys
import numpy as np
import xarray as xr

def main(path):
    ds = xr.open_dataset(path)
    print(f"\n=== {path} ===")
    print(f"{'Período':<10}{'Media (no-cero)':<18}{'Max':<10}")

    medias = []
    for i in range(1, 47):
        var = f"LAI{i:02d}"
        if var not in ds:
            print(f"{var:<10}NO EXISTE")
            continue
        arr = ds[var].values
        nonzero = arr[arr > 0]
        media = nonzero.mean() if nonzero.size > 0 else 0.0
        medias.append((var, media, arr.max()))
        print(f"{var:<10}{media:<18.4f}{arr.max():<10.2f}")

    # Detectar bloques de valores idénticos (placeholder)
    print("\n--- Grupos de períodos con media IDÉNTICA (huella de placeholder) ---")
    valores_unicos = {}
    for var, media, _ in medias:
        key = round(media, 6)
        valores_unicos.setdefault(key, []).append(var)

    for valor, periodos in sorted(valores_unicos.items(), key=lambda x: -len(x[1])):
        if len(periodos) > 1:
            print(f"  Media={valor:.4f} compartida por {len(periodos)} períodos: {periodos}")

    if all(len(v) == 1 for v in valores_unicos.values()):
        print("  Ningún valor se repite exactamente -> cada período parece tener dato distinto (buena señal)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 chequeo_46_periodos.py <ruta_al_archivo.ncf>")
        sys.exit(1)
    main(sys.argv[1])
