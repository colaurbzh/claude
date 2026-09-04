from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .anonymizer import MASK_MODE, PSEUDONYMIZE_MODE, Anonymizer
from .detectors import DEFAULT_DETECTOR_KEYS
from .formats import HANDLERS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="doc-anonymizer",
        description=(
            "Anonymise un document (txt, md, csv, docx, pdf) en détectant et en "
            "remplaçant les informations personnelles courantes (email, téléphone, "
            "IBAN, carte bancaire, NIR, IP, URL, dates, adresses, et noms de "
            "personnes/organisations/lieux avec --ner)."
        ),
    )
    parser.add_argument("input", type=Path, help="Fichier source à anonymiser")
    parser.add_argument(
        "-o", "--output", type=Path, default=None,
        help="Fichier de sortie (par défaut : <nom>.anonymise<extension>)",
    )
    parser.add_argument(
        "--mode", choices=[MASK_MODE, PSEUDONYMIZE_MODE], default=MASK_MODE,
        help="mask : remplace par des balises [TYPE_N] (défaut). "
             "pseudonymize : remplace par des valeurs fictives plausibles.",
    )
    parser.add_argument(
        "--types", default=",".join(DEFAULT_DETECTOR_KEYS),
        help=f"Types à détecter, séparés par des virgules parmi : {', '.join(DEFAULT_DETECTOR_KEYS)} "
             "(défaut : tous)",
    )
    parser.add_argument(
        "--ner", action="store_true",
        help="Active la détection de noms de personnes/organisations/lieux via spaCy "
             "(nécessite `pip install doc-anonymizer[ner]` et un modèle spaCy téléchargé)",
    )
    parser.add_argument(
        "--language", default="fr", choices=["fr", "en"],
        help="Langue du modèle spaCy à utiliser avec --ner (défaut : fr)",
    )
    parser.add_argument(
        "--mapping-out", type=Path, default=None,
        help="Écrit la table de correspondance (valeur d'origine -> remplacement) dans ce fichier JSON. "
             "À conserver séparément et en sécurité : sa diffusion avec le document annule l'anonymisation.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Affiche les journaux détaillés")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    if not args.input.exists():
        parser.error(f"Fichier introuvable : {args.input}")

    suffix = args.input.suffix.lower()
    handler = HANDLERS.get(suffix)
    if handler is None:
        supported = ", ".join(sorted(HANDLERS))
        parser.error(f"Format non pris en charge : {suffix} (formats supportés : {supported})")

    output_path = args.output or args.input.with_suffix(f".anonymise{args.input.suffix}")
    entity_types = [t.strip() for t in args.types.split(",") if t.strip()]

    anonymizer = Anonymizer(
        entity_types=entity_types,
        mode=args.mode,
        use_ner=args.ner,
        language=args.language,
    )

    if args.ner:
        from .ner import load_ner
        if load_ner(args.language) is None:
            logging.warning(
                "--ner demandé mais spaCy ou le modèle '%s' est indisponible : "
                "la détection de noms sera ignorée. Installez avec "
                "`pip install doc-anonymizer[ner] && python -m spacy download %s`.",
                args.language,
                "fr_core_news_sm" if args.language == "fr" else "en_core_web_sm",
            )

    match_count = handler(args.input, output_path, anonymizer)

    print(f"{match_count} élément(s) anonymisé(s). Fichier écrit : {output_path}")

    if args.mapping_out:
        args.mapping_out.write_text(
            json.dumps(anonymizer.mapping, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Table de correspondance écrite : {args.mapping_out} (à conserver en sécurité)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
