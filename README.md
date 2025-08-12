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
```bash
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
├── main.py                 # Sistema principal
├── requirements.txt        # Dependências Python
├── install.sh             # Script instalação Linux/Mac
├── install.bat            # Script instalação Windows
├── SGP/                   # Pasta com documentos PDF
│   ├── documento1.pdf
│   └── documento2.pdf
└── faissDB/               # Base de dados (criada automaticamente)
    ├── index.faiss
    ├── index.pkl
    ├── sgp_hash.json
    └── cache_respostas.json
```

## 🔧 Configurações Avançadas

### Modelos Alternativos (mais rápidos)
```python
# No main.py, linha ~204:
llm = OllamaLLM(model="mistral:7b")  # Mais rápido que llama3.2
# ou
llm = OllamaLLM(model="qwen2:7b")    # Alternativa rápida
```

### Ajustar Número de Chunks
```python
# No main.py, linha ~287:
retriever = database.as_retriever(search_kwargs={"k": 4})  # Mais rápido
# ou
retriever = database.as_retriever(search_kwargs={"k": 8})  # Mais preciso
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

## 🔮 Melhorias Futuras

- Interface web com Streamlit/Gradio
- Busca híbrida (semântica + keyword)
- Streaming de respostas
- Suporte a mais formatos (DOCX, TXT)
- API REST para integração
- Dashboard de métricas

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs do sistema
2. Confirme que Ollama está rodando
3. Teste com documentos pequenos primeiro
4. Verifique conexão de rede

---

**Desenvolvido para otimizar consultas jurídicas na Polícia Federal** 🇧🇷
