"""Moteur d'anonymisation : détection d'entités puis remplacement dans le texte."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from .detectors import DEFAULT_DETECTOR_KEYS, RawMatch, run_regex_detectors
from .ner import find_named_entities

MASK_MODE = "mask"
PSEUDONYMIZE_MODE = "pseudonymize"

_PSEUDO_FIRST_NAMES = [
    "Alex", "Camille", "Dominique", "Sacha", "Lou", "Noa", "Charlie", "Andrea",
]
_PSEUDO_LAST_NAMES = [
    "Martin", "Bernard", "Dubois", "Petit", "Durand", "Leroy", "Moreau", "Simon",
]


@dataclass(frozen=True)
class EntityMatch:
    start: int
    end: int
    text: str
    entity_type: str


@dataclass
class AnonymizationResult:
    text: str
    matches: List[EntityMatch] = field(default_factory=list)
    mapping: Dict[str, str] = field(default_factory=dict)


def _resolve_overlaps(matches: List[RawMatch]) -> List[RawMatch]:
    """En cas de chevauchement entre détecteurs, garde le match le plus long
    (ex : une adresse contenant un code postal ne doit pas être coupée)."""
    ordered = sorted(matches, key=lambda m: (m.start, -(m.end - m.start)))
    resolved: List[RawMatch] = []
    last_end = -1
    for m in ordered:
        if m.start >= last_end:
            resolved.append(m)
            last_end = m.end
    return resolved


class Anonymizer:
    def __init__(
        self,
        entity_types: Optional[Iterable[str]] = None,
        mode: str = MASK_MODE,
        use_ner: bool = False,
        language: str = "fr",
    ):
        if mode not in (MASK_MODE, PSEUDONYMIZE_MODE):
            raise ValueError(f"Mode inconnu : {mode}")
        self.entity_types = tuple(entity_types) if entity_types else DEFAULT_DETECTOR_KEYS
        self.mode = mode
        self.use_ner = use_ner
        self.language = language

        # Mapping conservé sur toute la durée de vie de l'instance pour que
        # la même valeur d'origine produise toujours le même remplacement,
        # y compris entre plusieurs paragraphes/fichiers traités ensemble.
        self._mapping: Dict[str, str] = {}
        self._counters: Dict[str, int] = {}

    def detect(self, text: str) -> List[EntityMatch]:
        raw: List[RawMatch] = run_regex_detectors(text, self.entity_types)
        if self.use_ner:
            raw.extend(find_named_entities(text, self.language))
        resolved = _resolve_overlaps(raw)
        return [EntityMatch(m.start, m.end, m.text, m.entity_type) for m in resolved]

    def _replacement_for(self, entity_type: str, original: str) -> str:
        cache_key = f"{entity_type}::{original}"
        if cache_key in self._mapping:
            return self._mapping[cache_key]

        count = self._counters.get(entity_type, 0) + 1
        self._counters[entity_type] = count

        if self.mode == MASK_MODE:
            replacement = f"[{entity_type}_{count}]"
        else:
            replacement = self._pseudonym(entity_type, count)

        self._mapping[cache_key] = replacement
        return replacement

    @staticmethod
    def _pseudonym(entity_type: str, count: int) -> str:
        if entity_type == "PERSONNE":
            first = _PSEUDO_FIRST_NAMES[(count - 1) % len(_PSEUDO_FIRST_NAMES)]
            last = _PSEUDO_LAST_NAMES[(count - 1) % len(_PSEUDO_LAST_NAMES)]
            suffix = "" if count <= len(_PSEUDO_LAST_NAMES) else f" {count}"
            return f"{first} {last}{suffix}"
        if entity_type == "EMAIL":
            return f"personne{count}@exemple.fr"
        if entity_type == "TELEPHONE":
            return f"06 00 00 {count // 100:02d} {count % 100:02d}"
        if entity_type == "IBAN":
            return f"FR76XXXXXXXXXXXXXXXXXXX{count:03d}"
        if entity_type == "CARTE_BANCAIRE":
            return f"4111 1111 1111 {1000 + count}"
        if entity_type == "NIR":
            return f"1XXXXXXXXXXX{count:02d}"
        if entity_type == "ADRESSE_IP":
            return f"10.0.{count // 254}.{count % 254 + 1}"
        if entity_type == "URL":
            return f"https://exemple-{count}.fr"
        if entity_type == "ORGANISATION":
            return f"Société {count}"
        if entity_type == "LIEU":
            return f"Ville {count}"
        if entity_type == "ADRESSE":
            return f"[ADRESSE_{count}]"
        return f"[{entity_type}_{count}]"

    def anonymize_text(self, text: str) -> AnonymizationResult:
        matches = self.detect(text)
        if not matches:
            return AnonymizationResult(text=text, matches=[], mapping={})

        pieces = []
        cursor = 0
        for m in matches:
            pieces.append(text[cursor:m.start])
            pieces.append(self._replacement_for(m.entity_type, m.text))
            cursor = m.end
        pieces.append(text[cursor:])

        return AnonymizationResult(
            text="".join(pieces),
            matches=matches,
            mapping=dict(self._mapping),
        )

    @property
    def mapping(self) -> Dict[str, str]:
        """Table originale -> remplacement accumulée depuis la création de
        cette instance. À conserver séparément du document anonymisé : sa
        diffusion avec le document annule l'anonymisation."""
        return dict(self._mapping)
