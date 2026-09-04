from doc_anonymizer.anonymizer import Anonymizer


def test_mask_mode_replaces_and_is_consistent():
    text = "Contactez jean@exemple.fr ou re-écrivez à jean@exemple.fr."
    anonymizer = Anonymizer(entity_types=["email"], mode="mask")
    result = anonymizer.anonymize_text(text)

    assert "jean@exemple.fr" not in result.text
    assert result.text.count("[EMAIL_1]") == 2
    assert len(result.matches) == 2


def test_mask_mode_increments_counter_per_distinct_value():
    text = "a@exemple.fr et b@exemple.fr"
    anonymizer = Anonymizer(entity_types=["email"], mode="mask")
    result = anonymizer.anonymize_text(text)

    assert "[EMAIL_1]" in result.text
    assert "[EMAIL_2]" in result.text


def test_pseudonymize_mode_produces_plausible_values():
    text = "Email : test@exemple.fr"
    anonymizer = Anonymizer(entity_types=["email"], mode="pseudonymize")
    result = anonymizer.anonymize_text(text)

    assert "test@exemple.fr" not in result.text
    assert "@exemple.fr" in result.text


def test_no_match_returns_original_text_untouched():
    anonymizer = Anonymizer(entity_types=["email"], mode="mask")
    result = anonymizer.anonymize_text("Rien à signaler ici.")
    assert result.text == "Rien à signaler ici."
    assert result.matches == []


def test_mapping_is_reusable_across_calls():
    anonymizer = Anonymizer(entity_types=["email"], mode="mask")
    anonymizer.anonymize_text("a@exemple.fr")
    result2 = anonymizer.anonymize_text("a@exemple.fr encore")
    assert "[EMAIL_1]" in result2.text
    assert anonymizer.mapping["EMAIL::a@exemple.fr"] == "[EMAIL_1]"


def test_overlap_resolution_prefers_longest_match():
    text = "12 rue des Lilas, 75001 Paris"
    anonymizer = Anonymizer(entity_types=["address"], mode="mask")
    result = anonymizer.anonymize_text(text)
    assert len(result.matches) == 1
    assert result.matches[0].entity_type == "ADRESSE"
