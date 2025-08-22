from __future__ import annotations
from typing import List, Dict, Any, Optional

from langchain.embeddings.base import Embeddings
from langchain_ollama import OllamaEmbeddings

# Prefer the new package, fallback to community for compatibility
try:  # LangChain >= 0.0.37 moved Qdrant into a separate package
    from langchain_qdrant import Qdrant as LCQdrant  # type: ignore
except Exception:  # pragma: no cover
    from langchain_community.vectorstores import Qdrant as LCQdrant  # type: ignore
try:
    from qdrant_client import QdrantClient  # type: ignore
except Exception:  # pragma: no cover
    QdrantClient = None  # type: ignore

from src.config.settings import Settings
from src.pf_rag.embed_index import SbertEmbeddings
from src.pf_rag.types import Chunk


class QdrantIndexer:
    """Qdrant indexer for local embedded usage with upsert/delete capabilities."""

    def __init__(self, backend: str = Settings.EMBEDDING_BACKEND):
        if backend == "ollama":
            self.embeddings: Embeddings = OllamaEmbeddings(model=Settings.EMBEDDING_MODEL)
        else:
            self.embeddings = SbertEmbeddings()
        # Don't create client here - let LangChain manage it to avoid conflicts
        if QdrantClient is None:
            raise RuntimeError("qdrant-client não instalado. Instale qdrant-client para usar backend Qdrant.")
        self.collection = Settings.QDRANT_COLLECTION

    def _get_client(self):
        """Get a temporary client for operations that need direct access."""
        return QdrantClient(path=Settings.QDRANT_PATH)

    def _collection_exists(self) -> bool:
        try:  # type: ignore
            client = self._get_client()
            cols = client.get_collections().collections
            return any(getattr(c, "name", None) == self.collection for c in cols)
        except Exception:
            return False

    def ensure_collection(self) -> None:
        # Intencionalmente não criamos aqui, pois criar requer vector_size.
        # Operações de criação ficam a cargo do wrapper LangChain quando adicionamos textos.
        return

    @staticmethod
    def chunk_to_point(ch: Chunk) -> Dict[str, Any]:
        md = {k: v for k, v in ch.__dict__.items() if k != "texto"}
        md.setdefault("file_path", ch.origem_pdf.get("arquivo"))
        md.setdefault("anchor_id", ch.anchor_id)
        return {
            "text": ch.texto,
            "metadata": md,
        }

    def to_texts_and_metadatas(self, chunks: List[Chunk]) -> tuple[List[str], List[Dict[str, Any]]]:
        texts: List[str] = []
        metas: List[Dict[str, Any]] = []
        for ch in chunks:
            texts.append(ch.texto)
            md = {k: v for k, v in ch.__dict__.items() if k != "texto"}
            md.setdefault("file_path", ch.origem_pdf.get("arquivo"))
            metas.append(md)
        return texts, metas

    def build_qdrant(self, chunks: List[Chunk], progress_callback=None):
        texts, metas = self.to_texts_and_metadatas(chunks)
        
        if progress_callback:
            progress_callback(0.1, f"Preparando {len(texts)} chunks para indexação...")
        
        # Use from_texts for both langchain_qdrant and community versions
        vs = LCQdrant.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metas,
            url=None,  # Use path instead
            path=Settings.QDRANT_PATH,
            collection_name=self.collection,
        )
        
        if progress_callback:
            progress_callback(1.0, f"Base Qdrant criada com {len(texts)} chunks")
        
        return vs

    def load_qdrant(self) -> Optional[object]:
        try:
            if not self._collection_exists():
                return None
            return LCQdrant(
                embedding=self.embeddings,
                url=None,  # Use path instead
                path=Settings.QDRANT_PATH,
                collection_name=self.collection,
            )
        except Exception:
            return None

    def add_chunks(self, vs: object, chunks: List[Chunk]) -> None:
        texts, metas = self.to_texts_and_metadatas(chunks)
        # Some versions accept "metadatas", others "metadatas" only — use kwargs
        vs.add_texts(texts=texts, metadatas=metas)

    def delete_by_file(self, vs: object, file_path: str) -> int:
        try:
            if not self._collection_exists():
                return 0
            import os as _os
            key = _os.path.basename(file_path)
            vs.delete(where={"file_path": key})
            return 1
        except Exception:
            return 0

    def clear_collection(self) -> None:
        try:
            # Remove a coleção por completo (novo build criará novamente)
            client = self._get_client()
            client.delete_collection(collection_name=self.collection)
        except Exception:
            pass
