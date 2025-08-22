from __future__ import annotations
import re
from typing import List, Tuple
from .types import PDFPage
from .io_pdf import get_layout_extras

HIFEN_LINHA = re.compile(r"(\w+)-\n(\w+)")
ESPACOS = re.compile(r"[ \t]+")


def _remove_headers_footers(pages: List[PDFPage]) -> List[PDFPage]:
    """Remove headers/footers repetitivos por heurística simples."""
    # Coleta as primeiras e últimas linhas de cada página, usando leitura já ordenada
    # Heurística com sinais de layout: não remover cabeçalhos estruturais (Capítulo/Seção/Título)
    heads = {}
    foots = {}
    for p in pages:
        lines = [l.strip() for l in p.text.splitlines() if l.strip()]
        if not lines:
            continue
        head = lines[0]
        tail = lines[-1]
        heads[head] = heads.get(head, 0) + 1
        foots[tail] = foots.get(tail, 0) + 1

    # Considera header/footer quando aparece em >= 50% das páginas e não parece rubrica de capítulo
    def is_noise(line: str) -> bool:
        if not line:
            return False
        upper = line.upper()
        # Não tratar como ruído se parecer seção estruturante
        if upper.startswith("CAPÍTULO") or upper.startswith("CAPITULO") or upper.startswith("SEÇÃO") or upper.startswith("SECAO") or upper.startswith("TÍTULO") or upper.startswith("TITULO"):
            return False
        return True

    # Seja mais conservador com headers; mais permissivo com footers
    head_threshold = max(3, int(0.7 * max(heads.values()) if heads else 0))
    foot_threshold = max(2, int(0.5 * max(foots.values()) if foots else 0))

    common_heads = {k for k, v in heads.items() if v >= head_threshold and is_noise(k)}
    common_foots = {k for k, v in foots.items() if v >= foot_threshold and is_noise(k)}

    cleaned: List[PDFPage] = []
    for p in pages:
        lines = p.text.splitlines()
        if lines and lines[0].strip() in common_heads:
            lines = lines[1:]
        if lines and lines[-1].strip() in common_foots:
            lines = lines[:-1]
        cleaned.append(PDFPage(index=p.index, text="\n".join(lines)))
    return cleaned


def clean_text(raw_text: str, pages: List[PDFPage]) -> Tuple[str, List[PDFPage]]:
    """
    Normaliza texto: corrige hifenização, remove headers/footers repetidos, normaliza espaços.
    Retorna texto limpo e páginas limpas.
    """
    # Atualiza páginas
    pages2 = _remove_headers_footers(pages)

    # Corrige hifenização em cada página
    fixed_pages: List[PDFPage] = []
    for p in pages2:
        t = HIFEN_LINHA.sub(r"\1\2", p.text)
        t = ESPACOS.sub(" ", t)
        fixed_pages.append(PDFPage(index=p.index, text=t))

    full = "\n".join(p.text for p in fixed_pages)
    # Unifica quebras indevidas de parágrafo dentro do mesmo dispositivo (heurística leve)
    full = re.sub(r"(Art\.|§|[IVXLCDM]+|[a-z]\))\s*\n+(?=\S)", r"\1 ", full)

    return full, fixed_pages
