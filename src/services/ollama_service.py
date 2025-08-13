"""
Serviço para verificação e comunicação com Ollama
"""
import requests
import sys
from typing import Tuple
from ..config.settings import Settings


class OllamaService:
    """Serviço para gerenciar conexão com Ollama"""

    @staticmethod
    def check_connection() -> Tuple[bool, str]:
        """
        Verifica se o Ollama está rodando
        Returns: (conectado, codigo_erro)
        """
        try:
            response = requests.get(
                Settings.get_ollama_api_url("tags"),
                timeout=Settings.OLLAMA_TIMEOUT
            )
            return True, "OK"

        except requests.exceptions.ConnectionError:
            return False, "CONNECTION_REFUSED"
        except requests.exceptions.Timeout:
            return False, "TIMEOUT"
        except requests.exceptions.ProxyError:
            return False, "PROXY_ERROR"
        except KeyboardInterrupt:
            sys.exit(130)
        except Exception as e:
            return False, f"UNKNOWN_ERROR: {str(e)}"

    @staticmethod
    def print_connection_error(error_code: str) -> None:
        """Imprime mensagens de erro específicas para cada tipo de falha"""
        print("❌ Erro de conectividade com Ollama")

        if error_code == "CONNECTION_REFUSED":
            print("🔧 Solução: Ollama não está rodando. Execute 'ollama serve' no terminal")
        elif error_code == "PROXY_ERROR":
            print("🌐 Solução: Problema de proxy. Configure bypass para localhost ou use VPN")
        elif error_code == "TIMEOUT":
            print("⏱️ Solução: Timeout de conexão. Verifique se o Ollama está respondendo")
        else:
            print(f"❓ Erro: {error_code}")

        print("\n📋 Passos para configurar Ollama:")
        print("1. Baixe: https://ollama.ai/")
        print("2. Execute: ollama pull nomic-embed-text")
        print("3. Execute: ollama pull llama3.2")
        print("4. Inicie: ollama serve")
        print("\n⚡ O sistema continuará rodando e tentará reconectar automaticamente...")

    @staticmethod
    def print_processing_error(error_str: str) -> None:
        """Imprime mensagens de erro durante processamento"""
        if "Connection refused" in error_str or "503" in error_str:
            print("❌ Conectividade perdida com Ollama")
            print("🔧 Execute 'ollama serve' e tente refazer a pergunta")
        elif "proxy" in error_str.lower():
            print("❌ Bloqueio de proxy detectado")
            print("🌐 Configure bypass para localhost:11434 e tente novamente")
        elif "Failed to connect to Ollama" in error_str:
            print("❌ Falha na conexão com Ollama")
            print("🔧 Verifique se o serviço está rodando e tente novamente")
        else:
            print(f"❌ Erro inesperado: {error_str[:80]}...")
            print("🔧 Tente reiniciar o Ollama e refaça a pergunta")
