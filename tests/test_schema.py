from src.schema import LabEntry, canonicalize_url, deduplicate_labs, normalize_lab_name


def test_normalize_lab_name_collapses_whitespace() -> None:
    assert normalize_lab_name("  AI   Lab\n") == "AI Lab"


def test_canonicalize_url_adds_scheme_and_strips_fragment_and_trailing_slash() -> None:
    assert canonicalize_url("example.org/lab/#team") == "https://example.org/lab"


def test_deduplicate_labs_uses_uni_name_and_domain_key() -> None:
    first = LabEntry(
        university="ethz",
        lab_name="Vision Lab",
        lab_website="https://example.org/lab-a",
        source_page="https://seed",
        extraction_method="adapter",
    )
    duplicate = LabEntry(
        university="ETHZ",
        lab_name=" Vision   Lab ",
        lab_website="https://example.org/lab-b",
        source_page="https://seed",
        extraction_method="adapter",
    )
    unique = LabEntry(
        university="ETHZ",
        lab_name="NLP Lab",
        lab_website="https://example.org/nlp",
        source_page="https://seed",
        extraction_method="adapter",
    )

    deduped = deduplicate_labs([first, duplicate, unique])

    assert len(deduped) == 2
    assert first in deduped
    assert unique in deduped
