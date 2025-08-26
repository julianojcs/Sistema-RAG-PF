from __future__ import annotations
import time
import os
import shutil
import glob
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

        # Clean up any old timestamped directories on initialization
        self._cleanup_old_qdrant_dirs()

    def _cleanup_old_qdrant_dirs(self):
        """Remove old Qdrant directories created with timestamps to avoid clutter."""
        try:
            # Get the base directory where Qdrant folders would be
            base_dir = os.path.dirname(Settings.QDRANT_PATH)
            base_name = os.path.basename(Settings.QDRANT_PATH)

            # Find all directories matching pattern like "qdrantDB_1234567890"
            pattern = os.path.join(base_dir, f"{base_name}_*")
            old_dirs = glob.glob(pattern)

            for old_dir in old_dirs:
                # Only remove if it matches timestamp pattern (numeric suffix)
                dir_name = os.path.basename(old_dir)
                if '_' in dir_name:
                    suffix = dir_name.split('_')[-1]
                    if suffix.isdigit():
                        try:
                            shutil.rmtree(old_dir, ignore_errors=True)
                            print(f"🧹 Removida pasta Qdrant antiga: {dir_name}")
                        except Exception:
                            pass
        except Exception:
            pass

    def _get_client(self):
        """Get a temporary client for operations that need direct access."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return QdrantClient(path=Settings.QDRANT_PATH)
            except Exception as e:
                if "already accessed by another instance" in str(e):
                    if attempt < max_retries - 1:
                        # Wait and retry without creating new paths
                        time.sleep(2 + attempt)
                        continue
                    else:
                        # Last attempt: force clear and try once more
                        self._clear_storage_lock()
                        time.sleep(1)
                        try:
                            return QdrantClient(path=Settings.QDRANT_PATH)
                        except Exception:
                            # If absolutely fails, raise the original error
                            raise e
                else:
                    raise e

    def _clear_storage_lock(self):
        """Remove storage folder to clear locks (last resort)."""
        try:
            if os.path.exists(Settings.QDRANT_PATH):
                shutil.rmtree(Settings.QDRANT_PATH, ignore_errors=True)
                time.sleep(0.5)  # Brief pause for filesystem
        except Exception:
            pass

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

        # Clear any existing locks/instances before creating new
        max_retries = 3
        for attempt in range(max_retries):
            try:
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

            except Exception as e:
                if "already accessed by another instance" in str(e):
                    if attempt < max_retries - 1:
                        # Clear locks and retry (without creating new paths)
                        self._clear_storage_lock()
                        time.sleep(2 + attempt)
                        continue
                    else:
                        # Final attempt failed - raise descriptive error
                        raise RuntimeError(
                            f"Erro: Outra instância do Qdrant está acessando '{Settings.QDRANT_PATH}'. "
                            "Feche outras instâncias do sistema ou aguarde alguns segundos."
                        ) from e
                else:
                    raise e
                    raise e

    def load_qdrant(self) -> Optional[object]:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self._collection_exists():
                    return None
                return LCQdrant(
                    embedding=self.embeddings,
                    url=None,  # Use path instead
                    path=Settings.QDRANT_PATH,
                    collection_name=self.collection,
                )
            except Exception as e:
                if "already accessed by another instance" in str(e):
                    if attempt < max_retries - 1:
                        time.sleep(1 + attempt)
                        continue
                    else:
                        # Last resort: return None to force rebuild
                        return None
                else:
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
        """Clear collection with robust handling of locked instances."""
        try:
            # First try the normal way
            client = self._get_client()
            client.delete_collection(collection_name=self.collection)
        except Exception as e:
            # If locked, try to remove storage folder entirely
            if "already accessed by another instance" in str(e):
                self._clear_storage_lock()
            else:
                # Try one more time after brief pause
                try:
                    time.sleep(1)
                    client = self._get_client()
                    client.delete_collection(collection_name=self.collection)
                except Exception:
                    # Final fallback: remove storage folder
                    self._clear_storage_lock()
