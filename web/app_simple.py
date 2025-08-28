import os
import sys
import json
import warnings
import logging
import sqlite3
import pickle
import base64
from pathlib import Path

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

def init_session_state():
    """Inicialização básica do estado da sessão."""
    if 'last_query' not in st.session_state:
        st.session_state.last_query = ""

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
    """Initialize service with simple progress bar"""
    if 'service_initialized' not in st.session_state:
        # Check if database needs to be built
        mudancas_detectadas, _ = FileUtils.check_folder_changes()
        needs_build = mudancas_detectadas or not os.path.exists(Settings.FAISS_DB_PATH)

        if needs_build:
            st.info("🔄 Base de dados precisa ser criada/atualizada. Processando...")

            # Simple progress bar
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            def progress_callback(fraction: float, message: str):
                progress_bar.progress(fraction)
                status_text.text(message)

            # Build database
            try:
                ingest_index(progress_callback=progress_callback)
                progress_bar.progress(1.0)
                status_text.text("✅ Base de dados criada com sucesso!")
                st.success("✅ Sistema pronto para uso!")
                st.session_state['service_initialized'] = True

                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()

            except Exception as e:
                st.error(f"❌ Erro ao criar base de dados: {str(e)}")
                return None
        else:
            st.session_state['service_initialized'] = True

    return get_service()

@st.cache_resource(show_spinner=False)
def get_ollama_service() -> OllamaService:
    return OllamaService()

@st.cache_resource(show_spinner=False)
def get_searcher() -> Searcher:
    return Searcher()

# UI Functions
def render_sidebar():
    """Renderiza a barra lateral com configurações."""
    with st.sidebar:
        st.title("🛡️ Sistema RAG-PF")
        st.markdown("---")

        # Configurações básicas
        st.subheader("⚙️ Configurações")

        # Status do sistema
        st.subheader("📊 Status do Sistema")
        service = get_service()
        if service:
            searcher = get_searcher()
            if hasattr(searcher, 'index') and searcher.index is not None:
                try:
                    total_docs = searcher.index.ntotal
                    st.success(f"✅ Sistema ativo\n📄 {total_docs} documentos indexados")
                except:
                    st.info("📊 Sistema carregado")
            else:
                st.info("📊 Sistema em inicialização")
        else:
            st.warning("⚠️ Sistema não inicializado")

        # Controles de limpeza
        st.markdown("---")
        st.subheader("🧹 Manutenção")

        if st.button("🗑️ Limpar Cache"):
            st.cache_resource.clear()
            st.rerun()

def render_query_interface():
    """Renderiza a interface principal de consulta."""
    st.title("🤖 Consulta RAG")
    st.markdown("Digite sua pergunta sobre os documentos normativos da PF:")

    # Input da pergunta
    query = st.text_area(
        "💬 Sua pergunta:",
        value=st.session_state.last_query,
        height=100,
        placeholder="Ex: Quais são os prazos para progressão funcional?"
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        if st.button("🔍 Consultar", type="primary", disabled=not query.strip()):
            if query.strip():
                st.session_state.last_query = query
                process_query(query)

    with col2:
        if st.button("🧹 Limpar"):
            st.session_state.last_query = ""
            st.rerun()

def process_query(query: str):
    """Processa uma consulta do usuário."""
    service = get_service_with_progress()

    if not service:
        st.error("❌ Erro ao inicializar o sistema")
        return

    try:
        with st.spinner("🔍 Buscando resposta..."):
            # Realizar consulta
            response = service.query(query)

            # Exibir resposta
            st.markdown("### 💡 Resposta")
            st.markdown(response['answer'])

            # Exibir fontes
            if response.get('sources'):
                st.markdown("### 📚 Fontes Consultadas")
                for i, source in enumerate(response['sources'], 1):
                    with st.expander(f"📄 Fonte {i} - Score: {source.get('score', 'N/A'):.3f}"):
                        st.markdown(f"**Texto:** {source['text'][:500]}...")
                        if source.get('metadata'):
                            st.json(source['metadata'])

    except Exception as e:
        st.error(f"❌ Erro ao processar consulta: {str(e)}")

def render_chunk_inspector():
    """Renderiza o inspetor de chunks."""
    st.title("🧩 Inspetor de Chunks")
    st.markdown("Explore os chunks indexados no sistema:")

    try:
        # Carregar chunks do JSONL
        jsonl_path = os.path.join(Settings.FAISS_DB_PATH, "chunks.jsonl")

        if not os.path.exists(jsonl_path):
            st.warning("⚠️ Arquivo de chunks não encontrado. Execute o processamento primeiro.")
            return

        chunks = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    chunks.append(json.loads(line))

        if not chunks:
            st.info("📄 Nenhum chunk encontrado.")
            return

        st.success(f"✅ {len(chunks)} chunks carregados")

        # Filtros
        col1, col2 = st.columns(2)

        with col1:
            search_text = st.text_input("🔍 Buscar texto:", placeholder="Digite para filtrar chunks...")

        with col2:
            # Filtro por documento
            documentos = sorted(set(chunk.get('metadata', {}).get('origem_pdf', {}).get('arquivo', 'Desconhecido')
                                  for chunk in chunks))
            doc_filter = st.selectbox("📁 Filtrar por documento:", ["Todos"] + documentos)

        # Aplicar filtros
        filtered_chunks = chunks

        if search_text:
            filtered_chunks = [chunk for chunk in filtered_chunks
                             if search_text.lower() in chunk.get('text', '').lower()]

        if doc_filter != "Todos":
            filtered_chunks = [chunk for chunk in filtered_chunks
                             if chunk.get('metadata', {}).get('origem_pdf', {}).get('arquivo', '') == doc_filter]

        st.info(f"📊 Mostrando {len(filtered_chunks)} de {len(chunks)} chunks")

        # Paginação
        items_per_page = 10
        total_pages = max(1, (len(filtered_chunks) + items_per_page - 1) // items_per_page)

        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1

        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.button("⬅️ Anterior") and st.session_state.current_page > 1:
                st.session_state.current_page -= 1
                st.rerun()

        with col2:
            st.markdown(f"**Página {st.session_state.current_page} de {total_pages}**")

        with col3:
            if st.button("➡️ Próxima") and st.session_state.current_page < total_pages:
                st.session_state.current_page += 1
                st.rerun()

        # Mostrar chunks da página atual
        start_idx = (st.session_state.current_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(filtered_chunks))

        for i in range(start_idx, end_idx):
            render_chunk_card(filtered_chunks[i], i + 1)

    except Exception as e:
        st.error(f"❌ Erro ao carregar chunks: {str(e)}")

def render_chunk_card(chunk: dict, index: int):
    """Renderiza um card para um chunk individual."""
    with st.expander(f"🧩 Chunk {index}", expanded=False):

        metadata = chunk.get('metadata', {})

        # Header com informações básicas
        col1, col2, col3 = st.columns(3)

        with col1:
            nivel = metadata.get('nivel', 'documento')
            rotulo = metadata.get('rotulo', '')
            title = f"{nivel.title()}"
            if rotulo:
                title += f" {rotulo}"
            st.markdown(f"### 🧩 {title}")

        with col2:
            st.metric("Tokens", metadata.get('tokens_estimados', 'N/A'))

        with col3:
            st.metric("Tamanho", f"{len(chunk['text'])} chars")

        # Metadados principais
        col1, col2 = st.columns(2)

        with col1:
            # Origem
            origem_pdf = metadata.get('origem_pdf', {})
            if isinstance(origem_pdf, dict):
                arquivo = origem_pdf.get('arquivo', 'N/A')
                if arquivo != 'N/A':
                    arquivo = arquivo.split('\\')[-1]
                st.markdown(f"**📁 Documento:** {arquivo}")

                paginas = origem_pdf.get('paginas', [])
                if paginas:
                    st.markdown(f"**📄 Páginas:** {len(paginas)} páginas")

            # Hierarquia
            caminho = metadata.get('caminho_hierarquico', [])
            if caminho:
                st.markdown(f"**🗂️ Hierarquia:** {' > '.join(caminho)}")

        with col2:
            # Posição
            posicao = metadata.get('posicao_documento')
            if posicao:
                st.markdown(f"**📍 Posição:** {posicao}")

            # IDs
            chunk_id = metadata.get('chunk_id')
            if chunk_id:
                st.markdown(f"**🆔 ID:** {chunk_id}")

        # Conteúdo do texto
        st.markdown("---")
        st.markdown("**📝 Conteúdo:**")
        st.markdown(chunk['text'])

        # Metadados completos (colapsado)
        with st.expander("🔍 Metadados Completos"):
            st.json(metadata)

def render_main_interface():
    """Renderiza a interface principal com abas."""
    # Sidebar
    render_sidebar()

    # Abas principais
    tab1, tab2 = st.tabs(["🤖 Consulta RAG", "🧩 Inspetor de Chunks"])

    with tab1:
        render_query_interface()

    with tab2:
        render_chunk_inspector()

def main():
    """Função principal da aplicação."""
    # Inicialização
    init_session_state()

    # Interface principal
    render_main_interface()

if __name__ == "__main__":
    main()
