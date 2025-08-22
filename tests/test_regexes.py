from src.pf_rag import regexes as RX


def test_pf_numeracao():
    s = "Instrução Normativa nº 12/2023-DIREX/DPF"
    m = RX.PF_NUMERACAO.search(s)
    assert m, "Deve detectar espécie/numero/ano/unidade"
    assert m.group(1).lower().startswith("instru"), m.groups()
    assert m.group(2) == "12"
    assert m.group(3) == "2023"
    assert m.group(4) == "DIREX/DPF"


def test_artigo_paragrafo():
    assert RX.ARTIGO.match("Art. 5º Esta norma...")
    assert RX.PARAGRAFO.match("§ 1º O procedimento...")
    assert RX.PARAGRAFO_UNICO.match("Parágrafo Único ...")


def test_inciso_alinea_item():
    assert RX.INCISO.match("I - do procedimento")
    assert RX.ALINEA.match("a) item de lista")
    assert RX.ITEM.match("1. primeiro")
