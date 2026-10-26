"""Ensure the browser entry point and its bundled assets ship with the API."""

from html.parser import HTMLParser

from fastapi.testclient import TestClient

from app.main import app


class PageAssets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "script" and attributes.get("src"):
            self.paths.append(attributes["src"])
        if tag == "link" and attributes.get("rel") == "stylesheet":
            self.paths.append(attributes["href"])


def test_browser_page_and_linked_assets_are_served():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert response.headers["cache-control"] == "no-cache"
        parser = PageAssets()
        parser.feed(response.text)
        assert parser.paths, "The UI must include its browser assets"
        for path in parser.paths:
            assert path.startswith("/assets/")
            asset = client.get(path)
            assert asset.status_code == 200, path
            assert asset.content, path
            assert not asset.headers["content-type"].startswith("text/html"), path
