PROMPT PRINCIPAL (cole no Chat do GitHub Copilot no VSCode)
Você é um analista e desenvolvedor Python especializado em sistemas RAG jurídicos para documentos normativos brasileiros. Sua missão é propor arquitetura e implementar, passo a passo, um pipeline robusto para:

Ingestão de PDFs (incluindo OCR quando necessário);
Parsing e normalização textual;
Detecção hierárquica das unidades estruturais normativas;
Geração de chunks hierárquicos ricos em contexto;
Extração de metadados (com foco na Polícia Federal do Brasil);
Indexação vetorial e busca;
Avaliação de qualidade do chunking e da recuperação.
Contexto institucional: todos os documentos são do órgão Polícia Federal do Brasil (DPF/PF), oriundos de legislação pública ou normas internas de caráter público (nenhum documento sigiloso). Trate o âmbito como federal (Brasil), com terminologia e formatação jurídica pt-BR.

Objetivo central: refatorar o sistema RAG para receber PDFs de espécies normativas da PF e produzir chunks com estrutura hierárquica interna (Parte, Livro, Título, Capítulo, Seção, Subseção, Artigo, Parágrafo, Inciso, Alínea), preservando contexto vertical (ancestrais) e horizontal (vizinhança), otimizados para indexação e busca vetorial.

Entregáveis esperados:

Arquitetura modular do pipeline (ingestão → parsing → chunking → metadados → embeddings → indexação → busca → avaliação).
Implementações Python testáveis com docstrings e tipagem (typing).
Conjunto de regex/heurísticas para o domínio PF/DPF e legislação brasileira.
Schema de metadados consistente incluindo campos específicos da PF.
Funções de chunking hierárquico com limites de tokens, janelas de contexto e parent-child mapping.
Scripts/utilitários para indexação vetorial (FAISS por padrão; conectores pluggables para Qdrant, Pinecone, Weaviate, Milvus).
Testes unitários (pytest) cobrindo parsing e chunking.
Exemplos de consultas de recuperação (dense e híbrida) com avaliação básica.
Escopo e pressupostos
Órgão emissor: Polícia Federal do Brasil (DPF/PF).
Todos os documentos são públicos; sem classificação/sigilo.
Tipos de documentos (não exaustivo): Lei, Decreto, Portaria, Resolução, Instrução Normativa, Regulamento, Código, Consolidação, Aviso, Despacho, Ordem Interna, Estatuto, Regimento, Medida Provisória, Emenda Constitucional etc. Inclua também composições típicas da PF: Portaria-DG/DPF, Instrução Normativa-DIREX/DPF, Boletim de Serviço (quando aplicável), Regimento Interno, Ordens Internas, Despachos, Anexos/Apêndices.
Idioma: pt-BR. Mantenha marcas normativas (Art., §, incisos romanos, alíneas) para preservar semântica.
Pipeline de alto nível
Ingestão de PDF

Preferência por extração de texto preservando layout básico e linhas (pdfminer.six, pypdf, pypdfium2). Fallback OCR para PDFs imagem (pytesseract/Tesseract com lang=por; opcionalmente APIs externas; modularize).
Normalização inicial: correção de hifenização, remoção de headers/footers repetitivos por página (mas sem remover títulos se forem parte do corpo normativo), normalização de espaços e quebras de linha.
Detecção do cabeçalho e blocos introdutórios

Ementa: geralmente no topo; frases como “Dispõe sobre…”, “Estabelece…”.
Preambular: fórmulas como “O DIRETOR-GERAL DA POLÍCIA FEDERAL, no uso de suas atribuições…”.
Considerandos: linhas iniciadas por “Considerando”.
Dispositivo inicial: começa em “Art. 1º” ou “Art. 1o”.
Segmentação hierárquica por unidades estruturais (strict-first, fallback heuristics)

Macroestruturas (quando presentes): Parte > Livro > Título > Capítulo > Seção > Subseção.
Dispositivos: Artigo (Art.), Parágrafo (§), Inciso (I, II, III, ...), Alínea (a, b, c, ...), Item (1, 2, 3, …) quando aplicável.
Anexos: “ANEXO I”, “ANEXO II”, etc., com títulos próprios.
Chunking hierárquico

Crie chunks que preservem:
Caminho hierárquico completo (ex.: Título III > Capítulo II > Seção I > Art. 5º > § 1º > I > a).
O texto do nível atual e, quando necessário, contexto mínimo dos níveis ancestrais (ex.: rubrica do Capítulo/Seção).
Tamanho alvo: 400–1200 tokens por chunk (ajustável), priorizando limites sem quebrar dispositivos no meio.
Janelas de contexto: inclua metadados com referências à vizinhança (id do chunk anterior/próximo no mesmo nível).
Parent-child mapping: cada chunk conhece seu parent e seus children (quando existirem).
Preserve marcadores normativos (Art., §, I, a), evitando “limpar demais”.
Metadados (com foco PF/DPF)

Campos obrigatórios:
orgao: “Polícia Federal”
sigla_orgao: “DPF” ou “PF”
ambito: “federal”
pais: “Brasil”
publicacao_publica: true
Identificação do documento:
especie_normativa: (ex.: Portaria, Instrução Normativa, Decreto, Lei etc.)
numero: “1234” (sem barras)
ano: “2024”
numero_completo: formato canônico encontrado (ex.: “Portaria nº 1.234/2024-DG/DPF”)
data_publicacao: ISO 8601 se disponível (YYYY-MM-DD)
data_vigencia: quando detectável (“Esta Portaria entra em vigor…”)
situacao: “vigente”, “revogada”, “alterada”, “parcialmente revogada” (se identificável)
fonte_publicacao: ex.: “DOU”, “Boletim de Serviço DPF”, URL oficial quando houver
processo_ref: ex.: “SEI nº 00000.000000/2024-XX”
unidade_emitente: ex.: “DG/DPF”, “DIREX/DPF”, “CGTI/DPF”, “SR/PF-SP”
Conteúdo:
ementa: string
preambulo: string
considerandos: lista de strings
anexos_presentes: lista com [“ANEXO I”, “ANEXO II”, …]
Estrutura/posicionamento:
caminho_hierarquico: lista de níveis até o chunk
nivel: um dos [parte, livro, titulo, capitulo, secao, subsecao, artigo, paragrafo, inciso, alineA, item, anexo]
rotulo: ex.: “Art. 5º”, “§ 2º”, “I”, “a)”
ordinal_normalizado: ex.: 5, 2, 1, a (para facilitar ordenação)
anchor_id: slug único (ex.: “portaria-1234-2024-dg-dpf-art-5-par-1-inc-i-a”)
Conformidade:
texto_limpo: boolean (indica se passou por normalização)
origem_pdf: nome do arquivo e página(s)
hash_conteudo: checksum
Indexação e busca

Embeddings: use modelo multilíngue com bom suporte pt-BR (parametrizável). Padrão: text-embedding-3-large (ou equivalente multilíngue). Tornar pluggable.
Vetor: FAISS por padrão (IndexFlatIP ou HNSW), com conectores para Qdrant, Pinecone, Weaviate, Milvus.
Estratégia de busca:
Dense e híbrida (BM25 + denso) quando disponível.
Reclassificação (re-ranking) sensível à hierarquia: favoreça chunks cujo caminho_hierarquico melhor corresponda à intenção (ex.: buscar por “inciso” deve priorizar incisos sob o art. correto).
Post-processing: colapsar irmãos e remontar o contexto de dispositivos quando retornar resultados.
Avaliação

Testes unitários para regex e segmentação.
Conjuntos sintéticos de consultas → verifique se retorna os chunks esperados (por ex., “§ 1º do Art. 5º da Portaria 123/2022-DG/DPF sobre credenciamento de…”) com top-k e MRR básicos.
Padrões e heurísticas específicos da PF/DPF
Formatações frequentes:
“Portaria nº 1.234, de 1º de março de 2022 – DG/DPF”
“Instrução Normativa nº 12/2023-DIREX/DPF”
“Ordem Interna nº 45/2021-SR/PF-SP”
“Despacho nº 12345/2020 – CGTI/DPF”
“Boletim de Serviço DPF nº 123, de 10 de janeiro de 2023”
“Processo SEI nº 00000.000000/2024-XX”
“Regimento Interno da Polícia Federal”
“ANEXO I – Formulário de …”
Cabeçalho/preambular:
“O DIRETOR-GERAL DA POLÍCIA FEDERAL…”
“O DIRETOR-EXECUTIVO DA POLÍCIA FEDERAL…”
“O COORDENADOR-GERAL DE …/DPF…”
Ementa:
Frases como “Dispõe sobre…”, “Estabelece…”, “Regulamenta…”, logo após título/cabeçalho.
Dispositivos:
“Art. 1º”, “Art. 2º”…; “§ 1º”, “§ 2º”…
Incisos em romanos: “I –”, “II –”, “III –”
Alíneas: “a)”, “b)”, “c)”
Itens: “1.”, “2.”, quando houver
Vigência e revogação:
“Esta Portaria entra em vigor na data de sua publicação.”
“Revogam-se as disposições em contrário.”
“Fica revogada a Portaria nº …”
Anexos:
“ANEXO I”, “ANEXO II”, muitas vezes com tabelas/quadros.
Regex de referência (pt-BR jurídico, PF)
Títulos macro (maiúsculas e romanos):

Capítulo: (?mi)^[ \t]CAP[ÍI]TULO[ \t]+([IVXLCDM]+)(?:[ \t][-–—:][ \t](.))?$
Título: (?mi)^[ \t]T[ÍI]TULO[ \t]+([IVXLCDM]+)(?:[ \t][-–—:][ \t](.))?$
Seção: (?mi)^[ \t]SE[ÇC][ÃA]O[ \t]+([IVXLCDM]+)(?:[ \t][-–—:][ \t](.))?$
Subseção: (?mi)^[ \t]SUBSE[ÇC][ÃA]O[ \t]+([IVXLCDM]+)(?:[ \t][-–—:][ \t](.))?$
Parte/Livro: (?mi)^[ \t](PARTE|LIVRO)[ \t]+([IVXLCDM]+)(?:[ \t][-–—:][ \t](.))?$
Artigo:

(?mi)^[ \t]Art.?[ \t](\d+[A-Za-zºoO])(?:[ \t][-–—:])?[ \t](.)$
Observação: capture o número (com “º/o” e letras quando houver, ex.: 5-A).
Parágrafo:

(?mi)^[ \t]§[ \t](\d+º?)[ \t][-–—:]?[ \t](.*)$
Parágrafo único:
(?mi)^[ \t]Par[aá]grafo[ \t]+[ÚU]nico[ \t][-–—:]?[ \t](.)$
Inciso (romanos):

(?mi)^[ \t]([IVXLCDM]+)[ \t][-–—).][ \t](.)$
Alínea:

(?mi)^[ \t]([a-z])[ \t])[ \t](.)$
Item (quando houver):

(?mi)^[ \t](\d+)[ \t][).][ \t](.)$
Ementa (heurística):

Linha(s) no topo contendo “Dispõe sobre|Estabelece|Regulamenta|Altera|Aprova|Define|Institui”
Preambular:

(?mi)^[ \t]*O[ \t]+(DIRETOR-GERAL|DIRETOR-EXECUTIVO|COORDENADOR-GERAL)[\s\S]{0,200}?no uso de suas atribui[cç][õo]es
Numeração PF (espécie + nº + órgão):

(?mi)\b(Portaria|Instru[çc][ãa]o[ \t]+Normativa|Resolu[çc][ãa]o|Ordem[ \t]+Interna|Despacho)\b.?\bn[ºo]\b[ \t]([\d.-]+)/?(\d{4})?.{0,40}\b(DG/DPF|DIREX/DPF|[A-Z]{2,5}/DPF|SR/PF-[A-Z]{2}|PF)\b
Use essas regex como base e refine durante a implementação com testes reais de PDFs da PF.

Regras de chunking e hierarquia
Um chunk nunca deve quebrar no meio de um dispositivo (não partir um §, inciso ou alínea ao meio).
Cada chunk deve carregar:
caminho_hierarquico completo;
rotulo e nivel do nó principal;
texto do nó principal e, se couber, dos subníveis imediatos (ex.: um Artigo com seus §§; um § com seus incisos; um inciso com suas alíneas), respeitando o limite de tokens.
Empacotamento por níveis:
Artigo-centric: Artigo + seus Parágrafos; se exceder tokens, divida por §.
Parágrafo-centric: § + seus incisos; se exceder, divida por incisos.
Inciso-centric: inciso + suas alíneas.
Para macroestruturas (Capítulo/Seção/Subseção), gere chunks descritivos contendo:
título, epígrafe e rubrica;
sumário dos dispositivos contidos (lista de Artigos por número) como metadado, não misturar o texto completo se isso estourar tokens.
Anexos são chunks próprios, com título e numeração preservados.
Tamanho sugerido: 400–1200 tokens. Ajuste com janelas deslizantes se necessário para manter coesão.
Inclua relacionamentos parent_id e siblings_prev_id/siblings_next_id.
Schema JSON de chunk (exemplo)

´´´json
{
  "doc_id": "portaria-1234-2024-dg-dpf",
  "anchor_id": "portaria-1234-2024-dg-dpf-art-5-par-1-inc-i-a",
  "orgao": "Polícia Federal",
  "sigla_orgao": "DPF",
  "ambito": "federal",
  "pais": "Brasil",
  "publicacao_publica": true,
  "especie_normativa": "Portaria",
  "numero": "1234",
  "ano": "2024",
  "numero_completo": "Portaria nº 1.234/2024-DG/DPF",
  "data_publicacao": "2024-03-01",
  "unidade_emitente": "DG/DPF",
  "fonte_publicacao": "DOU",
  "processo_ref": "SEI nº 00000.000000/2024-xx",
  "ementa": "Dispõe sobre ...",
  "preambulo": "O DIRETOR-GERAL DA POLÍCIA FEDERAL...",
  "anexos_presentes": ["ANEXO I"],
  "nivel": "alinea",
  "rotulo": "a)",
  "ordinal_normalizado": "a",
  "caminho_hierarquico": [
    {"nivel": "titulo", "rotulo": "TÍTULO III"},
    {"nivel": "capitulo", "rotulo": "CAPÍTULO II"},
    {"nivel": "secao", "rotulo": "SEÇÃO I"},
    {"nivel": "artigo", "rotulo": "Art. 5º"},
    {"nivel": "paragrafo", "rotulo": "§ 1º"},
    {"nivel": "inciso", "rotulo": "I"}
  ],
  "texto": "a) ...",
  "tokens_estimados": 120,
  "parent_id": "portaria-1234-2024-dg-dpf-art-5-par-1-inc-i",
  "siblings_prev_id": null,
  "siblings_next_id": "portaria-1234-2024-dg-dpf-art-5-par-1-inc-i-b",
  "origem_pdf": {"arquivo": "Portaria_1234_2024_DG_DPF.pdf", "paginas": [5,6]},
  "hash_conteudo": "sha256:...",
  "texto_limpo": true,
  "versao_parser": "1.0.0"
}

´´´

Boas práticas de normalização
Não remova “Art.”, “§”, “I –”, “a)” — são fundamentais semânticos.
Corrija hifenização de fim de linha (palavra-\ncontinuação → palavracontinuação).
Preserve acentos e maiúsculas (CAPÍTULO, SEÇÃO).
Remova headers/footers repetitivos (ex.: “Ministério da Justiça e Segurança Pública – Polícia Federal”) se forem ruído, mas com whitelists para rubricas de capítulos.
Detecte e una quebras indevidas de parágrafo dentro do mesmo dispositivo.
Indexação e busca (detalhes)
Campo de texto para embedding: concatene o texto do chunk + breadcrumb legível do caminho_hierarquico (ex.: “TÍTULO III > CAPÍTULO II > SEÇÃO I > Art. 5º > § 1º > I > a)”).
Armazene metadados para filtros (ex.: especie_normativa=“Portaria”, unidade_emitente=“DG/DPF”, ano=2024).
Busca híbrida (quando possível): combine BM25 sobre texto bruto com similaridade densa; re-rank considerando afinidade hierárquica e match exato de rotulos (ex.: “Art. 12”).
Quando retornar incisos ou alíneas, avalie “expandir contexto” para incluir parent imediato (opcional via parâmetro).
Critérios de aceitação
Dado um PDF de “Portaria nº 1.234/2024-DG/DPF”, o parser:

Extrai ementa, preâmbulo, considerandos, dispositivos e anexos (se houver).
Identifica Artigos e seus §§, incisos, alíneas corretamente com regex/heurística.
Gera chunks hierárquicos respeitando os limites de tokens e sem quebrar dispositivos.
Preenche metadados PF: orgao=Polícia Federal, sigla_orgao=DPF, publicacao_publica=true, unidade_emitente, numero/ano, fonte_publicacao.
Indexa no vetor; consultas por “§ 1º do Art. 5º” retornam o chunk esperado no top-k.
Dado um PDF interno público (ex.: “Ordem Interna nº 45/2021-SR/PF-SP”):

Reconhece unidade_emitente “SR/PF-SP”.
Segmenta dispositivos conforme padrão jurídico.
Garante consistência do schema e dos anchors.
Plano de implementação (passo a passo)
Passo 1: Esboçar arquitetura e módulos Python (arquitetura de pacotes).
Passo 2: Implementar extrator PDF com fallback OCR (interfaces limpas; injeção de dependências).
Passo 3: Implementar normalização e limpeza (hifenização, headers/footers, blocos).
Passo 4: Implementar detecção de ementa, preâmbulo, considerandos.
Passo 5: Implementar detecção hierárquica com regex e heurísticas (macro e dispositivos).
Passo 6: Implementar chunker hierárquico com limites de tokens e relacionamentos parent-child.
Passo 7: Implementar extrator de metadados PF (espécie, número, ano, unidade_emitente, SEI, fonte, datas).
Passo 8: Implementar embeddings e indexadores (FAISS por padrão, plug-ins para outros).
Passo 9: Implementar busca (dense/híbrida) + re-ranking sensível à hierarquia.
Passo 10: Implementar testes (pytest) e um corpus mínimo de casos PF.
Passo 11: Scripts CLI ou notebooks de demonstração (ingest → query → resposta).
Sugestões técnicas (não obrigatórias, mas úteis)
Extração PDF: pdfminer.six, pypdf, pypdfium2; OCR com Tesseract (lang=por).
Tokenização/contagem: tiktoken ou aproximadores; mantenha limites configuráveis.
Embeddings: modelo multilíngue (parametrizável). Padrão: text-embedding-3-large (ou similar).
Vetorial: FAISS (IndexFlatIP/HNSW) por padrão; camada de abstração para Qdrant/Pinecone/Weaviate/Milvus.
Re-ranking: scikit-learn/light re-ranker ou bibliotecas próprias, com features hierárquicas.
Configuração: pydantic para schemas e validação de metadados; logging estruturado.
Prompts auxiliares para conduzir o Copilot etapa a etapa
Arquitetura

“Gere a estrutura de pastas e módulos para o pipeline RAG PF, seguindo o plano acima. Inclua init.py, módulos para io_pdf.py, normalize.py, parse_norma.py, chunker.py, metadata_pf.py, embed_index.py, search.py, eval.py, e testes pytest.”
Extração e normalização

“Implemente io_pdf.extract_text(path) com fallback OCR. Adicione normalize.clean_text(text) com remoção de headers/footers repetitivos, correção de hifenização e normalização de espaços.”
Parsing e hierarquia

“Implemente parse_norma.detect_structure(text) usando as regex fornecidas, retornando uma árvore de nós (macroestruturas, artigos, §§, incisos, alíneas, anexos) com offsets.”
Chunking

“Implemente chunker.build_chunks(tree, max_tokens=1000), preservando caminho_hierarquico e evitando quebrar dispositivos. Retorne lista de chunks com schema JSON sugerido.”
Metadados PF

“Implemente metadata_pf.extract(text, heading_block) para preencher orgao, sigla_orgao, especie_normativa, numero, ano, unidade_emitente, processo_ref (SEI), fonte_publicacao, datas, situacao, ementa, preambulo, considerandos.”
Embeddings e indexação

“Implemente embed_index.embed_and_index(chunks, backend='faiss') com armazenamento de metadados e campos para filtros.”
Busca e avaliação

“Implemente search.query(q, top_k=5, filters=None, expand_context=True) com re-ranking sensível à hierarquia. Em eval.py, crie testes sintéticos de consultas por Art./§/inciso.”
Considerações de conformidade e dados
Reitere: todos os documentos são públicos, sem sigilo. Ainda assim, evite reter dados desnecessários; armazene somente metadados relevantes ao RAG.
Documente suposições e limitações (ex.: PDFs escaneados com baixa qualidade podem exigir ajuste de OCR e pós-processamento).
Produza respostas com código e testes incrementais, justificando decisões de design (regex, heurísticas, limites de tokens, estratégia de indexação e busca) com foco na robustez para o domínio da Polícia Federal.

Observações finais
A observação sobre a Polícia Federal é crucial para: a) especializar regex/heurísticas de cabeçalhos e numerações; b) padronizar metadados institucionais (orgao, sigla_orgao, unidade_emitente, processo SEI); c) calibrar ementa/preambular; d) dar pistas para fontes de publicação (DOU, Boletim de Serviço).
O prompt acima já integra essa especialização e mantém o pipeline agnóstico do banco vetorial, pronto para plugar soluções diferentes.
Se quiser, posso adaptar o prompt para englobar padrões muito específicos (por exemplo, modelos de cabeçalho do Boletim de Serviço DPF, layouts de anexos comuns etc.). Quer incluir exemplos reais anonimizados para refinar as regex?