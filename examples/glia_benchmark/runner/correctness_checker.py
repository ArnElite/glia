"""
runner/correctness_checker.py
─────────────────────────────
Simple correctness checker for benchmark responses.

Scores a response by checking how many key terms from the source
document appear in it. Returns a score from 0.0 to 1.0.

No external dependencies — just string matching.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional


# Words too common to be useful as correctness signals
_STOPWORDS = {
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "for",
    "of", "and", "or", "but", "with", "this", "that", "are", "was",
    "be", "by", "from", "as", "has", "have", "had", "not", "also",
}


def _extract_key_terms(text: str, max_terms: int = 10) -> List[str]:
    """
    Pull out the most distinctive words from a piece of text.
    Filters stopwords and short tokens, deduplicates, returns lowercase.
    """
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    seen = set()
    terms = []
    for w in words:
        if w not in _STOPWORDS and w not in seen:
            seen.add(w)
            terms.append(w)
        if len(terms) >= max_terms:
            break
    return terms


def score_response(response: str, source_doc: Dict) -> float:
    """
    Score a response against the source document.

    Returns a float in [0.0, 1.0]:
      1.0 = all key terms from source found in response
      0.0 = no key terms found

    Parameters
    ----------
    response    : the text returned by standard or glia track
    source_doc  : dict with at least 'title' and/or 'content' keys
    """
    if not response or not source_doc:
        return 0.0

    # Build reference text from doc title + first 200 chars of content
    title   = source_doc.get("title", "")
    content = source_doc.get("content", "")[:200]
    reference = f"{title} {content}"

    key_terms = _extract_key_terms(reference)
    if not key_terms:
        return 0.0

    response_lower = response.lower()
    hits = sum(1 for term in key_terms if term in response_lower)
    return round(hits / len(key_terms), 3)


def compare_tracks(
    standard_response: str,
    glia_response: str,
    source_doc: Dict,
) -> Dict:
    """
    Score both tracks against the same source doc and return a comparison dict.

    Returns
    -------
    {
        "standard_score": float,
        "glia_score":     float,
        "winner":         "standard" | "glia" | "tie",
        "delta":          float,   # glia_score - standard_score
        "key_terms":      List[str],
    }
    """
    title   = source_doc.get("title", "")
    content = source_doc.get("content", "")[:200]
    reference = f"{title} {content}"
    key_terms = _extract_key_terms(reference)

    std_score  = score_response(standard_response, source_doc)
    glia_score = score_response(glia_response,     source_doc)
    delta      = round(glia_score - std_score, 3)

    if abs(delta) < 0.05:
        winner = "tie"
    elif glia_score > std_score:
        winner = "glia"
    else:
        winner = "standard"

    return {
        "standard_score": std_score,
        "glia_score":     glia_score,
        "winner":         winner,
        "delta":          delta,
        "key_terms":      key_terms,
    }
