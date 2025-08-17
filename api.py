# api.py
from __future__ import annotations

import os
from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware   # 👈 EKLENDİ
from pydantic import BaseModel, Field

from models import Library, Book


# ------------ Pydantic Şemaları ------------
class ISBNIn(BaseModel):
    isbn: str = Field(..., min_length=5, description="Ör: 9780441172719 veya 978-0441172719")


class BookOut(BaseModel):
    title: str
    author: str
    isbn: str
    kind: str  # Book / ComicBook / Magazine

    @staticmethod
    def from_book(b: Book) -> "BookOut":
        return BookOut(title=b.title, author=b.author, isbn=b.isbn, kind=b.__class__.__name__)


# ------------ Uygulama Fabrikası ------------
def create_app(db_path: str | None = None) -> FastAPI:
    """
    Testlerde farklı bir DB yolu verebilmek için app'i fabrika ile kuruyoruz.
    Varsayılan: 'library.json'
    """
    app = FastAPI(title="Library API", version="1.0.0")

    # 🌍 CORS Middleware — herkese açık
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],       # tüm domainlere izin ver
        allow_methods=["*"],       # GET, POST, DELETE, vs.
        allow_headers=["*"],       # tüm header'lara izin ver
    )

    # Tek bir Library örneği: uygulama yaşamı boyunca paylaşılsın
    db_file = db_path or os.getenv("LIB_DB_PATH", "library.json")
    app.state.lib = Library(db_file)

    # ------------- Endpoint'ler -------------

    @app.get("/books", response_model=List[BookOut])
    def list_books():
        """Kütüphanedeki tüm kitapları döndürür."""
        items = app.state.lib.list_books()
        return [BookOut.from_book(b) for b in items]

    @app.post("/books", response_model=BookOut, status_code=status.HTTP_201_CREATED)
    def add_book(payload: ISBNIn):
        """
        Body: {"isbn": "<numara>"}
        - ISBN string verilirse Aşama 2'deki mantık tetiklenir (Open Library'den çeker).
        - Başarı: 201 + eklenen kitabı döner
        - Hata: 409 (zaten var) | 404 (bulunamadı) | 400 (geçersiz)
        """
        isbn = (payload.isbn or "").strip()
        if not isbn:
            raise HTTPException(status_code=400, detail="ISBN boş olamaz.")

        # Zaten var mı? (basit kontrol — normalization yapmıyoruz)
        if app.state.lib.find_book(isbn) is not None:
            raise HTTPException(status_code=409, detail="Bu ISBN zaten kayıtlı.")

        ok = app.state.lib.add_book(isbn)
        if not ok:
            raise HTTPException(status_code=404, detail="ISBN bulunamadı veya dış servis hatası.")

        # yeni eklenen kitabı geri oku ve döndür
        b = app.state.lib.find_book(isbn)
        return BookOut.from_book(b)

    @app.delete("/books/{isbn}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_book(isbn: str):
        """
        Belirtilen ISBN'e sahip kitabı siler.
        - Başarı: 204
        - Yoksa: 404
        """
        ok = app.state.lib.remove_book(isbn)
        if not ok:
            raise HTTPException(status_code=404, detail="Silinecek ISBN bulunamadı.")
        return  # 204

    return app


# Varsayılan uygulama (yerel çalıştırma)
app = create_app()
