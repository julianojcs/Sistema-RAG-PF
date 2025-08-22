"""
Pipeline RAG especializado para documentos normativos da Polícia Federal (DPF/PF).

Módulos principais:
- io_pdf: extração de texto de PDFs com fallback OCR
- normalize: limpeza e normalização textual
- regexes: padrões regex para estruturas jurídicas brasileiras
- parse_norma: detecção hierárquica de unidades normativas
- chunker: geração de chunks hierárquicos com contexto
- metadata_pf: extração de metadados específicos da PF
- embed_index: embeddings e indexação vetorial
- search: consulta densa e híbrida com re-ranking hierárquico
- eval: utilitários de avaliação
"""

__all__ = [
    "io_pdf",
    "normalize",
    "regexes",
    "parse_norma",
    "chunker",
    "metadata_pf",
    "embed_index",
    "search",
    "eval",
]
