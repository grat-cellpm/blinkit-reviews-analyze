"""Embedding + vector retrieval with optional Chroma/ST, TF-IDF fallback."""

from __future__ import annotations

import json
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings

_HAS_ST = False
_HAS_CHROMA = False

try:
    from sentence_transformers import SentenceTransformer  # noqa: F401

    _HAS_ST = True
except Exception:
    _HAS_ST = False

try:
    import chromadb  # noqa: F401

    _HAS_CHROMA = True
except Exception:
    _HAS_CHROMA = False


def _store_path() -> Path:
    settings = get_settings()
    path = Path(settings.chroma_path)
    path.mkdir(parents=True, exist_ok=True)
    return path / "tfidf_index.pkl"


@lru_cache
def get_embedding_model():
    if not _HAS_ST:
        return None
    from sentence_transformers import SentenceTransformer

    settings = get_settings()
    return SentenceTransformer(settings.embedding_model)


def get_chroma_collection():
    if not _HAS_CHROMA:
        return None
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    settings = get_settings()
    Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=settings.chroma_path,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        name="blinkit_reviews",
        metadata={"hnsw:space": "cosine"},
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    if model is None:
        raise RuntimeError("sentence-transformers not available")
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return [v.tolist() for v in vectors]


def _load_tfidf_store() -> dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return {"ids": [], "documents": [], "metadatas": [], "vectorizer": None, "matrix": None}
    with path.open("rb") as f:
        return pickle.load(f)


def _save_tfidf_store(store: dict[str, Any]) -> None:
    with _store_path().open("wb") as f:
        pickle.dump(store, f)


def _upsert_tfidf(
    ids: list[str],
    documents: list[str],
    metadatas: list[dict[str, Any]],
) -> int:
    from sklearn.feature_extraction.text import TfidfVectorizer

    store = _load_tfidf_store()
    id_to_idx = {rid: i for i, rid in enumerate(store["ids"])}

    for rid, doc, meta in zip(ids, documents, metadatas):
        if rid in id_to_idx:
            i = id_to_idx[rid]
            store["documents"][i] = doc
            store["metadatas"][i] = meta
        else:
            store["ids"].append(rid)
            store["documents"].append(doc)
            store["metadatas"].append(meta)
            id_to_idx[rid] = len(store["ids"]) - 1

    if not store["documents"]:
        return 0

    vectorizer = TfidfVectorizer(max_features=4096, ngram_range=(1, 2), stop_words="english")
    matrix = vectorizer.fit_transform(store["documents"])
    store["vectorizer"] = vectorizer
    store["matrix"] = matrix
    _save_tfidf_store(store)
    return len(ids)


def _query_tfidf(query: str, top_k: int) -> list[dict[str, Any]]:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    store = _load_tfidf_store()
    if not store["documents"] or store["vectorizer"] is None or store["matrix"] is None:
        return []

    q_vec = store["vectorizer"].transform([query])
    sims = cosine_similarity(q_vec, store["matrix"]).flatten()
    if len(sims) == 0:
        return []
    top_idx = np.argsort(sims)[::-1][:top_k]
    items: list[dict[str, Any]] = []
    for i in top_idx:
        score = float(sims[i])
        if score <= 0:
            continue
        items.append(
            {
                "review_id": store["ids"][i],
                "content": store["documents"][i],
                "metadata": store["metadatas"][i],
                "relevance_score": round(score, 4),
            }
        )
    return items


def upsert_review_embeddings(
    ids: list[str],
    documents: list[str],
    metadatas: list[dict[str, Any]],
) -> int:
    if not ids:
        return 0

    # Prefer Chroma + sentence-transformers when available
    if _HAS_ST and _HAS_CHROMA:
        collection = get_chroma_collection()
        embeddings = embed_texts(documents)
        batch = 64
        for i in range(0, len(ids), batch):
            collection.upsert(
                ids=ids[i : i + batch],
                documents=documents[i : i + batch],
                embeddings=embeddings[i : i + batch],
                metadatas=metadatas[i : i + batch],
            )
        return len(ids)

    return _upsert_tfidf(ids, documents, metadatas)


def query_similar(query: str, top_k: int | None = None) -> list[dict[str, Any]]:
    settings = get_settings()
    k = top_k or settings.rag_top_k

    if _HAS_ST and _HAS_CHROMA:
        collection = get_chroma_collection()
        if collection is not None and collection.count() > 0:
            q_emb = embed_texts([query])[0]
            result = collection.query(
                query_embeddings=[q_emb],
                n_results=min(k, collection.count()),
                include=["documents", "metadatas", "distances"],
            )
            items: list[dict[str, Any]] = []
            docs = result.get("documents", [[]])[0]
            metas = result.get("metadatas", [[]])[0]
            dists = result.get("distances", [[]])[0]
            ids = result.get("ids", [[]])[0]
            for i, doc in enumerate(docs):
                dist = dists[i] if i < len(dists) else 1.0
                score = max(0.0, 1.0 - float(dist))
                meta = metas[i] if i < len(metas) else {}
                items.append(
                    {
                        "review_id": ids[i] if i < len(ids) else meta.get("review_id"),
                        "content": doc,
                        "metadata": meta,
                        "relevance_score": round(score, 4),
                    }
                )
            return items

    return _query_tfidf(query, k)


def backend_info() -> dict[str, Any]:
    return {
        "sentence_transformers": _HAS_ST,
        "chromadb": _HAS_CHROMA,
        "vector_backend": "chroma+st" if (_HAS_ST and _HAS_CHROMA) else "tfidf",
        "index_exists": _store_path().exists() or (_HAS_CHROMA and get_chroma_collection() is not None),
    }


# Keep json import available for debugging dumps
_ = json
