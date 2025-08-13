"""
Serviço principal do sistema RAG
"""
import sys
from typing import Optional
from langchain.chains import RetrievalQA
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate

from ..config.settings import Settings
from ..utils.cache_utils import CacheUtils
from ..services.document_service import DocumentService
from ..services.ollama_service import OllamaService


class RAGService:
    """Serviço principal para consultas RAG"""

    def __init__(self):
        self.cache = CacheUtils()
        self.document_service = DocumentService()
        self.qa_chain = None
        self._initialize_chain()

    def _initialize_chain(self):
        """Inicializa a cadeia RAG"""
        print("🤖 Inicializando sistema RAG...")

        # Carrega/cria base de dados
        database = self.document_service.load_or_create_database()
        if not database:
            print("❌ Falha ao carregar base de dados")
            sys.exit(1)

        # Verifica conexão com Ollama
        conectado, erro = OllamaService.check_connection()
        if not conectado:
            print("❌ Ollama não está acessível")
            OllamaService.print_connection_error(erro)
            sys.exit(1)

        print("✅ Ollama conectado!")

        # Cria chain RAG
        self._create_qa_chain(database)

    def _create_qa_chain(self, database):
        """Cria a cadeia de perguntas e respostas"""
        retriever = database.as_retriever(search_kwargs={"k": Settings.RETRIEVAL_K})

        # Template de prompt otimizado
        prompt_template = """Use o contexto fornecido para responder à pergunta de forma precisa e específica.

Contexto relevante:
{context}

Pergunta: {question}

Instruções:
- Responda apenas com base no contexto fornecido
- Se a informação não estiver no contexto, diga "Informação não encontrada no contexto fornecido"
- Seja específico e cite detalhes relevantes quando disponíveis
- Mantenha a resposta clara e organizada

Resposta:"""

        custom_prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        llm = OllamaLLM(model=Settings.LLM_MODEL)

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": custom_prompt},
            return_source_documents=False
        )

        print("✅ Sistema RAG inicializado com sucesso!")

    def answer_question(self, pergunta: str) -> Optional[str]:
        """Responde uma pergunta usando o sistema RAG"""
        # Tenta buscar no cache primeiro
        resposta_cache = self.cache.get_cached_response(pergunta)
        if resposta_cache:
            print("⚡ Resposta do cache!")
            return resposta_cache

        try:
            print("🔍 Buscando resposta...")

            # Verifica conexão antes de consultar
            conectado, erro = OllamaService.check_connection()
            if not conectado:
                print("❌ Conexão perdida com Ollama")
                OllamaService.print_connection_error(erro)
                return None

            # Faz a consulta
            resposta = self.qa_chain.run(pergunta)

            # Salva no cache
            self.cache.save_response(pergunta, resposta)

            return resposta

        except Exception as e:
            error_str = str(e)
            print("❌ Erro ao processar pergunta:")

            if "Connection refused" in error_str or "503" in error_str:
                print("🔧 Ollama perdeu conexão durante consulta")
                print("💡 Execute 'ollama serve' e tente novamente")
            elif "proxy" in error_str.lower():
                print("🌐 Bloqueio de proxy detectado")
                print("💡 Configure bypass para localhost:11434")
            else:
                print(f"📝 Detalhes: {error_str[:150]}...")

            return None
