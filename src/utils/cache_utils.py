"""
Utilitários para cache de respostas
"""
import os
import json
import time
from typing import Optional, Dict, Any
from functools import lru_cache
from ..config.settings import Settings


class CacheUtils:
    """Utilitários para gerenciamento de cache"""

    def __init__(self):
        self.cache_respostas: Dict[str, Any] = {}
        self.load_cache()

    def normalize_question(self, pergunta: str) -> str:
        """Normaliza pergunta para busca no cache"""
        return pergunta.lower().strip().replace("?", "").replace(".", "")

    def load_cache(self) -> None:
        """Carrega cache de respostas do disco"""
        try:
            if os.path.exists(Settings.CACHE_FILE):
                with open(Settings.CACHE_FILE, "r", encoding="utf-8") as f:
                    self.cache_respostas = json.load(f)
                print(f"📋 Cache carregado: {len(self.cache_respostas)} respostas em memória")
        except Exception as e:
            print(f"⚠️ Erro ao carregar cache: {e}")
            self.cache_respostas = {}

    def save_cache(self) -> None:
        """Salva cache de respostas no disco"""
        try:
            os.makedirs(Settings.FAISS_DB_PATH, exist_ok=True)
            with open(Settings.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cache_respostas, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Erro ao salvar cache: {e}")

    def get_cached_response(self, pergunta: str) -> Optional[Dict[str, Any]]:
        """Busca resposta no cache"""
        pergunta_norm = self.normalize_question(pergunta)
        return self.cache_respostas.get(pergunta_norm)

    def save_response(self, pergunta: str, resposta: str) -> None:
        """Salva resposta no cache"""
        pergunta_norm = self.normalize_question(pergunta)
        self.cache_respostas[pergunta_norm] = {
            "resposta": resposta,
            "timestamp": time.time(),
            "pergunta_original": pergunta
        }

    def get_cache_size(self) -> int:
        """Retorna tamanho do cache"""
        return len(self.cache_respostas)

    def clear_all(self) -> None:
        """Limpa completamente o cache em memória e no disco."""
        self.cache_respostas = {}
        try:
            if os.path.exists(Settings.CACHE_FILE):
                os.remove(Settings.CACHE_FILE)
        except Exception:
            pass

    @lru_cache(maxsize=Settings.CACHE_LRU_SIZE)
    def semantic_search_cache(self, pergunta_hash: str, k: int = Settings.RETRIEVAL_K):
        """Cache LRU para buscas semânticas"""
        # Esta função será usada pelo serviço de RAG
        return None
