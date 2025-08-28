#!/usr/bin/env python3
"""
Script para analisar como funciona a hierarquização de chunks no sistema RAG PF
"""

import json
from pathlib import Path
from typing import Dict, List, Any

def explain_chunking_system():
    """
    Explica como funciona o sistema de chunking hierárquico do RAG PF
    """

    print("=" * 80)
    print("🔍 SISTEMA DE CHUNKING HIERÁRQUICO - RAG POLÍCIA FEDERAL")
    print("=" * 80)

    print("\n📚 1. COMO FUNCIONA A CRIAÇÃO DE CHUNKS")
    print("-" * 50)

    print("""
🔄 Pipeline de Processamento:
1️⃣ Extração PDF → Texto bruto + layout (via Docling)
2️⃣ Normalização → Limpeza de headers/footers, hifenização
3️⃣ Parsing Hierárquico → Detecção de estrutura usando regex
4️⃣ Chunking Layout-Aware → Criação de chunks respeitando hierarquia
5️⃣ Embeddings → Vetorização dos chunks (768 dimensões)
6️⃣ Indexação → Armazenamento no Qdrant
""")

    print("\n🏗️ 2. ESTRUTURA HIERÁRQUICA DETECTADA")
    print("-" * 50)

    print("""
📋 Hierarquia Normativa (em ordem de granularidade):
┌── documento (raiz)
├── parte (PARTE I, II, etc.)
├── livro (LIVRO I, II, etc.)
├── titulo (TÍTULO I, II, etc.)
├── capitulo (CAPÍTULO I, II, etc.)
├── secao (SEÇÃO I, II, etc.)
├── subsecao (SUBSEÇÃO I, II, etc.)
├── artigo (Art. 1º, 2º, etc.)
├── paragrafo (§ 1º, § 2º, Parágrafo único)
├── inciso (I, II, III, etc.)
├── alinea (a), b), c), etc.)
├── item (1, 2, 3, etc.)
└── anexo (ANEXO I, II, etc.)
""")

    print("\n🎯 3. ESTRATÉGIA DE CHUNKING")
    print("-" * 50)

    print("""
✂️ Regras de Chunking:
• NUNCA quebrar no meio de um dispositivo
• Chunk ideal: ~1000 tokens (adaptativo)
• Preservar contexto hierárquico completo
• Evitar cortar tabelas (layout-aware)
• Criar relações parent-child e siblings

📊 Estratégias por Nível:
• Artigo-centric: Artigo + seus §§ (se couber)
• Parágrafo-centric: § + seus incisos
• Inciso-centric: inciso + suas alíneas
• Macroestruturas: título + sumário dos artigos
""")

    print("\n🗂️ 4. ONDE A HIERARQUIA É ARMAZENADA")
    print("-" * 50)

    print("""
📍 Localização dos Dados Hierárquicos:

🗄️ Qdrant Database: /qdrantDB/collection/pf_normativos/
├── storage.sqlite (metadados da coleção)
├── storage.sqlite-x-points-1-point.bin (pontos individuais)
└── collection/
    └── pf_normativos/
        ├── storage.sqlite (índice principal)
        └── *.bin (chunks vetorizados)

💾 Estrutura de Cada Chunk:
{
  "id": "6033932a52ee40b4a68111287a51a74f",
  "vector": [768 dimensões],
  "payload": {
    "page_content": "texto do chunk",
    "metadata": {
      "doc_id": "documento-pf",
      "anchor_id": "documento-pf-alinea-p",
      "nivel": "alinea",
      "rotulo": "P)",
      "caminho_hierarquico": [
        {"nivel": "capitulo", "rotulo": "CAPÍTULO I"},
        {"nivel": "artigo", "rotulo": "Art. 5º"},
        {"nivel": "paragrafo", "rotulo": "§ 1º"},
        {"nivel": "alinea", "rotulo": "P)"}
      ],
      "parent_id": "documento-pf-paragrafo-1",
      "siblings_prev_id": "documento-pf-alinea-o",
      "siblings_next_id": "documento-pf-inciso-c",
      ...
    }
  }
}
""")

    print("\n🏷️ 5. PARA QUE SERVEM OS METADADOS")
    print("-" * 50)

    print("""
🎯 Funcionalidades dos Metadados:

📍 Navegação Hierárquica:
• caminho_hierarquico: breadcrumb completo
• parent_id/siblings_*: relações familiares
• anchor_id: identificador único e SEO-friendly

🔍 Busca Inteligente:
• nivel + rotulo: busca por "Art. 5º", "§ 1º"
• doc_id: filtro por documento específico
• origem_pdf: rastreabilidade ao arquivo fonte

🏛️ Metadados Institucionais:
• orgao: "Polícia Federal"
• sigla_orgao: "DPF"
• unidade_emitente: "DG/DPF", "SR/PF-SP"
• especie_normativa: "Portaria", "Instrução Normativa"
• numero/ano: "1234/2024"

📊 Controle de Qualidade:
• hash_conteudo: detecção de mudanças
• versao_parser: versionamento do pipeline
• tokens_estimados: controle de tamanho
• texto_limpo: flag de processamento

🎨 Layout Intelligence:
• layout_refs: referências a tabelas/figuras
• origem_pdf.paginas: localização no PDF original

💡 Casos de Uso:
1. "Mostre o Art. 5º da Portaria 123" → filtro por nivel+rotulo
2. "Contexto do §1º" → usar parent_id para pegar artigo pai
3. "Próximo item" → usar siblings_next_id
4. "Documentos da DG/DPF" → filtro por unidade_emitente
5. "Tabelas do Cap. II" → filtro por nivel+layout_refs
""")

    print("\n🔧 6. FLUXO TÉCNICO DE IMPLEMENTAÇÃO")
    print("-" * 50)

    print("""
📁 Módulos Principais:
├── src/pf_rag/parse_norma.py → detecção hierárquica via regex
├── src/pf_rag/chunker.py → criação de chunks com metadados
├── src/pf_rag/types.py → definição das estruturas de dados
├── src/pf_rag/metadata_pf.py → extração de metadados PF
└── src/vector_backends/qdrant_backend.py → persistência no Qdrant

🔄 Fluxo de Dados:
PDF → Docling → Texto+Layout → Regex → Nodes → Chunks → Embeddings → Qdrant
""")

    print("\n✅ 7. VANTAGENS DO SISTEMA")
    print("-" * 50)

    print("""
🚀 Benefícios da Hierarquização:
• 🎯 Precisão: busca específica por dispositivos
• 🧭 Contexto: navegação pai-filho-irmão
• 📊 Layout: preservação de tabelas inteiras
• 🏛️ Compliance: metadados específicos da PF
• 🔍 Auditoria: rastreabilidade completa
• ⚡ Performance: chunks otimizados por estrutura
• 🔧 Manutenção: versionamento e detecção de mudanças
""")

    print("\n" + "=" * 80)

def analyze_sample_chunk():
    """
    Analisa um chunk de exemplo para demonstrar a estrutura
    """

    print("\n🔍 ANÁLISE DE CHUNK DE EXEMPLO")
    print("=" * 50)

    # Exemplo baseado no arquivo desserializado
    sample_chunk = {
        "id": "6033932a52ee40b4a68111287a51a74f",
        "vector_dimensions": 768,
        "payload": {
            "page_content": "Presidência da República",
            "metadata": {
                "doc_id": "documento-pf",
                "anchor_id": "documento-pf-alinea-p",
                "nivel": "alinea",
                "rotulo": "P)",
                "ordinal_normalizado": "P",
                "caminho_hierarquico": [
                    {"nivel": "alinea", "rotulo": "P)"}
                ],
                "tokens_estimados": 6,
                "parent_id": None,
                "siblings_prev_id": None,
                "siblings_next_id": "documento-pf-inciso-c",
                "origem_pdf": {
                    "arquivo": "SGP\\Emenda Constitucional nº 103.pdf",
                    "paginas": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
                },
                "hash_conteudo": "f1f78a7fb509811017f3488542afef4732d5efb43a8b54a417435f6b5d677406",
                "versao_parser": "1.0.0",
                "orgao": "Polícia Federal",
                "sigla_orgao": "DPF",
                "ambito": "federal",
                "pais": "Brasil",
                "data_publicacao": "2019-11-12",
                "situacao": "revogada",
                "fonte_publicacao": "DOU",
                "ementa": "Altera o sistema de previdência social e estabelece"
            }
        }
    }

    print("📋 Informações do Chunk:")
    print(f"  🆔 ID: {sample_chunk['id']}")
    print(f"  📝 Conteúdo: '{sample_chunk['payload']['page_content']}'")
    print(f"  📊 Dimensões do vetor: {sample_chunk['vector_dimensions']}")

    metadata = sample_chunk['payload']['metadata']
    print(f"\n🏗️ Estrutura Hierárquica:")
    print(f"  📍 Nível: {metadata['nivel']}")
    print(f"  🏷️ Rótulo: {metadata['rotulo']}")
    print(f"  🔗 Anchor ID: {metadata['anchor_id']}")
    print(f"  🧭 Caminho: {' > '.join([p['rotulo'] for p in metadata['caminho_hierarquico']])}")

    print(f"\n🔗 Relacionamentos:")
    print(f"  👆 Parent: {metadata['parent_id']}")
    print(f"  ⬅️ Anterior: {metadata['siblings_prev_id']}")
    print(f"  ➡️ Próximo: {metadata['siblings_next_id']}")

    print(f"\n🏛️ Metadados Institucionais:")
    print(f"  🏢 Órgão: {metadata['orgao']} ({metadata['sigla_orgao']})")
    print(f"  🌍 Âmbito: {metadata['ambito']} - {metadata['pais']}")
    print(f"  📅 Publicação: {metadata['data_publicacao']}")
    print(f"  📊 Status: {metadata['situacao']}")
    print(f"  📰 Fonte: {metadata['fonte_publicacao']}")

    print(f"\n📄 Rastreabilidade:")
    print(f"  📁 Arquivo: {metadata['origem_pdf']['arquivo']}")
    print(f"  📃 Páginas: {len(metadata['origem_pdf']['paginas'])} páginas")
    print(f"  🔒 Hash: {metadata['hash_conteudo'][:16]}...")
    print(f"  🏷️ Parser: v{metadata['versao_parser']}")
    print(f"  🎯 Tokens: {metadata['tokens_estimados']}")

if __name__ == "__main__":
    explain_chunking_system()
    analyze_sample_chunk()

    print("\n" + "🎉" * 20)
    print("✅ Análise completa do sistema de chunking hierárquico!")
    print("📚 Para mais detalhes, consulte a documentação em docs/")
