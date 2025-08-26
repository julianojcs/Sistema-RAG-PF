#!/usr/bin/env python3
"""
Script para limpar pastas antigas do Qdrant com timestamp
Uso: python cleanup_qdrant.py
"""

import os
import glob
import shutil
from src.config.settings import Settings

def cleanup_old_qdrant_dirs():
    """Remove pastas antigas do Qdrant criadas com timestamp."""
    try:
        # Get the base directory where Qdrant folders would be
        base_dir = os.path.dirname(Settings.QDRANT_PATH) or "."
        base_name = os.path.basename(Settings.QDRANT_PATH)

        # Find all directories matching pattern like "qdrantDB_1234567890"
        pattern = os.path.join(base_dir, f"{base_name}_*")
        old_dirs = glob.glob(pattern)

        if not old_dirs:
            print("✅ Nenhuma pasta Qdrant antiga encontrada")
            return

        print(f"🔍 Encontradas {len(old_dirs)} pastas antigas:")
        for old_dir in old_dirs:
            print(f"   - {os.path.basename(old_dir)}")

        for old_dir in old_dirs:
            # Only remove if it matches timestamp pattern (numeric suffix)
            dir_name = os.path.basename(old_dir)
            if '_' in dir_name:
                suffix = dir_name.split('_')[-1]
                if suffix.isdigit():
                    try:
                        shutil.rmtree(old_dir, ignore_errors=True)
                        print(f"🧹 Removida: {dir_name}")
                    except Exception as e:
                        print(f"❌ Erro ao remover {dir_name}: {e}")
                else:
                    print(f"⚠️  Ignorada (não é timestamp): {dir_name}")

        print("✅ Limpeza concluída")

    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")

if __name__ == "__main__":
    print("🧹 Limpando pastas antigas do Qdrant...")
    cleanup_old_qdrant_dirs()
