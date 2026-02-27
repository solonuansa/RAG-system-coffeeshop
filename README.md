# Coffee Shop RAG System

Sistem RAG (Retrieval-Augmented Generation) untuk rekomendasi coffee shop di Yogyakarta berbasis data Instagram menggunakan ChromaDB dan Groq API.

## Deskripsi

Sistem ini dibangun melalui serangkaian tahap pemrosesan data, mulai dari pengumpulan data Instagram, pembersihan teks, pemodelan topik, ekstraksi informasi dengan LLM, hingga penyimpanan ke knowledge base berbasis vektor untuk keperluan retrieval dan generasi jawaban.

### Alur Pipeline

1. **Pengumpulan Data** - Data caption Instagram coffee shop di Yogyakarta dikumpulkan menggunakan Instagrapi.

2. **Preprocessing & Pemodelan Topik (LDA)** - Caption dibersihkan dari spam, noise, dan stopword, lalu dimodelkan menggunakan Latent Dirichlet Allocation (LDA) dengan 4 topik. Setiap caption diberi label dominan (single-label) maupun label multi (multi-label) berdasarkan distribusi probabilitas topik. Label topik yang digunakan: Menu Variatif, Ngopi Santai, Area Lengkap, dan WFC Nyaman.

3. **Ekstraksi Informasi dengan LLM** - Setiap caption diproses menggunakan model Gemma 2 9B CPT Sahabatai Instruct (`GoToCompany/gemma2-9b-cpt-sahabatai-v1-instruct`) melalui platform modal.com untuk mengekstrak dua komponen: deskripsi (informasi faktual tempat, menu, atau jam operasional) dan opini (penilaian eksplisit maupun implisit terhadap tempat, menu, atau suasana).

4. **Pembangunan Knowledge Base** - Hasil ekstraksi disusun menjadi dokumen terstruktur, lalu dikonversi menjadi vector embeddings menggunakan `intfloat/multilingual-e5-large` dan disimpan ke ChromaDB secara persisten.

5. **Retrieval & Generasi Jawaban** - Sistem menerima query pengguna, mencari dokumen relevan dari ChromaDB, lalu menghasilkan jawaban menggunakan Groq API (model `llama-3.3-70b-versatile`).

## Struktur Project

```
RAG/
├── data/
│   ├── processed/        # Data hasil preprocessing dan kategorisasi LDA
│   └── vector_store/     # ChromaDB vector database (di-ignore git)
├── src/
│   ├── __init__.py
│   ├── ingest.py         # Load & persiapan dokumen dari CSV
│   ├── embed.py          # Embedding menggunakan sentence-transformers
│   ├── retriever.py      # Pencarian dokumen relevan dari ChromaDB
│   └── generator.py      # Generasi jawaban menggunakan Groq API
├── config/
│   └── settings.py       # Konfigurasi model, path, dan parameter sistem
├── archive/              # Notebook eksplorasi dan kode lama
├── app.py                # Entry point aplikasi
├── reingest.py           # Script untuk rebuild vector store
├── requirements.txt
├── .env                  # API key 
└── README.md
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Groq API Key

Dapatkan API key dari https://console.groq.com/, lalu buat file `.env` di root project:

```
GROQ_API_KEY=your_api_key_here
```

Atau set secara manual di terminal:

**Windows PowerShell:**
```powershell
$env:GROQ_API_KEY = "your_api_key_here"
```

**Windows CMD:**
```cmd
set GROQ_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export GROQ_API_KEY="your_api_key_here"
```

### 3. Jalankan Aplikasi

```bash
python app.py
```

## Cara Menggunakan

### Sebagai Script

```bash
python app.py
```

### Sebagai Module

```python
from app import RAGApp

app = RAGApp()
response = app.query("Rekomendasikan coffee shop untuk bekerja")
app.print_response(response)
```

### Format Response

```python
{
    "answer": "Rekomendasi dari sistem...",
    "sources": [
        {"nama": "Nama Coffee Shop", "lokasi": "Lokasi"},
        ...
    ]
}
```

## Konfigurasi

Edit `config/settings.py` untuk mengubah:
- Embedding model (default: `intfloat/multilingual-e5-large`)
- Groq model (default: `llama-3.3-70b-versatile`)
- Jumlah dokumen yang di-retrieve (`TOP_K_RESULTS`)
- Temperature dan max tokens
- System prompt dan prompt template

## Komponen

### `src/embed.py`
Mengelola embedding teks menggunakan `intfloat/multilingual-e5-large` via sentence-transformers dengan format passage/query.

### `src/retriever.py`
Mengambil dokumen paling relevan dari ChromaDB berdasarkan similarity search, lalu memformat context untuk dikirim ke LLM.

### `src/generator.py`
Mengirim context dan query ke Groq API menggunakan model `llama-3.3-70b-versatile` untuk menghasilkan jawaban.

### `src/ingest.py`
Memuat data dari CSV hasil preprocessing, menyusun dokumen terstruktur, dan menyimpannya ke ChromaDB.

### `reingest.py`
Script untuk melakukan rebuild ulang vector store dari data terbaru jika terdapat perubahan pada data processed.

## Contoh Query

- "Rekomendasikan coffee shop yang nyaman untuk bekerja"
- "Ada tempat kopi dengan area outdoor di Sleman?"
- "Coffee shop dengan menu variatif dan harga terjangkau"
- "Tempat kopi yang cocok untuk meeting"

## Archive

Notebook eksplorasi (EDA, preprocessing, LDA, knowledge base) dan kode scraping Instagrapi tersimpan di folder `archive/`.

## Catatan

- Sistem menggunakan ChromaDB yang sudah dibangun sebelumnya. Untuk rebuild, jalankan `reingest.py` atau gunakan notebook di `archive/notebooks/`.
- Groq API tersedia secara gratis dengan rate limit. Cek status di https://console.groq.com/.
- Model embedding `intfloat/multilingual-e5-large` akan diunduh otomatis saat pertama kali dijalankan.
- Folder `data/vector_store/` dan file `.env` tidak di-track git.