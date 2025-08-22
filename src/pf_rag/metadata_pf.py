from __future__ import annotations
import re
from typing import Optional
from .types import PFDocumentMetadata, HeadingBlock
from . import regexes as RX


def _canon_doc_id(especie: Optional[str], numero: Optional[str], ano: Optional[str], unidade: Optional[str]) -> str:
    parts = []
    if especie:
        parts.append(especie.lower().replace(" ", "-"))
    if numero:
        parts.append(numero.replace(".", ""))
    if ano:
        parts.append(ano)
    if unidade:
        parts.append(unidade.lower().replace("/", "-").replace(" ", ""))
    return "-".join(parts) if parts else "documento-pf"


def extract(text: str, heading: HeadingBlock, filename: str) -> PFDocumentMetadata:
    especie = numero = ano = numero_completo = data_publicacao = None
    unidade = fonte = processo = situacao = None

    m = RX.PF_NUMERACAO.search(text[:4000])
    if m:
        especie = m.group(1)
        numero = m.group(2).replace(".", "") if m.group(2) else None
        ano = m.group(3) if m.group(3) else None
        unidade = m.group(4)
        numero_completo = m.group(0).strip()

    m2 = RX.SEI_PROC.search(text)
    if m2:
        processo = m2.group(1)

    m3 = RX.DATA_PUB.search(text[:2000])
    if m3:
        dia, mes, ano_pub = m3.groups()
        mes_num = RX.MESES.get(mes.lower())
        if mes_num:
            data_publicacao = f"{ano_pub}-{mes_num}-{int(dia):02d}"

    # Fonte simples (heurística)
    if "boletim de serviço" in text.lower():
        fonte = "Boletim de Serviço DPF"
    elif "dou" in text.lower() or "diário oficial" in text.lower() or "diario oficial" in text.lower():
        fonte = "DOU"

    # Situação (heurística mínima)
    if "fica revogada" in text.lower() or "revogam-se" in text.lower():
        situacao = "revogada"

    doc_id = _canon_doc_id(especie, numero, ano, unidade)

    return PFDocumentMetadata(
        doc_id=doc_id,
        especie_normativa=especie,
        numero=numero,
        ano=ano,
        numero_completo=numero_completo,
        data_publicacao=data_publicacao,
        data_vigencia=None,
        situacao=situacao,
        fonte_publicacao=fonte,
        processo_ref=processo,
        unidade_emitente=unidade,
        ementa=heading.ementa,
        preambulo=heading.preambulo,
        considerandos=heading.considerandos,
        anexos_presentes=heading.anexos_presentes,
    )
