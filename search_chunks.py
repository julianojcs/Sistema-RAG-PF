#!/usr/bin/env python3
"""
🔍 Buscador Específico de Chunks no Qdrant
Permite buscar chunks por critérios específicos (nível, documento, etc.)
"""

import sqlite3
import pickle
import base64
import json
import argparse
from pathlib import Path

def search_chunks_by_criteria(nivel=None, documento=None, rotulo=None, limit=10, full_text=False):
    """Busca chunks por critérios específicos"""
    db_path = Path("qdrantDB/collection/pf_normativos/storage.sqlite")

    if not db_path.exists():
        print("❌ Arquivo não encontrado:", db_path)
        return

    print(f"🔍 BUSCA DE CHUNKS")
    print("="*50)
    print(f"Filtros aplicados:")
    if nivel: print(f"  📊 Nível: {nivel}")
    if documento: print(f"  📄 Documento: {documento}")
    if rotulo: print(f"  🏷️ Rótulo: {rotulo}")
    print(f"  📋 Limite: {limit} resultados")
    if full_text:
        print(f"  📄 Modo: TEXTO COMPLETO")
    else:
        print(f"  📄 Modo: TEXTO TRUNCADO (use --full-text para ver completo)")
    print()

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Buscar todos os pontos para filtrar
        cursor.execute("SELECT id, point FROM points;")
        all_points = cursor.fetchall()

        found_chunks = []

        for encoded_id, point_blob in all_points:
            try:
                point_data = pickle.loads(point_blob)

                if hasattr(point_data, 'payload') and point_data.payload:
                    metadata = point_data.payload.get('metadata', {})

                    # Aplicar filtros
                    match = True

                    if nivel and metadata.get('nivel') != nivel:
                        match = False

                    if documento and documento.lower() not in metadata.get('origem_pdf', {}).get('arquivo', '').lower():
                        match = False

                    if rotulo and metadata.get('rotulo') != rotulo:
                        match = False

                    if match:
                        decoded_id = pickle.loads(base64.b64decode(encoded_id))
                        found_chunks.append({
                            'id': decoded_id,
                            'text': point_data.payload.get('page_content', ''),
                            'metadata': metadata
                        })

                        if len(found_chunks) >= limit:
                            break

            except Exception:
                continue

        # Mostrar resultados
        print(f"📊 Encontrados: {len(found_chunks)} chunks")
        print("="*50)

        for i, chunk in enumerate(found_chunks, 1):
            print(f"\n🧩 CHUNK {i}")
            print("-" * 30)
            print(f"🆔 ID: {chunk['id']}")

            metadata = chunk['metadata']
            if 'nivel' in metadata:
                print(f"📊 Nível: {metadata['nivel']}")
            if 'rotulo' in metadata:
                print(f"🏷️ Rótulo: {metadata['rotulo']}")
            if 'origem_pdf' in metadata:
                arquivo = metadata['origem_pdf'].get('arquivo', 'N/A')
                print(f"📁 Arquivo: {arquivo}")
            if 'tokens_estimados' in metadata:
                print(f"🔤 Tokens: {metadata['tokens_estimados']}")

            # Texto
            text = chunk['text']
            if full_text:
                print(f"📄 Texto completo:\n{text}")
            else:
                preview = text[:100] + "..." if len(text) > 100 else text
                print(f"📄 Texto: {preview}")
            print(f"    Tamanho: {len(text)} caracteres")

        conn.close()

    except Exception as e:
        print(f"❌ Erro na busca: {e}")

def list_available_values():
    """Lista valores disponíveis para filtros"""
    db_path = Path("qdrantDB/collection/pf_normativos/storage.sqlite")

    if not db_path.exists():
        print("❌ Arquivo não encontrado:", db_path)
        return

    print("📋 VALORES DISPONÍVEIS PARA FILTROS")
    print("="*50)

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Analisar amostra
        cursor.execute("SELECT point FROM points LIMIT 100;")
        sample_points = cursor.fetchall()

        niveis = set()
        documentos = set()
        rotulos = set()

        for point_blob, in sample_points:
            try:
                point_data = pickle.loads(point_blob)

                if hasattr(point_data, 'payload') and point_data.payload:
                    metadata = point_data.payload.get('metadata', {})

                    if 'nivel' in metadata:
                        niveis.add(metadata['nivel'])

                    if 'origem_pdf' in metadata and 'arquivo' in metadata['origem_pdf']:
                        arquivo = metadata['origem_pdf']['arquivo']
                        # Extrair nome do arquivo
                        nome_arquivo = arquivo.split('\\')[-1].split('.')[0]
                        documentos.add(nome_arquivo)

                    if 'rotulo' in metadata:
                        rotulos.add(metadata['rotulo'])

            except Exception:
                continue

        print(f"📊 Níveis hierárquicos disponíveis ({len(niveis)}):")
        for nivel in sorted(niveis):
            print(f"  - {nivel}")

        print(f"\n📄 Documentos disponíveis ({len(documentos)}):")
        for doc in sorted(list(documentos)[:10]):  # Mostrar apenas 10
            print(f"  - {doc}")
        if len(documentos) > 10:
            print(f"  ... e mais {len(documentos) - 10} documentos")

        print(f"\n🏷️ Rótulos mais comuns ({min(10, len(rotulos))}):")
        rotulos_sorted = sorted(list(rotulos))[:10]
        for rotulo in rotulos_sorted:
            print(f"  - {rotulo}")

        conn.close()

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Buscar chunks específicos no Qdrant")
    parser.add_argument("--nivel", help="Filtrar por nível (artigo, paragrafo, inciso, alinea)")
    parser.add_argument("--documento", help="Filtrar por documento (nome parcial)")
    parser.add_argument("--rotulo", help="Filtrar por rótulo exato")
    parser.add_argument("--limit", type=int, default=10, help="Limite de resultados (padrão: 10)")
    parser.add_argument("--full-text", action="store_true", help="Mostrar texto completo dos chunks sem truncamento")
    parser.add_argument("--list-values", action="store_true", help="Listar valores disponíveis para filtros")

    args = parser.parse_args()

    if args.list_values:
        list_available_values()
    else:
        search_chunks_by_criteria(
            nivel=args.nivel,
            documento=args.documento,
            rotulo=args.rotulo,
            limit=args.limit,
            full_text=args.full_text
        )
