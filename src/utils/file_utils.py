"""
Utilitários para manipulação de arquivos e hash
"""
import os
import glob
import hashlib
import json
from typing import List, Tuple
from ..config.settings import Settings


class FileUtils:
    """Utilitários para manipulação de arquivos"""

    @staticmethod
    def get_pdf_files() -> List[str]:
        """Retorna lista de arquivos PDF na pasta SGP"""
        return glob.glob(f"{Settings.SGP_FOLDER}/*.pdf")

    @staticmethod
    def generate_folder_hash() -> str:
        """Gera hash MD5 dos arquivos PDF na pasta SGP"""
        try:
            arquivos_pdf = FileUtils.get_pdf_files()
            if not arquivos_pdf:
                return "vazio"

            # Ordena os arquivos para hash consistente
            arquivos_pdf.sort()
            hash_dados = []

            for arquivo in arquivos_pdf:
                stat = os.stat(arquivo)
                hash_dados.append(f"{arquivo}:{stat.st_size}:{stat.st_mtime}")

            # Gera hash MD5 da lista de arquivos
            hash_string = "|".join(hash_dados)
            return hashlib.md5(hash_string.encode()).hexdigest()

        except Exception as e:
            print(f"⚠️ Erro ao verificar pasta SGP: {e}")
            return "erro"

    @staticmethod
    def save_hash(hash_value: str) -> None:
        """Salva hash da pasta no arquivo"""
        try:
            os.makedirs(Settings.FAISS_DB_PATH, exist_ok=True)
            with open(Settings.HASH_FILE, "w") as f:
                json.dump({"hash": hash_value}, f)
        except Exception:
            pass

    @staticmethod
    def load_saved_hash() -> str:
        """Carrega hash salvo do arquivo"""
        try:
            if os.path.exists(Settings.HASH_FILE):
                with open(Settings.HASH_FILE, "r") as f:
                    dados = json.load(f)
                    return dados.get("hash", "")
        except Exception:
            pass
        return ""

    @staticmethod
    def check_folder_changes() -> Tuple[bool, str]:
        """
        Verifica se houve mudanças na pasta SGP
        Returns: (mudanças_detectadas, hash_atual)
        """
        hash_atual = FileUtils.generate_folder_hash()
        hash_salvo = FileUtils.load_saved_hash()

        if not hash_salvo:
            return True, hash_atual  # Primeira execução

        return hash_atual != hash_salvo, hash_atual
