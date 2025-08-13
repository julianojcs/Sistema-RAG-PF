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
    SGP_FOLDER = "SGP"
    FAISS_DB_PATH = "faissDB"
    CACHE_FILE = "faissDB/cache_respostas.json"
    HASH_FILE = "faissDB/sgp_hash.json"

    # RAG Configurações
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 200
    RETRIEVAL_K = 6
    CACHE_LRU_SIZE = 50

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
