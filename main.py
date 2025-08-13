"""
Sistema RAG (Retrieval-Augmented Generation) para Consulta de Documentos
Desenvolvido para a Polícia Federal - Busca inteligente em documentos PDF

Versão Modular - Arquitetura refatorada para melhor manutenibilidade
Autor: Sistema refatorado com arquitetura modular
Data: 2024
"""

import sys
import os

# Adiciona o diretório src ao path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.rag_service import RAGService


def imprimir_cabecalho():
    """Imprime cabeçalho do sistema"""
    print("🚀 Sistema RAG para Consulta de Documentos")
    print("📋 Polícia Federal - Busca Inteligente em Legislação")
    print("⚡ Versão Modular com Cache Otimizado")
    print("=" * 50)


def loop_principal(rag_service):
    """Loop principal de interação com o usuário"""
    print("🚀 Sistema pronto! Cache ativo para respostas rápidas.")
    print("\n💡 Dicas:")
    print("   - Digite 'sair' para encerrar")
    print("   - O sistema usa cache para respostas mais rápidas")
    print("   - Perguntas similares são respondidas instantaneamente")
    print("=" * 50)

    while True:
        try:
            pergunta = input("\n❓ Digite sua pergunta: ").strip()

            if pergunta.lower() in ['sair', 'exit', 'quit']:
                print("👋 Encerrando sistema...")
                break

            if not pergunta:
                print("⚠️ Digite uma pergunta válida")
                continue

            print("🔍 Processando...")
            resposta = rag_service.answer_question(pergunta)

            if resposta:
                print("\n✅ Resposta:")
                print("-" * 30)
                print(resposta)
                print("-" * 30)
            else:
                print("❌ Não foi possível processar a pergunta")
                print("💡 Verifique se o Ollama está funcionando")

        except KeyboardInterrupt:
            print("\n\n👋 Sistema interrompido pelo usuário")
            break
        except Exception as e:
            print(f"\n❌ Erro inesperado: {str(e)[:100]}...")
            print("💡 Tente novamente ou reinicie o sistema")


def main():
    """Função principal do sistema"""
    try:
        # Cabeçalho
        imprimir_cabecalho()

        # Inicializa o serviço RAG
        rag_service = RAGService()

        # Loop principal de interação
        loop_principal(rag_service)

    except KeyboardInterrupt:
        print("\n\n👋 Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro crítico na inicialização: {str(e)}")
        print("🔧 Verifique se:")
        print("   - O Ollama está instalado e rodando")
        print("   - Existem arquivos PDF na pasta SGP/")
        print("   - As dependências estão instaladas")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
