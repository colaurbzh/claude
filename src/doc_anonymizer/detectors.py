"""Détecteurs regex pour les principales informations personnelles.

Chaque détecteur retourne des correspondances (start, end, text) trouvées
dans une chaîne de caractères. Les détecteurs à fort taux de faux positifs
(carte bancaire, NIR) appliquent une validation de la clé de contrôle pour
limiter le bruit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable, List


@dataclass(frozen=True)
class RawMatch:
    start: int
    end: int
    text: str
    entity_type: str


def _luhn_valid(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _nir_valid(digits: str) -> bool:
    """Valide un NIR (numéro de sécurité sociale français) à 15 chiffres
    via sa clé de contrôle (97 - (nombre mod 97))."""
    if len(digits) != 15:
        return False
    number, key = digits[:13], digits[13:]
    # Le code département 2A/2B (Corse) n'est pas géré ici : cas rare, ignoré.
    try:
        n = int(number)
    except ValueError:
        return False
    expected = 97 - (n % 97)
    return expected == int(key)


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

PHONE_FR_RE = re.compile(
    r"(?<!\d)(?:\+33[\s.\-]?|0)[1-9](?:[\s.\-]?\d{2}){4}(?!\d)"
)

PHONE_INTL_RE = re.compile(
    r"(?<!\d)\+(?!33)[1-9]\d{0,2}(?:[\s.\-]?\d{2,4}){3,5}(?!\d)"
)

IBAN_RE = re.compile(
    r"(?<![A-Z0-9])[A-Z]{2}\d{2}[\s]?(?:[A-Z0-9]{4}[\s]?){2,7}[A-Z0-9]{1,4}(?![A-Z0-9])"
)

CARD_CANDIDATE_RE = re.compile(r"(?<!\d)(?:\d[\s\-]?){13,19}(?!\d)")

NIR_CANDIDATE_RE = re.compile(r"(?<!\d)[12]\s?\d{2}\s?\d{2}\s?(?:\d{2}|2[AB])\s?\d{3}\s?\d{3}\s?\d{2}(?!\d)")

IP_RE = re.compile(
    r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?!\d)"
)

URL_RE = re.compile(r"\bhttps?://[^\s<>\"]+")

DATE_RE = re.compile(
    r"\b(?:0?[1-9]|[12]\d|3[01])[/\-.](?:0?[1-9]|1[0-2])[/\-.](?:\d{4}|\d{2})\b"
)

POSTAL_ADDRESS_FR_RE = re.compile(
    r"\b\d{1,4}[\s,]+"
    r"(?:rue|avenue|boulevard|impasse|chemin|allée|place|route|quai|clos|square)"
    r"[\s]+(?:[A-Za-zÀ-ÿ'\-]+[\s]*){1,5},?\s*\d{5}\s+[A-Za-zÀ-ÿ'\-\s]{2,40}",
    re.IGNORECASE,
)


def _find_email(text: str) -> Iterable[RawMatch]:
    for m in EMAIL_RE.finditer(text):
        yield RawMatch(m.start(), m.end(), m.group(), "EMAIL")


def _find_phone(text: str) -> Iterable[RawMatch]:
    seen_spans = []
    for m in PHONE_FR_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 9 <= len(digits) <= 11:
            seen_spans.append((m.start(), m.end()))
            yield RawMatch(m.start(), m.end(), m.group(), "TELEPHONE")
    for m in PHONE_INTL_RE.finditer(text):
        if any(a <= m.start() < b for a, b in seen_spans):
            continue
        digits = re.sub(r"\D", "", m.group())
        if 8 <= len(digits) <= 15:
            yield RawMatch(m.start(), m.end(), m.group(), "TELEPHONE")


def _find_iban(text: str) -> Iterable[RawMatch]:
    for m in IBAN_RE.finditer(text):
        candidate = m.group().replace(" ", "")
        if 15 <= len(candidate) <= 34 and candidate[:2].isalpha() and candidate[2:4].isdigit():
            yield RawMatch(m.start(), m.end(), m.group(), "IBAN")


def _find_card(text: str) -> Iterable[RawMatch]:
    for m in CARD_CANDIDATE_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and _luhn_valid(digits):
            yield RawMatch(m.start(), m.end(), m.group(), "CARTE_BANCAIRE")


def _find_nir(text: str) -> Iterable[RawMatch]:
    for m in NIR_CANDIDATE_RE.finditer(text):
        digits = re.sub(r"\s", "", m.group())
        if "2A" in digits.upper() or "2B" in digits.upper():
            continue
        if _nir_valid(digits):
            yield RawMatch(m.start(), m.end(), m.group(), "NIR")


def _find_ip(text: str) -> Iterable[RawMatch]:
    for m in IP_RE.finditer(text):
        yield RawMatch(m.start(), m.end(), m.group(), "ADRESSE_IP")


def _find_url(text: str) -> Iterable[RawMatch]:
    for m in URL_RE.finditer(text):
        yield RawMatch(m.start(), m.end(), m.group(), "URL")


def _find_date(text: str) -> Iterable[RawMatch]:
    for m in DATE_RE.finditer(text):
        yield RawMatch(m.start(), m.end(), m.group(), "DATE")


def _find_address(text: str) -> Iterable[RawMatch]:
    for m in POSTAL_ADDRESS_FR_RE.finditer(text):
        yield RawMatch(m.start(), m.end(), m.group(), "ADRESSE")


# Registre des détecteurs disponibles, activables individuellement via la CLI.
DETECTORS: dict[str, Callable[[str], Iterable[RawMatch]]] = {
    "email": _find_email,
    "phone": _find_phone,
    "iban": _find_iban,
    "card": _find_card,
    "nir": _find_nir,
    "ip": _find_ip,
    "url": _find_url,
    "date": _find_date,
    "address": _find_address,
}

DEFAULT_DETECTOR_KEYS = tuple(DETECTORS.keys())


def run_regex_detectors(text: str, keys: Iterable[str]) -> List[RawMatch]:
    matches: List[RawMatch] = []
    for key in keys:
        detector = DETECTORS.get(key)
        if detector is None:
            raise ValueError(f"Détecteur inconnu : {key}")
        matches.extend(detector(text))
    return matches
