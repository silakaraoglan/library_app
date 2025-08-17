# main.py
from models import Book, ComicBook, Magazine, Library

def print_menu():
    print("\n--- Kütüphane ---")
    print("1) Kitap Ekle")
    print("2) Kitap Sil (ISBN)")
    print("3) Kitapları Listele")
    print("4) Kitap Ara (ISBN)")
    print("5) Başlığa Göre Ara")          # YENİ
    print("6) Yazara Göre Listele")       # YENİ
    print("7) Çıkış")


def prompt_book_type() -> str:
    print("\nEklenecek eser türünü seç:")
    print("1) Book (normal kitap)")
    print("2) ComicBook (çizgi roman)")
    print("3) Magazine (dergi)")
    choice = input("Seçim: ").strip()
    mapping = {"1": "Book", "2": "ComicBook", "3": "Magazine"}
    return mapping.get(choice, "Book")

def handle_add(lib: Library):
    kind = prompt_book_type()

    title = input("Başlık: ").strip()
    author = input("Yazar: ").strip()
    isbn = input("ISBN: ").strip()

    if kind == "ComicBook":
        illustrator = input("Çizer (illustrator): ").strip()
        book = ComicBook(title=title, author=author, isbn=isbn, illustrator=illustrator)
    elif kind == "Magazine":
        # Basit/sağlam okuma:
        while True:
            issue_raw = input("Sayı (issue_number): ").strip()
            if issue_raw.isdigit():
                issue_number = int(issue_raw)
                break
            print("Lütfen pozitif bir sayı girin.")
        book = Magazine(title=title, author=author, isbn=isbn, issue_number=issue_number)
    else:
        book = Book(title=title, author=author, isbn=isbn)

    ok = lib.add_book(book)
    print("Eklendi ✅" if ok else "Eklenemedi ❌ (Aynı ISBN zaten var mı / ISBN boş mu?)")

def handle_add_auto(lib: Library):
    isbn = input("ISBN: ").strip()
    ok = lib.add_book(isbn)  # <-- sadece ISBN string veriyoruz
    print("Eklendi ✅ (Open Library)" if ok else "Eklenemedi ❌ (İnternet/ISBN bulunamadı ya da ISBN zaten var)")

def handle_remove(lib: Library):
    isbn = input("Silinecek ISBN: ").strip()
    ok = lib.remove_book(isbn)
    print("Silindi ✅" if ok else "Bulunamadı ❌")

def handle_list(lib: Library):
    items = lib.list_books()
    if not items:
        print("Kütüphane boş.")
        return
    print("\n--- Tüm Kitaplar ---")
    for i, b in enumerate(items, start=1):
        # Polimorfizm: __str__ her sınıfta farklı
        print(f"{i}. {b}")

def handle_find(lib: Library):
    isbn = input("Aranacak ISBN: ").strip()
    b = lib.find_book(isbn)
    if b:
        print("Bulundu:", b)
    else:
        print("Bulunamadı ❌")

def handle_find_by_title(lib: Library):
    title = input("Başlık: ").strip()
    b = lib.find_by_title(title)
    print(b if b else "Bulunamadı ❌")

def handle_list_by_author(lib: Library):
    author = input("Yazar: ").strip()
    items = lib.list_by_author(author)
    if not items:
        print("Bu yazar için kayıt yok.")
    else:
        for i, b in enumerate(items, start=1):
            print(f"{i}. {b}")


def main():
    lib = Library("library.json")
    while True:
        print_menu()
        choice = input("Seçim: ").strip()
        if choice == "1":
            handle_add(lib)
        elif choice == "2":
            handle_remove(lib)
        elif choice == "3":
            handle_list(lib)
        elif choice == "4":
            handle_find(lib)
        elif choice == "5":
            handle_find_by_title(lib)     # YENİ
        elif choice == "6":
            handle_list_by_author(lib)    # YENİ
        elif choice == "7":
            print("Görüşmek üzere 👋")
            break
        else:
            print("Geçersiz seçim!")


if __name__ == "__main__":
    main()
