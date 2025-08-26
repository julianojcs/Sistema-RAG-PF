import os
import sys
import json
import warnings
import logging

# Suprimir warnings de PDF com cores inválidas
warnings.filterwarnings('ignore', message='Cannot set gray non-stroke color')
warnings.filterwarnings('ignore', category=UserWarning)
logging.getLogger('pdfminer').setLevel(logging.ERROR)

import streamlit as st

# Ensure src is on path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE_DIR)
sys.path.append(os.path.join(ROOT, "src"))

from src.core.rag_service import RAGService
from src.services.ollama_service import OllamaService
from src.pf_rag.search import Searcher
from src.pf_rag.cli import ingest_index
from src.pf_rag.embed_index import Indexer
from src.vector_backends.qdrant_backend import QdrantIndexer
from src.utils.file_utils import FileUtils
from src.config.settings import Settings
from src.pf_rag.io_pdf import extract_text
from src.pf_rag.normalize import clean_text
from src.pf_rag.parse_norma import detect_structure
from src.pf_rag.metadata_pf import extract as meta_extract
from src.pf_rag.chunker import build_chunks
from src.pf_rag.export_jsonl import export_chunks_jsonl
from src.utils.ingest_manifest import diff_current_vs_manifest, save_manifest

st.set_page_config(page_title="Sistema RAG-PF", page_icon="🛡️", layout="wide")

# Utility function para extração de PDF sem warnings
def safe_extract_text(pdf_path: str):
    """Extrai texto de PDF suprimindo warnings de cores inválidas"""
    import io
    import contextlib

    with contextlib.redirect_stderr(io.StringIO()):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return extract_text(pdf_path)

# Cached singletons
@st.cache_resource(show_spinner=False)
def get_service() -> RAGService:
    return RAGService()

def get_service_with_progress():
    """Initialize service with progress bar if needed"""
    if 'service_initialized' not in st.session_state:
        # Check if database needs to be built
        from src.utils.file_utils import FileUtils
        import os

        mudancas_detectadas, _ = FileUtils.check_folder_changes()
        needs_build = mudancas_detectadas or not os.path.exists(Settings.FAISS_DB_PATH)

        if needs_build:
            st.info("🔄 Base de dados precisa ser criada/atualizada. Processando...")

            # Progress bar
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            def progress_callback(fraction: float, message: str):
                progress_bar.progress(fraction)
                status_text.text(message)

            # Create service with progress and error handling
            try:
                from src.core.rag_service import RAGService
                service = RAGService(progress_callback=progress_callback)

                progress_bar.progress(1.0)
                status_text.text("✅ Inicialização concluída!")
                st.session_state['service_initialized'] = service

                # Clear progress elements
                progress_bar.empty()
                status_text.empty()

            except Exception as e:
                error_msg = str(e)
                if "already accessed by another instance" in error_msg:
                    st.error("❌ **Erro**: Outra instância do sistema está rodando. Por favor:")
                    st.markdown("""
                    1. **Feche outras instâncias** do Streamlit ou terminal com RAG
                    2. **Aguarde 10 segundos** e recarregue a página (F5)
                    3. Se persistir, **reinicie o navegador**
                    """)
                    st.info("💡 Este erro ocorre quando múltiplas instâncias tentam acessar o mesmo banco Qdrant")
                else:
                    st.error(f"❌ Erro na inicialização: {error_msg}")

                # Clear progress elements
                progress_bar.empty()
                status_text.empty()
                st.stop()
        else:
            st.session_state['service_initialized'] = get_service()

    return st.session_state['service_initialized']

st.title("🛡️ Sistema RAG-PF — Interface Web")
st.caption("Consulta inteligente a espécies normativas da Polícia Federal (RAG)")

# Helper to format breadcrumb from metadata
def format_breadcrumb(md: dict) -> str:
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
        # Normalizações leves
        r = (rotulo or "").strip()
        # Remover símbolos duplicados
        r = r.replace("§", "").strip()

        # Parágrafo único
        if nivel == "paragrafo":
            low = r.lower().replace("ú", "u").strip()
            if "unico" in low or low == "unico":
                return "Parágrafo único"
            return f"Parágrafo {r}" if r else "Parágrafo"

        # Alínea sem fechamento automático
        if nivel == "alinea":
            return f"Alínea {r}" if r else "Alínea"

        # Artigo - verificar se já contém "Art."
        if nivel == "artigo":
            nome = mapa.get(nivel, nivel.capitalize())
            # Se o rótulo já contém "Art.", não duplicar
            if r and r.startswith("Art."):
                return r
            return f"{nome} {r}" if r else nome

        nome = mapa.get(nivel, nivel.capitalize())
        return f"{nome} {r}" if r else nome

    if not isinstance(md, dict):
        return md or "Trecho"

    # Preferir breadcrumb pronto se parecer legível
    bc = md.get("breadcrumb")
    if isinstance(bc, str) and any(tok in bc for tok in ["Capítulo", "Seção", "Subseção", "Art.", "Parágrafo", "Inciso", "Alínea", "Item", "Anexo"]):
        return bc

    # Construir caminho hierárquico
    caminho = md.get("caminho_hierarquico") or []
    if isinstance(caminho, list):
        # Criar uma cópia do caminho
        path = list(caminho)

        # Adicionar elemento atual apenas se não estiver já presente
        elemento_atual = {"nivel": md.get("nivel"), "rotulo": md.get("rotulo")}
        nivel_atual = elemento_atual.get("nivel")
        rotulo_atual = elemento_atual.get("rotulo")

        # Verificar se o último elemento do caminho é igual ao atual
        if path and isinstance(path[-1], dict):
            ultimo = path[-1]
            if (ultimo.get("nivel") != nivel_atual or
                ultimo.get("rotulo") != rotulo_atual):
                path.append(elemento_atual)
        else:
            # Se não há caminho ou último elemento não é dict, adicionar
            if nivel_atual or rotulo_atual:
                path.append(elemento_atual)

        # Gerar labels sem duplicações
        labels = []
        for n in path:
            if isinstance(n, dict):
                label = fmt_label(n.get("nivel", ""), n.get("rotulo", ""))
                if label and label not in labels:  # Evitar duplicações exatas
                    labels.append(label)

        if labels:
            return " > ".join(labels)

    # Fallbacks
    return md.get("rotulo") or "Trecho"

# Connectivity status
connected, err = OllamaService.check_connection()
status_col1, status_col2 = st.columns([1, 3])
with status_col1:
    st.markdown("**Ollama:** " + ("✅ online (local)" if connected else "❌ offline"))
with status_col2:
    if not connected:
        with st.expander("Como habilitar o Ollama local"):
            st.markdown("""
            1. Baixe: https://ollama.ai/
            2. Baixe os modelos: `ollama pull nomic-embed-text` e `ollama pull llama3.2`
            3. Inicie o serviço: `ollama serve`
            """)

# Sidebar options
with st.sidebar:
    st.header("Configurações")
    show_retrieval = st.toggle("Mostrar trechos relevantes", value=True)
    top_k = st.slider("Top-K", min_value=3, max_value=10, value=5, step=1)
    export_jsonl = st.toggle("Exportar JSONL dos chunks", value=True)

    st.header("Arquivos")
    # Lista PDFs atuais
    try:
        existing = FileUtils.get_pdf_files()
    except Exception:
        existing = []
    if existing:
        with st.expander(f"PDFs atuais ({len(existing)})"):
            for p in existing:
                st.caption(os.path.basename(p))
    else:
        st.caption("Nenhum PDF encontrado em '" + Settings.PDF_FOLDER + "'.")

    # Upload de PDFs
    uploads = st.file_uploader("Enviar PDFs", type=["pdf"], accept_multiple_files=True)
    if uploads:
        os.makedirs(Settings.PDF_FOLDER, exist_ok=True)
        saved = 0
        for uf in uploads:
            name = os.path.basename(uf.name)
            dest = os.path.join(Settings.PDF_FOLDER, name)
            try:
                with open(dest, "wb") as f:
                    f.write(uf.getbuffer())
                saved += 1
            except Exception as e:
                st.warning(f"Falha ao salvar {name}: {e}")
        if saved:
            st.success(f"{saved} arquivo(s) salvo(s) em {Settings.PDF_FOLDER}/")

    # Botão de reindexação
    reindex = st.button("Reindexar base (ingestão)")

# Initialize service
try:
    service = get_service_with_progress()
except SystemExit:
    st.error("Falha na inicialização do serviço. Verifique os logs.")
    st.stop()

# Reindex handling
if 'did_reindex' not in st.session_state:
    st.session_state['did_reindex'] = False

if reindex:
    try:
        # Barra de progresso
        pbar = st.progress(0.0, text="Preparando ingestão...")
        status = st.empty()

        # Detectar alterações via manifest (incremental)
        added, modified, removed, new_map = diff_current_vs_manifest()
        if not added and not modified and not removed:
            pbar.progress(1.0, text="Nada a fazer")
            st.info("Nenhuma alteração detectada nos PDFs. Nada para reindexar.")
        else:
            # Caminhos: full rebuild se houver removidos ou modificados; incremental se apenas adicionados
            do_full = bool(removed or modified)
            use_qdrant = str(Settings.VECTOR_DB_BACKEND).lower().startswith("qdrant")
            indexer = Indexer()
            qindex = QdrantIndexer() if use_qdrant else None

            if do_full:
                status.markdown("Executando reindexação completa...")
                pdfs = FileUtils.get_pdf_files()
                all_chunks = []
                total_files = max(1, len(pdfs))
                for idx, pdf in enumerate(pdfs, start=1):
                    status.markdown(f"Processando `{os.path.basename(pdf)}` ({idx}/{len(pdfs)})...")
                    try:
                        raw, pages, ocr = safe_extract_text(pdf)
                        text, pages2 = clean_text(raw, pages)
                        nodes, heading = detect_structure(text)
                        meta = meta_extract(text, heading, os.path.basename(pdf))
                        chunks = build_chunks(nodes, text, meta, pdf, [p.index for p in pages2])
                        all_chunks.extend(chunks)
                    except Exception as e:
                        st.warning(f"Erro ao processar {os.path.basename(pdf)}: {e}")
                        continue
                    pbar.progress(min(0.2, idx/total_files*0.2), text=f"Chunks acumulados: {len(all_chunks)}")

                def cb(frac: float, msg: str):
                    val = 0.2 + frac * 0.8
                    pbar.progress(min(1.0, val), text=f"Indexando: {msg}")

                if use_qdrant and qindex is not None:
                    try:
                        qindex.clear_collection()
                    except Exception:
                        pass
                    # Also try to remove the storage folder if locked
                    import shutil
                    try:
                        if os.path.exists(Settings.QDRANT_PATH):
                            shutil.rmtree(Settings.QDRANT_PATH, ignore_errors=True)
                    except Exception:
                        pass
                    db = qindex.build_qdrant(all_chunks)
                else:
                    db = indexer.build_faiss(all_chunks, progress_cb=cb)
                    indexer.save_faiss(db, Settings.FAISS_DB_PATH)

                # Export JSONL (full overwrite)
                if export_jsonl and Settings.EXPORT_CHUNKS_JSONL:
                    try:
                        msg = export_chunks_jsonl(all_chunks, Settings.CHUNKS_JSONL_PATH)
                        st.info(msg)
                    except Exception as e:
                        st.warning(f"Falha ao exportar JSONL: {e}")

            else:
                # Incremental: se houver modificados/remoções e backend for Qdrant, podemos aplicar deletes antes de adicionar
                if use_qdrant and qindex is not None and (removed or modified):
                    status.markdown("Aplicando deleções por arquivo no Qdrant...")
                    db_existing = qindex.load_qdrant()
                    if db_existing is not None:
                        for fp in (removed + modified):
                            try:
                                qindex.delete_by_file(db_existing, fp)
                            except Exception:
                                pass

                # Incremental: apenas adicionados
                status.markdown("Executando ingestão incremental (apenas novos arquivos)...")
                added = added or []
                if not added:
                    pbar.progress(1.0, text="Nada a adicionar")
                    st.info("Nenhum arquivo novo para adicionar.")
                    raise SystemExit(0)

                # Construir chunks apenas dos novos PDFs
                all_new_chunks = []
                total_files = max(1, len(added))
                for idx, pdf in enumerate(added, start=1):
                    status.markdown(f"Processando `{os.path.basename(pdf)}` ({idx}/{len(added)})...")
                    try:
                        raw, pages, ocr = safe_extract_text(pdf)
                        text, pages2 = clean_text(raw, pages)
                        nodes, heading = detect_structure(text)
                        meta = meta_extract(text, heading, os.path.basename(pdf))
                        chunks = build_chunks(nodes, text, meta, pdf, [p.index for p in pages2])
                        all_new_chunks.extend(chunks)
                    except Exception as e:
                        st.warning(f"Erro ao processar {os.path.basename(pdf)}: {e}")
                        continue
                    pbar.progress(min(0.2, idx/total_files*0.2), text=f"Novos chunks: {len(all_new_chunks)}")

                # Carregar base existente (se houver) e apenas adicionar textos/metadados
                if use_qdrant and qindex is not None:
                    db = qindex.load_qdrant()
                else:
                    db = Indexer.load_faiss(Settings.FAISS_DB_PATH)
                if db is None:
                    # Primeira indexação: crie do zero
                    def cb(frac: float, msg: str):
                        val = 0.2 + frac * 0.8
                        pbar.progress(min(1.0, val), text=f"Indexando: {msg}")

                    if use_qdrant and qindex is not None:
                        db = qindex.build_qdrant(all_new_chunks)
                    else:
                        db = indexer.build_faiss(all_new_chunks, progress_cb=cb)
                        indexer.save_faiss(db, Settings.FAISS_DB_PATH)

                    # Export JSONL (overwrite, primeira vez)
                    if export_jsonl and Settings.EXPORT_CHUNKS_JSONL:
                        try:
                            msg = export_chunks_jsonl(all_new_chunks, Settings.CHUNKS_JSONL_PATH)
                            st.info(msg)
                        except Exception as e:
                            st.warning(f"Falha ao exportar JSONL: {e}")
                else:
                    # Incremental: adicionar ao índice existente
                    if use_qdrant and qindex is not None:
                        pbar.progress(0.4, text="Adicionando novos vetores ao Qdrant...")
                        qindex.add_chunks(db, all_new_chunks)
                        pbar.progress(1.0, text="Concluído")
                    else:
                        texts, metas = indexer.to_texts_and_metadatas(all_new_chunks)
                        pbar.progress(0.4, text="Gerando embeddings dos novos chunks...")
                        try:
                            db.add_texts(texts, metadatas=metas)
                            pbar.progress(0.9, text="Salvando índice atualizado em disco...")
                            indexer.save_faiss(db, Settings.FAISS_DB_PATH)
                        finally:
                            pbar.progress(1.0, text="Concluído")

                    # Export JSONL (append)
                    if export_jsonl and Settings.EXPORT_CHUNKS_JSONL:
                        try:
                            os.makedirs(os.path.dirname(Settings.CHUNKS_JSONL_PATH), exist_ok=True)
                            mode = "a" if os.path.exists(Settings.CHUNKS_JSONL_PATH) else "w"
                            with open(Settings.CHUNKS_JSONL_PATH, mode, encoding="utf-8") as f:
                                for ch in all_new_chunks:
                                    f.write(json.dumps(ch.__dict__, ensure_ascii=False) + "\n")
                            st.info(f"{len(all_new_chunks)} novos chunks anexados em {Settings.CHUNKS_JSONL_PATH}")
                        except Exception as e:
                            st.warning(f"Falha ao exportar JSONL (append): {e}")

            # Atualizar serviço em memória e reconstruir chain
            service.document_service.database = db
            try:
                service.rebuild_chain()
            except Exception:
                pass

            # Atualizar manifest e limpar cache de Q/A
            try:
                save_manifest(new_map)
            except Exception:
                pass
            try:
                service.cache.clear_all()
            except Exception:
                pass

            st.session_state['did_reindex'] = True
            pbar.progress(1.0, text="Concluído")
            st.success("Índice atualizado com sucesso!")
    except SystemExit:
        # Early exit path (e.g., no added files)
        pass
    except Exception as e:
        st.error(f"Erro durante reindexação: {e}")

# Query input
query = st.text_input("Digite sua pergunta", placeholder="Ex.: O que diz o art. 8º sobre benefícios?")
btn = st.button("Consultar", type="primary")

# Handle query
if btn and query.strip():
    with st.spinner("Consultando..."):
        answer = service.answer_question(query.strip())
    if answer:
        st.subheader("Resposta")
        st.write(answer)

        # Retrieval preview
        if show_retrieval and service.document_service and service.document_service.database:
            try:
                searcher = Searcher(service.document_service.database)
                docs = searcher.query(query.strip(), top_k=top_k)
                with st.expander("Ver trechos relevantes"):
                    for i, d in enumerate(docs, start=1):
                        md = d.metadata or {}
                        title = format_breadcrumb(md)
                        st.markdown(f"**{i}. {title}**")
                        # Páginas (quando disponíveis) e sinalização de tabelas
                        paginas = None
                        try:
                            origem = md.get('origem_pdf') or {}
                            paginas = origem.get('paginas')
                        except Exception:
                            paginas = None
                        tables_flag = ""
                        if 'layout_refs' in md or 'layout_refs' in d.metadata:
                            lrs = md.get('layout_refs') or []
                            if any(getattr(x, 'get', lambda k, d=None: None)('type') == 'table' for x in lrs):
                                tables_flag = " • contém tabela"
                        st.caption(f"Nível: {md.get('nivel')} • Âncora: {md.get('anchor_id')}" + (f" • Páginas: {paginas}" if paginas else "") + tables_flag)
                        st.write(d.page_content)
                        st.divider()
            except Exception as e:
                st.warning(f"Não foi possível exibir trechos relevantes: {e}")
    else:
        st.warning("Não foi possível obter resposta.")

st.markdown("---")
st.caption("Executa 100% local. Modelos via Ollama local e indexação FAISS/Qdrant em disco.")
