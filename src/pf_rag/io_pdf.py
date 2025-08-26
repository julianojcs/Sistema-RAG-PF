from __future__ import annotations
import os
import warnings
import logging
from typing import List, Tuple, Dict, Any
from .types import PDFPage

# Suprimir warnings específicos do pdfminer sobre cores inválidas
warnings.filterwarnings('ignore', message='Cannot set gray non-stroke color')
warnings.filterwarnings('ignore', message='Invalid float value')

# Configurar logging do pdfminer para ERROR apenas (suprime warnings)
logging.getLogger('pdfminer').setLevel(logging.ERROR)

from pdfminer.high_level import extract_text as pdfminer_extract_text  # type: ignore

try:
    import pytesseract  # type: ignore
    from PIL import Image  # type: ignore
    import pdf2image  # type: ignore
except Exception:  # pragma: no cover
    pytesseract = None  # type: ignore
    Image = None  # type: ignore
    pdf2image = None  # type: ignore

from src.config.settings import Settings

# Docling optional import
try:  # pragma: no cover
    from docling.document_converter import DocumentConverter  # type: ignore
    from docling.models.converter import ConverterConfig  # type: ignore
    from docling.models.doc import DoclingDocument, TextBlock, TableBlock  # type: ignore
except Exception:
    DocumentConverter = None  # type: ignore
    ConverterConfig = None  # type: ignore
    DoclingDocument = None  # type: ignore
    TextBlock = None  # type: ignore
    TableBlock = None  # type: ignore

# Cache interno para extras de layout por arquivo (usado pelo chunker)
_LAYOUT_CACHE: Dict[str, Dict[str, Any]] = {}

def get_layout_extras(path: str) -> Dict[str, Any]:
    return _LAYOUT_CACHE.get(path, {})


def _extract_with_docling(path: str) -> Tuple[str, List[PDFPage], bool, Dict[str, Any]]:
    """Extrai usando Docling (quando habilitado) com preservação de layout.
    Retorna (texto, pages, ocr_usado=False, extras) onde extras pode conter blocos, tabelas, bbox por página.
    """
    if DocumentConverter is None:
        raise RuntimeError("Docling não instalado")
    cfg = ConverterConfig()
    converter = DocumentConverter(cfg)
    doc = converter.convert(path)
    # Concatenar blocos em ordem de leitura
    pages: List[PDFPage] = []
    texts: List[str] = []
    page_map: Dict[int, List[Dict[str, Any]]] = {}
    full_cursor = 0
    def _bbox_to_list(bbox: Any):
        try:
            # Docling bbox may have attributes x0,y0,x1,y1 or similar
            if bbox is None:
                return None
            xs = [getattr(bbox, k, None) for k in ("x0", "y0", "x1", "y1")]
            if all(v is not None for v in xs):
                return [float(v) for v in xs]  # type: ignore
            if isinstance(bbox, (list, tuple)):
                return [float(v) for v in bbox]
        except Exception:
            return None
        return None

    for p in doc.pages:  # type: ignore[attr-defined]
        page_text_parts: List[str] = []
        blocks: List[Dict[str, Any]] = []
        page_cursor = 0
        for b in p.blocks:
            if isinstance(b, TextBlock):
                page_text_parts.append(b.text)
                start_local = page_cursor
                end_local = page_cursor + len(b.text)
                page_cursor = end_local + 1  # assume a quebra entre blocos
                blocks.append({
                    "type": "text",
                    "text": b.text,
                    "bbox": _bbox_to_list(getattr(b, "bbox", None)),
                    "page_no": p.page_no,
                    "start": None,  # preenchido após montar página
                    "end": None,
                    "_local": (start_local, end_local),
                })
            elif isinstance(b, TableBlock):
                # Renderizar tabela como texto com separadores simples
                tbl_text = "\n".join(["\t".join([str(c) for c in row]) for row in b.to_matrix()])
                page_text_parts.append(tbl_text)
                start_local = page_cursor
                end_local = page_cursor + len(tbl_text)
                page_cursor = end_local + 1
                blocks.append({
                    "type": "table",
                    "text": tbl_text,
                    "bbox": _bbox_to_list(getattr(b, "bbox", None)),
                    "page_no": p.page_no,
                    "start": None,
                    "end": None,
                    "_local": (start_local, end_local),
                })
        page_text = "\n".join(page_text_parts)
        pages.append(PDFPage(index=p.page_no, text=page_text))
        texts.append(page_text)
        # Preencher offsets absolutos dos blocos
        abs_base = full_cursor
        pg_blocks: List[Dict[str, Any]] = []
        for blk in blocks:
            l0, l1 = blk.pop("_local")  # type: ignore
            blk["start"] = abs_base + l0
            blk["end"] = abs_base + l1
            pg_blocks.append(blk)
        page_map[p.page_no] = pg_blocks
        # +1 para o separador de página "\f" que será adicionado na concatenação
        full_cursor += len(page_text) + 1
    full_text = "\f".join(texts)
    extras = {"layout_blocks": page_map}
    _LAYOUT_CACHE[path] = extras
    return full_text, pages, False, extras


def _safe_pdfminer_extract(path: str) -> str:
    """
    Wrapper robusto para pdfminer que captura warnings sobre cores inválidas.
    """
    import io
    import sys
    import contextlib

    # Capturar stderr temporariamente para suprimir warnings
    old_stderr = sys.stderr

    try:
        with contextlib.redirect_stderr(io.StringIO()):
            # Suprimir warnings temporariamente
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                text = pdfminer_extract_text(path) or ""
                return text
    except Exception as e:
        # Log apenas erros críticos, não warnings de cor
        if "gray non-stroke color" not in str(e):
            print(f"Erro na extração PDF: {e}")
        return ""
    finally:
        sys.stderr = old_stderr


def extract_text(path: str) -> Tuple[str, List[PDFPage], bool]:
    """
    Extrai o texto do PDF com preferência por Docling (layout-aware).
    Fallback: pdfminer + OCR. Returns: (texto_concatenado, pages, ocr_usado)
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    text = ""
    ocr_used = False
    pages: List[PDFPage] = []
    # Docling preferencial
    if Settings.DOCLING_ENABLED and DocumentConverter is not None:
        try:
            full_text, pages, ocr_used, extras = _extract_with_docling(path)
            # Guardar extras em arquivo lateral opcional (para debug/auditoria)
            # Poderíamos expor via metadados em etapas posteriores
            return full_text, pages, ocr_used
        except Exception:
            # Fallback silencioso
            pass

    try:
        text = _safe_pdfminer_extract(path)
    except Exception:
        text = ""

    if text.strip():
        # pdf pesquisável
        split = text.split("\f") if "\f" in text else text.split("\x0c")
        for i, t in enumerate(split):
            pages.append(PDFPage(index=i + 1, text=t))
        return text, pages, ocr_used

    # Fallback OCR
    if Settings.OCR_ENABLED and pdf2image is not None and pytesseract is not None:
        images = pdf2image.convert_from_path(path)
        buf: List[str] = []
        for i, img in enumerate(images):
            page_text = pytesseract.image_to_string(img, lang=Settings.OCR_LANG)
            pages.append(PDFPage(index=i + 1, text=page_text))
            buf.append(page_text)
        ocr_used = True
        return "\n\n".join(buf), pages, ocr_used

    # Sem OCR disponível
    raise RuntimeError("Falha ao extrair texto do PDF (sem OCR disponível)")
