from __future__ import annotations
from typing import Any, Dict, Optional
from src.config.settings import Settings

try:
    from rank_bm25 import BM25Okapi  # type: ignore
except Exception:
    BM25Okapi = None  # type: ignore


class Searcher:
    def __init__(self, db: Any):
        self.db = db
        # preparo BM25 (opcional) apenas quando possível extrair corpus localmente
        self.bm25 = None
        try:
            if Settings.BM25_ENABLED and BM25Okapi is not None and hasattr(self.db, "docstore"):
                texts = [d.page_content for d in self.db.docstore._dict.values()]  # type: ignore[attr-defined]
                tokenized = [t.lower().split() for t in texts]
                self.bm25 = BM25Okapi(tokenized)
        except Exception:
            self.bm25 = None

    def query(self, q: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None, expand_context: bool = True):
        # Dense
        docs_dense = self.db.similarity_search(q, k=top_k * 3)

        if self.bm25 is not None:
            # Híbrida: combinar com BM25
            texts = [d.page_content for d in self.db.docstore._dict.values()]  # type: ignore
            scores = self.bm25.get_scores(q.lower().split())
            scored = sorted(zip(texts, scores), key=lambda x: x[1], reverse=True)[: top_k * 3]
            bm25_set = set(t for t, _ in scored)
            docs_dense = [d for d in docs_dense if d.page_content in bm25_set] + docs_dense

        # Re-ranking simples sensível a hierarquia: boost por match exato de rótulos
        def score_doc(d) -> float:
            meta = d.metadata or {}
            breadcrumb = meta.get("breadcrumb", "").lower()
            s = 0.0
            for tok in ["art.", "§", "capítulo", "seção", "inciso", "alínea"]:
                if tok in q.lower() and tok in breadcrumb:
                    s += 0.5
            if any(part in breadcrumb for part in q.lower().split()):
                s += 0.2
            return s

        reranked = sorted(docs_dense, key=lambda d: score_doc(d), reverse=True)[:top_k]
        return reranked
