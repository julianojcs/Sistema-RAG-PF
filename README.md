# 🤖 Sistema RAG - Polícia Federal

Sistema de Recuperação e Geração Aumentada (RAG) especializado para consulta de espécies normativas da Polícia Federal com pipeline hierárquico e interface web moderna.

## 🚀 Funcionalidades

### 🛡️ RAG PF-Específico
- ✅ **Pipeline Hierárquico**: Parsing estruturado de normas (Art., §, Incisos, Alíneas)
- ✅ **Docling Integration**: Extração layout-aware com detecção de tabelas e bbox
- ✅ **Metadados Ricos**: Breadcrumbs, níveis hierárquicos, rastreamento de páginas
- ✅ **Busca Híbrida**: Dense (embeddings) + BM25 (keywords) com reranking

### 🌐 Interface Web Moderna
- ✅ **Streamlit UI**: Interface responsiva para usuários não-técnicos
- ✅ **Upload PDFs**: Envio direto pela interface com drag-and-drop
- ✅ **Reindex Incremental**: Detecção automática via manifest (10x mais rápido)
- ✅ **Preview Retrieval**: Visualização de trechos com páginas e indicação de tabelas

### 🗃️ Dual Backend Vetorial
- ✅ **Qdrant Embedded**: Operações granulares (delete/upsert por arquivo)
- ✅ **FAISS Fallback**: Performance superior para read-only
- ✅ **Switching Transparente**: Configuração via Settings.VECTOR_DB_BACKEND

### 📤 Auditoria e Qualidade
- ✅ **Export JSONL**: Auditoria completa com layout_refs e metadados PF
- ✅ **Cache Inteligente**: Respostas persistidas com clear automático pós-rebuild
- ✅ **Offline-First**: 100% local, nenhum dado sai do ambiente

## 📋 Pré-requisitos

- Python 3.11 ou superior
- Ollama instalado e configurado
- Arquivos PDF na pasta `SGP/`

## 🛠️ Instalação Rápida

### Windows
```cmd
install.bat
```

### Linux/Mac
```bash
chmod +x install.sh
./install.sh
```

### Instalação Manual
```bash
# Instalar dependências
pip install -r requirements.txt

# Instalar e configurar Ollama
# Visite: https://ollama.ai/
ollama pull nomic-embed-text
ollama pull llama3.2
```

## 🎯 Como Usar o Sistema

### 📋 **Pré-requisitos**
1. **Adicione documentos PDF** na pasta `SGP/`
2. **Inicie o Ollama**: `ollama serve`
3. **Instale dependências**: `pip install -r requirements.txt`

### 🖥️ **Versão CLI (Linha de Comando)**

#### Execução Básica
```bash
# Execução padrão com interface CLI
python main.py
```

#### Comandos Avançados
```bash
# Executar com backend Qdrant (recomendado)
PF_RAG_VECTOR_DB=qdrant python main.py

# Executar com FAISS (compatibilidade)
PF_RAG_VECTOR_DB=faiss python main.py

# Modo verbose para debug
PF_RAG_VERBOSE=true python main.py

# Forçar reconstrução da base
rm -rf faissDB/ qdrantDB/ && python main.py
```

#### Processamento Manual via CLI
```bash
# Indexação manual dos documentos
python -c "from src.pf_rag.cli import ingest_index; ingest_index()"

# Análise de calibração dos chunks
python -c "from src.pf_rag.calibrate import analyze_folder, write_markdown_report; analyze_folder('SGP'); write_markdown_report()"

# Export de chunks para auditoria
python -c "from src.pf_rag.export_jsonl import export_chunks_jsonl; export_chunks_jsonl()"
```

### 🌐 **Versão Web (Interface Streamlit)**

#### Execução da Interface Web
```bash
# Iniciar servidor web (padrão na porta 8501)
python -m streamlit run web/app.py

# Especificar porta personalizada
python -m streamlit run web/app.py --server.port 8080

# Acessar de outras máquinas na rede
python -m streamlit run web/app.py --server.address 0.0.0.0

# Alternativa se streamlit estiver no PATH
streamlit run web/app.py
```

**🔧 Problema no Windows?** Se `streamlit` não for encontrado, use sempre `python -m streamlit`

#### Funcionalidades da Interface Web
- ✅ **Upload de PDFs**: Drag-and-drop para adicionar documentos
- ✅ **Reindexação**: Interface visual com barra de progresso
- ✅ **Preview de Retrieval**: Visualização dos chunks encontrados
- ✅ **Breadcrumbs Hierárquicos**: Navegação por estrutura normativa
- ✅ **Cache Visual**: Indicadores de cache hits/misses
- ✅ **Configurações**: Ajuste de parâmetros via interface

### ⚙️ **Configurações Avançadas via Variáveis de Ambiente**

```bash
# Backend do banco vetorial (qdrant recomendado)
export PF_RAG_VECTOR_DB=qdrant        # ou faiss

# Habilitar extração com Docling (layout-aware)
export PF_RAG_USE_DOCLING=true

# Configurar OCR para PDFs escaneados
export PF_RAG_OCR_ENABLED=true
export PF_RAG_OCR_LANG=por

# Ajustar tamanho dos chunks
export PF_RAG_TOKEN_MIN=400
export PF_RAG_TOKEN_MAX=1200

# Modo offline (sem downloads de modelos)
export PF_RAG_OFFLINE=true

# Habilitar busca híbrida BM25
export PF_RAG_BM25_ENABLED=true

# Export automático de chunks para auditoria
export PF_RAG_EXPORT_JSONL=true
```

### 🔧 **Comandos de Manutenção**

```bash
# Limpar cache e forçar reconstrução
rm -rf faissDB/ qdrantDB/
python main.py

# Verificar status da base de dados
python -c "from src.utils.file_utils import FileUtils; print('Mudanças detectadas:', FileUtils.check_folder_changes()[0])"

# Testar conectividade Ollama
python -c "from src.services.ollama_service import OllamaService; print('Ollama OK:', OllamaService.check_connection()[0])"

# Exportar chunks para análise
python -c "from src.pf_rag.export_jsonl import export_chunks_jsonl; export_chunks_jsonl('faissDB/chunks_export.jsonl')"
```

### 🌍 **Acesso à Interface Web**

Após executar `python -m streamlit run web/app.py`, acesse:
- **Local**: http://localhost:8501
- **Rede**: http://[IP_DA_MAQUINA]:8501
- **Porta customizada**: http://localhost:[PORTA]

## 📊 Performance

| Tipo de Consulta | Tempo Médio | Cache Hit |
|------------------|-------------|-----------|
| Pergunta nova | 2-3 segundos | ❌ |
| Pergunta repetida | 0.01 segundos | ✅ |
| Startup | 1-2 segundos | - |

## 📁 Estrutura do Projeto

```
RAG/
├── main.py                     # 🎯 CLI - Ponto de entrada linha de comando
├── requirements.txt            # 📦 Dependências Python completas
├── install.sh                 # 🐧 Script instalação Linux/Mac
├── install.bat                # 🪟 Script instalação Windows
├── docs/                      # 📚 Documentação completa
│   ├── README.md              # 📁 Índice da documentação
│   ├── CHANGELOG.md           # 📋 Histórico detalhado de mudanças
│   ├── ARCHITECTURE.md        # 🏗️ Arquitetura e decisões técnicas
│   └── DOCUMENTATION_GUIDE.md # 📝 Guia de documentação
├── web/                       # 🌐 Interface Web Streamlit
│   └── app.py                 # 🖥️ Aplicação web principal
├── src/                       # 📂 Código fonte modular
│   ├── config/
│   │   └── settings.py        # ⚙️ Configurações centralizadas
│   ├── core/
│   │   └── rag_service.py     # 🧠 Lógica principal RAG
│   ├── services/
│   │   ├── document_service.py # 📄 Processamento de documentos
│   │   └── ollama_service.py   # 🔌 Conectividade Ollama
│   ├── utils/
│   │   ├── cache_utils.py     # ⚡ Sistema de cache otimizado
│   │   ├── file_utils.py      # 📁 Operações com arquivos
│   │   └── ingest_manifest.py # 📊 Manifesto para rebuild incremental
│   ├── pf_rag/                # 🛡️ Pipeline PF-específico
│   │   ├── cli.py             # 💻 Interface linha de comando
│   │   ├── io_pdf.py          # 📄 Extração PDF (Docling + OCR)
│   │   ├── parse_norma.py     # 📜 Parsing hierárquico normativo
│   │   ├── chunker.py         # ✂️ Chunking layout-aware
│   │   ├── search.py          # 🔍 Busca híbrida (dense + BM25)
│   │   ├── embed_index.py     # 🧮 Indexação e embeddings
│   │   ├── export_jsonl.py    # 📤 Export para auditoria
│   │   ├── metadata_pf.py     # 🏷️ Metadados específicos PF
│   │   ├── normalize.py       # 🧹 Normalização de texto
│   │   ├── regexes.py         # 🔤 Expressões regulares normativas
│   │   ├── types.py           # 📝 Tipos e estruturas de dados
│   │   ├── calibrate.py       # 📏 Calibração e análise
│   │   └── eval.py            # 📊 Avaliação de performance
│   └── vector_backends/       # 🗃️ Backends de banco vetorial
│       └── qdrant_backend.py  # 🚀 Cliente Qdrant embedded
├── tests/                     # 🧪 Testes automatizados
│   ├── conftest.py           # ⚙️ Configuração pytest
│   ├── test_parse_chunk.py   # 🧪 Testes parsing/chunking
│   └── test_regexes.py       # 🔤 Testes expressões regulares
├── SGP/                       # 📚 Documentos PDF fonte
│   ├── documento1.pdf         # 📄 PDFs normativos da PF
│   └── documento2.pdf         # 📄 Legislações e instruções
├── faissDB/                   # 🗃️ Base FAISS (legado/compatibilidade)
│   ├── index.faiss           # 🔍 Índice busca semântica FAISS
│   ├── index.pkl             # 📊 Metadados da base FAISS
│   ├── sgp_hash.json         # 🔐 Hash detecção mudanças
│   ├── cache_respostas.json  # ⚡ Cache respostas persistente
│   └── chunks.jsonl          # 📋 Export chunks (se habilitado)
└── qdrantDB/                  # 🚀 Base Qdrant (recomendado)
    └── collection/            # 📁 Coleções Qdrant embedded
```

### 🎯 **Componentes Principais**

#### 🌐 **Interface Web** (`web/app.py`)
- Upload drag-and-drop de PDFs
- Reindexação com progress visual
- Preview de retrieval com breadcrumbs
- Dashboard de métricas em tempo real

#### 🛡️ **Pipeline PF-Específico** (`src/pf_rag/`)
- Parsing hierárquico de normas (Art., §, Incisos)
- Chunking que preserva estrutura e tabelas
- Busca híbrida (embeddings + BM25)
- Metadados específicos para legislação PF

#### 🚀 **Backend Qdrant** (`src/vector_backends/`)
- Alternativa moderna ao FAISS
- Operações granulares (delete por arquivo)
- Embedded mode sem servidor externo
- Clear collection para rebuilds limpos

## 🔧 Configurações Avançadas

### Backend de Banco Vetorial
```bash
# Qdrant (recomendado) - moderno e eficiente
export PF_RAG_VECTOR_DB=qdrant

# FAISS (compatibilidade) - para sistemas legados
export PF_RAG_VECTOR_DB=faiss
```

### Modelos de LLM Alternativos
```bash
# Em src/config/settings.py ou via variável:
export LLM_MODEL="mistral:7b"        # Mais rápido que llama3.2
export LLM_MODEL="qwen2:7b"          # Alternativa rápida
export LLM_MODEL="llama3.2:latest"   # Padrão (mais preciso)
```

### Parâmetros de Chunking PF-Específico
```bash
# Tamanho dos chunks (em tokens)
export PF_RAG_TOKEN_MIN=400          # Mínimo por chunk
export PF_RAG_TOKEN_MAX=1200         # Máximo por chunk

# Ajustar retrieval (quantos chunks buscar)
export RETRIEVAL_K=4                 # Mais rápido (menos chunks)
export RETRIEVAL_K=8                 # Mais preciso (mais chunks)
```

### Extração Avançada de PDF
```bash
# Docling (recomendado) - layout-aware com tabelas
export PF_RAG_USE_DOCLING=true

# OCR para PDFs escaneados
export PF_RAG_OCR_ENABLED=true
export PF_RAG_OCR_LANG=por

# Busca híbrida com BM25
export PF_RAG_BM25_ENABLED=true
```

### Embeddings e Performance
```bash
# Backend de embeddings
export PF_RAG_EMBED_BACKEND=ollama   # Padrão com Ollama
export PF_RAG_EMBED_BACKEND=sbert    # Sentence-BERT local

# Batch size para indexação
export PF_RAG_EMBED_BATCH=64

# Modo offline (sem downloads)
export PF_RAG_OFFLINE=true
```

### Auditoria e Export
```bash
# Export automático de chunks para análise
export PF_RAG_EXPORT_JSONL=true
export PF_RAG_CHUNKS_JSONL=faissDB/chunks_audit.jsonl

# Verbose para debugging
export PF_RAG_VERBOSE=true
```

| Tipo de Consulta | Tempo Médio | Cache Hit |
|------------------|-------------|-----------|
| Pergunta nova | 2-3 segundos | ❌ |
| Pergunta repetida | 0.01 segundos | ✅ |
| Startup | 1-2 segundos | - |

## 📁 Estrutura do Projeto

```
RAG/
├── main.py                     # 🎯 Orquestrador principal (80 linhas)
├── requirements.txt            # 📦 Dependências Python
├── install.sh                 # 🐧 Script instalação Linux/Mac
├── install.bat                # 🪟 Script instalação Windows
├── docs/                      # 📚 Documentação completa
│   ├── README.md              # 📁 Índice da documentação
│   ├── CHANGELOG.md           # 📋 Histórico detalhado de mudanças
│   ├── ARCHITECTURE.md        # 🏗️ Arquitetura e decisões técnicas
│   └── DOCUMENTATION_GUIDE.md # 📝 Guia de documentação
├── src/                       # 📂 Código fonte modular
│   ├── config/
│   │   └── settings.py        # ⚙️ Configurações centralizadas
│   ├── core/
│   │   └── rag_service.py     # 🧠 Lógica principal RAG
│   ├── services/
│   │   ├── document_service.py # 📄 Processamento de documentos
│   │   └── ollama_service.py   # 🔌 Conectividade Ollama
│   └── utils/
│       ├── cache_utils.py     # ⚡ Sistema de cache otimizado
│       └── file_utils.py      # 📁 Operações com arquivos
├── docs/                      # 📚 Documentação técnica
│   ├── ARCHITECTURE.md        # 🏗️ Arquitetura e decisões técnicas
│   └── DOCUMENTATION_GUIDE.md # 📝 Guia de documentação
├── SGP/                       # 📚 Documentos PDF fonte
│   ├── documento1.pdf
│   └── documento2.pdf
└── faissDB/                   # 🗃️ Base de dados vetorial (auto-criada)
    ├── index.faiss           # 🔍 Índice de busca semântica
    ├── index.pkl             # 📊 Metadados da base
    ├── sgp_hash.json         # 🔐 Hash para detecção de mudanças
    └── cache_respostas.json  # ⚡ Cache de respostas persistente
```

## 🔧 Configurações Avançadas

### Modelos Alternativos (mais rápidos)
```python
# Em src/config/settings.py:
LLM_MODEL = "mistral:7b"        # Mais rápido que llama3.2
# ou
LLM_MODEL = "qwen2:7b"          # Alternativa rápida
```

### Ajustar Parâmetros de Busca
```python
# Em src/config/settings.py:
RETRIEVAL_K = 4                 # Mais rápido (menos chunks)
# ou
RETRIEVAL_K = 8                 # Mais preciso (mais chunks)
```

### Personalizar Chunking
```python
# Em src/config/settings.py:
CHUNK_SIZE = 300               # Chunks menores = mais precisão
CHUNK_OVERLAP = 100            # Menos overlap = mais velocidade
```

## 🐛 Solução de Problemas

### Erro: "Storage folder qdrantDB is already accessed by another instance"
```bash
# Causa: Múltiplas instâncias do sistema rodando simultaneamente

# Solução 1: Parar todas as instâncias
# - Feche todos os terminais/Streamlit do RAG
# - Aguarde 10 segundos e tente novamente

# Solução 2: Forçar limpeza do banco Qdrant
rm -rf qdrantDB/
python main.py

# Solução 3: Usar FAISS temporariamente
PF_RAG_VECTOR_DB=faiss python main.py

# Limpeza de pastas antigas (se houver qdrantDB_1234567890)
rm -rf qdrantDB_*
```

### Problema: Múltiplas pastas qdrantDB_timestamp
```bash
# O sistema pode criar pastas com timestamp em conflitos
# Exemplo: qdrantDB_1756149969, qdrantDB_1756150001

# Solução automática: O sistema agora limpa automaticamente
# Solução manual: Remover pastas antigas
find . -name "qdrantDB_*" -type d -exec rm -rf {} \;

# Manter apenas a pasta principal
ls qdrantDB/  # Esta deve ser a única pasta
```

### Erro: "streamlit command not found"
```bash
# No Windows, usar sempre:
python -m streamlit run web/app.py

# Ou adicionar ao PATH:
# C:\Users\[usuario]\AppData\Roaming\Python\Python313\Scripts
```

### Erro: "Ollama não encontrado"
```bash
# Verificar se Ollama está rodando
ollama serve

# Baixar modelos necessários
ollama pull nomic-embed-text
ollama pull llama3.2
```

### Erro: "pypdf not found"
```bash
pip install pypdf
```

### Sistema lento
1. Use modelos menores (`mistral:7b`)
2. Reduza número de chunks (`k=4`)
3. Verifique cache ativo

### Proxy corporativo
- Configure bypass para `localhost:11434`
- Ou use VPN para acessar Ollama

## 📈 Otimizações Implementadas

- **Cache persistente** com normalização inteligente
- **Chunks otimizados** (500 chars com overlap de 200)
- **Retrieval reduzido** (6 chunks em vez de 10)
- **Auto-reconexão** em caso de falhas
- **Detecção de mudanças** por hash MD5
- **Feedback em tempo real** de progresso

## 📈 Histórico de Versões

### 🆕 v3.0.0 - Sistema Completo com Interface Web (Atual)
- ✅ **Interface Web Streamlit** com upload drag-and-drop
- ✅ **Backend Qdrant** integrado como alternativa ao FAISS
- ✅ **Pipeline PF-Específico** com parsing hierárquico de normas
- ✅ **Docling Integration** para extração layout-aware de PDFs
- ✅ **Busca Híbrida** (embeddings + BM25)
- ✅ **Export de Chunks** para auditoria
- ✅ **Configuração via Environment Variables**

### v2.0.0 - Arquitetura Modular
- ✅ **Sistema modularizado** em componentes especializados
- ✅ **main.py otimizado** de 400+ para 80 linhas
- ✅ **Separação de responsabilidades** clara
- ✅ **Manutenibilidade** e testabilidade aprimoradas

### v1.2.0 - Sistema Otimizado
- ✅ **Cache de respostas** (99% melhoria: 47s → 0.01s)
- ✅ **Detecção automática** de mudanças nos documentos
- ✅ **Reconexão automática** com Ollama
- ✅ **Performance otimizada** com retrieval k=6

### v1.1.0 - RAG Básico
- ✅ **Sistema RAG** inicial com LangChain
- ✅ **Processamento PDF** automático
- ✅ **Base FAISS** para busca semântica
- ✅ **Interface CLI** interativa

## 🔮 Roadmap Futuro

### v3.1.0 - API REST
- [ ] **FastAPI backend** para integração com sistemas externos
- [ ] **Endpoints RESTful** para consultas programáticas
- [ ] **Documentação OpenAPI/Swagger** automática
- [ ] **Autenticação e autorização** baseada em tokens

### v3.2.0 - IA Avançada
- [ ] **Reranking de resultados** com modelos cross-encoder
- [ ] **Streaming de respostas** em tempo real
- [ ] **Suporte multilíngue** (português, inglês, espanhol)
- [ ] **Análise de sentimento** em documentos

### v4.0.0 - Recursos Empresariais
- [ ] **Dashboard Analytics** com métricas detalhadas
- [ ] **Auditoria completa** de consultas e respostas
- [ ] **Integração LDAP/AD** para autenticação corporativa
- [ ] **Multi-tenancy** para múltiplas organizações

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs do sistema
2. Confirme que Ollama está rodando
3. Teste com documentos pequenos primeiro
4. Verifique conexão de rede

## 📚 Documentação Adicional

- 📋 **[Histórico de Mudanças](docs/CHANGELOG.md)** - Todas as versões e implementações
- 🏗️ **[Arquitetura Técnica](docs/ARCHITECTURE.md)** - Detalhes técnicos e decisões de design
- 📝 **[Guia de Documentação](docs/DOCUMENTATION_GUIDE.md)** - Como manter a documentação atualizada
- 📁 **[Índice da Documentação](docs/README.md)** - Navegação organizada
- 🧩 **[Visão Técnica (PF RAG)](docs/TECHNICAL_OVERVIEW.md)** - Implementado, pendências, melhorias e guia de arquivos

---

**Desenvolvido para otimizar consultas jurídicas na Polícia Federal** 🇧🇷
