"""Détection de noms de personnes / organisations / lieux via spaCy.

Dépendance optionnelle : si spaCy ou le modèle demandé n'est pas installé,
`load_ner` renvoie None et l'appelant doit se rabattre sur la détection
regex uniquement.
"""

from __future__ import annotations

from typing import List, Optional

from .detectors import RawMatch

_NER_TYPE_MAP = {
    "PER": "PERSONNE",
    "PERSON": "PERSONNE",
    "ORG": "ORGANISATION",
    "LOC": "LIEU",
    "GPE": "LIEU",
}

_MODEL_BY_LANG = {
    "fr": "fr_core_news_sm",
    "en": "en_core_web_sm",
}

_nlp_cache: dict[str, object] = {}


def load_ner(language: str = "fr"):
    """Charge (et met en cache) le modèle spaCy demandé. Renvoie None si
    spaCy ou le modèle ne sont pas disponibles."""
    if language in _nlp_cache:
        return _nlp_cache[language]

    try:
        import spacy
    except ImportError:
        _nlp_cache[language] = None
        return None

    model_name = _MODEL_BY_LANG.get(language, language)
    try:
        nlp = spacy.load(model_name)
    except OSError:
        _nlp_cache[language] = None
        return None

    _nlp_cache[language] = nlp
    return nlp


def find_named_entities(text: str, language: str = "fr") -> List[RawMatch]:
    nlp = load_ner(language)
    if nlp is None:
        return []

    matches: List[RawMatch] = []
    doc = nlp(text)
    for ent in doc.ents:
        entity_type = _NER_TYPE_MAP.get(ent.label_)
        if entity_type is None:
            continue
        matches.append(RawMatch(ent.start_char, ent.end_char, ent.text, entity_type))
    return matches
