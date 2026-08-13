from zotlocal.models import citekey_from_data, format_authors, year_from_date


def test_citekey_from_data_reads_extra() -> None:
    assert citekey_from_data({"extra": "Citation Key: foo"}) == "foo"


def test_citekey_from_data_reads_fixture_extra(items_payload: list) -> None:
    data = next(row["data"] for row in items_payload if row["key"] == "PXW99EKT")
    assert data["extra"] == "Citation Key: vaswani_attention_2017"
    assert citekey_from_data(data) == "vaswani_attention_2017"


def test_format_authors_et_al() -> None:
    creators = [
        {"creatorType": "author", "firstName": "Ashish", "lastName": "Vaswani"},
        {"creatorType": "author", "firstName": "Noam", "lastName": "Shazeer"},
        {"creatorType": "author", "firstName": "Niki", "lastName": "Parmar"},
    ]
    assert format_authors(creators) == "Vaswani et al."


def test_year_from_date() -> None:
    assert year_from_date("2017-06-12") == "2017"
