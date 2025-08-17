# openlibrary_client.py
from __future__ import annotations
import re
import httpx

class OpenLibraryClient:
    BASE = "https://openlibrary.org"

    def _get_json(self, url: str, timeout: int = 10):
        r = httpx.get(url, timeout=timeout, follow_redirects=True)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def fetch_by_isbn(self, isbn: str) -> dict | None:
        """ISBN -> {title, author, isbn} (başarısızlıkta None)."""
        if not isbn:
            return None

        raw = isbn.strip()
        normalized = re.sub(r"[^0-9Xx]", "", raw)  # 978-... -> 978...

        # Önce ham, olmazsa normalize dene
        for candidate in [raw, normalized] if raw != normalized else [raw]:
            try:
                data = self._get_json(f"{self.BASE}/isbn/{candidate}.json")
            except (httpx.RequestError, httpx.HTTPStatusError):
                data = None
            if not data:
                continue

            title = data.get("title")
            if not title:
                continue

            # Yazar isimleri (opsiyonel)
            authors = []
            for a in data.get("authors", []):
                key = a.get("key")
                if not key:
                    continue
                try:
                    adata = self._get_json(f"{self.BASE}{key}.json")
                    name = adata.get("name") if adata else None
                    if name:
                        authors.append(name)
                except (httpx.RequestError, httpx.HTTPStatusError):
                    pass

            author_str = ", ".join(authors) if authors else "Unknown"
            return {"title": title, "author": author_str, "isbn": normalized or raw}

        return None

