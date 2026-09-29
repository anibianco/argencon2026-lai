# Correcciones de los revisores — ARGENCON #327

Fuente: `327-review-845.pdf` (Revisor 1, texto) y `327-review-817.pdf` (Revisor 2, comentarios sobre el PDF).
Entrega camera-ready: **29/10/2026**.

Estado: ✅ hecho · ⬜ pendiente · ❓ hay que decidir

## Revisor 1

| # | Comentario | Estado |
|---|---|---|
| 1 | Cita del mapa de ecorregiones: [21, 22] → Olson + Dinerstein | ✅ |
| 2 | MEGAN v3.2 citaba Opacka → citar Guenther MEGAN3 | ✅ |
| 3 | Wei 2024 y Bauwens 2018 sin citar | ✅ citadas en la Introducción |
| 4 | Patagonia −40/−60 % (texto) vs −25/−31 % (Tabla II) | ✅ texto con medianas por celda (−33 / −41 %) + explicación del agregado |
| 5 | Pie de Tabla II "top five by emission magnitude" | ✅ "cuatro mayores + Patagonian Steppe como contraste" + fila "Other ecoregions" |

## Revisor 2

| # | Pág. | Comentario | Estado |
|---|---|---|---|
| 1 | 1 | Definir MEGAN y WRF también en el resumen | ✅ |
| 2 | 1 | Keywords no deben repetir palabras del título ("Leaf Area Index", "Biogenic emissions") | ✅ Isoprene, MEGAN, MODIS, vegetation phenology, satellite remote sensing, … |
| 3 | 1 | Citas consecutivas como [7–9] | ✅ (automático con `cite`) |
| 4 | 1 | Formato de siglas uniforme: nombre completo (SIGLA) en todo el texto | ✅ revisadas todas |
| 5 | 2 | Definir MEGAN / WRF en Métodos | ✅ WRF y MODIS definidos en el cuerpo |
| 6 | 2 | Fig. 1: agregar norte y escala, agrandar leyenda | ✅ |
| 7 | 2 | Figuras y tablas arriba o abajo de la columna | ✅ (LaTeX `[!t]`) |
| 8 | 2 | Espacio en blanco en la página | ✅ (lo resuelve LaTeX) |
| 9 | 3 | Nombrar cada figura en el texto antes de que aparezca | ✅ cada figura va después de su primera mención en el código (LaTeX puede ubicarla arriba de la misma página, que es lo habitual en IEEE) |
| 10 | 3 | Definir ISOP | ✅ en Métodos |
| 11 | 3 | Definir WWF | ✅ (también NOA y UTC) |
| 12 | 4 | "(Dinerstein et al., 2017)" → número de referencia | ✅ |
| 13 | 4 | Fig. 3: norte y escala; moverla a Métodos (no es un resultado) | ✅ norte/escala y movida a Métodos (ahora es la Fig. 2) |
| 14 | 4 | Aclarar que el párrafo del Dry Chaco se refiere a la Tabla II | ✅ (y se corrigió "most extensive": la Patagonian Steppe tiene más celdas) |
| 15 | 4 | Figs. 4 y 5: norte, escala y contorno de ecorregiones | ✅ norte, escala y contornos de ecorregiones |
| 16 | 5 | "Guenther et al. [1]": ¿hace falta el apellido? | ✅ "reported in [1]" |
| 17 | 5 | "Q" resaltando "the" en "particularly in the Chaco" | ❓ parece una marca accidental; sin cambios |
| 18 | 6 | Formato de referencias: cuándo va "et al." (IEEE: >6 autores) | ✅ verificado contra Crossref; Khan 2025 y Richardson 2013 (6 autores) ahora completos |

## Referencias corregidas al verificar contra Crossref

- **Karl et al. 2018 (acp-2018-183)**: el DOI correspondía a otro artículo. El trabajo real es Kaser et al., *ACP* 22, 5603–5618, 2022.
- **Kavouras et al. 2007**: no existe con esos datos. El artículo con ese título es Liakakou et al., *Atmos. Environ.* 41, 1002–1010, 2007.
- **Sun et al. 2025**: páginas y DOI corregidos (15801–15818, acp-25-15801-2025).
- **Lin et al. 2023**: la primera autora es W. Lin, no X. Lin.

## Fuera del alcance de esta revisión (anotado para la tesis)

- Default LAI: el regrillado con Python reemplazó solo LAI01/LAI27; LAI02/LAI28 siguen con Fortran.
  La re-corrida de verano del 26/06 mezcla ambos → no se usa. El paper queda con la versión original.
- Pie de la Fig. 2: dice que el Default está corregido por VCF, pero se grafica LAIv/10 (`% VERIFICAR` en main.tex).
