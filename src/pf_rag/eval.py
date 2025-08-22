from __future__ import annotations
from typing import List, Tuple


def mrr_at_k(retrieved_lists: List[List[str]], gold_list: List[str], k: int = 5) -> float:
    """Calcula MRR@k. retrieved_lists é uma lista de listas de anchor_ids; gold_list contém os corretos."""
    import math
    def rr(retrieved: List[str]) -> float:
        for i, a in enumerate(retrieved[:k], start=1):
            if a in gold_list:
                return 1.0 / i
        return 0.0
    scores = [rr(lst) for lst in retrieved_lists]
    return sum(scores) / (len(scores) or 1)
