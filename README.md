# INF-8239 · Unidad 03 · Sistemas recomendadores

Autor académico: Edwin Ramón José Nolasco
Estudiante: Hairo Fermin – AG4949 · Práctica #5 (LAB08, 15 de octubre de 2026) y Práctica #6 (LAB09, 16 de octubre de 2026)

Proyecto de LAB08 y LAB09 sobre MovieLens Latest Small. LAB08 construye un baseline de **popularidad ponderada** y un modelo por **contenido** (TF-IDF de géneros + similitud coseno). LAB09 agrega un modelo **colaborativo por factorización**, un **corte temporal**, la evaluación de ratings y ranking, una **combinación híbrida**, el análisis de cold start y la comparación de desempeño frente a costo. El dataset de muestra de `tests/` solo prueba la arquitectura; la evidencia final usa MovieLens.

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
uv run python scripts/lab09_hybrid.py --factors 20 --epochs 12 --alpha 0.75 --seed 42
```
`lab08_content.py` genera `reports/popular_top10.csv` y `reports/content_recommendations.csv`. La aplicación permite elegir una película de referencia y muestra sus 10 películas más similares por género.

`lab09_hybrid.py` separa la última valoración de cada usuario para prueba, entrena la factorización y combina `alpha` × puntuación colaborativa + (1 − `alpha`) × puntuación de contenido sobre las 100 mejores candidatas colaborativas. Genera `reports/hybrid_metrics.json` (se sobrescribe en cada corrida) y `reports/cold_start_fallback.csv`.

### Comparación de políticas (script agregado)
```bash
uv run python scripts/lab09_compare.py --factors 20 --epochs 12 --alphas 0.25 0.75 --seeds 42 7 123
```
Evalúa popularidad ponderada, popularidad por conteo, contenido, colaborativo puro e híbrido con el mismo corte temporal, los mismos usuarios evaluables y el mismo catálogo de candidatas. Genera `reports/comparison_metrics.csv`, `reports/comparison_summary.csv` y `reports/profile_examples.csv` (Top-10 con títulos de un usuario con historial amplio, uno con historial pequeño y el fallback de un usuario nuevo). No modifica `src/` ni sobrescribe `hybrid_metrics.json`.

### Cambios al script de la guía
- **Compatibilidad con scikit-learn 1.9:** el perfil de géneros se convierte con `np.asarray(...)`, porque `cosine_similarity` ya no acepta `np.matrix`. Sin este cambio el script falla con `TypeError: np.matrix is not supported`.
- **Parámetro `--seed`** (por defecto 42), pasado a `MatrixFactorization` y registrado en las métricas, para repetir el experimento con varias semillas. Con 42 reproduce los resultados originales.

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

## Resultados de LAB09
Corte temporal *leave-one-out*: 587 de 610 usuarios son evaluables; en los otros 23, la película retenida no aparece en entrenamiento. Todas las corridas usan 20 factores y 12 épocas (≈ 206,220 parámetros, 1.6 MB en memoria).

| Configuración (3 semillas: 42, 7, 123) | RMSE | HitRate@10 | Cobertura | Entrenamiento |
| --- | --- | --- | --- | --- |
| `alpha` = 0.25 (domina contenido) | 1.026 | 0.027 ± 0.005 | 10.2 % | 20–29 s |
| `alpha` = 0.75 (domina colaborativo) | 1.026 | 0.035 ± 0.006 | 7.2 % | 17–19 s |

- **Ratings:** RMSE 1.026, casi igual a la desviación estándar de las valoraciones (1.04); la factorización apenas mejora a predecir la media.
- **Ranking:** con `alpha` = 0.75 el Top-10 acierta la película retenida en 3.5 % de los usuarios (Precision@10 ≈ 0.0035), frente a ≈ 0.1 % al azar.
- **Configuración híbrida seleccionada:** `alpha` = 0.75. Supera a 0.25 en HitRate@10 con las tres semillas (+3, +8 y +4 usuarios) con el mismo costo de cómputo. A cambio, recomienda unas 290 películas distintas menos.
- **Pareto:** el costo es igual (mismo modelo); con HitRate@10 como utilidad principal, 0.75 domina a 0.25. Si también se valora la cobertura, ninguna domina.
- **Usuario frío:** recibe las 10 películas de `cold_start_fallback.csv` (las más valoradas en entrenamiento), sin personalización.

### Comparación de políticas (mismo corte, 587 usuarios; `lab09_compare.py`)

| Política | HitRate@10 | Cobertura | Películas distintas | Entrenamiento |
| --- | --- | --- | --- | --- |
| Popularidad por conteo | 0.043 | 1.2 % | 118 | No |
| Híbrido `alpha` = 0.75 | 0.035 ± 0.006 | 7.2 % | ≈ 702 | Sí |
| Colaborativo puro | 0.035 ± 0.006 | 7.0 % | 680 | Sí |
| Popularidad ponderada | 0.032 | 0.6 % | 61 | No |
| Híbrido `alpha` = 0.25 | 0.027 ± 0.005 | 10.2 % | ≈ 984 | Sí |
| Contenido | 0.002 | 7.8 % | 755 | No |

- **La popularidad es el baseline a vencer.** La popularidad por conteo acierta 25 usuarios sin entrenar modelos; el mejor modelo personalizado, unos 21. La diferencia está dentro del ruido: la personalización no demuestra mejora en HitRate@10.
- **El aporte de la personalización es la cobertura:** el híbrido 0.75 reparte las recomendaciones en unas 700 películas frente a 118.
- **El híbrido 0.75 empata con el colaborativo puro** en HitRate y lo domina en cobertura; el colaborativo y la popularidad ponderada quedan dominados en la tabla de Pareto.
- **Decisión:** popularidad por conteo como baseline y fallback; híbrido `alpha` = 0.75 como mejor opción personalizada, justificada solo si se valora la cobertura.
- **Pruebas:** `uv run pytest tests/test_matrix_factorization.py tests/test_metrics.py -q` → 3 passed.

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
- `lab09_hybrid.py` no guarda el Top-10 de cada usuario ni el tamaño del modelo; solo métricas agregadas.
- El híbrido solo reordena las 100 candidatas de la factorización: una película sin valoraciones nunca llega al Top-10.
- El fallback de LAB09 ordena por cantidad de valoraciones, no por la popularidad ponderada de LAB08; solo 3 películas coinciden entre ambas listas.
- No se probaron otros valores de factores o épocas.
- El corte *leave-one-out* es por usuario, no global: el entrenamiento incluye valoraciones de otros usuarios posteriores a la fecha de prueba, lo que puede favorecer a la popularidad.
- Precision@K no está implementada; con una película retenida por usuario equivale a HitRate@K / K.

## Interpretación
No presente una recomendación como verdad. Documente datos, candidatos, puntuación, métricas, fallback y límites.

## Cita
F. Maxwell Harper and Joseph A. Konstan. 2015. *The MovieLens Datasets: History and Context*. ACM Transactions on Interactive Intelligent Systems (TiiS) 5, 4: 19:1–19:19. https://doi.org/10.1145/2827872
