#!/usr/bin/env python3
"""
Script para desserializar e analisar o conteúdo do arquivo storage.sqlite-x-points-1-point.bin
"""

import pickle
import json
from pathlib import Path

def deserialize_point_file(file_path):
    """
    Desserializa o arquivo de ponto do Qdrant e exibe seu conteúdo
    """
    try:
        with open(file_path, 'rb') as f:
            point_data = pickle.load(f)

        print("=" * 80)
        print("CONTEÚDO DESSERIALIZADO DO ARQUIVO QDRANT POINT")
        print("=" * 80)

        # Informações básicas do ponto
        print(f"\nTipo do objeto: {type(point_data)}")
        print(f"ID do ponto: {point_data.id}")

        # Informações do vetor
        if hasattr(point_data, 'vector') and point_data.vector:
            print(f"\nDimensões do vetor: {len(point_data.vector)}")
            print(f"Primeiros 10 valores do vetor: {point_data.vector[:10]}")
            print(f"Últimos 10 valores do vetor: {point_data.vector[-10:]}")

        # Payload (metadados)
        if hasattr(point_data, 'payload') and point_data.payload:
            print("\n" + "=" * 50)
            print("PAYLOAD (METADADOS DO DOCUMENTO)")
            print("=" * 50)

            # Conteúdo da página
            if 'page_content' in point_data.payload:
                print(f"\nConteúdo da página: '{point_data.payload['page_content']}'")

            # Metadados
            if 'metadata' in point_data.payload:
                metadata = point_data.payload['metadata']
                print(f"\nMetadados do documento:")
                print(f"  - ID do documento: {metadata.get('doc_id', 'N/A')}")
                print(f"  - ID da âncora: {metadata.get('anchor_id', 'N/A')}")
                print(f"  - Nível: {metadata.get('nivel', 'N/A')}")
                print(f"  - Rótulo: {metadata.get('rotulo', 'N/A')}")
                print(f"  - Ordinal normalizado: {metadata.get('ordinal_normalizado', 'N/A')}")

                # Informações do PDF de origem
                if 'origem_pdf' in metadata:
                    origem = metadata['origem_pdf']
                    print(f"\n  Origem PDF:")
                    print(f"    - Arquivo: {origem.get('arquivo', 'N/A')}")
                    print(f"    - Páginas: {origem.get('paginas', 'N/A')}")

                # Outras informações importantes
                print(f"\n  Informações adicionais:")
                print(f"    - Hash do conteúdo: {metadata.get('hash_conteudo', 'N/A')}")
                print(f"    - Versão do parser: {metadata.get('versao_parser', 'N/A')}")
                print(f"    - Órgão: {metadata.get('orgao', 'N/A')}")
                print(f"    - Sigla do órgão: {metadata.get('sigla_orgao', 'N/A')}")
                print(f"    - Âmbito: {metadata.get('ambito', 'N/A')}")
                print(f"    - País: {metadata.get('pais', 'N/A')}")
                print(f"    - Data de publicação: {metadata.get('data_publicacao', 'N/A')}")
                print(f"    - Situação: {metadata.get('situacao', 'N/A')}")
                print(f"    - Fonte de publicação: {metadata.get('fonte_publicacao', 'N/A')}")
                print(f"    - Ementa: {metadata.get('ementa', 'N/A')}")
                print(f"    - Tokens estimados: {metadata.get('tokens_estimados', 'N/A')}")

        print("\n" + "=" * 80)
        print("ESTRUTURA COMPLETA EM JSON")
        print("=" * 80)

        # Converter para dict para visualização JSON
        point_dict = {
            'id': point_data.id,
            'vector_dimensions': len(point_data.vector) if hasattr(point_data, 'vector') and point_data.vector else 0,
            'vector_sample': point_data.vector[:5] if hasattr(point_data, 'vector') and point_data.vector else [],
            'payload': point_data.payload if hasattr(point_data, 'payload') else {}
        }

        print(json.dumps(point_dict, indent=2, ensure_ascii=False, default=str))

        return point_data

    except Exception as e:
        print(f"Erro ao desserializar o arquivo: {e}")
        return None

def main():
    file_path = Path("c:/Users/juliano.jcs/RAG/qdrantDB/collection/pf_normativos/storage.sqlite-x-points-1-point.bin")

    if not file_path.exists():
        print(f"Arquivo não encontrado: {file_path}")
        return

    print(f"Desserializando arquivo: {file_path}")
    point_data = deserialize_point_file(file_path)

    if point_data:
        print(f"\n✅ Desserialização concluída com sucesso!")
        print(f"📄 Este é um ponto do Qdrant contendo dados sobre: '{point_data.payload.get('page_content', 'N/A')}'")
        print(f"📋 Documento: {point_data.payload.get('metadata', {}).get('origem_pdf', {}).get('arquivo', 'N/A')}")

if __name__ == "__main__":
    main()
