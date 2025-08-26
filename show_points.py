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

def show_point_details(limit=2):
    """Mostra detalhes completos de alguns pontos"""

    db_path = Path("qdrantDB/collection/pf_normativos/storage.sqlite")

    if not db_path.exists():
        print("❌ Arquivo não encontrado:", db_path)
        return

    print("📊 Visualizando conteúdo detalhado dos pontos...")
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
                    if key == 'chunk_text' and isinstance(value, str):
                        # Mostrar apenas início do texto
                        preview = value[:200] + "..." if len(value) > 200 else value
                        print(f"  📄 {key}: {preview}")
                    elif key == 'metadata' and isinstance(value, dict):
                        print(f"  📊 {key}:")
                        for meta_key, meta_value in value.items():
                            if isinstance(meta_value, str) and len(meta_value) > 100:
                                preview = meta_value[:100] + "..."
                                print(f"    - {meta_key}: {preview}")
                            else:
                                print(f"    - {meta_key}: {meta_value}")
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
    parser.add_argument("--mode", choices=["structure", "details", "all"], default="all",
                       help="Modo de inspeção: structure (estrutura), details (pontos), all (ambos)")
    parser.add_argument("--limit", type=int, default=2,
                       help="Número de pontos para mostrar em detalhes (padrão: 2)")

    args = parser.parse_args()

    if args.mode in ["structure", "all"]:
        if not inspect_database_structure():
            exit(1)

    if args.mode in ["details", "all"]:
        if args.mode == "all":
            print("\n" + "="*70)
        show_point_details(args.limit)
