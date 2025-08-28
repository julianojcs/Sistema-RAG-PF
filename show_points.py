#!/usr/bin/env python3
"""
� Inspetor Completo do Banco Qdrant
Ferramenta única para visualizar estrutura, metadados e conteúdo dos pontos armazenados
Combina funcionalidades de inspeção, decodificação e visualização detalhada
"""

import sqlite3
import pickle
import base64
import json
import argparse
from pathlib import Path

def inspect_database_structure():
    """Inspeciona estrutura básica do banco"""
    db_path = Path("qdrantDB/collection/pf_normativos/storage.sqlite")

    if not db_path.exists():
        print("❌ Arquivo não encontrado:", db_path)
        return False

    print("🔍 Estrutura do Banco Qdrant")
    print("="*50)

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Tabelas: {[t[0] for t in tables]}")

        # Estrutura da tabela points
        cursor.execute("PRAGMA table_info(points);")
        columns = cursor.fetchall()
        print(f"🏗️ Colunas da tabela 'points':")
        for col in columns:
            print(f"   - {col[1]}: {col[2]}")

        # Estatísticas básicas
        cursor.execute("SELECT COUNT(*) FROM points;")
        total = cursor.fetchone()[0]
        print(f"📊 Total de pontos: {total:,}")

        # Tamanho do arquivo
        file_size = db_path.stat().st_size
        print(f"💾 Tamanho: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")

        # Metadados da coleção
        meta_path = Path("qdrantDB/meta.json")
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                if 'collections' in meta and 'pf_normativos' in meta['collections']:
                    config = meta['collections']['pf_normativos']
                    print(f"🧮 Dimensões do vetor: {config.get('vectors', {}).get('size', 'N/A')}")
                    print(f"🎯 Distância: {config.get('vectors', {}).get('distance', 'N/A')}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Erro ao inspecionar: {e}")
        return False

def analyze_chunk_structure():
    """Analisa estrutura detalhada dos chunks armazenados"""
    db_path = Path("qdrantDB/collection/pf_normativos/storage.sqlite")

    if not db_path.exists():
        print("❌ Arquivo não encontrado:", db_path)
        return False

    print("🧩 ESTRUTURA DETALHADA DOS CHUNKS")
    print("="*60)

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Análise de uma amostra de chunks
        cursor.execute("SELECT point FROM points LIMIT 10;")
        sample_points = cursor.fetchall()

        # Estruturas encontradas
        chunk_structures = {}
        payload_fields = {}
        metadata_fields = {}
        text_lengths = []
        vector_dimensions = []

        print("🔍 Analisando estrutura de 10 chunks de exemplo...")

        for i, (point_blob,) in enumerate(sample_points, 1):
            try:
                point_data = pickle.loads(point_blob)

                # Estrutura básica do ponto
                point_type = type(point_data).__name__
                chunk_structures[point_type] = chunk_structures.get(point_type, 0) + 1

                # Análise do payload
                if hasattr(point_data, 'payload') and point_data.payload:
                    for key in point_data.payload.keys():
                        payload_fields[key] = payload_fields.get(key, 0) + 1

                    # Análise específica do page_content (texto do chunk)
                    if 'page_content' in point_data.payload:
                        text = point_data.payload['page_content']
                        text_lengths.append(len(text))

                    # Análise dos metadados
                    if 'metadata' in point_data.payload:
                        metadata = point_data.payload['metadata']
                        if isinstance(metadata, dict):
                            for meta_key in metadata.keys():
                                metadata_fields[meta_key] = metadata_fields.get(meta_key, 0) + 1

                # Análise do vetor
                if hasattr(point_data, 'vector') and point_data.vector:
                    if isinstance(point_data.vector, dict) and 'vector' in point_data.vector:
                        vector = point_data.vector['vector']
                    elif isinstance(point_data.vector, list):
                        vector = point_data.vector
                    else:
                        vector = point_data.vector

                    if isinstance(vector, list):
                        vector_dimensions.append(len(vector))

            except Exception as e:
                print(f"  ⚠️ Erro no chunk {i}: {e}")

        # Relatório da estrutura
        print(f"\n📊 ESTRUTURA DOS CHUNKS:")
        print(f"="*40)

        print(f"🏗️ Tipos de pontos encontrados:")
        for ptype, count in chunk_structures.items():
            print(f"  - {ptype}: {count} ocorrências")

        print(f"\n📋 Campos do payload (nível raiz):")
        for field, count in sorted(payload_fields.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {field}: {count}/10 chunks")

        print(f"\n🏷️ Campos dos metadados:")
        for field, count in sorted(metadata_fields.items(), key=lambda x: x[1], reverse=True)[:15]:
            print(f"  - {field}: {count}/10 chunks")
        if len(metadata_fields) > 15:
            print(f"  ... e mais {len(metadata_fields) - 15} campos")

        if text_lengths:
            avg_text = sum(text_lengths) / len(text_lengths)
            print(f"\n📄 Tamanho do texto (page_content):")
            print(f"  - Média: {avg_text:.0f} caracteres")
            print(f"  - Mínimo: {min(text_lengths)} caracteres")
            print(f"  - Máximo: {max(text_lengths)} caracteres")

        if vector_dimensions:
            print(f"\n🔢 Dimensões dos vetores:")
            print(f"  - Dimensões: {vector_dimensions[0]} (todos iguais)")
            print(f"  - Tipo: embeddings densos (float32)")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        return False

def show_chunk_examples(full_text=False):
    """Mostra exemplos detalhados de chunks com diferentes estruturas"""
    db_path = Path("qdrantDB/collection/pf_normativos/storage.sqlite")

    if not db_path.exists():
        print("❌ Arquivo não encontrado:", db_path)
        return False

    print("📋 EXEMPLOS DE CHUNKS ARMAZENADOS")
    if full_text:
        print("📄 Modo: TEXTO COMPLETO")
    else:
        print("📄 Modo: TEXTO TRUNCADO (use --full-text para ver completo)")
    print("="*50)

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Buscar chunks com diferentes níveis hierárquicos
        cursor.execute("SELECT id, point FROM points LIMIT 3;")
        examples = cursor.fetchall()

        for i, (encoded_id, point_blob) in enumerate(examples, 1):
            print(f"\n🧩 CHUNK {i}")
            print("-" * 30)

            # Decodificar
            decoded_id = pickle.loads(base64.b64decode(encoded_id))
            point_data = pickle.loads(point_blob)

            print(f"🆔 ID: {decoded_id}")

            # Estrutura do chunk
            if hasattr(point_data, 'payload') and point_data.payload:
                payload = point_data.payload

                # Texto do chunk
                if 'page_content' in payload:
                    text = payload['page_content']
                    if full_text:
                        print(f"📄 Texto completo:\n{text}")
                    else:
                        preview = text[:150] + "..." if len(text) > 150 else text
                        print(f"📄 Texto: {preview}")
                    print(f"    Tamanho: {len(text)} caracteres")

                # Metadados hierárquicos
                if 'metadata' in payload and isinstance(payload['metadata'], dict):
                    metadata = payload['metadata']

                    # Informações hierárquicas
                    if 'nivel' in metadata:
                        print(f"🏗️ Nível: {metadata['nivel']}")
                    if 'rotulo' in metadata:
                        print(f"🏷️ Rótulo: {metadata['rotulo']}")
                    if 'caminho_hierarquico' in metadata:
                        print(f"🗂️ Caminho: {metadata['caminho_hierarquico']}")

                    # Informações do documento
                    if 'origem_pdf' in metadata:
                        origem = metadata['origem_pdf']
                        if isinstance(origem, dict) and 'arquivo' in origem:
                            print(f"📁 Arquivo: {origem['arquivo']}")
                            if 'paginas' in origem:
                                print(f"📄 Páginas: {len(origem['paginas'])} páginas")

                    # Tokens e tamanho
                    if 'tokens_estimados' in metadata:
                        print(f"🔤 Tokens: {metadata['tokens_estimados']}")

            # Vetor
            if hasattr(point_data, 'vector'):
                if isinstance(point_data.vector, dict) and 'vector' in point_data.vector:
                    vector = point_data.vector['vector']
                elif isinstance(point_data.vector, list):
                    vector = point_data.vector
                else:
                    vector = point_data.vector

                if isinstance(vector, list):
                    print(f"🔢 Embedding: {len(vector)}D [{vector[0]:.6f}, {vector[1]:.6f}, ...]")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def show_point_details(limit=2, full_text=False):
    """Mostra detalhes completos de alguns pontos"""

    db_path = Path("qdrantDB/collection/pf_normativos/storage.sqlite")

    if not db_path.exists():
        print("❌ Arquivo não encontrado:", db_path)
        return

    print("📊 Visualizando conteúdo detalhado dos pontos...")
    if full_text:
        print("📄 Modo: TEXTO COMPLETO")
    else:
        print("📄 Modo: TEXTO TRUNCADO (use --full-text para ver completo)")
    print("="*70)

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Pegar alguns registros para análise detalhada
        cursor.execute("SELECT id, point FROM points LIMIT ?;", (limit,))
        records = cursor.fetchall()

        for i, (encoded_id, point_blob) in enumerate(records, 1):
            print(f"\n🔍 PONTO {i}")
            print("="*50)

            # Decodificar ID
            decoded_id = pickle.loads(base64.b64decode(encoded_id))
            print(f"🆔 ID: {decoded_id}")

            # Decodificar ponto completo
            point_data = pickle.loads(point_blob)

            print(f"📝 Tipo: {type(point_data).__name__}")
            print(f"🆔 Point ID: {point_data.id}")

            # Mostrar vetor (apenas dimensões por ser muito grande)
            if hasattr(point_data, 'vector') and point_data.vector:
                if isinstance(point_data.vector, dict) and 'vector' in point_data.vector:
                    vector = point_data.vector['vector']
                elif isinstance(point_data.vector, list):
                    vector = point_data.vector
                else:
                    vector = point_data.vector

                if isinstance(vector, list):
                    print(f"🔢 Vetor: {len(vector)} dimensões")
                    print(f"   Primeiros 5 valores: {vector[:5]}")
                    print(f"   Últimos 5 valores: {vector[-5:]}")
                else:
                    print(f"🔢 Vetor: {type(vector)}")

            # Mostrar payload (metadados)
            if hasattr(point_data, 'payload') and point_data.payload:
                print(f"\n📋 Payload (metadados):")
                payload = point_data.payload

                for key, value in payload.items():
                    if key == 'page_content' and isinstance(value, str):
                        # Mostrar texto do chunk
                        if full_text:
                            print(f"  📄 {key} (completo):\n{value}")
                        else:
                            preview = value[:200] + "..." if len(value) > 200 else value
                            print(f"  📄 {key}: {preview}")
                    elif key == 'chunk_text' and isinstance(value, str):
                        # Mostrar apenas início do texto (campo legado)
                        if full_text:
                            print(f"  📄 {key} (completo):\n{value}")
                        else:
                            preview = value[:200] + "..." if len(value) > 200 else value
                            print(f"  📄 {key}: {preview}")
                    elif key == 'metadata' and isinstance(value, dict):
                        print(f"  📊 {key}:")
                        for meta_key, meta_value in value.items():
                            if isinstance(meta_value, str) and len(meta_value) > 100 and not full_text:
                                preview = meta_value[:100] + "..."
                                print(f"    - {meta_key}: {preview}")
                            else:
                                print(f"    - {meta_key}: {meta_value}")
                    else:
                        if isinstance(value, str) and len(value) > 200 and not full_text:
                            preview = value[:200] + "..."
                            print(f"  🏷️ {key}: {preview}")
                        else:
                            print(f"  🏷️ {key}: {value}")

            print(f"\n💾 Tamanho total: {len(point_blob):,} bytes")

        # Mostrar estatísticas dos payloads
        print(f"\n📈 ESTATÍSTICAS GERAIS")
        print("="*30)

        # Contar campos mais comuns nos payloads
        cursor.execute("SELECT point FROM points LIMIT 100;")  # Amostra de 100
        sample_records = cursor.fetchall()

        payload_keys = {}
        for point_blob, in sample_records:
            try:
                point_data = pickle.loads(point_blob)
                if hasattr(point_data, 'payload') and point_data.payload:
                    for key in point_data.payload.keys():
                        payload_keys[key] = payload_keys.get(key, 0) + 1
            except:
                continue

        print(f"🏷️ Campos mais comuns nos payloads (amostra de 100):")
        for key, count in sorted(payload_keys.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {key}: {count} ocorrências")

        conn.close()

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspetor Completo do Banco Qdrant")
    parser.add_argument("--mode", choices=["structure", "details", "chunks", "examples", "all"], default="all",
                       help="Modo: structure (estrutura), details (pontos), chunks (análise chunks), examples (exemplos), all (tudo)")
    parser.add_argument("--limit", type=int, default=2,
                       help="Número de pontos para mostrar em detalhes (padrão: 2)")
    parser.add_argument("--full-text", action="store_true",
                       help="Mostrar texto completo dos chunks sem truncamento")

    args = parser.parse_args()

    if args.mode in ["structure", "all"]:
        if not inspect_database_structure():
            exit(1)

    if args.mode in ["chunks", "all"]:
        if args.mode == "all":
            print("\n" + "="*70)
        analyze_chunk_structure()

    if args.mode in ["examples", "all"]:
        if args.mode in ["all", "chunks"]:
            print("\n" + "="*70)
        show_chunk_examples(full_text=args.full_text)

    if args.mode in ["details", "all"]:
        if args.mode == "all":
            print("\n" + "="*70)
        show_point_details(args.limit, full_text=args.full_text)