# models.py
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import json


# ---------- Base Class ----------
@dataclass
class Book:
    """Her bir kitabı temsil eder."""
    title: str
    author: str
    isbn: str  # benzersiz kimlik

    def __str__(self) -> str:
        return f"{self.title} by {self.author} (ISBN: {self.isbn})"


# ---------- Derived Classes ----------
@dataclass
class ComicBook(Book):
    illustrator: str

    def __str__(self) -> str:
        return f"{self.title} (Comic) by {self.author}, illus. {self.illustrator} (ISBN: {self.isbn})"


@dataclass
class Magazine(Book):
    issue_number: int

    def __str__(self) -> str:
        return f"{self.title} Magazine Issue {self.issue_number} by {self.author} (ISBN: {self.isbn})"


# ---------- Library ----------
class Library:
    """Tüm kütüphane operasyonlarını ve JSON kalıcılığını yönetir."""
    def __init__(self, db_path: str | Path = "library.json") -> None:
        self.db_path = Path(db_path)
        self.books: List[Book] = []
        self._ensure_file()
        self.load_books()

    def _ensure_file(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            self.db_path.write_text("[]", encoding="utf-8")

    def add_book(self, book_or_isbn, client=None) -> bool:
        """
        İKİ MOD:
        - Book verildiğinde: eskisi gibi ekler (Stage 1 uyumlu)
        - str (ISBN) verildiğinde: Open Library'den bilgileri çekip ekler (Stage 2)

        Dönüş: eklendiyse True, aksi halde False.
        """
        # 1) Book nesnesi ise doğrudan eski yol
        if isinstance(book_or_isbn, Book):
            if any(b.isbn == book_or_isbn.isbn for b in self.books):
                return False
            self.books.append(book_or_isbn)
            self.save_books()
            return True

        # 2) Str ISBN ise Open Library'den çek
        if isinstance(book_or_isbn, str):
            from openlibrary_client import OpenLibraryClient
            client = client or OpenLibraryClient()

            result = client.fetch_by_isbn(book_or_isbn)
            if not result:
                return False

            # Duplicate kontrolü (aynı ISBN JSON'ımızda var mı?)
            if any(b.isbn == result["isbn"] for b in self.books):
                return False

            # Book oluştur ve kaydet
            b = Book(title=result["title"], author=result["author"], isbn=result["isbn"])
            self.books.append(b)
            self.save_books()
            return True

        # 3) Ne Book ne str → desteklemiyoruz
        return False


    def remove_book(self, isbn: str) -> bool:
        before = len(self.books)
        self.books = [b for b in self.books if b.isbn != isbn]
        removed = len(self.books) != before
        if removed:
            self.save_books()
        return removed

    def list_books(self) -> List[Book]:
        return list(self.books)

    def find_book(self, isbn: str) -> Optional[Book]:
        for b in self.books:
            if b.isbn == isbn:
                return b
        return None

    def load_books(self) -> None:
        try:
            raw = self.db_path.read_text(encoding="utf-8").strip()
            data = json.loads(raw) if raw else []
            self.books = []
            for item in data:
                type_ = item.pop("type", "Book")
                if type_ == "ComicBook":
                    self.books.append(ComicBook(**item))
                elif type_ == "Magazine":
                    self.books.append(Magazine(**item))
                else:
                    self.books.append(Book(**item))
        except (OSError, json.JSONDecodeError):
            self.books = []

    def save_books(self) -> None:
        data = []
        for b in self.books:
            entry = b.__dict__.copy()
            entry["type"] = b.__class__.__name__  # Book/ComicBook/Magazine
            data.append(entry)
        text = json.dumps(data, ensure_ascii=False, indent=2)
        self.db_path.write_text(text, encoding="utf-8")
        
    def find_by_title(self, title: str):
        """Başlığa göre tek kitap döndürür (büyük/küçük harf duyarsız)."""
        needle = (title or "").strip().lower()
        for b in self.books:
            if b.title.strip().lower() == needle:
                return b
        return None

    def list_by_author(self, author: str):
        """Yazara göre tüm kitapları listeler (büyük/küçük harf duyarsız)."""
        needle = (author or "").strip().lower()
        return [b for b in self.books if b.author.strip().lower() == needle]

