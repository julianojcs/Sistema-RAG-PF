## 1. Pré-requisitos

- **Python 3.8 ou superior** instalado no Windows.
- **pip** (gerenciador de pacotes do Python).
- **Ollama** instalado e rodando localmente ([Download Ollama](https://ollama.com/download)).
- **Instale os seguintes modelos depois de baixar o ollama pelo terminal:**
    ollama pull nomic-embed-text:latest
    ollama pull  llama3.2:latest

## 2. Instale as dependências
pip install langchain langchain-community langchain-ollama faiss-cpu


# PROPOSTA
#
# Chat adaptável a qualquer setor da pf, onde os servidores poderão tirar dúvidas
# relacionadas as mais diversas legislações


# PROBLEMAS
#
# - modelo alucina frequentemente, não respondendo coisas que estão sim na sua base
# - cita exceções onde não tem
# - quando a informação procurada tá no fim do documento, raramente a alcança
# - muito lento
# - temos que usar modelos gratuitos, pela falta de recurso
# - de onde puxar todas as legislações possíveis que competem os servidores de uma vez só?

