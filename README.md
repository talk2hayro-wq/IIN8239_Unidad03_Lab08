# INF-8239 · Unidad 03 · Sistemas recomendadores

Autor académico: Edwin Ramón José Nolasco
Estudiante: Hairo Fermin – AG4949 · Práctica #5 (LAB08) · 15 de octubre de 2026

Proyecto de LAB08 y LAB09. LAB08 construye dos políticas de recomendación sobre MovieLens Latest Small: un baseline de **popularidad ponderada** y un modelo por **contenido** (TF-IDF de géneros + similitud coseno). El dataset de muestra de `tests/` solo prueba la arquitectura; la evidencia final usa MovieLens.

> Una recomendación no es una verdad sobre los gustos de una persona. La lista depende de los datos observados, los candidatos permitidos y la función de puntuación.

## Requisitos
- [uv](https://docs.astral.sh/uv/) (probado con uv 0.12.23)
- Python 3.12 (`requires-python = ">=3.12,<3.13"`; uv lo instala si falta)
- Acceso a internet para descargar cerca de 1 MB desde `files.grouplens.org`

## Inicio
```bash
uv python install 3.12
uv sync
uv run pytest -q
uv run python scripts/download_data.py
uv run python scripts/audit_data.py
```
`uv sync` crea `.venv` e instala las dependencias fijadas en `uv.lock`. `download_data.py` imprime el SHA-256 de la descarga; compárelo con el registrado en `docs/DATASET_CARD.md`.

## Laboratorios
```bash
# LAB08: popularidad ponderada y contenido
uv run python scripts/lab08_content.py
uv run streamlit run app/streamlit_app.py

# LAB09: modelo híbrido (factorización matricial + contenido)
uv run python scripts/lab09_hybrid.py --factors 20 --epochs 12 --alpha 0.75
```
`lab08_content.py` genera `reports/popular_top10.csv` y `reports/content_recommendations.csv`. La aplicación permite elegir una película de referencia y muestra sus 10 películas más similares por género.

## Estructura
```
data/raw/             MovieLens descargado; no se edita ni se versiona
docs/                 Dataset Card y System Card
models/               Artefactos entrenados (vacío en LAB08)
reports/              Rankings, métricas y gráficos (no se versionan)
src/inf8239_u03/      Datos, modelos y métricas reutilizables
scripts/              Descarga, auditoría y experimentos
tests/                Contratos y comportamiento
app/                  Aplicación Streamlit
```

## Dataset y restricciones
- **Fuente:** MovieLens Latest Small (`ml-latest-small`), GroupLens Research, University of Minnesota. URL configurable con `MOVIELENS_URL` (ver `.env.example`).
- **Contenido usado:** `ratings.csv` (100,836 valoraciones de 610 usuarios, 0.5–5.0 estrellas, 1996–2018) y `movies.csv` (9,742 películas con géneros).
- **Versión:** es un conjunto de desarrollo que GroupLens puede cambiar; no es una versión archivada para resultados científicos compartidos. Por eso se registran la fecha, la URL y el hash de cada descarga.
- **Licencia:** uso para investigación y docencia. No se puede afirmar respaldo de la University of Minnesota ni de GroupLens; toda publicación debe citar el dataset; puede redistribuirse solo bajo las mismas condiciones; el uso comercial requiere permiso de GroupLens.
- **Población:** usuarios anónimos seleccionados al azar entre quienes habían valorado al menos 20 películas; no incluye datos demográficos.
- **No versionado:** los datos no se suben al repositorio (`data/raw/*` en `.gitignore`); cada persona los descarga con `scripts/download_data.py`.

Detalle completo en `docs/DATASET_CARD.md`.

## Resultados de LAB08
- **Popularidad ponderada** (m = 12 valoraciones, percentil 80): Top-10 encabezado por *The Shawshank Redemption* (4.395). Corrige medias con poca evidencia: *Dr. Strangelove* tiene mejor media que *Star Wars IV* (4.268 frente a 4.231), pero con 97 valoraciones frente a 251 queda en el puesto 9. La lista es igual para todos.
- **Contenido:** las recomendaciones comparten géneros, no garantizan preferencia. Hay empates en 1.0 cuando la combinación de géneros es común: 12 películas para *Toy Story*, 19 para *'Salem's Lot* y 83 para *10 Cloverfield Lane*; el orden dentro del empate es arbitrario.
- **Cold start:** 18 películas sin valoraciones no aparecen por popularidad, pero sí por contenido. Para usuarios sin historial, el respaldo es el Top-10 de popularidad.
- **Pruebas:** `uv run pytest -q` → 7 passed.

Modelos, riesgos y monitoreo en `docs/SYSTEM_CARD.md`.

## Publicación
```bash
uv export --format requirements.txt --output-file requirements-cloud.txt
```
- `requirements-cloud.txt` fija las 59 dependencias con hash para plataformas que no usan uv; `requirements-colab.txt` lista las dependencias mínimas para Colab.
- La aplicación usa rutas relativas a la raíz del proyecto (`src/inf8239_u03/config.py`).
- La plataforma debe permitir descargar el ZIP desde GroupLens; si faltan los datos, la aplicación indica ejecutar `scripts/download_data.py`.
- No se suben `.venv`, credenciales ni archivos temporales.

## Limitaciones conocidas
- La aplicación muestra el método y su limitación, pero no la fuente de los datos.
- `audit_data.py` imprime el rango de marcas temporales, pero no las valida con una regla.
- El modelo por contenido solo usa géneros: no distingue calidad ni tipo de obra (un documental puede recibir películas de ficción).

## Interpretación
No presente una recomendación como verdad. Documente datos, candidatos, puntuación, métricas, fallback y límites.

## Cita
F. Maxwell Harper and Joseph A. Konstan. 2015. *The MovieLens Datasets: History and Context*. ACM Transactions on Interactive Intelligent Systems (TiiS) 5, 4: 19:1–19:19. https://doi.org/10.1145/2827872
