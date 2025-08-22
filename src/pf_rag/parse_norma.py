from __future__ import annotations
import hashlib
import re
from typing import List, Tuple, Optional
from .types import Node, HeadingBlock
from . import regexes as RX


def _find_heading_blocks(text: str) -> HeadingBlock:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    ementa = None
    preambulo = None
    considerandos: List[str] = []

    # Ementa: heurística nas primeiras ~20 linhas
    head_sample = "\n".join(lines[:20])
    m = RX.EMENTA_HEUR.search(head_sample)
    if m:
        # Pega a linha completa da ementa
        for l in lines[:20]:
            if RX.EMENTA_HEUR.search(l):
                ementa = l
                break

    # Preâmbulo
    m2 = RX.PREAMBULO.search(text[:2000])
    if m2:
        s = m2.start()
        e = min(len(text), s + 600)
        preambulo = text[s:e].split("\n\n")[0].strip()

    # Considerandos
    for l in lines[:200]:
        if l.lower().startswith("considerando"):
            considerandos.append(l)

    return HeadingBlock(ementa=ementa, preambulo=preambulo, considerandos=considerandos)


def _node_id(parts: List[str]) -> str:
    base = "-".join(parts)
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def detect_structure(text: str) -> Tuple[List[Node], HeadingBlock]:
    """
    Detecta estrutura hierárquica (macro e dispositivos) e retorna lista de nós com offsets.
    Estratégia: varredura linha a linha com pilha de níveis.
    """
    heading = _find_heading_blocks(text)

    nodes: List[Node] = []
    stack: List[Node] = []

    def push(nivel: str, rotulo: str, start: int, title: Optional[str] = None):
        nid = _node_id([nivel, rotulo, str(start)])
        parent_id = stack[-1].id if stack else None
        node = Node(id=nid, nivel=nivel, rotulo=rotulo, start=start, end=start, parent_id=parent_id, title=title)
        if stack:
            stack[-1].children.append(node)
        nodes.append(node)
        stack.append(node)

    def close_until(levels: List[str], pos: int):
        while stack and stack[-1].nivel not in levels:
            stack[-1].end = pos
            stack.pop()

    # início com um root implícito
    push("documento", "ROOT", 0, title="Documento")

    offset = 0
    for line in text.splitlines(True):  # keepends
        l = line.strip()
        if not l:
            offset += len(line)
            continue

        # Macro-estruturas
        for rx, nivel in [
            (RX.PARTE_LIVRO, "parte"),
            (RX.TITULO, "titulo"),
            (RX.CAPITULO, "capitulo"),
            (RX.SECAO, "secao"),
            (RX.SUBSECAO, "subsecao"),
            (RX.ANEXO, "anexo"),
        ]:
            m = rx.match(l)
            if m:
                rot = (m.group(0) or l).strip()
                close_until(["documento"], offset)
                push(nivel, rot, offset)
                break
        else:
            # Dispositivos
            m = RX.ARTIGO.match(l)
            if m:
                rot = f"Art. {m.group(1)}"
                close_until(["documento", "parte", "livro", "titulo", "capitulo", "secao", "subsecao"], offset)
                push("artigo", rot, offset)
                offset += len(line)
                continue

            m = RX.PARAGRAFO.match(l) or RX.PARAGRAFO_UNICO.match(l)
            if m:
                rot = m.group(1) if m.re is RX.PARAGRAFO else "Parágrafo único"
                close_until(["artigo"], offset)
                push("paragrafo", rot, offset)
                offset += len(line)
                continue

            m = RX.INCISO.match(l)
            if m and RX.ROMAN.match(m.group(1)):
                rot = m.group(1)
                close_until(["paragrafo", "artigo"], offset)
                push("inciso", rot, offset)
                offset += len(line)
                continue

            m = RX.ALINEA.match(l)
            if m:
                rot = f"{m.group(1)})"
                close_until(["inciso", "paragrafo", "artigo"], offset)
                push("alinea", rot, offset)
                offset += len(line)
                continue

            m = RX.ITEM.match(l)
            if m:
                rot = m.group(1)
                close_until(["alinea", "inciso", "paragrafo", "artigo"], offset)
                push("item", rot, offset)
                offset += len(line)
                continue

        offset += len(line)

    # Fecha todos no final
    while stack:
        stack[-1].end = len(text)
        stack.pop()

    return nodes, heading
