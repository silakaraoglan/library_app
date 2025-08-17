# tests/test_api.py
import sys, os
# tests/ klasörünün bir üst klasörünü (proje kökünü) import yoluna ekle
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import os
import json
import httpx
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from api import create_app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch):
    # Her test için izole DB dosyası
    db = tmp_path / "library.json"
    app = create_app(str(db))
    return TestClient(app)


def test_get_books_initially_empty(client):
    r = client.get("/books")
    assert r.status_code == 200
    assert r.json() == []


def test_post_books_success_with_isbn(client, monkeypatch):
    # httpx.get'i taklit ederek Open Library çağrılarını sahte yanıtla dolduruyoruz
    def fake_get(url, timeout=10):
        # /isbn/<isbn>.json
        if url.endswith("/isbn/9780441172719.json"):
            payload = {"title": "Dune", "authors": [{"key": "/authors/OL2162288A"}]}
            return _resp(200, payload)
        # /authors/<key>.json
        if url.endswith("/authors/OL2162288A.json"):
            return _resp(200, {"name": "Frank Herbert"})
        return _resp(404, {"error": "not found"})

    def _resp(status, data):
        r = httpx.Response(status_code=status, request=httpx.Request("GET", "http://x"))
        r._content = json.dumps(data).encode("utf-8")
        return r

    monkeypatch.setattr(httpx, "get", fake_get)

    # POST /books
    r = client.post("/books", json={"isbn": "9780441172719"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["title"] == "Dune"
    assert body["author"] == "Frank Herbert"
    assert body["isbn"] == "9780441172719"
    assert body["kind"] == "Book"

    # GET /books → 1 kayıt
    r = client.get("/books")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_post_books_not_found_returns_404(client, monkeypatch):
    def fake_get(url, timeout=10):
        return httpx.Response(status_code=404, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    r = client.post("/books", json={"isbn": "0000000000"})
    assert r.status_code == 404
    assert "bulunamadı" in r.json()["detail"].lower()


def test_delete_books_flow(client, monkeypatch):
    # önce bir tane başarıyla ekleyelim
    def fake_get(url, timeout=10):
        if url.endswith("/isbn/9780132350884.json"):
            return _resp(200, {"title": "Clean Code", "authors": [{"key": "/authors/OL72011A"}]})
        if url.endswith("/authors/OL72011A.json"):
            return _resp(200, {"name": "Robert C. Martin"})
        return _resp(404, {"error": "not found"})

    def _resp(status, data):
        r = httpx.Response(status_code=status, request=httpx.Request("GET", "http://x"))
        r._content = json.dumps(data).encode("utf-8")
        return r

    monkeypatch.setattr(httpx, "get", fake_get)

    r = client.post("/books", json={"isbn": "9780132350884"})
    assert r.status_code == 201

    # sil
    r = client.delete("/books/9780132350884")
    assert r.status_code == 204

    # tekrar silmeye kalkınca 404
    r = client.delete("/books/9780132350884")
    assert r.status_code == 404
