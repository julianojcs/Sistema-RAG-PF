@echo off
REM Script de instalação para o Sistema RAG - Polícia Federal (Windows)

echo 🚀 Instalando dependências do Sistema RAG...

REM Atualiza pip
echo 📦 Atualizando pip...
python -m pip install --upgrade pip

REM Instala dependências principais
echo 📚 Instalando dependências do requirements.txt...
pip install -r requirements.txt

REM Verifica se Ollama está instalado
echo 🔍 Verificando Ollama...
ollama --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Ollama encontrado!

    REM Baixa modelos necessários
    echo 🧠 Baixando modelos necessários...
    echo ⏳ Baixando nomic-embed-text (para embeddings)...
    ollama pull nomic-embed-text

    echo ⏳ Baixando llama3.2 (para geração de respostas)...
    ollama pull llama3.2

    echo 🎉 Modelos baixados com sucesso!

) else (
    echo ❌ Ollama não encontrado!
    echo 📋 Para instalar o Ollama:
    echo 1. Visite: https://ollama.ai/
    echo 2. Baixe e instale para Windows
    echo 3. Execute: ollama serve
    echo 4. Execute este script novamente
)

echo.
echo ✅ Instalação concluída!
echo 🚀 Para iniciar o sistema, execute: python main.py
echo.
echo 📁 Certifique-se de ter arquivos PDF na pasta SGP/
pause
