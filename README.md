# Coffee Shop RAG System

Sistem RAG (Retrieval-Augmented Generation) sederhana untuk rekomendasi coffee shop di Yogyakarta menggunakan Groq API.

## 📋 Deskripsi

Project ini menggunakan ChromaDB sebagai vector store dan Groq API untuk fast inference. Sistem ini mengambil data coffee shop dari Instagram, membuat knowledge base, dan memberikan rekomendasi berdasarkan query pengguna.

## 📂 Struktur Project

```
RAG/
├── data/
│   ├── raw/              # Data mentah dari scraping
│   ├── processed/        # Data yang sudah diproses
│   └── vector_store/     # ChromaDB vector database
├── src/
│   ├── __init__.py
│   ├── ingest.py         # Data loading & processing
│   ├── embed.py          # Embedding logic
│   ├── retriever.py      # Document retrieval
│   └── generator.py      # LLM generation (Groq)
├── config/
│   └── settings.py       # Konfigurasi sistem
├── archive/              # File lama (notebooks, tests)
├── app.py                # Main application
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Groq API Key

Dapatkan API key dari: https://console.groq.com/

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

### 3. Run Application

```bash
python app.py
```

## 💡 Cara Menggunakan

### Sebagai Script

```bash
python app.py
```

### Sebagai Module

```python
from app import RAGApp

# Initialize
app = RAGApp()

# Query
response = app.query("Rekomendasikan coffee shop untuk bekerja")

# Print response
app.print_response(response)
```

### Response Format

```python
{
    "answer": "Rekomendasi dari sistem...",
    "sources": [
        {"nama": "Nama Coffee Shop", "lokasi": "Lokasi"},
        ...
    ]
}
```

## ⚙️ Konfigurasi

Edit [config/settings.py](config/settings.py) untuk mengubah:
- Embedding model
- Groq model
- Jumlah dokumen yang di-retrieve (TOP_K)
- Temperature dan max tokens
- System prompt

## 📊 Data

- **Raw data**: [data/raw/extracted_data_sahabatai.csv](data/raw/extracted_data_sahabatai.csv)
- **Processed data**: [data/processed/](data/processed/)
- **Vector store**: [data/vector_store/chroma_db/](data/vector_store/chroma_db/)

## 🔧 Komponen

### 1. Embedding (`src/embed.py`)
- Model: BAAI/bge-m3
- Mengkonversi text menjadi vector embeddings

### 2. Retriever (`src/retriever.py`)
- Mengambil dokumen relevan dari ChromaDB
- Format context untuk LLM

### 3. Generator (`src/generator.py`)
- Menggunakan Groq API (llama-3.1-70b-versatile)
- Generate response berdasarkan context

### 4. Ingest (`src/ingest.py`)
- Load dan process data CSV
- Prepare documents untuk vector store

## 📝 Contoh Query

- "Rekomendasikan coffee shop yang nyaman untuk bekerja"
- "Ada tempat kopi dengan area outdoor di Sleman?"
- "Coffee shop dengan menu variatif dan harga terjangkau"
- "Tempat kopi yang cocok untuk meeting"

## 🗂️ Archive

File lama (notebooks, tests, CLI) dipindahkan ke folder [archive/](archive/) untuk menjaga struktur tetap simpel.

## ⚠️ Notes

- Sistem ini menggunakan pre-built ChromaDB. Untuk rebuild, gunakan notebooks di archive
- Groq API gratis dengan rate limit - cek https://console.groq.com/
- Embedding model (bge-m3) akan di-download otomatis saat pertama kali dijalankan
