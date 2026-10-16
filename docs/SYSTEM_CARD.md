# System Card · Recomendador

## Usuarios y propósito
Sistema académico del curso INF-8239 (Unidad 03, LAB08) para estudiar cómo se construye y se interpreta un recomendador. Lo usan estudiantes y docentes en una ejecución local u offline. No está pensado para producción ni para decidir qué ve una persona real: la lista expresa similitud o popularidad, no preferencia individual garantizada.

## Catálogo y candidatos
- Catálogo: 9,742 películas de MovieLens Latest Small (ver `docs/DATASET_CARD.md`).
- Popularidad ponderada: candidatas las películas con al menos m = 12 valoraciones (percentil 80 del número de valoraciones por película).
- Contenido: candidatas todas las películas del catálogo excepto la consultada.
- Las 18 películas sin valoraciones solo pueden aparecer por contenido.

## Señales utilizadas
| Señal | Origen | Uso |
| --- | --- | --- |
| Valoración explícita (0.5–5.0) | `ratings.csv` | Media y número de valoraciones para la popularidad ponderada. |
| Géneros | `movies.csv` | Vector TF-IDF por película para la similitud por contenido. |

No se usan etiquetas (`tags.csv`), enlaces externos (`links.csv`) ni datos demográficos. Las marcas temporales no intervienen en LAB08; se reservan para la evaluación temporal de LAB09.

## Modelos y fallback
1. **Popularidad ponderada** (`weighted_popularity`): mezcla la media de cada película con la media global (3.5016) según su número de valoraciones, para que pocas valoraciones altas no dominen el ranking. Produce el mismo Top-10 para todos.
2. **Contenido** (`ContentRecommender`): TF-IDF de géneros y similitud coseno respecto de una película de referencia. Es el modelo de la aplicación Streamlit.
3. **Fallback:** para un usuario sin historial se usa el Top-10 de popularidad (no personalizado). Si faltan los datos, la aplicación se detiene y pide ejecutar `scripts/download_data.py`.

La factorización matricial y el modelo híbrido del proyecto corresponden a LAB09.

## Métricas offline
En LAB08 no se mide precisión de ranking; la evaluación es descriptiva:
- Popularidad: Top-10 con `count`, `mean` y `weighted_score` (`reports/popular_top10.csv`).
- Contenido: `content_score` y número de empates en cuatro consultas (Toy Story, 'Hellboy': The Seeds of Creation, 'Salem's Lot y 10 Cloverfield Lane).
- Pruebas automáticas: 7 aprobadas (contrato de datos, contenido, popularidad, split temporal, factorización y métricas).

Pendiente para LAB09: RMSE, HitRate@10 y cobertura del catálogo con partición temporal *leave-one-out*, comparadas contra la popularidad.

## Cold start, cobertura y diversidad
- **Cold start de ítem:** 18 películas sin valoraciones nunca entran al ranking de popularidad; el contenido sí puede recomendarlas porque tienen géneros.
- **Cold start de usuario:** no observado (todos los usuarios tienen 20 o más valoraciones); se cubre con el fallback de popularidad.
- **Cobertura:** la popularidad recomienda siempre las mismas 10 películas, el 0.10 % del catálogo.
- **Diversidad:** baja en el modelo por contenido. Las listas repiten la misma combinación de géneros y empatan en 1.0: 12 películas empatadas para Toy Story, 19 para 'Salem's Lot y 83 para 10 Cloverfield Lane. Dentro del empate, el orden lo decide `argsort`, no la calidad.

## Riesgos y monitoreo
**Riesgos:**
- Sobre-especialización: el contenido solo devuelve películas con los mismos géneros (por ejemplo, 100 % animación infantil para Toy Story).
- Empates arbitrarios: con combinaciones comunes de géneros, la lista visible es una selección sin criterio entre muchas películas equivalentes.
- Sesgo de popularidad: el baseline favorece clásicos con muchas valoraciones.
- Interpretación: un documental puede recibir recomendaciones de ficción (caso 'Hellboy': The Seeds of Creation), porque los géneros no distinguen el tipo de obra.
- Transparencia: la aplicación muestra el método y la limitación, pero no la fuente de los datos.
- Versión de datos: Latest Small puede cambiar; resultados con otro hash no son comparables.

**Monitoreo:**
- Verificar el SHA-256 en cada descarga.
- Ejecutar `uv run pytest -q` antes de cada commit.
- Registrar en cada versión la cobertura del catálogo y el número de empates de las consultas de referencia.
