from conftest import PDF_URL, TEST_PORT
from zotlocal.client import Client
from zotlocal.pdf import find_pdfs


def test_find_pdfs_returns_attachment_with_url(library_opener) -> None:
    client = Client(port=TEST_PORT, timeout=0.2, opener=library_opener)
    found = find_pdfs(client, "PXW99EKT")
    assert found
    hit = next(row for row in found if row["key"] == "PDFATT01")
    assert hit["url"]
    assert hit["url"] == PDF_URL
    assert "pdf" in hit["contentType"]
