import re
from collections import Counter
from simhash import Simhash

_WORD_RE = re.compile(r"[A-Za-z0-9_]{2,}")

def _features_with_capped_weights(text: str, cap: int = 10):
    tokens = _WORD_RE.findall((text or "").lower())
    counts = Counter(tokens)
    for tok, cnt in counts.items():
        yield (tok, min(cnt, cap))

def simhash_text(text: str) -> int:
    feats = list(_features_with_capped_weights(text, cap=10))
    if not feats:
        return 0
    return Simhash(feats).value

def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")
