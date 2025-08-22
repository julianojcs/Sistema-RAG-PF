from __future__ import annotations
import os
import json
import hashlib
from typing import Dict, Tuple, List

from .file_utils import FileUtils
from ..config.settings import Settings

MANIFEST_PATH = os.path.join(Settings.FAISS_DB_PATH, "ingest_manifest.json")


def file_hash(path: str) -> str:
    try:
        stat = os.stat(path)
        h = hashlib.md5()
        h.update(f"{stat.st_size}:{stat.st_mtime}".encode())
        return h.hexdigest()
    except Exception:
        return "erro"


def load_manifest() -> Dict[str, Dict[str, str]]:
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("files", {})
        except Exception:
            return {}
    return {}


def save_manifest(files_map: Dict[str, Dict[str, str]]) -> None:
    os.makedirs(Settings.FAISS_DB_PATH, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump({"files": files_map}, f, ensure_ascii=False, indent=2)


def diff_current_vs_manifest() -> Tuple[List[str], List[str], List[str], Dict[str, Dict[str, str]]]:
    """
    Returns: (added, modified, removed, new_map)
    new_map maps path -> {"hash": md5}
    """
    current_files = FileUtils.get_pdf_files()
    current_map: Dict[str, Dict[str, str]] = {}
    for p in current_files:
        current_map[p] = {"hash": file_hash(p)}

    manifest_map = load_manifest()
    added, modified, removed = [], [], []

    for p, meta in current_map.items():
        if p not in manifest_map:
            added.append(p)
        elif meta.get("hash") != manifest_map.get(p, {}).get("hash"):
            modified.append(p)

    for p in manifest_map.keys():
        if p not in current_map:
            removed.append(p)

    return added, modified, removed, current_map
