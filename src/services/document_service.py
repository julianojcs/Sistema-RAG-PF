"""
Serviço para gerenciamento de documentos e base de dados
"""
import os
import sys
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

from ..config.settings import Settings
from ..utils.file_utils import FileUtils
from .ollama_service import OllamaService


class DocumentService:
    """Serviço para processamento de documentos e criação da base de dados"""

    def __init__(self):
        self.database: Optional[FAISS] = None
        self.embeddings = OllamaEmbeddings(model=Settings.EMBEDDING_MODEL)

    def load_or_create_database(self) -> Optional[FAISS]:
        """Carrega base existente ou cria nova se necessário"""
        print("⚡ Verificando base de dados...")

        # Verifica se houve mudanças na pasta SGP
        mudancas_detectadas, hash_atual = FileUtils.check_folder_changes()

        if mudancas_detectadas:
            if os.path.exists(Settings.FAISS_DB_PATH):
                print("🔄 Mudanças detectadas na pasta SGP. Recriando base de dados...")
            else:
                print("📁 Primeira execução. Criando base de dados...")
            self.database = None
        else:
            self.database = self._load_existing_database()
            if self.database:
                print("✅ Base de dados carregada (sem mudanças)!")
                return self.database

        # Se chegou aqui, precisa criar nova base
        self.database = self._create_new_database()
        if self.database:
            FileUtils.save_hash(hash_atual)

        return self.database

    def _load_existing_database(self) -> Optional[FAISS]:
        """Carrega base de dados existente"""
        try:
            return FAISS.load_local(
                Settings.FAISS_DB_PATH,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        except Exception as e:
            print("⚠️ Erro ao carregar base de dados. Recriando...")
            return None

    def _create_new_database(self) -> Optional[FAISS]:
        """Cria nova base de dados a partir dos documentos"""
        print("📄 Processando documentos da pasta SGP...")

        # Carrega documentos
        docs = self._load_documents()
        if not docs:
            return None

        # Processa documentos em chunks
        documents = self._split_documents(docs)

        # Cria embeddings e base FAISS
        return self._create_faiss_database(documents)

    def _load_documents(self) -> List:
        """Carrega documentos PDF da pasta SGP"""
        try:
            # Verifica arquivos PDF
            arquivos_pdf = FileUtils.get_pdf_files()
            print(f"📁 Encontrados {len(arquivos_pdf)} arquivos PDF: {[os.path.basename(f) for f in arquivos_pdf]}")

            # Carrega documentos (cada página vira um documento)
            loader = DirectoryLoader(f"{Settings.SGP_FOLDER}/", glob="*.pdf", loader_cls=PyPDFLoader)
            docs = loader.load()

            if not docs:
                print("❌ Nenhum documento PDF encontrado na pasta SGP/")
                print("📁 Adicione arquivos PDF válidos na pasta SGP/ e reinicie o programa")
                sys.exit(1)

            print(f"📋 Total de páginas carregadas: {len(docs)}")
            return docs

        except ImportError as e:
            if "pypdf" in str(e):
                print("❌ Biblioteca pypdf não encontrada")
                print("🔧 Execute: pip install pypdf")
            else:
                print(f"❌ Erro de importação: {str(e)}")
            sys.exit(1)

        except Exception as e:
            print(f"❌ Erro ao carregar documentos: {str(e)[:100]}...")
            print("🔧 Verifique se os arquivos PDF não estão corrompidos")
            sys.exit(1)

    def _split_documents(self, docs: List) -> List:
        """Divide documentos em chunks"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Settings.CHUNK_SIZE,
            chunk_overlap=Settings.CHUNK_OVERLAP,
            separators=Settings.get_separators()
        )

        print("🔧 Dividindo documentos em chunks...")
        documents = text_splitter.split_documents(docs)
        print(f"📊 Criados {len(documents)} chunks de texto")

        return documents

    def _create_faiss_database(self, documents: List) -> Optional[FAISS]:
        """Cria base FAISS com embeddings"""
        print("🧠 Criando embeddings e base de dados...")
        print("⚠️ Este processo pode demorar alguns minutos...")

        try:
            # Verifica conexão com Ollama
            conectado, erro = OllamaService.check_connection()
            if not conectado:
                print("❌ Ollama não está acessível para criar embeddings")
                OllamaService.print_connection_error(erro)
                sys.exit(1)

            print("✅ Ollama acessível, criando embeddings...")
            database = FAISS.from_documents(documents, self.embeddings)

            print("💾 Salvando base de dados...")
            database.save_local(Settings.FAISS_DB_PATH)
            print("✅ Base de dados criada e hash salvo!")

            return database

        except Exception as e:
            error_str = str(e)
            print("❌ Erro ao criar base de dados:")

            if "Connection refused" in error_str or "503" in error_str:
                print("🔧 Ollama perdeu conexão durante o processamento")
                print("💡 Execute 'ollama serve' e tente novamente")
            elif "proxy" in error_str.lower():
                print("🌐 Bloqueio de proxy detectado")
                print("💡 Configure bypass para localhost:11434")
            else:
                print(f"📝 Detalhes: {error_str[:150]}...")

            sys.exit(1)
