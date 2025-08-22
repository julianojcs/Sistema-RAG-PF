"""
Configurações centralizadas do Sistema RAG-PF
"""
import os

class Settings:
    """Configurações do sistema"""

    # Ollama
    OLLAMA_URL = "http://localhost:11434"
    OLLAMA_TIMEOUT = 5
    EMBEDDING_MODEL = "nomic-embed-text:latest"
    LLM_MODEL = "llama3.2:latest"

    # Paths
    # Pasta de PDFs (nome canônico: SGP)
    PDF_FOLDER = os.environ.get("PF_RAG_PDF_FOLDER", "SGP")
    FAISS_DB_PATH = os.environ.get("PF_RAG_FAISS_PATH", "faissDB")
    QDRANT_PATH = os.environ.get("PF_RAG_QDRANT_PATH", "qdrantDB")
    CACHE_FILE = "faissDB/cache_respostas.json"
    HASH_FILE = "faissDB/sgp_hash.json"
    CHUNKS_JSONL_PATH = os.environ.get("PF_RAG_CHUNKS_JSONL", "faissDB/chunks.jsonl")
    EXPORT_CHUNKS_JSONL = os.environ.get("PF_RAG_EXPORT_JSONL", "true").lower() == "true"

    # RAG Configurações
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 200
    RETRIEVAL_K = 6
    CACHE_LRU_SIZE = 50

    # Pipeline PF RAG
    TOKEN_TARGET_MIN = int(os.environ.get("PF_RAG_TOKEN_MIN", 400))
    TOKEN_TARGET_MAX = int(os.environ.get("PF_RAG_TOKEN_MAX", 1200))
    OCR_ENABLED = os.environ.get("PF_RAG_OCR_ENABLED", "true").lower() == "true"
    OCR_LANG = os.environ.get("PF_RAG_OCR_LANG", "por")
    EMBEDDING_BACKEND = os.environ.get("PF_RAG_EMBED_BACKEND", "ollama").lower()  # ollama | sbert
    BM25_ENABLED = os.environ.get("PF_RAG_BM25_ENABLED", "true").lower() == "true"
    VECTOR_INDEX_NAME = os.environ.get("PF_RAG_INDEX_NAME", "pf_normativos")
    VECTOR_DB_BACKEND = os.environ.get("PF_RAG_VECTOR_DB", "qdrant").lower()  # faiss | qdrant | chroma (futuro)
    QDRANT_COLLECTION = os.environ.get("PF_RAG_QDRANT_COLLECTION", VECTOR_INDEX_NAME)
    EMBED_BATCH_SIZE = int(os.environ.get("PF_RAG_EMBED_BATCH", 64))
    VERBOSE = os.environ.get("PF_RAG_VERBOSE", "true").lower() == "true"
    DOCLING_ENABLED = os.environ.get("PF_RAG_USE_DOCLING", "true").lower() == "true"

    # Modo offline por padrão: impede downloads remotos de modelos (ex.: sentence-transformers)
    OFFLINE_MODE = os.environ.get("PF_RAG_OFFLINE", "true").lower() == "true"
    if OFFLINE_MODE:
        # Efeito apenas no processo atual; garante operação sem rede para libs HuggingFace
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")

    # Sistema
    AUTO_SAVE_INTERVAL = 5  # Salva cache a cada 5 perguntas

    @classmethod
    def get_separators(cls):
        """Retorna separadores para divisão de chunks"""
        return ["\n\n", "\n", ". ", " ", ""]

    @classmethod
    def get_ollama_api_url(cls, endpoint="tags"):
        """Constrói URL da API Ollama"""
        return f"{cls.OLLAMA_URL}/api/{endpoint}"
