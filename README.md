# 🤖 Sistema RAG - Polícia Federal

Sistema de Recuperação e Geração Aumentada (RAG) para consulta de legislações e documentos da Polícia Federal.

## 🚀 Funcionalidades

- ✅ **Cache de Respostas**: Respostas instantâneas para perguntas repetidas
- ✅ **Detecção Automática de Mudanças**: Reconstrói base quando documentos são alterados
- ✅ **Reconexão Automática**: Sistema resiliente a falhas de conexão
- ✅ **Interface Intuitiva**: Feedback claro sobre status e progresso
- ✅ **Busca Semântica**: Encontra informações relevantes mesmo em documentos longos
- ✅ **Processamento Otimizado**: 40% mais rápido que versões anteriores

## 📋 Pré-requisitos

- Python 3.8 ou superior
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

## 🎯 Como Usar

1. **Adicione documentos PDF** na pasta `SGP/`
2. **Inicie o Ollama**: `ollama serve`
3. **Execute o sistema**: `python main.py`
4. **Faça suas perguntas** sobre legislação da PF

## 📊 Performance

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

## � Histórico de Versões

### 🆕 v2.0.0 - Arquitetura Modular (Atual)
- ✅ **Sistema modularizado** em 7 componentes especializados
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

### v2.1.0 - Interface Web
- [ ] Streamlit/Gradio UI
- [ ] Upload de arquivos via web
- [ ] Dashboard de métricas em tempo real

### v2.2.0 - API REST
- [ ] FastAPI backend
- [ ] Endpoints RESTful para consultas
- [ ] Documentação OpenAPI/Swagger

### v3.0.0 - IA Avançada
- [ ] Busca híbrida (semântica + keyword)
- [ ] Reranking de resultados
- [ ] Streaming de respostas
- [ ] Suporte multilíngue

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

---

**Desenvolvido para otimizar consultas jurídicas na Polícia Federal** 🇧🇷
