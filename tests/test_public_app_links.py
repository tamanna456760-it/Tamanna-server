from pathlib import Path


def test_public_landing_page_links_to_chat_and_admin_apps():
    page = (Path(__file__).resolve().parents[1] / "Wabsite" / "Index.html").read_text()
    assert 'href="https://tamanna456760-it.github.io/tamanna-website/"' in page
    assert 'href="https://tamanna456760-it.github.io/tamanna-website/admin/"' in page
    assert "Open Tamanna AI Chat" in page
    assert "Open Tamanna Admin" in page
