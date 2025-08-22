from src.pf_rag.parse_norma import detect_structure
from src.pf_rag.chunker import build_chunks
from src.pf_rag.types import PFDocumentMetadata

SAMPLE = """
PORTARIA Nº 1.234, de 1º de março de 2024 – DG/DPF
Dispõe sobre procedimentos de teste.

O DIRETOR-GERAL DA POLÍCIA FEDERAL, no uso de suas atribuições...

CAPÍTULO I - DAS DISPOSIÇÕES GERAIS
Seção I - Do Início

Art. 1º Esta Portaria dispõe...
§ 1º Para fins desta Portaria...
I - primeiro inciso;
a) primeira alínea;

Art. 2º Outras disposições.
Parágrafo Único As exceções...

ANEXO I – Formulário
"""


def test_detect_and_chunk():
    nodes, heading = detect_structure(SAMPLE)
    meta = PFDocumentMetadata(
        doc_id="portaria-1234-2024-dg-dpf",
        especie_normativa="Portaria",
        numero="1234",
        ano="2024",
        numero_completo="Portaria nº 1.234/2024-DG/DPF",
        data_publicacao="2024-03-01",
        data_vigencia=None,
        situacao=None,
        fonte_publicacao="DOU",
        processo_ref=None,
        unidade_emitente="DG/DPF",
        ementa=heading.ementa,
        preambulo=heading.preambulo,
        considerandos=heading.considerandos,
        anexos_presentes=heading.anexos_presentes,
    )
    chunks = build_chunks(nodes, SAMPLE, meta, "sample.pdf", [1])
    assert any(c.nivel == "artigo" and c.rotulo.startswith("Art. 1") for c in chunks)
    assert any(c.nivel == "paragrafo" for c in chunks)
    assert any(c.nivel == "inciso" for c in chunks)
    assert any(c.nivel == "alinea" for c in chunks)
