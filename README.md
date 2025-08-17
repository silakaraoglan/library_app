# Library App (OOP → Open Library API → FastAPI)

Bu proje, üç aşamada gelişen bir kütüphane uygulamasıdır:
1) **OOP CLI**: Kitap ekleme/silme/listeleme (JSON dosyasında kalıcı).
2) **Harici API Entegrasyonu**: ISBN ile Open Library'den başlık/yazar çekme.
3) **FastAPI**: Kütüphaneye HTTP üzerinden erişim (GET/POST/DELETE).

## Proje Yapısı
```
library_app/
  api.py
  main.py
  models.py
  openlibrary_client.py
  storage/
    library.json
  tests/
    test_models.py
    test_api.py
  requirements.txt
  README.md
```

## Kurulum
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Aşama 1: CLI (OOP)
```bash
python main.py
```
Menü:
- 1) ISBN ile Kitap Ekle (Open Library)  ← Aşama 2 mantığı entegre
- 5) Manuel Kitap Ekle (Başlık/Yazar/ISBN) ← Aşama 1 geriye uyum

Veriler `storage/library.json` dosyasında saklanır.

## Aşama 2: Open Library ile ISBN’den çekme
- `openlibrary_client.py` dosyası `httpx` ile verileri çeker.
- CLI’de **1** seçeneği bu işlevi kullanır.

## Aşama 3: FastAPI
Sunucuyu başlat:
```bash
uvicorn api:app --reload
```
- **Docs**: [http://127.0.0.1:8000/docs](https://library-app-d9m3.onrender.com/docs)
- **GET /books**: Tüm kitapları döndürür.
- **POST /books**: `{ "isbn": "9780441172719" }` gibi bir body ile kitabı ekler.
- **DELETE /books/{isbn}**: ISBN ile siler.

## Testler
```bash
pytest -q
```

> `tests/test_api.py`, gerçek ağ çağrısı yapmamak için FastAPI dependency override ile `fetch_book_by_isbn` fonksiyonunu sahte vericiyle değiştirir.
