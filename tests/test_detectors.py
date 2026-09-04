from doc_anonymizer.detectors import run_regex_detectors


def _texts(matches):
    return sorted(m.text for m in matches)


def test_email_detection():
    matches = run_regex_detectors("Contact : jean.dupont@exemple.fr pour info.", ["email"])
    assert _texts(matches) == ["jean.dupont@exemple.fr"]


def test_phone_fr_detection():
    text = "Appelez le 06 12 34 56 78 ou le +33 6 12 34 56 78."
    matches = run_regex_detectors(text, ["phone"])
    assert len(matches) == 2


def test_iban_detection():
    text = "IBAN : FR76 3000 6000 0112 3456 7890 189"
    matches = run_regex_detectors(text, ["iban"])
    assert len(matches) == 1
    assert matches[0].text.startswith("FR76")


def test_card_luhn_validation_rejects_invalid_number():
    # 16 chiffres mais échec de la clé de Luhn : ne doit pas être détecté.
    text = "Numéro : 1234 5678 9012 3456"
    matches = run_regex_detectors(text, ["card"])
    assert matches == []


def test_card_luhn_validation_accepts_valid_number():
    # Numéro de test Visa standard, valide au sens de Luhn.
    text = "Carte : 4111 1111 1111 1111"
    matches = run_regex_detectors(text, ["card"])
    assert len(matches) == 1


def test_nir_checksum_validation():
    # NIR valide construit avec sa clé de contrôle correcte (97 - n % 97).
    valid_nir = "185018712345673"
    matches = run_regex_detectors(f"NIR : {valid_nir}", ["nir"])
    assert len(matches) == 1

    invalid_nir = "185018712345699"
    matches = run_regex_detectors(f"NIR : {invalid_nir}", ["nir"])
    assert matches == []


def test_ip_detection():
    matches = run_regex_detectors("Adresse IP : 192.168.1.42", ["ip"])
    assert _texts(matches) == ["192.168.1.42"]


def test_url_detection():
    matches = run_regex_detectors("Voir https://exemple.fr/page?x=1 pour plus.", ["url"])
    assert _texts(matches) == ["https://exemple.fr/page?x=1"]


def test_date_detection():
    matches = run_regex_detectors("Né le 12/05/1990.", ["date"])
    assert _texts(matches) == ["12/05/1990"]


def test_unknown_detector_raises():
    import pytest

    with pytest.raises(ValueError):
        run_regex_detectors("texte", ["inconnu"])
