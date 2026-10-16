"""LAB09 · Comparación de políticas con el mismo corte temporal.

Evalúa popularidad (ponderada y por conteo), contenido, colaborativo puro e híbrido
sobre los mismos usuarios evaluables y el mismo catálogo de candidatas que
scripts/lab09_hybrid.py. Además guarda el Top-10 de tres perfiles de ejemplo.

Uso:
    uv run python scripts/lab09_compare.py --factors 20 --epochs 12 --alphas 0.25 0.75 --seeds 42 7 123
"""
from __future__ import annotations

import argparse
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from inf8239_u03.config import MOVIELENS_DIR, ROOT
from inf8239_u03.data import load_movielens
from inf8239_u03.metrics import catalog_coverage, hit_rate_at_k
from inf8239_u03.recommenders import MatrixFactorization, temporal_leave_one_out, weighted_popularity

K = 10
CANDIDATES = 100  # mismas 100 candidatas colaborativas que lab09_hybrid.py

parser = argparse.ArgumentParser()
parser.add_argument("--factors", type=int, default=20)
parser.add_argument("--epochs", type=int, default=12)
parser.add_argument("--alphas", type=float, nargs="+", default=[0.25, 0.75])
parser.add_argument("--seeds", type=int, nargs="+", default=[42, 7, 123])
args = parser.parse_args()

ratings, movies = load_movielens(MOVIELENS_DIR)
train, test = temporal_leave_one_out(ratings)
train_items = sorted(train["movieId"].unique())
train_item_set = set(train_items)
evaluable = test[test["movieId"].isin(train_item_set)]  # el usuario siempre está en train
users = [int(u) for u in evaluable["userId"].unique()]
seen_by_user = {int(u): set(g) for u, g in train.groupby("userId")["movieId"]}

# Contenido: mismo perfil de géneros que lab09_hybrid.py
movie_table = movies.reset_index(drop=True).copy()
movie_table["genres_text"] = movie_table["genres"].str.replace("|", " ", regex=False)
genre_matrix = TfidfVectorizer().fit_transform(movie_table["genres_text"])
movie_row = {int(m): i for i, m in enumerate(movie_table["movieId"])}
train_rows = np.array([movie_row[int(m)] for m in train_items])
train_items_arr = np.array(train_items)


def genre_profile(user_id: int) -> np.ndarray:
    history = train.loc[train["userId"].eq(user_id), ["movieId", "rating"]]
    rows = [movie_row[int(m)] for m in history["movieId"]]
    weights = np.clip(history["rating"].to_numpy() - 2.5, 0.1, None)
    return np.asarray(genre_matrix[rows].multiply(weights[:, None]).sum(axis=0) / weights.sum())


def top_unseen(order_items, seen, k=K):
    return [int(m) for m in order_items if m not in seen][:k]


def minmax(values: np.ndarray) -> np.ndarray:
    return (values - values.min()) / max(values.max() - values.min(), 1e-9)


profiles = {u: genre_profile(u) for u in users}
content_full = {u: cosine_similarity(profiles[u], genre_matrix[train_rows]).ravel() for u in users}

rows_out = []
recs_by_policy = {}


def record(policy, recommendations, seed="", alpha="", seconds=0.0):
    hit = hit_rate_at_k(recommendations, evaluable, K)
    rows_out.append({
        "politica": policy, "alpha": alpha, "seed": seed,
        "hit_rate_at_10": hit, "precision_at_10": hit / K,
        "aciertos": int(round(hit * len(users))), "usuarios": len(users),
        "catalog_coverage": catalog_coverage(recommendations, len(train_items)),
        "peliculas_distintas": len({m for v in recommendations.values() for m in v}),
        "segundos": round(seconds, 2),
    })
    recs_by_policy[(policy, alpha, seed)] = recommendations


# 1) Popularidad ponderada (LAB08) calculada solo con entrenamiento
start = perf_counter()
pop_weighted = weighted_popularity(train, movies).index.tolist()
record("popularidad_ponderada", {u: top_unseen(pop_weighted, seen_by_user[u]) for u in users}, seconds=perf_counter() - start)

# 2) Popularidad por conteo (fallback de lab09_hybrid.py)
start = perf_counter()
pop_count = train.groupby("movieId")["rating"].agg(["mean", "count"]).sort_values(["count", "mean"], ascending=False).index.tolist()
record("popularidad_conteo", {u: top_unseen(pop_count, seen_by_user[u]) for u in users}, seconds=perf_counter() - start)

# 3) Contenido puro: perfil de géneros del usuario contra todo el catálogo de entrenamiento
start = perf_counter()
content_recs = {}
for u in users:
    order = train_items_arr[np.lexsort((train_items_arr, -content_full[u]))]  # desempate estable por movieId
    content_recs[u] = top_unseen(order, seen_by_user[u])
record("contenido", content_recs, seconds=perf_counter() - start)

# 4) Colaborativo puro y 5) híbrido, por semilla
for seed in args.seeds:
    start = perf_counter()
    model = MatrixFactorization(factors=args.factors, seed=seed).fit(train, epochs=args.epochs)
    train_seconds = perf_counter() - start
    item_pos = np.array([model.item_index[m] for m in train_items])
    collab_recs, candidates = {}, {}
    for u in users:
        scores = model.global_mean + model.item_factors[item_pos] @ model.user_factors[model.user_index[u]]
        mask = np.array([m not in seen_by_user[u] for m in train_items])
        cand_items, cand_scores = train_items_arr[mask], scores[mask]
        order = cand_scores.argsort()[::-1][:CANDIDATES]  # mismo orden que MatrixFactorization.top_n
        candidates[u] = (cand_items[order], cand_scores[order])
        collab_recs[u] = [int(m) for m in cand_items[order][:K]]
    record("colaborativo", collab_recs, seed=seed, seconds=train_seconds)
    for alpha in args.alphas:
        hybrid_recs = {}
        for u in users:
            items, scores = candidates[u]
            content = cosine_similarity(profiles[u], genre_matrix[[movie_row[int(m)] for m in items]]).ravel()
            hybrid = alpha * minmax(scores) + (1 - alpha) * minmax(content)
            hybrid_recs[u] = pd.Series(hybrid, index=items).nlargest(K).index.astype(int).tolist()
        record("hibrido", hybrid_recs, seed=seed, alpha=alpha, seconds=train_seconds)

# Resultados
reports = ROOT / "reports"
reports.mkdir(exist_ok=True)
results = pd.DataFrame(rows_out)
results.to_csv(reports / "comparison_metrics.csv", index=False)
summary = (results.assign(alpha=results["alpha"].astype(str))
           .groupby(["politica", "alpha"], sort=False)
           .agg(hit_rate_media=("hit_rate_at_10", "mean"), hit_rate_desv=("hit_rate_at_10", "std"),
                cobertura_media=("catalog_coverage", "mean"), peliculas_distintas=("peliculas_distintas", "mean"),
                corridas=("seed", "count")).reset_index())
summary.to_csv(reports / "comparison_summary.csv", index=False)

# Tres perfiles: historial amplio, historial pequeño y usuario nuevo
history_size = train.groupby("userId").size()
wide_user = int(history_size.loc[users].idxmax())
small_user = int(history_size.loc[users].idxmin())
first_seed, best_alpha = args.seeds[0], max(args.alphas)
titles = movies.set_index("movieId")["title"]
example_rows = []
for label, user in [("historial_amplio", wide_user), ("historial_pequeno", small_user)]:
    for policy, alpha, seed in [("popularidad_conteo", "", ""), ("contenido", "", ""),
                                ("colaborativo", "", first_seed), ("hibrido", best_alpha, first_seed)]:
        for rank, movie_id in enumerate(recs_by_policy[(policy, alpha, seed)][user], start=1):
            example_rows.append({"perfil": label, "userId": user, "valoraciones_train": int(history_size[user]),
                                 "politica": policy, "alpha": alpha, "seed": seed, "rank": rank,
                                 "movieId": movie_id, "title": titles[movie_id],
                                 "visto_en_train": movie_id in seen_by_user[user]})
new_user = int(ratings["userId"].max()) + 1  # no existe en entrenamiento
fallback = model.top_n(new_user, set(), K)  # usuario desconocido: el modelo devuelve una lista vacía
for rank, movie_id in enumerate(pop_count[:K], start=1):
    example_rows.append({"perfil": "usuario_nuevo", "userId": new_user, "valoraciones_train": 0,
                         "politica": "fallback_popularidad_conteo", "alpha": "", "seed": "", "rank": rank,
                         "movieId": int(movie_id), "title": titles[movie_id], "visto_en_train": False})
pd.DataFrame(example_rows).to_csv(reports / "profile_examples.csv", index=False)

pd.set_option("display.width", 140)
print(summary.round(4).to_string(index=False))
print(f"\nUsuarios evaluables: {len(users)} | Catálogo de entrenamiento: {len(train_items)}")
print(f"Perfiles: amplio={wide_user} ({history_size[wide_user]} valoraciones), "
      f"pequeño={small_user} ({history_size[small_user]}), nuevo={new_user} "
      f"(colaborativo devuelve {len(fallback)} ítems -> fallback no personalizado)")
print("Archivos: reports/comparison_metrics.csv, reports/comparison_summary.csv, reports/profile_examples.csv")
