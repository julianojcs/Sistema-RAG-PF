"""
Serviço para gerenciamento de documentos e base de dados
Refatorado para usar pipeline PF RAG (PDF -> normalização -> parsing -> chunking -> indexação FAISS)
"""
import os
import sys
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings

from ..config.settings import Settings
from ..utils.file_utils import FileUtils
from .ollama_service import OllamaService

# PF pipeline
from src.pf_rag.io_pdf import extract_text as pf_extract_text
from src.pf_rag.normalize import clean_text as pf_clean_text
from src.pf_rag.parse_norma import detect_structure as pf_detect
from src.pf_rag.metadata_pf import extract as pf_meta_extract
from src.pf_rag.chunker import build_chunks as pf_build_chunks
from src.pf_rag.embed_index import Indexer as PFIndexer, SbertEmbeddings
from src.vector_backends.qdrant_backend import QdrantIndexer
from src.pf_rag.export_jsonl import export_chunks_jsonl


class DocumentService:
    """Serviço para processamento de documentos e criação da base de dados"""

    def __init__(self):
        self.database: Optional[object] = None
        # Embeddings serão escolhidos conforme backend configurado
        if Settings.EMBEDDING_BACKEND == "sbert":
            self.embeddings = SbertEmbeddings()
        else:
            self.embeddings = OllamaEmbeddings(model=Settings.EMBEDDING_MODEL)

    def load_or_create_database(self, progress_callback=None) -> Optional[object]:
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

        # Se chegou aqui, precisa criar nova base (PF pipeline)
        self.database = self._create_pf_rag_database(progress_callback)
        if self.database:
            FileUtils.save_hash(hash_atual)

        return self.database

    def _load_existing_database(self) -> Optional[object]:
        """Carrega base de dados existente"""
        try:
            if Settings.VECTOR_DB_BACKEND == "qdrant":
                q = QdrantIndexer(backend=Settings.EMBEDDING_BACKEND)
                return q.load_qdrant()
            # Default: FAISS
            return FAISS.load_local(
                Settings.FAISS_DB_PATH,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        except Exception:
            print("⚠️ Erro ao carregar base de dados. Recriando...")
            return None

    def _create_pf_rag_database(self, progress_callback=None) -> Optional[object]:
        """Cria nova base FAISS usando pipeline PF (hierárquico)."""
        print("📄 Processando documentos da pasta SGP com pipeline PF RAG...")
        try:
            arquivos_pdf = FileUtils.get_pdf_files()
            if not arquivos_pdf:
                print("❌ Nenhum documento PDF encontrado na pasta SGP/")
                print("📁 Adicione arquivos PDF válidos na pasta SGP/ e reinicie o programa")
                sys.exit(1)

            import time
            all_chunks = []
            total_files = len(arquivos_pdf)

            for idx, pdf in enumerate(arquivos_pdf):
                if progress_callback:
                    file_progress = idx / total_files * 0.6  # 60% para processamento PDFs
                    progress_callback(file_progress, f"Processando {os.path.basename(pdf)} ({idx+1}/{total_files})")

                t0 = time.time()
                raw, pages, ocr = pf_extract_text(pdf)
                text, pages2 = pf_clean_text(raw, pages)
                nodes, heading = pf_detect(text)
                meta = pf_meta_extract(text, heading, os.path.basename(pdf))
                chunks = pf_build_chunks(nodes, text, meta, pdf, [p.index for p in pages2])
                all_chunks.extend(chunks)
                print(f"📦 {os.path.basename(pdf)} -> {len(chunks)} chunks em {time.time()-t0:.2f}s (OCR={ocr})")

            # Verifica conexão com Ollama somente se backend de embeddings for Ollama
            if Settings.EMBEDDING_BACKEND == "ollama":
                conectado, erro = OllamaService.check_connection()
                if not conectado:
                    print("❌ Ollama não está acessível para criar embeddings")
                    OllamaService.print_connection_error(erro)
                    sys.exit(1)

            if Settings.VECTOR_DB_BACKEND.startswith("qdrant"):
                if progress_callback:
                    progress_callback(0.65, f"Preparando indexação Qdrant ({len(all_chunks)} chunks)...")

                print(f"🧠 Criando embeddings e base Qdrant (chunks={len(all_chunks)})...")
                qindex = QdrantIndexer(backend=Settings.EMBEDDING_BACKEND)

                # Clear any existing storage to avoid conflicts (with retries)
                max_clear_attempts = 3
                for attempt in range(max_clear_attempts):
                    try:
                        qindex.clear_collection()
                        break
                    except Exception as e:
                        if "already accessed by another instance" in str(e):
                            print(f"⚠️ Tentativa {attempt + 1}: Aguardando liberação do Qdrant...")
                            import time
                            time.sleep(2 + attempt)
                            # Force clear storage on last attempt
                            if attempt == max_clear_attempts - 1:
                                qindex._clear_storage_lock()
                        else:
                            break

                # Also try to remove the storage folder if it exists and is locked
                import shutil
                try:
                    if os.path.exists(Settings.QDRANT_PATH):
                        shutil.rmtree(Settings.QDRANT_PATH, ignore_errors=True)
                        import time
                        time.sleep(0.5)  # Brief pause for filesystem
                except Exception:
                    pass

                def qdrant_callback(frac: float, msg: str):
                    # Map to 65%-95% range
                    val = 0.65 + (frac * 0.3)
                    if progress_callback:
                        progress_callback(val, f"Qdrant: {msg}")

                t0 = time.time()

                # Build with retry logic for instance conflicts
                max_build_attempts = 2
                db = None
                for attempt in range(max_build_attempts):
                    try:
                        db = qindex.build_qdrant(all_chunks, progress_callback=qdrant_callback)
                        break
                    except Exception as e:
                        if "already accessed by another instance" in str(e) and attempt < max_build_attempts - 1:
                            print(f"⚠️ Conflito de instância Qdrant, tentando novamente...")
                            qindex._clear_storage_lock()
                            import time
                            time.sleep(2)
                        else:
                            raise e

                if db is None:
                    raise RuntimeError("Falha ao criar base Qdrant após múltiplas tentativas")

                print(f"⏱️ Tempo embeddings+index: {time.time()-t0:.2f}s")
                # Qdrant embutido persiste via path automaticamente
            else:
                if progress_callback:
                    progress_callback(0.65, f"Preparando indexação FAISS ({len(all_chunks)} chunks)...")

                indexer = PFIndexer(backend=Settings.EMBEDDING_BACKEND)
                print(f"🧠 Criando embeddings hierárquicos e base FAISS (chunks={len(all_chunks)})...")

                def faiss_callback(frac: float, msg: str):
                    # Map to 65%-95% range
                    val = 0.65 + (frac * 0.3)
                    if progress_callback:
                        progress_callback(val, f"FAISS: {msg}")

                t0 = time.time()
                db = indexer.build_faiss(all_chunks, progress_callback=faiss_callback)
                print(f"⏱️ Tempo embeddings+index: {time.time()-t0:.2f}s")
                print("💾 Salvando base de dados...")
                indexer.save_faiss(db, Settings.FAISS_DB_PATH)

            # Export JSONL para auditoria
            if Settings.EXPORT_CHUNKS_JSONL:
                if progress_callback:
                    progress_callback(0.98, "Exportando JSONL para auditoria...")
                try:
                    msg = export_chunks_jsonl(all_chunks, Settings.CHUNKS_JSONL_PATH)
                    print("📝", msg)
                except Exception as e:
                    print(f"⚠️ Falha ao exportar JSONL: {e}")

            if progress_callback:
                progress_callback(1.0, "✅ Base de dados criada com sucesso!")
            print("✅ Base de dados criada (PF RAG)!")
            return db
        except Exception as e:
            print(f"❌ Erro ao criar base PF RAG: {str(e)[:150]}...")
            sys.exit(1)

    def _load_documents(self) -> List:
        """Carrega documentos PDF da pasta SGP"""
        try:
            # Verifica arquivos PDF
            arquivos_pdf = FileUtils.get_pdf_files()
            print(f"📁 Encontrados {len(arquivos_pdf)} arquivos PDF: {[os.path.basename(f) for f in arquivos_pdf]}")

            # Carrega documentos (cada página vira um documento)
            loader = DirectoryLoader(f"{Settings.PDF_FOLDER}/", glob="*.pdf", loader_cls=PyPDFLoader)
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
