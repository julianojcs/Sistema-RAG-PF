#!/bin/bash
# Script de instalação para o Sistema RAG - Polícia Federal

echo "🚀 Instalando dependências do Sistema RAG..."

# Atualiza pip
echo "📦 Atualizando pip..."
python -m pip install --upgrade pip

# Instala dependências principais
echo "📚 Instalando dependências do requirements.txt..."
pip install -r requirements.txt

# Verifica se Ollama está instalado
echo "🔍 Verificando Ollama..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama encontrado!"

    # Baixa modelos necessários
    echo "🧠 Baixando modelos necessários..."
    echo "⏳ Baixando nomic-embed-text (para embeddings)..."
    ollama pull nomic-embed-text

    echo "⏳ Baixando llama3.2 (para geração de respostas)..."
    ollama pull llama3.2

    echo "🎉 Modelos baixados com sucesso!"

else
    echo "❌ Ollama não encontrado!"
    echo "📋 Para instalar o Ollama:"
    echo "1. Visite: https://ollama.ai/"
    echo "2. Baixe e instale para seu sistema operacional"
    echo "3. Execute: ollama serve"
    echo "4. Execute este script novamente"
fi

echo ""
echo "✅ Instalação concluída!"
echo "🚀 Para iniciar o sistema, execute: python main.py"
echo ""
echo "📁 Certifique-se de ter arquivos PDF na pasta SGP/"
