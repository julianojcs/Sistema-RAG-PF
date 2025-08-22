from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple


@dataclass
class PDFPage:
    index: int
    text: str


@dataclass
class HeadingBlock:
    ementa: Optional[str] = None
    preambulo: Optional[str] = None
    considerandos: List[str] = field(default_factory=list)
    anexos_presentes: List[str] = field(default_factory=list)


@dataclass
class Node:
    id: str
    nivel: str
    rotulo: str
    start: int
    end: int
    children: List["Node"] = field(default_factory=list)
    parent_id: Optional[str] = None
    title: Optional[str] = None


@dataclass
class Chunk:
    doc_id: str
    anchor_id: str
    nivel: str
    rotulo: str
    ordinal_normalizado: str
    caminho_hierarquico: List[Dict[str, str]]
    texto: str
    tokens_estimados: int
    parent_id: Optional[str]
    siblings_prev_id: Optional[str]
    siblings_next_id: Optional[str]
    origem_pdf: Dict[str, Any]
    hash_conteudo: str
    texto_limpo: bool
    versao_parser: str
    # metadados PF
    orgao: str = "Polícia Federal"
    sigla_orgao: str = "DPF"
    ambito: str = "federal"
    pais: str = "Brasil"
    publicacao_publica: bool = True
    especie_normativa: Optional[str] = None
    numero: Optional[str] = None
    ano: Optional[str] = None
    numero_completo: Optional[str] = None
    data_publicacao: Optional[str] = None
    data_vigencia: Optional[str] = None
    situacao: Optional[str] = None
    fonte_publicacao: Optional[str] = None
    processo_ref: Optional[str] = None
    unidade_emitente: Optional[str] = None
    ementa: Optional[str] = None
    preambulo: Optional[str] = None
    considerandos: List[str] = field(default_factory=list)
    anexos_presentes: List[str] = field(default_factory=list)
    # Opcional: referências de layout (Docling) por página com bbox
    layout_refs: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PFDocumentMetadata:
    doc_id: str
    especie_normativa: Optional[str]
    numero: Optional[str]
    ano: Optional[str]
    numero_completo: Optional[str]
    data_publicacao: Optional[str]
    data_vigencia: Optional[str]
    situacao: Optional[str]
    fonte_publicacao: Optional[str]
    processo_ref: Optional[str]
    unidade_emitente: Optional[str]
    ementa: Optional[str]
    preambulo: Optional[str]
    considerandos: List[str]
    anexos_presentes: List[str]
