from __future__ import annotations
from typing import List, Dict, Any, Optional, Callable

from langchain_community.vectorstores import FAISS
from langchain.embeddings.base import Embeddings
from langchain_ollama import OllamaEmbeddings

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore

from src.config.settings import Settings
from .types import Chunk


class SbertEmbeddings(Embeddings):
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers não instalado")
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:  # type: ignore[override]
        return [list(map(float, v)) for v in self.model.encode(texts, show_progress_bar=False, normalize_embeddings=True)]

    def embed_query(self, text: str) -> List[float]:  # type: ignore[override]
        return list(map(float, self.model.encode([text], show_progress_bar=False, normalize_embeddings=True)[0]))


class Indexer:
    def __init__(self, backend: str = Settings.EMBEDDING_BACKEND):
        if backend == "ollama":
            self.embeddings: Embeddings = OllamaEmbeddings(model=Settings.EMBEDDING_MODEL)
        else:
            self.embeddings = SbertEmbeddings()

    def to_texts_and_metadatas(self, chunks: List[Chunk]) -> tuple[List[str], List[Dict[str, Any]]]:
        texts: List[str] = []
        metas: List[Dict[str, Any]] = []
        def fmt_label(nivel: str, rotulo: str) -> str:
            mapa = {
                "parte": "Parte",
                "livro": "Livro",
                "titulo": "Título",
                "capitulo": "Capítulo",
                "secao": "Seção",
                "subsecao": "Subseção",
                "artigo": "Art.",
                "paragrafo": "Parágrafo",
                "inciso": "Inciso",
                "alinea": "Alínea",
                "item": "Item",
                "anexo": "Anexo",
            }
            r = (rotulo or "").strip()
            r = r.replace("§", "").strip()
            if nivel == "paragrafo":
                low = r.lower().replace("ú", "u").strip()
                if "unico" in low or low == "unico":
                    return "Parágrafo único"
                return f"Parágrafo {r}" if r else "Parágrafo"
            if nivel == "alinea":
                return f"Alínea {r}" if r else "Alínea"
            nome = mapa.get(nivel, nivel.capitalize())
            if nivel == "artigo":
                return f"{nome} {r}" if r else nome
            return f"{nome} {r}" if r else nome
        for ch in chunks:
            # caminho_hierarquico já inclui o próprio nó atual
            caminho = ch.caminho_hierarquico
            breadcrumb = " > ".join([fmt_label(n["nivel"], n["rotulo"]) for n in caminho])
            text_for_embed = breadcrumb + "\n\n" + ch.texto
            texts.append(text_for_embed)
            md = {k: v for k, v in ch.__dict__.items() if k not in {"texto"}}
            md["breadcrumb"] = breadcrumb
            metas.append(md)
        return texts, metas

    def build_faiss(self, chunks: List[Chunk], progress_cb: Optional[Callable[[float, str], None]] = None) -> FAISS:
        import time
        texts, metas = self.to_texts_and_metadatas(chunks)
        bs = max(1, Settings.EMBED_BATCH_SIZE)
        if Settings.VERBOSE:
            print(f"🔢 Total de chunks: {len(texts)} | Batch: {bs}")
        if progress_cb:
            progress_cb(0.0, "Iniciando embeddings")
        # Fast path: some embeddings support internal batching via from_texts; fallback to manual batched add
        if hasattr(FAISS, "from_texts") and bs >= len(texts):
            t0 = time.time()
            db = FAISS.from_texts(texts, embedding=self.embeddings, metadatas=metas)
            if Settings.VERBOSE:
                print(f"✅ Embeddings concluídos em {time.time() - t0:.2f}s (single call)")
            if progress_cb:
                progress_cb(1.0, "Embeddings concluídos")
            return db
        # Manual batching
        db = None
        t0 = time.time()
        total_batches = (len(texts)+bs-1)//bs if len(texts) else 1
        for i in range(0, len(texts), bs):
            bt = texts[i:i+bs]
            bm = metas[i:i+bs]
            bstart = time.time()
            if db is None:
                db = FAISS.from_texts(bt, embedding=self.embeddings, metadatas=bm)
            else:
                db.add_texts(bt, metadatas=bm)
            if Settings.VERBOSE:
                print(f"🧩 Lote {i//bs + 1}/{total_batches} -> {len(bt)} itens em {time.time()-bstart:.2f}s")
            if progress_cb:
                frac = min(1.0, (i//bs + 1) / total_batches)
                progress_cb(frac, f"Lote {i//bs + 1}/{total_batches}")
        if Settings.VERBOSE:
            print(f"✅ Embeddings totais em {time.time() - t0:.2f}s")
        if progress_cb:
            progress_cb(1.0, "Embeddings concluídos")
        return db  # type: ignore

    def save_faiss(self, db: FAISS, path: str = Settings.FAISS_DB_PATH):
        db.save_local(path)

    @staticmethod
    def load_faiss(path: str = Settings.FAISS_DB_PATH, embeddings: Optional[Embeddings] = None) -> Optional[FAISS]:
        try:
            if embeddings is None:
                if Settings.EMBEDDING_BACKEND == "sbert":
                    embeddings = SbertEmbeddings()
                else:
                    embeddings = OllamaEmbeddings(model=Settings.EMBEDDING_MODEL)
            return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
        except Exception:
            return None
