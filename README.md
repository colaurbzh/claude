# doc-anonymizer

Anonymiseur de documents en ligne de commande : détecte et remplace les
informations personnelles courantes dans des fichiers `.txt`, `.md`,
`.csv`, `.docx` et `.pdf`.

## Installation

```bash
pip install -e .
# Optionnel : détection de noms de personnes/organisations/lieux
pip install -e ".[ner]"
python -m spacy download fr_core_news_sm
# Optionnel : vrai caviardage des PDF (sinon, repli sur un export .txt)
pip install -e ".[pdf-redact]"
```

## Utilisation

```bash
doc-anonymizer contrat.docx
doc-anonymizer export.csv -o export_anonyme.csv
doc-anonymizer rapport.pdf --mode pseudonymize
doc-anonymizer lettre.txt --ner --language fr --mapping-out mapping.json
```

Options principales :

| Option | Description |
|---|---|
| `-o, --output` | Fichier de sortie (défaut : `<nom>.anonymise<ext>`) |
| `--mode` | `mask` (balises `[TYPE_N]`, défaut) ou `pseudonymize` (valeurs fictives plausibles) |
| `--types` | Sous-ensemble de détecteurs à activer (`email,phone,iban,card,nir,ip,url,date,address`) |
| `--ner` | Active la détection de noms via spaCy (personnes, organisations, lieux) |
| `--language` | Langue du modèle spaCy (`fr` par défaut, ou `en`) |
| `--mapping-out` | Écrit la table valeur d'origine → remplacement dans un JSON séparé |

## Ce qui est détecté

Par regex (avec validation quand c'est possible) :

- Email
- Téléphone (FR et international)
- IBAN
- Carte bancaire (validée par la clé de Luhn)
- NIR / numéro de sécurité sociale français (validé par sa clé de contrôle)
- Adresse IP
- URL
- Date
- Adresse postale française (heuristique, format `N rue/avenue/... , CP Ville`)

Avec `--ner` (optionnel, nécessite spaCy) :

- Noms de personnes, organisations, lieux

## Limites — à lire avant tout usage réel

Cet outil est une aide à l'anonymisation, **pas une garantie de conformité
RGPD** ni une anonymisation certifiée irréversible. Il repose sur des
règles regex et, en option, un modèle de NER généraliste :

- Les faux négatifs sont possibles (formats de téléphone ou d'adresse non
  couverts, noms non reconnus par le NER, PII écrites de façon inhabituelle).
- Les faux positifs sont possibles (peu, grâce aux validations de clé, mais
  non nuls).
- **Docx** : un paragraphe est anonymisé comme un bloc de texte, puis
  réinjecté dans son premier "run" ; une mise en forme différente au sein
  d'un même paragraphe (ex. un mot en gras) n'est pas préservée si ce mot
  est remplacé. Les en-têtes, pieds de page et zones de texte ne sont pas
  traités.
- **PDF** : sans PyMuPDF, seul le texte extrait est anonymisé (export
  `.txt`), le PDF original n'est pas modifié. Avec PyMuPDF, le caviardage
  est réel (le texte est effacé du PDF), mais une correspondance répartie
  sur plusieurs lignes peut ne pas être localisée visuellement. Les PDF
  scannés (images sans couche texte) ne sont pas gérés : passer par un OCR
  au préalable.
- Le mode `pseudonymize` produit des valeurs plausibles mais **pas
  aléatoires de façon cryptographique** : ne pas l'utiliser comme mécanisme
  de sécurité.
- Le fichier `--mapping-out`, s'il est généré, permet de retrouver les
  valeurs d'origine : à conserver séparément du document anonymisé, et de
  façon sécurisée, ou à ne pas générer si l'irréversibilité est requise.

**Recommandation** : relire manuellement le document produit avant toute
diffusion, en particulier pour des données sensibles ou un contexte
réglementaire (RGPD, secret médical, etc.).

## Développement

```bash
pip install -e ".[dev]"
pytest
```
