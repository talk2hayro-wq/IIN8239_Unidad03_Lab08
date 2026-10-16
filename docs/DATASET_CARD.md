# Dataset Card · MovieLens

## Fuente, fecha, versión y hash
- **Fuente:** GroupLens Research, University of Minnesota.
- **URL:** https://files.grouplens.org/datasets/movielens/ml-latest-small.zip (variable `MOVIELENS_URL` en `src/inf8239_u03/config.py`).
- **Versión:** MovieLens Latest Small (`ml-latest-small`), generada por GroupLens el 26 de septiembre de 2018. Es un conjunto de desarrollo: GroupLens puede cambiarlo y advierte que no debe tratarse como una versión archivada para resultados científicos compartidos.
- **Fecha de descarga:** 2026-10-15.
- **SHA-256 del ZIP descargado:** `696d65a3dfceac7c45750ad32df2c259311949efec81f0f144fdfb91ebc9e436`.

Si una nueva descarga produce otro hash, los datos cambiaron y los resultados de este laboratorio no son comparables.

## Licencia y cita
Harper, F. M., & Konstan, J. A. (2015). DOI: 10.1145/2827872.

Cita completa: F. Maxwell Harper and Joseph A. Konstan. 2015. *The MovieLens Datasets: History and Context*. ACM Transactions on Interactive Intelligent Systems (TiiS) 5, 4: 19:1–19:19. https://doi.org/10.1145/2827872

Condiciones de uso según el README oficial de GroupLens:
- Puede usarse para cualquier propósito de investigación.
- No se puede afirmar ni insinuar respaldo de la University of Minnesota ni de GroupLens.
- Toda publicación que use el dataset debe reconocerlo con la cita anterior.
- Puede redistribuirse, incluso transformado, solo bajo estas mismas condiciones.
- No puede usarse con fines comerciales o lucrativos sin permiso de un miembro docente de GroupLens.
- GroupLens no garantiza la exactitud de los datos ni la validez de resultados basados en ellos.

## Archivos y diccionario
El ZIP contiene `ratings.csv`, `movies.csv`, `tags.csv` y `links.csv`. Este laboratorio usa solo los dos primeros.

**ratings.csv** (100,836 filas × 4 columnas)

| Columna | Tipo | Descripción |
| --- | --- | --- |
| `userId` | entero | Identificador anónimo del usuario. |
| `movieId` | entero | Identificador de la película; clave foránea hacia `movies.csv`. |
| `rating` | decimal | Valoración explícita de 0.5 a 5.0 en pasos de media estrella. |
| `timestamp` | entero | Segundos desde el 1 de enero de 1970 (UTC). |

**movies.csv** (9,742 filas × 3 columnas)

| Columna | Tipo | Descripción |
| --- | --- | --- |
| `movieId` | entero | Identificador único de la película. |
| `title` | texto | Título con el año de estreno entre paréntesis (13 títulos no lo incluyen). |
| `genres` | texto | Géneros separados por `\|`; 20 valores posibles, incluido `(no genres listed)` (34 películas). |

Archivos no utilizados: `tags.csv` (3,683 etiquetas libres de usuarios) y `links.csv` (`movieId`, `imdbId`, `tmdbId`).

## Procedimiento de descarga
```bash
uv run python scripts/download_data.py
uv run python scripts/audit_data.py
```
`download_data.py` descarga el ZIP, calcula su SHA-256, rechaza rutas inseguras dentro del ZIP y lo extrae en `data/raw/`. `audit_data.py` carga los datos con `load_movielens`, que valida columnas requeridas, clave foránea `movieId` y rango de ratings 0.5–5.0. Los datos no se suben al repositorio (`data/raw/*` está en `.gitignore`).

## Población observada y exclusiones
- 610 usuarios, 9,724 películas valoradas y 100,836 valoraciones entre el 29 de marzo de 1996 y el 24 de septiembre de 2018.
- Densidad: 1.70 % de los pares usuario–película del catálogo (100,836 / (610 × 9,742)).
- GroupLens seleccionó usuarios al azar entre quienes habían valorado al menos 20 películas. No hay usuarios con poco historial, así que el cold start de usuario no se observa y debe simularse.
- 18 películas del catálogo no tienen ninguna valoración (9,742 − 9,724).
- Identificadores anónimos; no hay datos demográficos.

## Calidad, sesgos y usos prohibidos
**Calidad:** sin errores de contrato (columnas, claves foráneas y rango de ratings). Valoración media 3.50 (desviación 1.04); mediana 3.5; Q1 3.0; Q3 4.0.

**Sesgos:**
- Autoselección: las personas valoran lo que eligieron ver, así que las valoraciones tienden a ser positivas y una celda vacía no significa rechazo.
- Popularidad: pocas películas acumulan muchas valoraciones; los métodos basados en interacciones favorecen a esas películas.
- Población: usuarios activos (20 o más valoraciones) de un sitio de recomendación; no representan al público general.
- Géneros: etiquetas amplias y desbalanceadas (Drama en 4,361 películas, Film-Noir en 87), lo que provoca empates en la similitud por contenido.

**Usos prohibidos:**
- Uso comercial o lucrativo sin permiso de GroupLens.
- Presentar resultados como respaldados por la University of Minnesota o GroupLens.
- Intentar reidentificar a los usuarios anónimos.
- Presentar una recomendación como verdad sobre los gustos de una persona, o comparar resultados con otros estudios sin verificar que usan la misma versión (hash).
