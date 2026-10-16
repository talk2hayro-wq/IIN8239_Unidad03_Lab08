# System Card · Recomendador

## Usuarios y propósito
Sistema académico del curso INF-8239 (Unidad 03, LAB08 y LAB09) para estudiar cómo se construye y se interpreta un recomendador. Lo usan estudiantes y docentes en una ejecución local u offline. No está pensado para producción ni para decidir qué ve una persona real: la lista expresa similitud o popularidad, no preferencia individual garantizada.

## Catálogo y candidatos
- Catálogo: 9,742 películas de MovieLens Latest Small (ver `docs/DATASET_CARD.md`).
- Popularidad ponderada: candidatas las películas con al menos m = 12 valoraciones (percentil 80 del número de valoraciones por película).
- Contenido: candidatas todas las películas del catálogo excepto la consultada.
- Las 18 películas sin valoraciones solo pueden aparecer por contenido.
- Factorización e híbrido (LAB09): candidatas las 9,701 películas con valoraciones en entrenamiento que el usuario no ha valorado; el híbrido reordena solo las 100 mejores candidatas colaborativas.

## Señales utilizadas
| Señal | Origen | Uso |
| --- | --- | --- |
| Valoración explícita (0.5–5.0) | `ratings.csv` | Media y número de valoraciones para la popularidad ponderada. |
| Géneros | `movies.csv` | Vector TF-IDF por película para la similitud por contenido. |
| Interacciones usuario–película | `ratings.csv` | Factores latentes de usuarios y películas (LAB09). |
| Marca temporal | `ratings.csv` | Corte temporal: la última valoración de cada usuario va a prueba (LAB09). |

No se usan etiquetas (`tags.csv`), enlaces externos (`links.csv`) ni datos demográficos.

## Modelos y fallback
1. **Popularidad ponderada** (`weighted_popularity`): mezcla la media de cada película con la media global (3.5016) según su número de valoraciones, para que pocas valoraciones altas no dominen el ranking. Produce el mismo Top-10 para todos.
2. **Contenido** (`ContentRecommender`): TF-IDF de géneros y similitud coseno respecto de una película de referencia. Es el modelo de la aplicación Streamlit.
3. **Factorización matricial** (`MatrixFactorization`, LAB09): media global + producto de vectores latentes de usuario y película, entrenados con descenso de gradiente estocástico. Configuración: 20 factores, 12 épocas, tasa de aprendizaje 0.01, regularización 0.05; ≈ 206,220 parámetros (1.6 MB en memoria).
4. **Híbrido** (LAB09): `alpha` × puntuación colaborativa normalizada + (1 − `alpha`) × similitud entre el perfil de géneros del usuario y cada candidata. **Configuración seleccionada: `alpha` = 0.75.**
5. **Fallback:** para un usuario sin historial, LAB09 usa `reports/cold_start_fallback.csv`: las 10 películas con más valoraciones en entrenamiento (desempate por media), no personalizadas. En LAB08 el respaldo propuesto era el Top-10 de popularidad ponderada. Si faltan los datos, la aplicación se detiene y pide ejecutar `scripts/download_data.py`.

## Métricas offline
En LAB08 no se mide precisión de ranking; la evaluación es descriptiva:
- Popularidad: Top-10 con `count`, `mean` y `weighted_score` (`reports/popular_top10.csv`).
- Contenido: `content_score` y número de empates en cuatro consultas (Toy Story, 'Hellboy': The Seeds of Creation, 'Salem's Lot y 10 Cloverfield Lane).
- Pruebas automáticas: 7 aprobadas (contrato de datos, contenido, popularidad, split temporal, factorización y métricas).

LAB09, con partición temporal *leave-one-out* (587 usuarios evaluables de 610) y tres semillas (42, 7, 123):

| Configuración | RMSE | HitRate@10 | Precision@10 | Cobertura | Entrenamiento |
| --- | --- | --- | --- | --- | --- |
| `alpha` = 0.25 | 1.026 | 0.027 ± 0.005 | ≈ 0.0027 | 10.2 % | 20–29 s |
| `alpha` = 0.75 (seleccionada) | 1.026 | 0.035 ± 0.006 | ≈ 0.0035 | 7.2 % | 17–19 s |

- El RMSE es casi igual a la desviación estándar de las valoraciones (1.04): la factorización apenas mejora a predecir la media.
- `alpha` = 0.75 supera a 0.25 en HitRate@10 con las tres semillas al mismo costo; 0.25 cubre más catálogo. Con costo igual y HitRate@10 como utilidad principal, 0.75 domina en la tabla de Pareto.
- Precision@10 se calcula como HitRate@10 / 10 (una película retenida por usuario).
- Pruebas: 3 aprobadas en factorización y métricas.

Comparación con el mismo corte y los mismos 587 usuarios (`scripts/lab09_compare.py`):

| Política | HitRate@10 | Cobertura | ¿Dominada en Pareto? |
| --- | --- | --- | --- |
| Popularidad por conteo | 0.043 | 1.2 % | No |
| Híbrido `alpha` = 0.75 | 0.035 ± 0.006 | 7.2 % | No |
| Colaborativo puro | 0.035 ± 0.006 | 7.0 % | Sí (por el híbrido 0.75) |
| Popularidad ponderada | 0.032 | 0.6 % | Sí (por la popularidad por conteo) |
| Híbrido `alpha` = 0.25 | 0.027 ± 0.005 | 10.2 % | No |
| Contenido | 0.002 | 7.8 % | No |

La personalización no demuestra mejora en HitRate@10 frente a la popularidad por conteo (≈ 21 frente a 25 usuarios, diferencia dentro del ruido); su aporte es la cobertura. Decisión: popularidad por conteo como baseline y fallback; híbrido `alpha` = 0.75 como opción personalizada cuando se valore la cobertura.

## Cold start, cobertura y diversidad
- **Cold start de ítem:** 18 películas sin valoraciones nunca entran al ranking de popularidad; el contenido sí puede recomendarlas porque tienen géneros.
- **Cold start de ítem en la evaluación (LAB09):** 23 películas retenidas no estaban en entrenamiento; esos usuarios no se evalúan y el híbrido no puede recomendarlas, porque solo reordena candidatas colaborativas.
- **Cold start de usuario:** no observado (todos los usuarios tienen 20 o más valoraciones); se cubre con el fallback de popularidad, que no es personalizado.
- **Cobertura:** la popularidad recomienda siempre las mismas 10 películas, el 0.10 % del catálogo. El híbrido con `alpha` = 0.75 recomienda entre 675 y 752 películas distintas a 587 usuarios (7.2 %); con 0.25, entre 941 y 1,033 (10.2 %).
- **Diversidad:** baja en el modelo por contenido. Las listas repiten la misma combinación de géneros y empatan en 1.0: 12 películas empatadas para Toy Story, 19 para 'Salem's Lot y 83 para 10 Cloverfield Lane. Dentro del empate, el orden lo decide `argsort`, no la calidad.

## Riesgos y monitoreo
**Riesgos:**
- Sobre-especialización: el contenido solo devuelve películas con los mismos géneros (por ejemplo, 100 % animación infantil para Toy Story).
- Empates arbitrarios: con combinaciones comunes de géneros, la lista visible es una selección sin criterio entre muchas películas equivalentes.
- Sesgo de popularidad: el baseline favorece clásicos con muchas valoraciones.
- Interpretación: un documental puede recibir recomendaciones de ficción (caso 'Hellboy': The Seeds of Creation), porque los géneros no distinguen el tipo de obra.
- Transparencia: la aplicación muestra el método y la limitación, pero no la fuente de los datos.
- Versión de datos: Latest Small puede cambiar; resultados con otro hash no son comparables.
- Popularidad dominante (LAB09): con `alpha` = 0.75, 587 usuarios comparten unas 700 películas y todo usuario nuevo recibe la misma lista.
- Sesgo de selección: solo se observan valoraciones de películas que la persona eligió ver; una celda vacía no es rechazo.
- Ausencia de demografía: no pueden afirmarse resultados por grupos poblacionales.
- Retroalimentación: en uso real, las películas recomendadas recibirían más valoraciones y el siguiente entrenamiento las favorecería aún más; una evaluación offline no lo mide.

**Monitoreo:**
- Verificar el SHA-256 en cada descarga.
- Ejecutar `uv run pytest -q` antes de cada commit.
- Registrar en cada versión la cobertura del catálogo y el número de empates de las consultas de referencia.
- Repetir el experimento híbrido con varias semillas (`--seed`) antes de cambiar `alpha`, y vigilar que la cobertura no baje de la línea base (7.2 %).
