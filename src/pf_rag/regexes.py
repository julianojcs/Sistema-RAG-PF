import re

# Regex base para títulos macro em pt-BR jurídico
CAPITULO = re.compile(r"(?mi)^\s*CAP[ÍI]TULO\s+([IVXLCDM]+)(?:\s*[-–—:]\s*(.*))?$")
TITULO = re.compile(r"(?mi)^\s*T[ÍI]TULO\s+([IVXLCDM]+)(?:\s*[-–—:]\s*(.*))?$")
SECAO = re.compile(r"(?mi)^\s*SE[ÇC][ÃA]O\s+([IVXLCDM]+)(?:\s*[-–—:]\s*(.*))?$")
SUBSECAO = re.compile(r"(?mi)^\s*SUBSE[ÇC][ÃA]O\s+([IVXLCDM]+)(?:\s*[-–—:]\s*(.*))?$")
PARTE_LIVRO = re.compile(r"(?mi)^\s*(PARTE|LIVRO)\s+([IVXLCDM]+)(?:\s*[-–—:]\s*(.*))?$")

ARTIGO = re.compile(r"(?mi)^\s*Art(?:igo)?\.?\s*(\d+[A-Za-zºoO-]?)\.?\s*[-–—:]?\s*(.*)$")
PARAGRAFO = re.compile(r"(?mi)^\s*§\s*(\d+º?)\s*[-–—:]?\s*(.*)$")
PARAGRAFO_UNICO = re.compile(r"(?mi)^\s*Par[aá]grafo\s+[ÚU]nico\s*[-–—:]?\s*(.*)$")
INCISO = re.compile(r"(?mi)^\s*([IVXLCDM]+)\s*[-–—)\.]?\s*(.*)$")
ALINEA = re.compile(r"(?mi)^\s*([a-z])\s*[\)\.-]?\s*(.*)$")
ITEM = re.compile(r"(?mi)^\s*(\d+)\s*[)\.-]\s*(.*)$")

ANEXO = re.compile(r"(?mi)^\s*ANEXO\s+([IVXLCDM]+|\d+|[ÚU]NICO|UNICO)(?:\s*[-–—:]\s*(.*))?$")
EMENTA_HEUR = re.compile(r"(?mi)\b(Disp[óo]e sobre|Estabelece|Regulamenta|Altera|Aprova|Define|Institui)\b[\s\S]{0,260}$")
PREAMBULO = re.compile(r"(?mi)^\s*O\s+(DIRETOR-GERAL(?:\s+DA\s+POL[ÍI]CIA\s+FEDERAL)?|DIRETOR-EXECUTIVO|SECRET[ÁA]RIO-EXECUTIVO|COORDENADOR-GERAL|SUPERINTENDENTE(?:\s+REGIONAL)?)\b[\s\S]{0,220}?no uso de suas atribui[cç][õo]es")

PF_NUMERACAO = re.compile(r"(?mi)\b(Portaria|Instru[çc][ãa]o\s+Normativa|Resolu[çc][ãa]o|Ordem\s+Interna|Despacho)\b.*?n[ºo]\b\s*([\d\.\-]+)\/?(\d{4})?.{0,80}?\b(DG\/DPF|DIREX\/DPF|[A-Z]{2,5}\/DPF|SR\/PF-[A-Z]{2}|PF)\b")
SEI_PROC = re.compile(r"(?mi)SEI\s*n[ºo]\s*(\d{5,}\.\d{6}\/\d{4}-[A-Z]{2})")
DATA_PUB = re.compile(r"(?mi)de\s+(\d{1,2})\s+de\s+([a-zçãéí]+)\s+de\s+(\d{4})")

ROMAN = re.compile(r"^(?=[MDCLXVI])(M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3}))$", re.IGNORECASE)

MESES = {
    "janeiro": "01",
    "fevereiro": "02",
    "março": "03",
    "marco": "03",
    "abril": "04",
    "maio": "05",
    "junho": "06",
    "julho": "07",
    "agosto": "08",
    "setembro": "09",
    "outubro": "10",
    "novembro": "11",
    "dezembro": "12",
}
