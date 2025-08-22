from __future__ import annotations
import json
import os
from typing import Iterable

from .types import Chunk


def chunk_to_dict(ch: Chunk) -> dict:
    d = ch.__dict__.copy()
    # texto completo pode ser grande; mantemos como está para auditoria
    # layout_refs já é serializável (bbox normalizado)
    return d


def export_chunks_jsonl(chunks: Iterable[Chunk], out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    count = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for ch in chunks:
            rec = chunk_to_dict(ch)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1
    return f"{count} chunks exportados em {out_path}"
