# Instagram Post & Comment Scraper

Peralatan riset untuk melakukan scraping data profil pengguna, postingan, dan komentar dari Instagram secara otomatis. Data yang diambil akan disimpan secara terstruktur ke dalam database PostgreSQL.

## 🚀 Fitur Utama

- **Profile Scraper**: Mengambil informasi detail profil user (bio, jumlah follower, verified status, dll).
- **Post Scraper**: Mengambil metadata postingan (caption, jumlah likes, jumlah komentar, waktu posting).
- **Comment Scraper**: Mengambil komentar dari postingan tertentu termasuk jumlah likes per komentar.
- **Database Integration**: Penyimpanan terpusat menggunakan PostgreSQL dengan SQLAlchemy ORM.
- **Browser Automation**: Menggunakan Playwright untuk login yang lebih aman dan handling konten dinamis.
- **Auto-Patch**: Dilengkapi patch otomatis untuk menangani masalah validasi Pydantic pada konten Reels/Video.

## 📋 Prasyarat

- **Python**: Versi 3.10 atau lebih baru.
- **PostgreSQL**: Database lokal atau remote.
- **Web Browser**: Google Chrome atau Chromium terinstal di sistem.

## 🛠️ Instalasi

1. **Clone project dan masuk ke direktori**:
   ```bash
   cd Magang
   ```

2. **Buat dan aktifkan virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Untuk Linux/macOS
   # atau
   venv\Scripts\activate     # Untuk Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r req.txt
   ```

4. **Install Playwright browser**:
   ```bash
   playwright install chromium
   ```

## ⚙️ Konfigurasi Database

1. **Buat database baru** di PostgreSQL, contoh: `magang` atau `instagram_research`.
2. **Jalankan script SQL** yang tersedia untuk membuat tabel:
   ```bash
   psql -U your_username -d your_db_name -f queries.sql
   ```
3. **Tambahkan akun Instagram** ke tabel `instagram_accounts`. Akun ini akan digunakan oleh scraper untuk melakukan login.
   ```sql
   INSERT INTO instagram_accounts (username, password_encrypted, status)
   VALUES ('username_anda', 'password_anda', 'active');
   ```

## 📄 Cara Penggunaan

Proses scraping dilakukan dalam 3 tahap berurutan:

### Tahap 1: Scraping Profil Pengguna
Gunakan `users.py` untuk mengambil data profil dari daftar username yang ada di database.
```bash
python users.py
```

### Tahap 2: Scraping Postingan
Setelah data user tersedia, gunakan `posts.py` untuk mengambil daftar postingan terbaru dari user tersebut.
```bash
python posts.py
```

### Tahap 3: Scraping Komentar
Terakhir, gunakan `comments.py` untuk mengambil semua komentar dari postingan yang sudah terdaftar di database.
```bash
python comments.py
```

## ⚠️ Catatan Penting

- **Rate Limiting**: Instagram memiliki limitasi yang ketat. Script ini sudah dilengkapi dengan `time.sleep()`, namun tetap berhati-hatilah agar akun Anda tidak terkena banned.
- **Headless Mode**: Secara default script berjalan dalam mode `headless=True`. Jika ingin melihat proses browser, ubah di inisialisasi `InstagramScraper` dalam masing-masing script.
- **Patch Instagrapi**: File `patch_instagrapi.py` secara otomatis dijalankan untuk memperbaiki bug pada library `instagrapi` saat memproses konten Reels.

## 📂 Struktur Proyek

- `instagr.py`: Kelas utama `InstagramScraper` dan logika inti.
- `models.py`: Definisi tabel database menggunakan SQLAlchemy.
- `users.py`, `posts.py`, `comments.py`: Script entry-point untuk proses scraping.
- `queries.sql`: Schema database.
- `patch_instagrapi.py`: Perbaikan bug library pihak ketiga.
