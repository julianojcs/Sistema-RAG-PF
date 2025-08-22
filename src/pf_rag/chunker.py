from __future__ import annotations
import hashlib
from typing import List, Dict, Any, Optional
from .types import Node, Chunk, PFDocumentMetadata
from .io_pdf import get_layout_extras
from src.config.settings import Settings


def estimate_tokens(text: str) -> int:
    # Aproximação simples: 1 token ~ 4 chars em pt-BR (ajustável)
    return max(1, int(len(text) / 4))


def slugify(*parts: str) -> str:
    s = "-".join(parts)
    s = s.lower()
    s = s.replace(" ", "-")
    s = s.replace("/", "-")
    s = s.replace("º", "o").replace("°", "o")
    s = "".join(ch for ch in s if ch.isalnum() or ch in "-_")
    return s


HIER_ORDER = [
    "documento",
    "parte",
    "livro",
    "titulo",
    "capitulo",
    "secao",
    "subsecao",
    "artigo",
    "paragrafo",
    "inciso",
    "alinea",
    "item",
    "anexo",
]


def _ordinal_normalizado(nivel: str, rotulo: str) -> str:
    import re
    if nivel == "artigo":
        m = re.search(r"(\d+)", rotulo)
        return m.group(1) if m else rotulo
    if nivel == "paragrafo":
        m = re.search(r"(\d+)", rotulo)
        return m.group(1) if m else "unico" if "único" in rotulo.lower() or "unico" in rotulo.lower() else rotulo
    if nivel in {"inciso", "alinea", "item"}:
        return rotulo.strip(".) ")
    return rotulo


def _breadcrumb(node: Node, id_to_node: Dict[str, Node]) -> List[Dict[str, str]]:
    path = []
    cur = node
    while cur:
        path.append({"nivel": cur.nivel, "rotulo": cur.rotulo})
        cur = id_to_node.get(cur.parent_id) if cur.parent_id else None
    path.reverse()
    # Inclui o próprio nó e remove o nível raiz 'documento'
    return [p for p in path if p["nivel"] != "documento"]


def build_chunks(nodes: List[Node], text: str, meta: PFDocumentMetadata, pdf_file: str, pages: List[int]) -> List[Chunk]:
    id_to_node = {n.id: n for n in nodes}
    # Layout extras (Docling) para evitar cortes ruins e enriquecer metadados
    layout = get_layout_extras(pdf_file)
    layout_map = layout.get("layout_blocks", {}) if isinstance(layout, dict) else {}

    # lista linear por ordem e gerar chunks por granularidade, respeitando limites
    level_priority = {lvl: i for i, lvl in enumerate(HIER_ORDER)}
    sorted_nodes = [n for n in nodes if n.nivel in level_priority]
    sorted_nodes.sort(key=lambda n: (n.start, level_priority[n.nivel]))

    chunks: List[Chunk] = []
    prev_by_parent: Dict[str, Optional[str]] = {}

    for n in sorted_nodes:
        if n.nivel == "documento":
            continue
        content = text[n.start:n.end].strip()
        if not content:
            continue
        tokens = estimate_tokens(content)
        if tokens > Settings.TOKEN_TARGET_MAX and n.children:
            # dividir em filhos imediatos
            for c in n.children:
                c_text = text[c.start:c.end].strip()
                if not c_text:
                    continue
                c_tokens = estimate_tokens(c_text)
                # Evitar cortar tabelas ao meio: se um bloco Table cai no meio do range pai, manter inteiro no filho corrente
                layout_refs = []
                try:
                    pg_blocks = sum((layout_map.get(pi, []) for pi in pages), [])
                    for blk in pg_blocks:
                        if blk.get("type") == "table":
                            if not (blk["end"] <= c.start or blk["start"] >= c.end):
                                layout_refs.append(blk)
                except Exception:
                    pass
                anchor = slugify(meta.doc_id, n.nivel, _ordinal_normalizado(n.nivel, n.rotulo), c.nivel, _ordinal_normalizado(c.nivel, c.rotulo))
                parent_anchor = slugify(meta.doc_id, n.nivel, _ordinal_normalizado(n.nivel, n.rotulo))
                prev_id = prev_by_parent.get(parent_anchor)
                chunk = Chunk(
                    doc_id=meta.doc_id,
                    anchor_id=anchor,
                    nivel=c.nivel,
                    rotulo=c.rotulo,
                    ordinal_normalizado=_ordinal_normalizado(c.nivel, c.rotulo),
                    caminho_hierarquico=_breadcrumb(c, id_to_node),
                    texto=c_text,
                    tokens_estimados=c_tokens,
                    parent_id=parent_anchor,
                    siblings_prev_id=prev_id,
                    siblings_next_id=None,
                    origem_pdf={"arquivo": pdf_file, "paginas": pages},
                    hash_conteudo=hashlib.sha256(c_text.encode("utf-8")).hexdigest(),
                    texto_limpo=True,
                    versao_parser="1.0.0",
                )
                if layout_refs:
                    chunk.layout_refs = layout_refs
                # preencher metadados PF
                chunk.__dict__.update({
                    "especie_normativa": meta.especie_normativa,
                    "numero": meta.numero,
                    "ano": meta.ano,
                    "numero_completo": meta.numero_completo,
                    "data_publicacao": meta.data_publicacao,
                    "data_vigencia": meta.data_vigencia,
                    "situacao": meta.situacao,
                    "fonte_publicacao": meta.fonte_publicacao,
                    "processo_ref": meta.processo_ref,
                    "unidade_emitente": meta.unidade_emitente,
                    "ementa": meta.ementa,
                    "preambulo": meta.preambulo,
                    "considerandos": meta.considerandos,
                    "anexos_presentes": meta.anexos_presentes,
                })
                if prev_id:
                    # set next of prev
                    for ch in chunks[::-1]:
                        if ch.anchor_id == prev_id:
                            ch.siblings_next_id = anchor
                            break
                chunks.append(chunk)
                prev_by_parent[parent_anchor] = anchor
        else:
            anchor = slugify(meta.doc_id, n.nivel, _ordinal_normalizado(n.nivel, n.rotulo))
            parent_anchor = None
            if n.parent_id and id_to_node[n.parent_id].nivel != "documento":
                parent = id_to_node[n.parent_id]
                parent_anchor = slugify(meta.doc_id, parent.nivel, _ordinal_normalizado(parent.nivel, parent.rotulo))
            prev_id = prev_by_parent.get(parent_anchor or "root")
            layout_refs = []
            try:
                pg_blocks = sum((layout_map.get(pi, []) for pi in pages), [])
                for blk in pg_blocks:
                    if blk.get("type") == "table":
                        if not (blk["end"] <= n.start or blk["start"] >= n.end):
                            layout_refs.append(blk)
            except Exception:
                pass
            chunk = Chunk(
                doc_id=meta.doc_id,
                anchor_id=anchor,
                nivel=n.nivel,
                rotulo=n.rotulo,
                ordinal_normalizado=_ordinal_normalizado(n.nivel, n.rotulo),
                caminho_hierarquico=_breadcrumb(n, id_to_node),
                texto=content,
                tokens_estimados=tokens,
                parent_id=parent_anchor,
                siblings_prev_id=prev_id,
                siblings_next_id=None,
                origem_pdf={"arquivo": pdf_file, "paginas": pages},
                hash_conteudo=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                texto_limpo=True,
                versao_parser="1.0.0",
            )
            if layout_refs:
                chunk.layout_refs = layout_refs
            chunk.__dict__.update({
                "especie_normativa": meta.especie_normativa,
                "numero": meta.numero,
                "ano": meta.ano,
                "numero_completo": meta.numero_completo,
                "data_publicacao": meta.data_publicacao,
                "data_vigencia": meta.data_vigencia,
                "situacao": meta.situacao,
                "fonte_publicacao": meta.fonte_publicacao,
                "processo_ref": meta.processo_ref,
                "unidade_emitente": meta.unidade_emitente,
                "ementa": meta.ementa,
                "preambulo": meta.preambulo,
                "considerandos": meta.considerandos,
                "anexos_presentes": meta.anexos_presentes,
            })
            if prev_id:
                for ch in chunks[::-1]:
                    if ch.anchor_id == prev_id:
                        ch.siblings_next_id = anchor
                        break
            chunks.append(chunk)
            prev_by_parent[parent_anchor or "root"] = anchor

    return chunks
