from __future__ import annotations
import glob
import os
import statistics
from typing import Dict, List, Tuple

from src.config.settings import Settings
from .io_pdf import extract_text
from .normalize import clean_text
from .parse_norma import detect_structure
from .chunker import build_chunks, estimate_tokens
from . import regexes as RX


def _shorten(s: str, n: int = 180) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 3] + "..."


def analyze_folder(pdf_folder: str | None = None) -> Dict[str, any]:
    folder = pdf_folder or Settings.PDF_FOLDER
    pdfs = glob.glob(os.path.join(folder, "*.pdf"))
    if not pdfs:
        raise RuntimeError(f"Nenhum PDF encontrado em {folder}")

    reports: List[Dict[str, any]] = []
    all_chunk_tokens: List[int] = []
    regex_counts = {
        "ARTIGO": 0,
        "PARAGRAFO": 0,
        "INCISO": 0,
        "ALINEA": 0,
        "ITEM": 0,
        "CAPITULO": 0,
        "TITULO": 0,
        "SECAO": 0,
        "SUBSECAO": 0,
        "ANEXO": 0,
    }

    examples: Dict[str, List[str]] = {k: [] for k in regex_counts.keys()}

    for pdf in pdfs:
        try:
            raw, pages, _ = extract_text(pdf)
            text, pages2 = clean_text(raw, pages)
            nodes, heading = detect_structure(text)
            # regex sweep on first 200 lines
            for l in text.splitlines()[:2000]:
                ls = l.strip()
                if not ls:
                    continue
                if RX.ARTIGO.match(ls):
                    regex_counts["ARTIGO"] += 1
                    if len(examples["ARTIGO"]) < 5:
                        examples["ARTIGO"].append(_shorten(ls))
                if RX.PARAGRAFO.match(ls) or RX.PARAGRAFO_UNICO.match(ls):
                    regex_counts["PARAGRAFO"] += 1
                    if len(examples["PARAGRAFO"]) < 5:
                        examples["PARAGRAFO"].append(_shorten(ls))
                if (m := RX.INCISO.match(ls)) and RX.ROMAN.match(m.group(1)):
                    regex_counts["INCISO"] += 1
                    if len(examples["INCISO"]) < 5:
                        examples["INCISO"].append(_shorten(ls))
                if RX.ALINEA.match(ls):
                    regex_counts["ALINEA"] += 1
                    if len(examples["ALINEA"]) < 5:
                        examples["ALINEA"].append(_shorten(ls))
                if RX.ITEM.match(ls):
                    regex_counts["ITEM"] += 1
                    if len(examples["ITEM"]) < 5:
                        examples["ITEM"].append(_shorten(ls))
                if RX.CAPITULO.match(ls):
                    regex_counts["CAPITULO"] += 1
                    if len(examples["CAPITULO"]) < 5:
                        examples["CAPITULO"].append(_shorten(ls))
                if RX.TITULO.match(ls):
                    regex_counts["TITULO"] += 1
                    if len(examples["TITULO"]) < 5:
                        examples["TITULO"].append(_shorten(ls))
                if RX.SECAO.match(ls):
                    regex_counts["SECAO"] += 1
                    if len(examples["SECAO"]) < 5:
                        examples["SECAO"].append(_shorten(ls))
                if RX.SUBSECAO.match(ls):
                    regex_counts["SUBSECAO"] += 1
                    if len(examples["SUBSECAO"]) < 5:
                        examples["SUBSECAO"].append(_shorten(ls))
                if RX.ANEXO.match(ls):
                    regex_counts["ANEXO"] += 1
                    if len(examples["ANEXO"]) < 5:
                        examples["ANEXO"].append(_shorten(ls))

            # chunk to get token distribution
            from .metadata_pf import extract as meta_extract
            meta = meta_extract(text, heading, os.path.basename(pdf))
            chunks = build_chunks(nodes, text, meta, os.path.basename(pdf), [p.index for p in pages2])
            toks = [c.tokens_estimados for c in chunks]
            all_chunk_tokens.extend(toks)
            reports.append({
                "file": os.path.basename(pdf),
                "chunks": len(chunks),
                "tokens_min": min(toks) if toks else 0,
                "tokens_p50": statistics.median(toks) if toks else 0,
                "tokens_p90": int(statistics.quantiles(toks, n=10)[-1]) if len(toks) >= 10 else (max(toks) if toks else 0),
                "tokens_max": max(toks) if toks else 0,
            })
        except Exception as e:
            reports.append({"file": os.path.basename(pdf), "error": str(e)[:120]})

    summary = {
        "files": len(pdfs),
        "regex_counts": regex_counts,
        "examples": examples,
        "reports": reports,
    }

    if all_chunk_tokens:
        summary["tokens"] = {
            "min": min(all_chunk_tokens),
            "p50": statistics.median(all_chunk_tokens),
            "p90": int(statistics.quantiles(all_chunk_tokens, n=10)[-1]) if len(all_chunk_tokens) >= 10 else max(all_chunk_tokens),
            "max": max(all_chunk_tokens),
            "mean": int(statistics.mean(all_chunk_tokens)),
        }
        # heuristic suggestion: min near 30th percentile, max near 85-90th
        q = statistics.quantiles(all_chunk_tokens, n=10) if len(all_chunk_tokens) >= 10 else []
        suggested_min = int(q[2]) if q else max(200, min(all_chunk_tokens))
        suggested_max = int(q[8]) if q else max(800, max(all_chunk_tokens))
        summary["suggested_thresholds"] = {"TOKEN_TARGET_MIN": suggested_min, "TOKEN_TARGET_MAX": suggested_max}

    return summary


def write_markdown_report(out_path: str, data: Dict[str, any]) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Relatório de Calibração (SGP)\n\n")
        f.write(f"Arquivos analisados: {data.get('files', 0)}\n\n")
        if "tokens" in data:
            t = data["tokens"]
            f.write("## Distribuição de tokens por chunk\n\n")
            f.write(f"- min: {t['min']}\n- p50: {t['p50']}\n- p90: {t['p90']}\n- max: {t['max']}\n- mean: {t['mean']}\n\n")
        if "suggested_thresholds" in data:
            s = data["suggested_thresholds"]
            f.write("## Sugeridos\n\n")
            f.write(f"- TOKEN_TARGET_MIN: {s['TOKEN_TARGET_MIN']}\n- TOKEN_TARGET_MAX: {s['TOKEN_TARGET_MAX']}\n\n")
        f.write("## Cobertura de regex\n\n")
        for k, v in (data.get("regex_counts") or {}).items():
            f.write(f"- {k}: {v}\n")
        f.write("\n## Exemplos anonimizados\n\n")
        for k, arr in (data.get("examples") or {}).items():
            if not arr:
                continue
            f.write(f"### {k}\n\n")
            for ex in arr:
                f.write(f"- {ex}\n")
            f.write("\n")
        f.write("## Por arquivo\n\n")
        for r in data.get("reports", []):
            if "error" in r:
                f.write(f"- {r['file']}: erro: {r['error']}\n")
            else:
                f.write(f"- {r['file']}: chunks={r['chunks']} tokens(min/p50/p90/max)={r['tokens_min']}/{r['tokens_p50']}/{r['tokens_p90']}/{r['tokens_max']}\n")
