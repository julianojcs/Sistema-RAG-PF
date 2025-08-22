from __future__ import annotations
import glob
import json
import os
from typing import List

from src.config.settings import Settings
from .io_pdf import extract_text
from .normalize import clean_text
from .parse_norma import detect_structure
from .metadata_pf import extract as meta_extract
from .chunker import build_chunks
from .embed_index import Indexer, SbertEmbeddings
from .types import PFDocumentMetadata
from .export_jsonl import export_chunks_jsonl
from .calibrate import analyze_folder, write_markdown_report


def ingest_index(pdf_folder: str | None = None, index_path: str | None = None) -> None:
    pdf_folder = pdf_folder or Settings.PDF_FOLDER
    index_path = index_path or Settings.FAISS_DB_PATH
    pdfs = glob.glob(os.path.join(pdf_folder, "*.pdf"))
    if not pdfs:
        raise RuntimeError(f"Nenhum PDF encontrado em {pdf_folder}. Certifique-se de colocar os arquivos em 'SGP/'")

    all_chunks = []
    for pdf in pdfs:
        raw, pages, ocr = extract_text(pdf)
        text, pages2 = clean_text(raw, pages)
        nodes, heading = detect_structure(text)
        meta = meta_extract(text, heading, os.path.basename(pdf))
        chunks = build_chunks(nodes, text, meta, os.path.basename(pdf), [p.index for p in pages2])
        all_chunks.extend(chunks)

    indexer = Indexer()
    db = indexer.build_faiss(all_chunks)
    indexer.save_faiss(db, index_path)
    # Export JSONL (auditoria)
    from src.config.settings import Settings
    if Settings.EXPORT_CHUNKS_JSONL:
        msg = export_chunks_jsonl(all_chunks, Settings.CHUNKS_JSONL_PATH)
        print("📝", msg)


def query_cli(question: str, top_k: int = 5) -> List[dict]:
    from .search import Searcher
    from langchain_community.vectorstores import FAISS
    from langchain_ollama import OllamaEmbeddings

    if Settings.EMBEDDING_BACKEND == "sbert":
        embeddings = SbertEmbeddings()
    else:
        embeddings = OllamaEmbeddings(model=Settings.EMBEDDING_MODEL)

    db = FAISS.load_local(Settings.FAISS_DB_PATH, embeddings, allow_dangerous_deserialization=True)
    searcher = Searcher(db)
    docs = searcher.query(question, top_k=top_k)
    results = []
    for d in docs:
        md = d.metadata
        results.append({
            "anchor_id": md.get("anchor_id"),
            "breadcrumb": md.get("breadcrumb"),
            "nivel": md.get("nivel"),
            "rotulo": md.get("rotulo"),
            "texto": d.page_content[:400] + ("..." if len(d.page_content) > 400 else ""),
        })
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline PF RAG - ingestão e busca (offline por padrão)")
    parser.add_argument("command", choices=["ingest", "query", "calibrate"], help="Comando a executar")
    parser.add_argument("--q", dest="query_text", help="Consulta para buscar")
    args = parser.parse_args()

    if args.command == "ingest":
        ingest_index()
        print("✅ Índice FAISS atualizado em", Settings.FAISS_DB_PATH)
    elif args.command == "query":
        if not args.query_text:
            raise SystemExit("Informe --q com a consulta")
        res = query_cli(args.query_text)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.command == "calibrate":
        data = analyze_folder()
        out = os.path.join("docs", "sgp_calibration.md")
        write_markdown_report(out, data)
        print("✅ Relatório gerado em", out)
