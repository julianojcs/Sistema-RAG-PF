# 🔧 Visão Geral Técnica - Sistema RAG PF

## 🛡️ Pipeline PF-Específico

### 📄 1. Extração de PDF (`src/pf_rag/io_pdf.py`)

**Docling (Preferencial)**:
- Layout-aware extraction com detecção de estruturas
- Text blocks, tables, images identificados
- Bounding boxes normalizados (0-1 coordinates)
- Metadata por página: width, height, index
- Cache persistente de layout_extras por arquivo

**Fallback (pdfminer + OCR)**:
- pdfminer.six para texto direto
- pdf2image + pytesseract para OCR se necessário
- Mesmo formato de saída que Docling

### 🧹 2. Normalização (`src/pf_rag/normalize.py`)

**Limpeza Inteligente**:
- Header/footer removal conservativo
- Preserva: "Capítulo", "Seção", "Título" (estruturas reais)
- Remove: footers repetitivos, numeração de página
- Hifenização: reconstitui palavras quebradas
- Espaçamento: normaliza múltiplos espaços/quebras

### 📊 3. Parsing Hierárquico (`src/pf_rag/parse_norma.py`)

**Regex Estrutural**:
```python
ESTRUTURAS = {
    "artigo": r"^Art\.?\s*(\d+(?:[º°]?-?[A-Z]?)?)",
    "paragrafo": r"^§\s*(\d+(?:[º°])?|\w+)",
    "inciso": r"^([IVX]+)\s*[-–]\s*",
    "alinea": r"^([a-z])\)\s*",
    "capitulo": r"^CAPÍTULO\s+([IVX]+|[0-9]+)",
    "secao": r"^SEÇÃO\s+([IVX]+|[0-9]+)",
    # ... mais estruturas
}
```

**Hierarquia Detectada**:
- **Título/Livro/Parte** → **Capítulo** → **Seção** → **Artigo** → **Parágrafo** → **Inciso** → **Alínea** → **Item**

### ✂️ 4. Chunking Layout-Aware (`src/pf_rag/chunker.py`)

**Estratégia Inteligente**:
- Evita cortar tabelas: consulta layout_refs antes de chunking
- Se bloco contém tabela, preserva integridade
- Chunk size adaptativo baseado na estrutura

**Metadados Ricos**:
- breadcrumb: "Capítulo I > Art. 5º > § 1º"
- nivel: "paragrafo", rotulo: "1º"
- caminho_hierarquico: [{nivel, rotulo}, ...]
- origem_pdf: {arquivo, paginas: [1,2,3]}
- layout_refs: [{type: "table", bbox: [x1,y1,x2,y2]}, ...]

### 🧠 5. Embeddings e Indexação (`src/pf_rag/embed_index.py`)

**Backends Suportados**:
- **Ollama (padrão)**: nomic-embed-text:latest, 768D, 100% offline
- **SBERT (alternativo)**: all-MiniLM-L6-v2, 384D, multilingual

**Vector Stores**:
- **Qdrant (padrão)**: Embedded client, operações granulares, metadata filtering
- **FAISS (fallback)**: CPU-optimized, read-only, rebuild completo

### 🔍 6. Busca Híbrida (`src/pf_rag/search.py`)

**Dense + Sparse**:
- **Dense (Semantic)**: Vector similarity search, contexto semântico
- **BM25 (Keywords)**: Keyword-based ranking, termos técnicos específicos
- **Hierarchy-aware reranking**: Boost para chunks do mesmo artigo/capítulo

## 🗃️ Backends de Banco Vetorial

### 🚀 Qdrant Embedded (Padrão)

**Vantagens**:
- ✅ **Granularidade**: Delete/upsert por arquivo específico
- ✅ **Metadata**: Filtering avançado por campos
- ✅ **Performance**: Otimizado para high-dimensional vectors
- ✅ **Embedded**: Sem servidor externo necessário
- ✅ **Incremental**: Updates eficientes

**Configuração**:
```python
VECTOR_DB_BACKEND = "qdrant"
QDRANT_PATH = "./qdrantDB"
QDRANT_COLLECTION = "pf_normativos"
```

### 📦 FAISS (Fallback)

**Vantagens**:
- ✅ **Performance**: Extremamente rápido para read-only
- ✅ **Simplicidade**: Menos overhead
- ✅ **Estabilidade**: Mature library

**Limitações**:
- ❌ **Updates**: Rebuild completo necessário
- ❌ **Deletes**: Não suportado nativamente
- ❌ **Metadata**: Filtering limitado

## 🌐 Interface Web Streamlit

### 📱 Componentes Principais

**Status Dashboard**:
- Ollama connectivity status (Online/Offline indicator)
- Model availability check
- Auto-reconnection feedback

**Upload & Management**:
- PDF upload via file_uploader
- Multiple files support
- Progress feedback
- SGP/ folder management

**Reindexação Inteligente**:
- Manifest-based diff (Hash MD5 per-file tracking)
- Added/Modified/Removed detection
- Incremental vs Full rebuild strategy
- Progress bar com status detalhado

**Query & Preview**:
- Interactive question answering
- Retrieval preview opcional
- Breadcrumb navigation
- Page numbers e table indicators

### 🔄 Rebuild Strategies

**Incremental (Qdrant Only)**:
1. Detecta via manifest diff
2. Processa apenas novos PDFs
3. add_chunks() no índice existente
4. Append JSONL export
5. Rebuild chain + clear cache

**Full Rebuild**:
1. Clear collection/delete storage
2. Processa todos os PDFs
3. Build novo índice from scratch
4. Overwrite JSONL export
5. Rebuild chain + clear cache

## 📤 Export e Auditoria

### 📋 JSONL Export (`src/pf_rag/export_jsonl.py`)

**Conteúdo Completo**:
```json
{
  "texto": "Content do chunk",
  "nivel": "artigo",
  "rotulo": "5º",
  "breadcrumb": "Capítulo I > Art. 5º",
  "anchor_id": "art-5",
  "caminho_hierarquico": [...],
  "origem_pdf": {
    "arquivo": "regulamento.pdf",
    "paginas": [12, 13]
  },
  "layout_refs": [
    {"type": "text", "bbox": [0.1, 0.2, 0.9, 0.8]}
  ]
}
```

**Modes de Export**:
- **Overwrite**: Full rebuild, substitui arquivo
- **Append**: Incremental, adiciona ao final

## ⚙️ Configurações Principais

### 🔧 Settings Core (`src/config/settings.py`)

```python
# Backend Selection
VECTOR_DB_BACKEND = "qdrant"  # "faiss" | "qdrant"
EMBEDDING_BACKEND = "ollama"  # "ollama" | "sbert"

# Offline Mode (Security)
OFFLINE_MODE = True
TRANSFORMERS_OFFLINE = True
HF_HUB_OFFLINE = True

# Docling Integration
DOCLING_ENABLED = True  # Prefer Docling, fallback if needed

# Export & Audit
EXPORT_CHUNKS_JSONL = True
CHUNKS_JSONL_PATH = "./faissDB/chunks_export.jsonl"

# Performance Tuning
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
RETRIEVAL_K = 6
```

## 🛡️ Compliance & Security

**Offline-First**:
- Todos os modelos executam localmente
- Nenhum dado sai do ambiente
- Flags de ambiente forçam modo offline

**Auditoria**:
- Export JSONL completo dos chunks
- Rastreamento de origem (arquivo + páginas)
- Layout metadata para possível highlight futuro

**Incremental Safety**:
- Manifest tracking previne data loss
- Cache clearing automático mantém consistência
- Fallback para full rebuild em caso de erro

## 🚀 Próximos Passos

### 🎯 Roadmap Técnico

1. **Visual Highlights**: Overlay de bbox na UI para mostrar exatamente onde está o conteúdo
2. **API REST**: FastAPI wrapper para integração externa  
3. **Advanced Evaluation**: Métricas automáticas de qualidade (RAGAS, etc.)
4. **Multi-document**: Support para Word, Excel além de PDF
5. **Performance Analytics**: Dashboard de métricas detalhadas

- `src/config/settings.py`: configurações centrais (pastas, modelos, batch, OCR, backend de embeddings, modo offline, etc.).

- `src/core/rag_service.py`: orquestra o RAG (carrega base via `DocumentService`, cria RetrievalQA com LLM Ollama local, usa cache e consulta via `.invoke`).

- `src/services/document_service.py`: verifica mudanças na pasta `SGP/`, ingere PDFs pelo pipeline PF RAG, cria e salva o índice FAISS.

- `src/services/ollama_service.py`: checa conectividade com Ollama local e imprime instruções de configuração offline.

- `src/utils/file_utils.py`: lista PDFs em `SGP/`, gera e persiste hash da pasta para detectar mudanças.

- `src/utils/cache_utils.py`: cache de respostas (arquivo JSON), normalização de chave e LRU auxiliar.

- `src/pf_rag/io_pdf.py`: extração de texto e páginas; OCR opcional.

- `src/pf_rag/normalize.py`: limpeza/normalização de texto (rodapé, hifenização, espaços, junção de linhas).

- `src/pf_rag/regexes.py`: regex e padrões para detectar cabeçalhos e dispositivos (artigo, parágrafo, inciso, alínea, etc.).

- `src/pf_rag/parse_norma.py`: parsing hierárquico usando pilha para construir nós e heading inicial do documento.

- `src/pf_rag/metadata_pf.py`: extrai metadados específicos da PF/DPF e cria `doc_id` canônico.

- `src/pf_rag/chunker.py`: cria chunks com breadcrumbs, âncoras e limites de tokens; inclui relações hierárquicas.

- `src/pf_rag/embed_index.py`: provê `Indexer` com backends de embeddings (Ollama/SBERT), conversão texto+metadados, batching, salvar/carregar FAISS.

- `src/pf_rag/search.py`: busca densa + BM25 opcional e re-ranking simples sensível a hierarquia.

- `src/pf_rag/eval.py`: métrica simples (MRR@k).

- `src/pf_rag/cli.py`: comandos `ingest`, `query` e `calibrate` (usa backend configurado; offline por padrão).

- `src/pf_rag/calibrate.py`: analisa a coleção `SGP/`, agrega estatísticas e gera `docs/sgp_calibration.md` com recomendações.

- `docs/ARCHITECTURE.md`: arquitetura geral do projeto (referência).

- `docs/README.md`: visão geral de uso e documentação.

- `docs/prompt.md`: prompt/escopo detalhado do pipeline PF RAG.

- `docs/sgp_calibration.md`: relatório de calibração gerado pela ferramenta.

- `SPG/` (se existir) e `SGP/`: pastas de PDFs; usar `SGP/` como padrão.

- `faissDB/`: armazena o índice FAISS e o cache de respostas.
