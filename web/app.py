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

@st.cache_resource(show_spinner=False)
def get_searcher():
    """Get searcher instance with database"""
    service = get_service()
    if service and hasattr(service, 'document_service') and service.document_service.database:
        return Searcher(service.document_service.database)
    return None

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

# ============================================================================
# FUNÇÕES PARA VISUALIZAÇÃO DE PONTOS E CHUNKS
# ============================================================================

@st.cache_data
def get_qdrant_points(offset=0, limit=10):
    """Busca pontos do banco Qdrant com paginação"""
    db_path = Path("qdrantDB/collection/pf_normativos/storage.sqlite")

    if not db_path.exists():
        return [], 0

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Total de registros
        cursor.execute("SELECT COUNT(*) FROM points")
        total = cursor.fetchone()[0]

        # Buscar registros com paginação
        cursor.execute("SELECT id, point FROM points LIMIT ? OFFSET ?", (limit, offset))
        records = cursor.fetchall()

        points = []
        for encoded_id, point_blob in records:
            try:
                decoded_id = pickle.loads(base64.b64decode(encoded_id))
                point_data = pickle.loads(point_blob)

                # Extrair informações básicas
                info = {
                    'id': decoded_id,
                    'point_id': getattr(point_data, 'id', None),
                    'payload': getattr(point_data, 'payload', {}),
                    'vector_size': 0,
                    'text_preview': '',
                    'metadata': {},
                    'raw_data': point_data
                }

                # Processar payload
                if info['payload']:
                    if 'page_content' in info['payload']:
                        text = info['payload']['page_content']
                        info['text_preview'] = text[:200] + "..." if len(text) > 200 else text

                    if 'metadata' in info['payload']:
                        info['metadata'] = info['payload']['metadata']

                # Processar vetor
                if hasattr(point_data, 'vector') and point_data.vector:
                    if isinstance(point_data.vector, dict) and 'vector' in point_data.vector:
                        vector = point_data.vector['vector']
                    elif isinstance(point_data.vector, list):
                        vector = point_data.vector
                    else:
                        vector = point_data.vector

                    if isinstance(vector, list):
                        info['vector_size'] = len(vector)

                points.append(info)

            except Exception as e:
                st.error(f"Erro ao processar ponto: {e}")
                continue

        conn.close()
        return points, total

    except Exception as e:
        st.error(f"Erro ao acessar banco: {e}")
        return [], 0

def render_points_browser():
    """Renderiza o navegador de pontos do Qdrant"""
    st.title("🔍 Navegador de Pontos Qdrant")
    st.markdown("Explore os pontos indexados no banco vetorial com busca e filtros avançados")

    # Verificar se o banco existe
    db_path = Path("qdrantDB/collection/pf_normativos/storage.sqlite")
    if not db_path.exists():
        st.error("❌ Banco Qdrant não encontrado. Execute a indexação primeiro.")
        return

    # Filtros e busca
    with st.container():
        st.markdown("### 🔍 Filtros e Busca")

        col1, col2, col3 = st.columns(3)

        with col1:
            search_text = st.text_input(
                "🔎 Buscar no texto",
                placeholder="Digite palavras-chave...",
                help="Busca no conteúdo dos chunks"
            )

        with col2:
            nivel_filter = st.selectbox(
                "📊 Filtrar por nível",
                ["Todos", "artigo", "paragrafo", "inciso", "alinea", "capitulo", "secao", "titulo", "anexo"],
                help="Filtrar por nível hierárquico"
            )

        with col3:
            doc_filter = st.selectbox(
                "📁 Filtrar por documento",
                ["Todos"] + ["LEI 8112.pdf", "IN 289.pdf", "Emenda Constitucional nº 103.pdf", "Instrução-normativa-100-dg-dpf-22-março-2016.pdf"],
                help="Filtrar por documento origem"
            )

    # Configurações de paginação
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        page_size = st.selectbox("Itens por página", [5, 10, 20, 50], index=1)

    with col2:
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 0

        # Buscar total para calcular páginas
        _, total = get_qdrant_points(0, 1)
        total_pages = max(1, (total + page_size - 1) // page_size)

        page_input = st.number_input(
            f"Página (1-{total_pages})",
            min_value=1,
            max_value=total_pages,
            value=st.session_state.current_page + 1
        )
        st.session_state.current_page = page_input - 1

    with col3:
        st.info(f"📊 Total: {total:,} pontos • Página {page_input} de {total_pages}")

    # Buscar pontos
    offset = st.session_state.current_page * page_size
    points, _ = get_qdrant_points(offset, page_size)

    # Aplicar filtros no frontend (para simplificar)
    if search_text or nivel_filter != "Todos" or doc_filter != "Todos":
        filtered_points = []
        for point in points:
            # Filtro de texto
            if search_text:
                text_content = point.get('text_preview', '') + str(point.get('payload', {}).get('page_content', ''))
                if search_text.lower() not in text_content.lower():
                    continue

            # Filtro de nível
            if nivel_filter != "Todos":
                metadata = point.get('metadata', {})
                if metadata.get('nivel') != nivel_filter:
                    continue

            # Filtro de documento
            if doc_filter != "Todos":
                metadata = point.get('metadata', {})
                origem = metadata.get('origem_pdf', {})
                arquivo = origem.get('arquivo', '') if isinstance(origem, dict) else ''
                if doc_filter not in arquivo:
                    continue

            filtered_points.append(point)

        points = filtered_points
        st.info(f"🔍 Filtros aplicados: {len(points)} pontos encontrados")

    if not points:
        st.warning("Nenhum ponto encontrado com os filtros aplicados.")
        return

    # Navegação melhorada
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        if st.button("⏮️ Primeira", disabled=st.session_state.current_page <= 0):
            st.session_state.current_page = 0
            st.rerun()

    with col2:
        if st.button("⬅️ Anterior", disabled=st.session_state.current_page <= 0):
            st.session_state.current_page -= 1
            st.rerun()

    with col3:
        if st.button("➡️ Próxima", disabled=st.session_state.current_page >= total_pages - 1):
            st.session_state.current_page += 1
            st.rerun()

    with col4:
        if st.button("⏭️ Última", disabled=st.session_state.current_page >= total_pages - 1):
            st.session_state.current_page = total_pages - 1
            st.rerun()

    # Lista de pontos
    st.markdown("### 📋 Pontos Encontrados")

    for i, point in enumerate(points):
        with st.container():
            # Card do ponto com design moderno
            st.markdown(f"""
            <div style="
                border: 1px solid #e0e4e7;
                border-radius: 12px;
                padding: 20px;
                margin: 12px 0;
                background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                transition: all 0.3s ease;
                border-left: 4px solid #1f77b4;
            ">
            """, unsafe_allow_html=True)

            # Header do card
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                # Título baseado nos metadados
                metadata = point['metadata']
                if isinstance(metadata, dict):
                    nivel = metadata.get('nivel', 'documento')
                    rotulo = metadata.get('rotulo', '')

                    # Ícones por nível
                    nivel_icons = {
                        'artigo': '📜',
                        'paragrafo': '📝',
                        'inciso': '📋',
                        'alinea': '🔤',
                        'capitulo': '📚',
                        'secao': '📑',
                        'titulo': '📖',
                        'anexo': '📎'
                    }
                    icon = nivel_icons.get(nivel, '📄')

                    title = f"{nivel.title()}"
                    if rotulo:
                        title += f" • {rotulo}"
                else:
                    title = f"Ponto {offset + i + 1}"
                    icon = '🧩'

                st.markdown(f"**{icon} {title}**")

                # Preview do texto
                if point['text_preview']:
                    st.markdown(f"<div style='color: #666; font-style: italic; margin-top: 8px;'>{point['text_preview']}</div>", unsafe_allow_html=True)

            with col2:
                # Métricas com ícones
                vector_info = f"{point['vector_size']}D" if point['vector_size'] else "N/A"
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="font-size: 24px; color: #1f77b4;">🔢</div>
                    <div style="font-weight: bold; color: #333;">{vector_info}</div>
                    <div style="font-size: 12px; color: #666;">Embedding</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                # Botão estilizado para ver detalhes
                detail_clicked = st.button(
                    "👁️ Detalhes",
                    key=f"detail_{point['id']}",
                    help="Ver detalhes completos",
                    type="secondary"
                )
                if detail_clicked:
                    st.session_state.selected_point = point
                    st.session_state.show_detail = True
                    st.rerun()

            # Informações rápidas com badges
            if isinstance(metadata, dict):
                badges = []

                # Arquivo origem
                if 'origem_pdf' in metadata and isinstance(metadata['origem_pdf'], dict):
                    arquivo = metadata['origem_pdf'].get('arquivo', '')
                    if arquivo:
                        arquivo = os.path.basename(arquivo)
                        badges.append(f"📁 {arquivo}")

                # Tokens
                if 'tokens_estimados' in metadata:
                    badges.append(f"🔤 {metadata['tokens_estimados']} tokens")

                # Páginas
                if 'origem_pdf' in metadata and isinstance(metadata['origem_pdf'], dict):
                    paginas = metadata['origem_pdf'].get('paginas', [])
                    if paginas and len(paginas) > 0:
                        badges.append(f"📄 {len(paginas)} páginas")

                if badges:
                    badge_html = " • ".join([f"<span style='background: #e3f2fd; padding: 2px 8px; border-radius: 12px; font-size: 12px; color: #1565c0;'>{badge}</span>" for badge in badges])
                    st.markdown(f"<div style='margin-top: 12px;'>{badge_html}</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # Modal de detalhes
    if st.session_state.get('show_detail', False) and 'selected_point' in st.session_state:
        render_point_detail_modal()

def render_point_detail_modal():
    """Renderiza modal com detalhes completos do ponto"""
    point = st.session_state.selected_point

    # Header do modal
    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown("### 🔍 Detalhes do Ponto")

    with col2:
        if st.button("❌ Fechar", key="close_modal"):
            st.session_state.show_detail = False
            if 'selected_point' in st.session_state:
                del st.session_state.selected_point
            st.rerun()

    # Container estilizado para o modal
    with st.container():
        st.markdown("""
        <div style="
            border: 2px solid #1f77b4;
            border-radius: 10px;
            padding: 20px;
            background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            margin: 10px 0;
        ">
        """, unsafe_allow_html=True)

        # Abas de conteúdo
        tab1, tab2, tab3, tab4 = st.tabs(["📄 Texto", "🏷️ Metadados", "🔢 Vetor", "🧬 Raw Data"])

        with tab1:
            st.subheader("📄 Conteúdo do Texto")
            if point['payload'] and 'page_content' in point['payload']:
                text = point['payload']['page_content']
                st.markdown(f"**Tamanho:** {len(text)} caracteres")
                st.text_area("Texto completo:", value=text, height=400, key="text_content")
            else:
                st.info("Nenhum texto encontrado no payload.")

        with tab2:
            st.subheader("🏷️ Metadados Estruturados")
            metadata = point['metadata']

            if isinstance(metadata, dict) and metadata:
                # Informações principais
                col1, col2 = st.columns(2)

                with col1:
                    if 'nivel' in metadata:
                        st.metric("📊 Nível", metadata['nivel'])
                    if 'rotulo' in metadata:
                        st.metric("🏷️ Rótulo", metadata['rotulo'])
                    if 'tokens_estimados' in metadata:
                        st.metric("🔤 Tokens", metadata['tokens_estimados'])

                with col2:
                    if 'origem_pdf' in metadata and isinstance(metadata['origem_pdf'], dict):
                        origem = metadata['origem_pdf']
                        if 'arquivo' in origem:
                            arquivo = os.path.basename(origem['arquivo'])
                            st.metric("📁 Arquivo", arquivo)
                        if 'paginas' in origem and isinstance(origem['paginas'], list):
                            st.metric("📄 Páginas", len(origem['paginas']))

                # Hierarquia
                if 'caminho_hierarquico' in metadata:
                    st.subheader("🗂️ Caminho Hierárquico")
                    caminho = metadata['caminho_hierarquico']
                    if isinstance(caminho, list):
                        for i, item in enumerate(caminho):
                            if isinstance(item, dict):
                                nivel = item.get('nivel', 'N/A')
                                rotulo = item.get('rotulo', '')
                                st.markdown(f"**{i+1}.** {nivel}" + (f" - {rotulo}" if rotulo else ""))

                # Metadados completos
                with st.expander("🔍 Metadados Completos"):
                    st.json(metadata)
            else:
                st.info("Nenhum metadado estruturado encontrado.")

        with tab3:
            st.subheader("🔢 Embedding Vetorial")
            raw_data = point['raw_data']

            if hasattr(raw_data, 'vector') and raw_data.vector:
                if isinstance(raw_data.vector, dict) and 'vector' in raw_data.vector:
                    vector = raw_data.vector['vector']
                elif isinstance(raw_data.vector, list):
                    vector = raw_data.vector
                else:
                    vector = raw_data.vector

                if isinstance(vector, list):
                    st.metric("🔢 Dimensões", len(vector))

                    # Visualização do vetor
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("🎯 Primeiros 10 valores")
                        for i, val in enumerate(vector[:10]):
                            st.write(f"{i+1}: {val:.6f}")

                    with col2:
                        st.subheader("🎯 Últimos 10 valores")
                        start_idx = len(vector) - 10
                        for i, val in enumerate(vector[-10:]):
                            st.write(f"{start_idx + i + 1}: {val:.6f}")

                    # Gráfico simples dos primeiros valores (se matplotlib disponível)
                    try:
                        import matplotlib.pyplot as plt
                        fig, ax = plt.subplots(1, 1, figsize=(10, 4))
                        ax.plot(vector[:50], marker='o', markersize=2)
                        ax.set_title("Primeiros 50 valores do embedding")
                        ax.set_xlabel("Dimensão")
                        ax.set_ylabel("Valor")
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                    except ImportError:
                        st.info("Matplotlib não disponível para visualização do gráfico")
                else:
                    st.info(f"Vetor encontrado mas formato não reconhecido: {type(vector)}")
            else:
                st.info("Nenhum vetor encontrado neste ponto.")

        with tab4:
            st.subheader("🧬 Dados Brutos")
            st.markdown("**Tipo do objeto:** " + str(type(point['raw_data'])))
            st.markdown("**ID do ponto:** " + str(point['point_id']))

            # Payload completo
            if point['payload']:
                with st.expander("📦 Payload Completo"):
                    st.json(point['payload'])

            # Informações técnicas
            with st.expander("⚙️ Informações Técnicas"):
                st.json({
                    'id': str(point['id']),
                    'point_id': str(point['point_id']),
                    'vector_size': point['vector_size'],
                    'payload_keys': list(point['payload'].keys()) if point['payload'] else []
                })

        st.markdown("</div>", unsafe_allow_html=True)

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

# ============================================================================
# SISTEMA DE NAVEGAÇÃO
# ============================================================================

# Inicializar estado da sessão
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0
if 'show_detail' not in st.session_state:
    st.session_state.show_detail = False
if 'current_route' not in st.session_state:
    st.session_state.current_route = 'home'

# Navegação principal
st.sidebar.title("🧭 Navegação")
navigation = st.sidebar.radio(
    "Selecione a seção:",
    ["🏠 Consulta RAG", "🔍 Navegador de Pontos"],
    index=0 if st.session_state.current_route == 'home' else 1
)

# Atualizar rota baseado na navegação
if navigation == "🔍 Navegador de Pontos":
    if st.session_state.current_route != 'points':
        st.session_state.current_route = 'points'
        st.rerun()
else:
    if st.session_state.current_route != 'home':
        st.session_state.current_route = 'home'
        st.rerun()

# Renderizar página baseada na navegação
if st.session_state.current_route == 'points':
    render_points_browser()
    st.stop()  # Para não continuar com o resto da interface

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
    st.markdown("---")
    st.header("⚙️ Configurações")
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

# ============================================================================
# FUNÇÕES AUXILIARES PARA INTERFACE
# ============================================================================

def render_sidebar():
    """Renderiza a barra lateral com informações do sistema"""
    with st.sidebar:
        st.markdown("---")
        st.subheader("📊 Status do Sistema")

        # Verificar status do serviço
        try:
            service = get_service()
            if service:
                searcher = get_searcher()
                if searcher and hasattr(searcher, 'db') and searcher.db is not None:
                    # Para Qdrant, tentar obter contagem
                    try:
                        if hasattr(searcher.db, '_client'):
                            # Qdrant
                            result = searcher.db._client.count(collection_name="pf_normativos")
                            total_docs = result.count
                        else:
                            # FAISS
                            total_docs = searcher.db.index.ntotal if hasattr(searcher.db, 'index') else 0
                        st.success(f"✅ Sistema ativo\n📄 {total_docs} documentos indexados")
                    except:
                        st.success("✅ Sistema ativo")
                else:
                    st.info("📊 Sistema em inicialização")
            else:
                st.warning("⚠️ Sistema não inicializado")
        except Exception as e:
            st.error(f"❌ Erro no sistema: {str(e)}")

        # Controles de limpeza
        st.markdown("---")
        st.subheader("🧹 Manutenção")

        if st.button("🗑️ Limpar Cache"):
            st.cache_resource.clear()
            st.rerun()

def render_main_interface():
    """Renderiza a interface principal"""
    render_sidebar()

def main():
    """Função principal da aplicação"""
    render_main_interface()

if __name__ == "__main__":
    main()
