# tests/test_library_full.py
# Amaç: Book / ComicBook / Magazine / Library API'sini ve JSON kalıcılığı test etmek.
import sys, os
# tests/ klasörünün bir üst klasörünü (proje kökünü) import yoluna ekle
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pathlib import Path
from models import Book, ComicBook, Magazine, Library


def test_book_str_format():
    # __str__ formatı örnekteki gibi olmalı
    b = Book("Ulysses", "James Joyce", "978-0199535675")
    assert str(b) == "Ulysses by James Joyce (ISBN: 978-0199535675)"


def test_comicbook_and_magazine_str_formats():
    cb = ComicBook("Watchmen", "Alan Moore", "9780930289232", illustrator="Dave Gibbons")
    mg = Magazine("National Geographic", "Various", "9770036871375", issue_number=481)

    # ComicBook: ilave bilgi "illus. <isim>" içermeli
    s_cb = str(cb)
    assert "Watchmen" in s_cb
    assert "illus. Dave Gibbons" in s_cb
    assert "(ISBN: 9780930289232)" in s_cb

    # Magazine: "Magazine Issue <no>" formatını içermeli
    s_mg = str(mg)
    assert "National Geographic Magazine Issue 481" in s_mg
    assert "(ISBN: 9770036871375)" in s_mg


def test_add_find_list_and_persistence(tmp_path: Path):
    # İzole JSON dosyasıyla çalışalım
    db = tmp_path / "library.json"
    lib = Library(db)

    b1 = Book("Dune", "Frank Herbert", "9780441172719")
    b2 = ComicBook("Batman: Year One", "Frank Miller", "9781401207526", illustrator="David Mazzucchelli")
    b3 = Magazine("Scientific American", "Various", "9770036871375", issue_number=202)

    assert lib.add_book(b1) is True
    assert lib.add_book(b2) is True
    assert lib.add_book(b3) is True

    # list_books çalışıyor mu?
    items = lib.list_books()
    assert len(items) == 3
    # find_book ISBN ile doğru nesneyi bulmalı
    assert lib.find_book("9780441172719").title == "Dune"
    assert lib.find_book("9781401207526").title.startswith("Batman")
    assert lib.find_book("9770036871375").title == "Scientific American"

    # Kalıcılık: yeni bir Library örneği aynı dosyadan yükleyince tipler korunmalı
    lib_reloaded = Library(db)
    found_dune = lib_reloaded.find_book("9780441172719")
    found_batman = lib_reloaded.find_book("9781401207526")
    found_natgeo = lib_reloaded.find_book("9770036871375")

    assert isinstance(found_dune, Book) and type(found_dune) is Book
    assert isinstance(found_batman, ComicBook)
    assert isinstance(found_natgeo, Magazine)


def test_duplicate_isbn_blocked(tmp_path: Path):
    db = tmp_path / "library.json"
    lib = Library(db)

    assert lib.add_book(Book("Clean Code", "Robert C. Martin", "9780132350884")) is True
    # Aynı ISBN'le başka bir kitap eklemeye çalışma → eklenmemeli
    assert lib.add_book(Book("Clean Code (2nd copy)", "Robert C. Martin", "9780132350884")) is False
    assert len(lib.list_books()) == 1


def test_remove_and_persist(tmp_path: Path):
    db = tmp_path / "library.json"
    lib = Library(db)

    lib.add_book(Book("The Hobbit", "J.R.R. Tolkien", "9780345339683"))
    lib.add_book(ComicBook("Spider-Man", "Stan Lee", "9781401235420", illustrator="Steve Ditko"))

    # Silme
    assert lib.remove_book("9780345339683") is True
    assert lib.find_book("9780345339683") is None
    assert len(lib.list_books()) == 1  # sadece çizgi roman kaldı

    # Yeniden yükle: silinmiş kitap geri gelmemeli
    lib2 = Library(db)
    assert lib2.find_book("9780345339683") is None
    # kalan kitap doğru tipte mi?
    remaining = lib2.list_books()[0]
    assert isinstance(remaining, ComicBook)

# --- AŞAMA 2: ISBN ile otomatik ekleme testleri ---

class DummyClient:
    """Gerçek HTTP çağrısı yapmadan OpenLibraryClient davranışını taklit eder."""
    def __init__(self, payload=None):
        self.payload = payload
    def fetch_by_isbn(self, isbn: str):
        return self.payload

def test_add_book_with_isbn_success(tmp_path: Path):
    db = tmp_path / "library.json"
    lib = Library(db)

    # API'nin döndüreceği veriyi simüle ediyoruz
    payload = {"title": "Dune", "author": "Frank Herbert", "isbn": "9780441172719"}
    ok = lib.add_book("9780441172719", client=DummyClient(payload))
    assert ok is True

    found = lib.find_book("9780441172719")
    assert found is not None
    assert found.title == "Dune"
    assert found.author == "Frank Herbert"

def test_add_book_with_isbn_not_found(tmp_path: Path):
    db = tmp_path / "library.json"
    lib = Library(db)

    # API başarısız/404 senaryosu: payload=None
    ok = lib.add_book("0000000000", client=DummyClient(payload=None))
    assert ok is False  # program çökmemeli, sadece eklemesin
    assert lib.find_book("0000000000") is None
