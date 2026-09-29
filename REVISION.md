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
| 2 | 1 | Keywords no deben repetir palabras del título ("Leaf Area Index", "Biogenic emissions") | ⬜ |
| 3 | 1 | Citas consecutivas como [7–9] | ✅ (automático con `cite`) |
| 4 | 1 | Formato de siglas uniforme: nombre completo (SIGLA) en todo el texto | ⬜ revisar todo |
| 5 | 2 | Definir MEGAN / WRF en Métodos | ⬜ WRF no está definido en el cuerpo |
| 6 | 2 | Fig. 1: agregar norte y escala, agrandar leyenda | ✅ |
| 7 | 2 | Figuras y tablas arriba o abajo de la columna | ✅ (LaTeX `[!t]`) |
| 8 | 2 | Espacio en blanco en la página | ✅ (lo resuelve LaTeX) |
| 9 | 3 | Nombrar cada figura en el texto antes de que aparezca | ⬜ chequear en el PDF final |
| 10 | 3 | Definir ISOP | ⬜ |
| 11 | 3 | Definir WWF | ⬜ |
| 12 | 4 | "(Dinerstein et al., 2017)" → número de referencia | ✅ |
| 13 | 4 | Fig. 3: norte y escala; moverla a Métodos (no es un resultado) | ✅ norte/escala · ⬜ mover a Métodos |
| 14 | 4 | Aclarar que el párrafo del Dry Chaco se refiere a la Tabla II | ⬜ |
| 15 | 4 | Figs. 4 y 5: norte, escala y contorno de ecorregiones | ✅ norte/escala · ⬜ contornos de ecorregiones |
| 16 | 5 | "Guenther et al. [1]": ¿hace falta el apellido? | ⬜ |
| 17 | 5 | "Q" sobre "…being the hig…" (sin explicación) | ❓ ver en el PDF del revisor |
| 18 | 6 | Formato de referencias: cuándo va "et al." (IEEE: >6 autores) | ⬜ 12 refs con "et al." a revisar |

## Fuera del alcance de esta revisión (anotado para la tesis)

- Default LAI: el regrillado con Python reemplazó solo LAI01/LAI27; LAI02/LAI28 siguen con Fortran.
  La re-corrida de verano del 26/06 mezcla ambos → no se usa. El paper queda con la versión original.
- Pie de la Fig. 2: dice que el Default está corregido por VCF, pero se grafica LAIv/10 (`% VERIFICAR` en main.tex).
