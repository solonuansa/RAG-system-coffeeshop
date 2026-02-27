# Dokumentasi Kode Sistem RAG Coffee Shop

## Table of Contents
- [Overview Sistem](#overview-sistem)
- [config/settings.py](#configsettingspy)
- [src/embed.py](#srcembedpy)
- [src/ingest.py](#srcingestpy)
- [src/retriever.py](#srcretrieverpy)
- [src/generator.py](#srcgeneratorpy)
- [reingest.py](#reingestpy)
- [app.py](#apppy)

---

## Overview Sistem

Sistem RAG (Retrieval-Augmented Generation) untuk rekomendasi Coffee Shop yang menggabungkan:
1. **Retrieval**: Mencari dokumen relevan dari vector database (ChromaDB)
2. **Generation**: Menggunakan LLM (Groq API) untuk menghasilkan jawaban berdasarkan konteks yang diambil

### Tech Stack
- **LLM**: Groq API (llama-3.3-70b-versatile)
- **Vector Database**: ChromaDB
- **Embedding**: sentence-transformers (intfloat/multilingual-e5-large)
- **Orchestration**: LangChain
- **Data Processing**: pandas

---

## config/settings.py

File ini berisi semua konfigurasi global untuk sistem RAG. Semua pengaturan didefinisikan di sini agar mudah diubah tanpa mengedit file lain.

```python
import os
from pathlib import Path
```
- `import os`: Mengimpor modul os untuk akses environment variables
- `from pathlib import Path`: Mengimpor Path untuk manipulasi path file dengan cara yang lebih modern dan cross-platform

```python
# Path
BASE_DIR = Path(__file__).parent.parent
```
- `Path(__file__)`: Mengambil path absolut dari file settings.py saat ini
- `.parent`: Naik satu level ke folder parent (config/)
- `.parent.parent`: Naik dua level ke root project (folder RAG/)
- Hasilnya adalah path absolut ke root project RAG

```python
DATA_DIR = BASE_DIR / "data"
```
- Membuat path ke folder "data" di dalam BASE_DIR
- Path hasilnya: `RAG/data/`

```python
PROCESSED_DATA_DIR = DATA_DIR / "processed"
```
- Membuat path ke folder "processed" di dalam DATA_DIR
- Menyimpan file CSV yang sudah diproses
- Path hasilnya: `RAG/data/processed/`

```python
RAW_DATA_DIR = DATA_DIR / "raw"
```
- Membuat path ke folder "raw" di dalam DATA_DIR
- Menyimpan data mentah yang belum diproses
- Path hasilnya: `RAG/data/raw/`

```python
VECTOR_STORE_DIR = DATA_DIR / "vector_store" / "chroma_db"
```
- Membuat path ke folder ChromaDB untuk menyimpan vector store
- Path hasilnya: `RAG/data/vector_store/chroma_db/`
- ChromaDB akan menyimpan database SQLite dan file embeddings di sini

```python
# Models
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
```
- Nama model sentence transformer yang digunakan untuk embedding
- Model ini mendukung multi-lingual (bisa memprosesbahasa Indonesia, Inggris, dll)
- Menggunakan framework Hugging Face
- Model ini akan di-download otomatis saat pertama kali dijalankan

```python
GROQ_MODEL = "llama-3.3-70b-versatile"
```
- Nama model LLM dari Groq API yang digunakan untuk generate jawaban
- llama-3.3-70b-versatile adalah model dengan 70 miliar parameter
- Model ini cepat dan efisien karena dijalankan di infrastruktur Groq yang dioptimalkan

```python
# Embedding
EMBEDDING_BATCH_SIZE = 32
```
- Batch size saat melakukan embedding (mengubah teks menjadi vector)
- Artinya: 32 teks diproses sekaligus dalam satu batch
- Batch processing lebih efisien daripada memproses satu per satu
- Nilai ini diambil berdasarkan keseimbangan speed dan memory

```python
INGEST_BATCH_SIZE = 100
```
- Batch size saat memasukkan dokumen ke ChromaDB
- Artinya: 100 dokumen disimpan sekaligus
- Mencegah memory issues saat memproses banyak dokumen
- Nilai lebih besar dari EMBEDDING_BATCH_SIZE karena insert ke DB lebih ringan daripada embedding

```python
# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
```
- Mengambil Groq API key dari environment variable
- `os.getenv("GROQ_API_KEY", "")`: Cari environment variable bernama "GROQ_API_KEY", jika tidak ada return empty string ""
- API key harus diset di file `.env` atau di system environment
- API key ini digunakan untuk autentikasi ke Groq API

```python
# Retrieval
TOP_K_RESULTS = 5
```
- Jumlah dokumen yang akan diambil (retrieved) dari vector database untuk setiap query
- Artinya: sistem akan mengambil 5 dokumen paling relevan
- Nilai ini menentukan jumlah konteks yang diberikan ke LLM

```python
SCORE_THRESHOLD = 0.3
```
- Threshold untuk memfilter hasil retrieval berdasarkan similarity score
- Score adalah jarak atau similarity antara query dan dokumen (biasanya Euclidean distance)
- Semakin KECIL score = semakin relevan
- Nilai 0.3 berarti: hanya dokumen dengan score < 0.3 yang akan dipertimbangkan
- Threshold ini membantu mengfilter dokumen yang tidak relevan

```python
# Generation
MAX_TOKENS = 1024
```
- Maksimal jumlah token (kata/karakter) yang bisa di-generate oleh LLM
- 1024 token kira-kira setara dengan 700-800 kata
- Membatasi panjang jawaban agar tidak terlalu panjang dan biar efisien

```python
TEMPERATURE = 0.7
```
- Parameter yang mengontrol randomness/creativity dari jawaban LLM
- Rentang nilai: 0.0 sampai 2.0
- 0.0 = sangat konservatif, jawaban selalu sama untuk input yang sama
- 0.7 = balanced antara konsisten dan creative (cocok untuk chatbot)
- 1.0+ = sangat random dan creative
- Nilai 0.7 memberikan jawaban yang natural tapi tetap relevan

```python
API_TIMEOUT = 30.0
```
- Timeout (dalam detik) untuk setiap request ke Groq API
- Jika API tidak merespon dalam 30 detik, request akan dianggap gagal
- Mencegah aplikasi hang menunggu response tanpa batas

```python
# Retry
MAX_RETRIES = 3
```
- Maksimal jumlah percobaan retry jika request API gagal
- Jika request gagal, sistem akan mencoba lagi sampai 3 kali
- Menangani transient errors (error yang sementara, seperti network timeout)

```python
RETRY_DELAY = 2
```
- Delay (dalam detik) antara setiap percobaan retry
- Menunggu 2 detik sebelum mencoba lagi
- Memberikan waktu untuk API recover dari rate limit atau temporary errors

```python
# System prompt
SYSTEM_PROMPT = """Anda adalah asisten yang membantu memberikan informasi coffee shop di Yogyakarta.
Berdasarkan informasi yang diberikan, berikan rekomendasi yang relevan, jelas, dan membantu.
Fokus pada lokasi, suasana, menu, dan fasilitas yang tersedia.
Jika informasi tidak cukup, katakan dengan jujur."""
```
- System prompt adalah instruksi yang diberikan ke LMM untuk mengatur cara dia menjawab
- "Anda adalah asisten yang membantu..." - Menetapkan role LLM sebagai asisten
- "Berdasarkan informasi yang diberikan..." - Mengatakan ke LLM untuk menggunakan konteks yang diberikan
- "Fokus pada lokasi, suasana, menu, dan fasilitas..." - Menentukan aspek apa yang perlu dijelaskan
- "Jika informasi tidak cukup, katakan dengan jujur" - Mencegah LLM from halusinasi (mengarang info)

```python
# Prompt template 
CONTEXT_PROMPT_TEMPLATE = """Gunakan data berikut untuk menjawab pertanyaan.
Jika data tidak cukup, katakan dengan jujur.

Data:
{context}

Pertanyaan:
{query}

Jawaban:"""
```
- Template prompt untuk user message (query + konteks)
- Placeholder `{context}` akan diganti dengan dokumen yang di-retrieve
- Placeholder `{query}` akan diganti dengan pertanyaan user
- Format ini memastikan LLM punya semua informasi yang diperlukan untuk menjawab
- Akhiri dengan "Jawaban:" untuk menandakan tempat LLM harus mulai menjawab

---

## src/embed.py

File ini menangani embedding teks menjadi vector numeric menggunakan sentence transformers library.

```python
import logging
```
- Mengimpor logging module untuk menampilkan informasi dan error
- Logging lebih baik dari print karena bisa diatur levelnya (INFO, WARNING, ERROR)

```python
from sentence_transformers import SentenceTransformer
```
- Mengimpor SentenceTransformer dari library sentence-transformers
- Library ini menyediakan pretrained models untuk mengubah teks menjadi vector
- SentenceTransformer bisa download dan load model dari Hugging Face

```python
from typing import List
```
- Mengimpor List dari modul typing untuk type hints
- Memungkinkan kita mendeklarasikan tipe data untuk improve readability dan type checking

```python
from config.settings import EMBEDDING_MODEL
```
- Mengimpor konstanta EMBEDDING_MODEL dari config/settings.py
- Menghindari hardcoding nama model di dalam kode

```python
logger = logging.getLogger(__name__)
```
- Membuat logger dengan nama file ini (__name__ akan jadi "src.embed")
- Memudahkan tracking log dari setiap modul

```python
class EmbeddingModel:
    """Menangani embedding teks menggunakan sentence transformers"""
```
- Mendefinisikan class EmbeddingModel
- Encapsulate semua fungsi embedding ke dalam satu class
- Dokstring menjelaskan fungsi class ini

```python
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Inisialisasi model embedding
        
        Args:
            model_name: Nama model sentence transformer
        """
```
- Constructor class yang dipanggil saat objek dibuat: `model = EmbeddingModel()`
- Parameter `model_name` dengan default value dari EMBEDDING_MODEL
- Dokstring menjelaskan parameter

```python
        print(f"Memuat model embedding: {model_name}...")
```
- Menampilkan pesan loading model ke console
- Formatting f-string untuk menyisipkan nama model

```python
        self.model = SentenceTransformer(model_name)
```
- Menginisialisasi SentenceTransformer dengan nama model specified
- Ini akan:
  - Download model dari Hugging Face jika belum ada di cache
  - Load model ke memory
  - Model sekarang siap digunakan untuk embedding
- Model disimpan di `self.model` agar bisa diakses di method lain

```python
        print("✓ Model embedding berhasil dimuat")
```
- Menampilkan konfirmasi bahwa model berhasil dimuat

```python
    def embed_text(self, text: str) -> List[float]:
        """
        Embed satu teks
        
        Args:
            text: Teks yang akan di-embed
            
        Returns:
            Vector embedding
        """
```
- Method untuk meng-embed satu teks menjadi vector
- Parameter `text` dengan type hint String
- Return value dengan type hint List[float] (list of floats)
- Dokstring menjelaskan fungsi, args, dan return

```python
        return self.model.encode(text).tolist()
```
- `self.model.encode(text)`: Memanggil method encode dari SentenceTransformer
  - Input: string teks
  - Output: numpy array yang berisi vector embedding (biasanya 1024 dimensi untuk model e5-large)
  - Vector ini merepresentasikan semantic meaning dari teks dalam ruang numeric
- `.tolist()`: Convert numpy array ke Python list
- Return format: [0.1234, -0.5678, 0.3456, ...] (list of floats)

```python
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed beberapa teks sekaligus
        
        Args:
            texts: List teks yang akan di-embed
            
        Returns:
            List vector embedding
        """
```
- Method untuk meng-embed multiple texts sekaligus
- Lebih efisien daripada memanggil embed_text berulang kali
- Type hints:
  - Input: List[str] (list of strings)
  - Output: List[List[float]] (list of lists of floats)

```python
        return self.model.encode(texts).tolist()
```
- `self.model.encode(texts)`: Encode multiple texts dalam satu call
  - Memanfaatkan batch processing untuk lebih efisien
  - Outputs: 2D numpy array (N embeddings x D dimensions)
- `.tolist()`: Convert ke nested Python lists
- Return format: [[0.1234, -0.5678, ...], [0.9876, -0.4321, ...], ...]

---

## src/ingest.py

File ini menangani proses ingest data dari CSV ke vector database (ChromaDB).

```python
import re
```
- Mengimpor regex module untuk text cleaning
- Regex digunakan untuk pattern matching dan string replacement

```python
import logging
```
- Mengimpor logging untuk output信息和error

```python
import pandas as pd
```
- Mengimpor pandas library untuk data processing
- DataFrame adalah struktur data utama untuk meng-handle CSV dan tabular data

```python
from pathlib import Path
```
- Mengimpor Path untuk path manipulation yang cross-platform

```python
from typing import List
```
- Mengimpor List untuk type hints

```python
from langchain_core.documents import Document
```
- Mengimpor Document class dari langchain_core
- Document adalah struktur data standar LangChain yang menyimpan content dan metadata

```python
from langchain_chroma import Chroma
```
- Mengimpor Chroma vector store dari langchain_chroma
- Chroma adalah vector database yang integrated dengan LangChain

```python
from src.embed import EmbeddingModel
```
- Mengimpor EmbeddingModel class dari local file src/embed.py
- Used untuk create embeddings dari teks

```python
from config.settings import VECTOR_STORE_DIR, EMBEDDING_MODEL, PROCESSED_DATA_DIR, EMBEDDING_BATCH_SIZE, INGEST_BATCH_SIZE
```
- Mengimpor semua konfigurasi yang diperlukan dari settings
- Menghindari hardcoding values

```python
logger = logging.getLogger(__name__)
```
- Membuat logger khusus untuk file ini

```python
class DataIngestor:
    """Menangani loading dan ingest dokumen ke ChromaDB"""
```
- Class utama untuk mengorganisasi semua fungsi ingest
- Encapsulate seluruh proses dari CSV ke vector database

```python
    def __init__(self):
        """Inisialisasi data ingestor"""
```
- Constructor yang dipanggil saat: `ingestor = DataIngestor()`

```python
        self.embedding_model = EmbeddingModel(EMBEDDING_MODEL)
```
- Membuat instance EmbeddingModel
- Ini akan:
  - Load model embedding dari Hugging Face
  - Simpan di self.embedding_model agar bisa digunakan di method lain

```python
        self.embedding_function = self._create_embedding_function()
```
- Membuat embedding function yang kompatible dengan Chroma
- Chroma memerlukan function dengan method `embed_documents()` dan `embed_query()`
- Disimpan di self.embedding_function untuk digunakan saat ingest

```python
        VECTOR_STORE_DIR.parent.mkdir(parents=True, exist_ok=True)
```
- `VECTOR_STORE_DIR.parent`: Mendapatkan parent directory (vector_store/)
- `.mkdir(parents=True, exist_ok=True)`:
  - `parents=True`: Buat semua parent directories jika belum ada
  - `exist_ok=True`: Tidak error jika directory sudah exists
  - Ensures folder structure exists sebelum menyimpan data

```python
    def _create_embedding_function(self):
        """Buat fungsi embedding yang kompatibel dengan Chroma"""
```
- Private method (diawali underscore) untuk membuat custom embedding function
- Chroma memerlukan object dengan method specific

```python
        class EmbeddingWrapper:
```
- Membuat inner class EmbeddingWrapper
- Ini adalah adapter pattern: wrap EmbeddingModel agar compatible dengan Chroma API

```python
            def __init__(self, model):
                self.model = model
```
- Constructor untuk EmbeddingWrapper
- Menerima model (EmbeddingModel instance) dan menyimpannya

```python
            def embed_documents(self, texts):
                """Embed dokumen dengan prefix 'passage:'"""
```
- Method untuk meng-embed multiple documents passages
- Chroma akan memanggil method ini saat storing documents

```python
                texts = [f"passage: {t}" for t in texts]
```
- Menambahkan prefix "passage: " ke setiap teks
- List comprehension: iterate semua teks dan add prefix
- Prefix ini penting untuk model e5-large yang dilatih dengan instruction prefix
- "passage:" menandakan bahwa teks ini adalah passage dokumen, bukan query

```python
                return self.model.model.encode(
                    texts,
                    batch_size=EMBEDDING_BATCH_SIZE,
                    show_progress_bar=True,
                    normalize_embeddings=True
                ).tolist()
```
- `self.model.model.encode()`:
  - `texts`: List of teks dengan prefix
  - `batch_size=EMBEDDING_BATCH_SIZE`: Process 32 teks sekaligus
  - `show_progress_bar=True`: Tampilkan progress bar di console
  - `normalize_embeddings=True`: Normalisasi vectors ke unit length (L2 normalization)
    - Ini penting untuk similarity calculation dengan cosine similarity
    - Normalisasi menyamakan scale semua vectors
- `.tolist()`: Convert numpy array ke list

```python
            def embed_query(self, text):
                """Embed query dengan prefix 'query:'"""
```
- Method untuk meng-embed single query
- Dipanggil saat search/retrieval

```python
                return self.model.model.encode(
                    f"query: {text}",
                    normalize_embeddings=True
                ).tolist()
```
- Menambahkan prefix "query:" ke text
- Prefix ini berbeda dengan "passage:" untuk membedakan query dan passages
- Model e5-large dilatih untuk memahami perbedaan ini
- Mengembalikan vector embedding

```python
        return EmbeddingWrapper(self.embedding_model)
```
- Membuat instance EmbeddingWrapper dengan self.embedding_model
- Mengembalikan object yang compatible dengan Chroma

```python
    def _clean_text(self, text: str) -> str:
        """Membersihkan teks"""
```
- Private method untuk text preprocessing
- Input: raw string dari CSV
- Output: cleaned string

```python
        if pd.isna(text):
            return ""
```
- Cek apakah text adalah NaN (Not a Number - pandas null value)
- `pd.isna()` returns True untuk None, NaN, atau NA values
- Jika NaN, return empty string

```python
        text = str(text)
```
- Convert ke string untuk memastikan type consistency
- Menghandle jika ada numbers atau non-string data

```python
        text = re.sub(r"\s+", " ", text)
```
- Use regex untuk mengganti multiple whitespace dengan single space
- `r"\s+"`: Regex pattern untuk one or more whitespace characters (space, tab, newline)
- `re.sub(pattern, replacement, text)`: Replace semua matches dengan replacement
- Contoh: "Hello   world\n  test" → "Hello world test"

```python
        return text.strip()
```
- Menghapus whitespace di awal dan akhir string
- Contoh: "  hello world  " → "hello world"

```python
    def _build_content(self, row: pd.Series) -> str:
        """Membangun content field dari baris data"""
```
- Method untuk memformat satu baris data (row) menjadi string content
- Input: pandas Series (satu row dari DataFrame)
- Output: formatted string

```python
        return f"""Kategori: {row['kategori']}
Lokasi: {row['lokasi']}
Sumber: {row['source']}

Deskripsi:
{row['deskripsi']}

Opini:
{row['opini']}"""
```
- Multiline f-string untuk format content
- Mengambil kolom 'kategori', 'lokasi', 'source', 'deskripsi', 'opini' dari row
- Format ini membuat content yang structured dan easy to read
- Contoh output:
  ```
  Kategori: Coffee Shop
  Lokasi: Jakarta Selatan
  Sumber: @coffee_shop_ig
  
  Deskripsi:
  Coffee shop dengan suasana cozy...
  
  Opini:
  Kopinya enak dan tempatnya instagramable...
  ```

```python
    def load_and_ingest_csv(self, csv_path: str):
        """
        Memuat dan ingest data dari CSV Sahabat AI
        
        Args:
            csv_path: Path ke file extracted_data_sahabatai.csv
        """
```
- Main method untuk load CSV dan ingest ke ChromaDB
- Ini adalah entry point untuk ingest process

```python
        csv_path = Path(csv_path)
```
- Convert string path ke Path object untuk cross-platform compatibility

```python
        if not csv_path.exists():
            raise FileNotFoundError(f"File tidak ditemukan: {csv_path}")
```
- Cek apakah file exists
- Jika tidak, raise FileNotFoundError dengan pesan yang jelas
- Ini memberikan error message yang helpful saat debugging

```python
        print(f"Memuat data dari: {csv_path}")
```
- Menampilkan pesan progress ke user

```python
        # Load CSV
        df = pd.read_csv(csv_path)
```
- `pd.read_csv()`: Load CSV file into pandas DataFrame
- DataFrame adalah 2D table dengan labeled columns and rows
- df sekarang berisi semua data dari CSV

```python
        print(f"✓ Berhasil memuat {len(df)} baris data")
        print()
```
- Menampilkan jumlah baris data yang berhasil dimuat
- Empty print() untuk spacing

```python
        # Validate required columns
        required_columns = ['Kota', 'Akun Instagram', 'Kategori Tempat', 'deskripsi', 'opini']
```
- Mendefinisikan list kolom yang harus ada di CSV
- Ini adalah struktur data yang diharapkan

```python
        missing_columns = [col for col in required_columns if col not in df.columns]
```
- List comprehension untuk mengecek kolom yang missing
- Iterate setiap column di required_columns
- Cek apakah column TIDAK ada di df.columns
- Jika missing, tambahkan ke missing_columns list
- Contoh: jika hanya 'deskripsi' yang missing → missing_columns = ['deskripsi']

```python
        if missing_columns:
            raise ValueError(
                f"Kolom yang dibutuhkan tidak ditemukan dalam CSV: {missing_columns}\n"
                f"Kolom yang tersedia: {list(df.columns)}"
            )
```
- Jika ada missing columns, raise ValueError
- Message error menunjukkan:
  - Kolom apa yang missing
  - Kolom apa yang tersedia di CSV
  - Ini membantu user mengerti apa yang salah

```python
        # Pilih kolom yang diperlukan
        df = df[required_columns]
```
- Select hanya kolom yang digunakan
- Menghapus kolom lain yang tidak needed
- df sekarang hanya punya 5 kolom

```python
        # Rename kolom
        df.columns = ['lokasi', 'source', 'kategori', 'deskripsi', 'opini']
```
- Rename kolom ke nama yang lebih clean dan consistent
- Mapping:
  - 'Kota' → 'lokasi'
  - 'Akun Instagram' → 'source'
  - 'Kategori Tempat' → 'kategori'
  - 'deskripsi' → 'deskripsi' (no change)
  - 'opini' → 'opini' (no change)

```python
        # Tambahkan ID
        df.insert(0, 'id', range(1, 1 + len(df)))
```
- `df.insert(0, 'id', ...)`: Insert kolom baru di position 0 (paling kiri)
- Nama kolom: 'id'
- Values: range(1, 1 + len(df)) → [1, 2, 3, ..., n]
- Setiap baris sekarang punya unique ID dari 1 sampai n
- ini berguna untuk tracking dan referencing

```python
        # Cleaning
        print("Membersihkan data...")
```
- Menampilkan pesan progress

```python
        for col in ["kategori", "lokasi", "source", "deskripsi", "opini"]:
            df[col] = df[col].apply(self._clean_text)
```
- Iterate setiap kolom teks
- `df[col].apply(self._clean_text)`: Apply function `_clean_text` ke setiap cell di kolom
- Apply sangat efisien untuk pandas operations
- Hasilnya: semua teks di-clean dan konsisten

```python
        # Build content
        print("Membangun content field...")
```
- Menampilkan pesan progress

```python
        df["content"] = df.apply(self._build_content, axis=1)
```
- Menambahkan kolom baru 'content' ke DataFrame
- `df.apply(self._build_content, axis=1)`:
  - Apply function `_build_content` ke setiap row
  - `axis=1`: Apply per row (not per column)
  - Setiap row dipassing sebagai pandas Series ke function
- Hasilnya: setiap row punya formatted content string

```python
        # Convert to LangChain Documents
        print("Mengkonversi ke LangChain documents...")
```
- Menampilkan pesan progress

```python
        documents = []
```
- Initialize empty list untuk menyimpan Document objects

```python
        for _, row in df.iterrows():
```
- `df.iterrows()`: Iterate setiap row di DataFrame
- Kita use `_` untuk index (tidak digunakan), `row` untuk data

```python
            documents.append(
                Document(
                    page_content=row["content"],
                    metadata={
                        "id": row["id"],
                        "kategori": row["kategori"],
                        "lokasi": row["lokasi"],
                        "source": row["source"],
                    },
                )
            )
```
- Create Document object untuk setiap row
- LangChain Document structure:
  - `page_content`: Teks utama dokumen (yang akan di-search)
  - `metadata`: Dictionary dengan tambahan informasi (tidak di-embed)
- Metadata yang disimpan:
  - `id`: Unique identifier
  - `kategori`: Kategori coffee shop
  - `lokasi`: Lokasi geografis
  - `source`: Sumber informasi (Instagram account)
- Append ke documents list

```python
        print(f"Total {len(documents)} dokumen siap untuk di-embed")
        print()
```
- Menampilkan jumlah dokumen yang berhasil dibuat
- Spacing

```python
        # Ingest ke Chroma
        print("Menyimpan ke ChromaDB")
```
- Menampilkan pesan progress

```python
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_function,
            persist_directory=str(VECTOR_STORE_DIR)
        )
```
- `Chroma.from_documents()`: Create Chroma vector store from documents
- Parameters:
  - `documents`: List of Document objects
  - `embedding`: Function untuk generate embeddings
  - `persist_directory`: Directory untuk menyimpan database (SQLite + files)
- Proses ini akan:
  - Generate embeddings untuk semua documents (via embed_documents)
  - Create index untuk similarity search
  - Save semua data ke disk
- Return vectorstore object

```python
        # Data otomatis tersimpan ke persist_directory
        print(f"Ingest selesai! {len(documents)} dokumen berhasil disimpan")
        print(f"Vector store tersimpan di: {VECTOR_STORE_DIR}")
```
- Menampilkan konfirmasi selesai
- Menunjukkan lokasi penyimpanan database

---

## src/retriever.py

File ini menangani retrieval dokumen relevan dari vector database (ChromaDB).

```python
import logging
```
- Mengimpor logging untuk messages

```python
from langchain_community.vectorstores import Chroma
```
- Mengimpor Chroma vector store dari langchain_community
- Ini adalah integrasi LangChain dengan Chroma database

```python
from src.embed import EmbeddingModel
```
- Mengimpor EmbeddingModel untuk generate embeddings dari query

```python
from config.settings import VECTOR_STORE_DIR, EMBEDDING_MODEL, TOP_K_RESULTS, EMBEDDING_BATCH_SIZE, SCORE_THRESHOLD
```
- Mengimpor konfigurasi yang dibutuhkan

```python
logger = logging.getLogger(__name__)
```
- Membuat logger untuk file ini

```python
class Retriever:
    """Menangani retrieval dokumen dari ChromaDB"""
```
- Class utama untuk retrieval operations

```python
    def __init__(self):
        """Inisialisasi retriever"""
```
- Constructor untuk Retriever

```python
        print("Memuat vector store...")
```
- Menampilkan pesan loading

```python
        # Validate vector store exists
        if not VECTOR_STORE_DIR.exists():
            raise FileNotFoundError(
                f"Vector store tidak ditemukan di {VECTOR_STORE_DIR}. "
                "Jalankan 'python reingest.py' terlebih dahulu untuk membuat vector store."
            )
```
- Cek apakah vector store directory exists
- Jika tidak, raise FileNotFoundError dengan pesan yang sangat helpful
- Message memberitahu user apa yang harus dilakukan (run reingest.py)

```python
        # Load embedding model
        self.embedding_model = EmbeddingModel(EMBEDDING_MODEL)
```
- Load sentence transformer model untuk embedding queries
- Model sama dengan yang digunakan saat ingest (penting untuk consistency)

```python
        self.embedding_function = self._create_embedding_function()
```
- Create embedding function compatible dengan Chroma (sama seperti di ingest.py)

```python
        # Load vector store
        try:
```
- Mulai try block untuk error handling

```python
            self.vectorstore = Chroma(
                persist_directory=str(VECTOR_STORE_DIR),
                embedding_function=self.embedding_function
            )
```
- Create Chroma instance yang connect ke existing database
- Parameters:
  - `persist_directory`: Directory dimana database disimpan
  - `embedding_function`: Function untuk embed new queries
- Ini memuat database yang sudah ada dari disk

```python
            doc_count = self.vectorstore._collection.count()
```
- Hitung jumlah dokumen di collection
- `_collection` adalah internal Chroma collection object
- `.count()` returns total documents

```python
            if doc_count == 0:
                raise ValueError("Vector store kosong. Jalankan 'python reingest.py' untuk mengisi data.")
```
- Cek apakah database kosong
- Jika kosong, raise ValueError dengan instruction
- Ini bisa terjadi jika directory exists tapi belum ada data

```python
            print(f"Vector store berhasil dimuat ({doc_count} dokumen)")
```
- Menampilkan konfirmasi berhasil load

```python
        except Exception as e:
            raise RuntimeError(f"Gagal memuat vector store: {str(e)}")
```
- Catch any exception saat load
- Wrap dalam RuntimeError dengan pesan yang lebih jelas
- Exception akan di-handle oleh caller

```python
    def _create_embedding_function(self):
        """Buat fungsi embedding yang kompatibel dengan Chroma"""
        class EmbeddingWrapper:
            def __init__(self, model):
                self.model = model
            
            def embed_documents(self, texts):
                texts = [f"passage: {t}" for t in texts]
                return self.model.model.encode(
                    texts,
                    batch_size=EMBEDDING_BATCH_SIZE,
                    normalize_embeddings=True
                ).tolist()
            
            def embed_query(self, text):
                return self.model.model.encode(
                    f"query: {text}",
                    normalize_embeddings=True
                ).tolist()
        
        return EmbeddingWrapper(self.embedding_model)
```
- Method yang SAMA PERSIS dengan yang ada di ingest.py
- Ini penting: embedding function harus sama antara ingest dan retrieval
- Otherwise vectors tidak akan bekerja properly
- Explanation sama seperti di ingest.py

```python
    def retrieve(self, query: str, k: int = TOP_K_RESULTS) -> list:
        """
        Retrieve dokumen relevan berdasarkan query menggunakan MMR dan score threshold
        
        Args:
            query: Query dari user
            k: Jumlah dokumen yang diambil (default dari settings)
            
        Returns:
            List dokumen relevan
        """
```
- Main method untuk retrieve dokumen
- Input: query string dan jumlah hasil
- Output: list of dictionaries dengan content dan metadata

```python
        # Gunakan MMR untuk diversity (ambil lebih banyak dulu)
        fetch_k = k * 2  # Ambil 2x lebih banyak untuk diversity
```
- Set fetch_k = k * 2
- fetch_k adalah jumlah dokumen diambil untuk MMR processing
- Kita ambil 2x lebih banyak untuk memberikan MMR lebih banyak pilihan
- MMR akan memilih k dokumen yang paling relevant dan diverse

```python
        results = self.vectorstore.max_marginal_relevance_search(
            query, 
            k=k, 
            fetch_k=fetch_k
        )
```
- `max_marginal_relevance_search()`: Retrieval method dengan MMR algorithm
- MMR (Maximal Marginal Relevance):
  - Maximizes relevance to query
  - Maximizes diversity between results
  - Menghindari returning too similar documents
- Parameters:
  - `query`: Query string untuk di-embed dan di-search
  - `k`: Final number of results to return (5)
  - `fetch_k`: Initial number to retrieve (10) before MMR filtering
- Returns: List of Document objects

```python
        # Format ke dict untuk kompatibilitas
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in results
        ]
```
- Convert Document objects ke dictionaries
- List comprehension untuk iterate semua results
- Format:
  ```python
  [
    {
      "content": "Kategori: Coffee Shop\nLokasi: Jakarta...",
      "metadata": {"id": 1, "kategori": "...", "lokasi": "...", "source": "..."}
    },
    ...
  ]
  ```
- Ini format yang lebih flexible dan easy to work with

```python
    def retrieve_with_threshold(self, query: str, k: int = TOP_K_RESULTS, threshold: float = SCORE_THRESHOLD) -> list:
        """
        Retrieve dokumen relevan dengan score threshold untuk memfilter hasil berkualitas rendah
        
        Args:
            query: Query dari user
            k: Jumlah dokumen yang diambil (default dari settings)
            threshold: Threshold untuk memfilter hasil (semakin kecil semakin ketat)
            
        Returns:
            List dokumen relevan yang lolos threshold
        """
```
- Method alternative yang lebih strict dengan score threshold
- Menggunakan similarity search dengan explicit score filtering

```python
        # Ambil lebih banyak dokumen untuk filtering
        fetch_k = k * 3
```
- Ambil 3x lebih banyak dokumen untuk threshold filtering
- Kita butuh more candidates karena banyak mungkin akan filtered out

```python
        results_with_scores = self.vectorstore.similarity_search_with_score(
            query, 
            k=fetch_k
        )
```
- `similarity_search_with_score()`: Basic similarity search
- Mengembalikan results WITH similarity scores
- Score adalah distance measurement (semakin kecil = semakin similar)
- Returns: list of tuples (Document, score)

```python
        # Filter berdasarkan threshold
        filtered_results = [
            (doc, score) for doc, score in results_with_scores 
            if score < threshold
        ]
```
- Filter results berdasarkan threshold
- Hanya keep documents dengan score < threshold
- List comprehension dengan conditional

```python
        # Ambil k hasil terbaik
        filtered_results = filtered_results[:k]
```
- Slice untuk ambil hanya top k hasil
- Hasil sudah sorted by score (paling relevant dulu)

```python
        # Format ke dict untuk kompatibilitas
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            }
            for doc, score in filtered_results
        ]
```
- Convert ke dictionary format sama seperti retrieve()
- Tapi dengan tambahan "score" field
- Format:
  ```python
  [
    {
      "content": "...",
      "metadata": {...},
      "score": 0.15
    },
    ...
  ]
  ```

```python
    def format_context(self, documents: list) -> str:
        """
        Format dokumen menjadi context string
        
        Args:
            documents: List dokumen
            
        Returns:
            Formatted context string
        """
```
- Method untuk format list of documents ke string yang bisa diberikan ke LLM
- Input: list of document dicts
- Output: formatted string

```python
        if not documents:
            return "Tidak ada dokumen relevan ditemukan."
```
- Handle empty list
- Return message kalau tidak ada results

```python
        context = "Informasi Relevan:\n\n"
```
- Initialize context string dengan header

```python
        for i, doc in enumerate(documents, 1):
```
- Iterate semua documents dengan index starting dari 1
- `enumerate(..., 1)`: start counting dari 1, not 0

```python
            context += f"--- Sumber {i} ---\n"
```
- Add separator untuk setiap source dengan number

```python
            context += doc["content"]
```
- Append document content ke context string

```python
            context += f"\n(Sumber: {doc['metadata'].get('source', 'Unknown')})\n\n"
```
- Append source info di end of each document
- `.get('source', 'Unknown')`: Safe access ke metadata, jika tidak ada return 'Unknown'
- Contoh akhir format:
  ```
  Informasi Relevan:

  --- Sumber 1 ---
  Kategori: Coffee Shop
  Lokasi: Jakarta Selatan
  Sumber: @coffee1

  Deskripsi:
  Tempat yang cozy...

  Opini:
  Kopi enak...

  (Sumber: @coffee1)

  --- Sumber 2 ---
  ...
  ```

```python
        return context
```
- Return formatted context string
- String ini akan dikirim ke LLM bersama dengan query

---

## src/generator.py

File ini menangani generate teks/response menggunakan Groq API dengan retry logic untuk handle errors.

```python
import time
```
- Mengimpor time module untuk sleep/retry delay
- Used untuk exponential backoff saat retry

```python
import logging
```
- Mengimpor logging untuk messages dan error tracking

```python
from groq import Groq
```
- Mengimpor Groq client from groq library
- Ini adalah SDK untuk berinteraksi dengan Groq API

```python
from groq import APIError, RateLimitError
```
- Mengimpor exception spesifik dari Groq
- `APIError`: General API errors
- `RateLimitError`: Error saat melewati rate limit

```python
from typing import Optional
```
- Mengimpor Optional untuk type hints

```python
from config.settings import GROQ_API_KEY, GROQ_MODEL, MAX_TOKENS, TEMPERATURE, SYSTEM_PROMPT, API_TIMEOUT, MAX_RETRIES, RETRY_DELAY, CONTEXT_PROMPT_TEMPLATE
```
- Mengimpor semua konfigurasi yang dibutuhkan

```python
# Setup logging
logging.basicConfig(level=logging.INFO)
```
- Configure logging untuk seluruh script
- Set default level ke INFO (menampilkan INFO, WARNING, ERROR)

```python
logger = logging.getLogger(__name__)
```
- Membuat logger untuk file ini

```python
class Generator:
    """Menangani generate teks menggunakan Groq API"""
```
- Class utama untuk text generation

```python
    def __init__(self, api_key: str = None, model: str = GROQ_MODEL):
        """
        Inisialisasi generator dengan Groq
        
        Args:
            api_key: API key Groq
            model: Nama model yang digunakan
        """
```
- Constructor untuk initialize Generator

```python
        self.api_key = api_key or GROQ_API_KEY
```
- Set api_key ke parameter jika diberikan, atau gunakan default dari settings
- `or` fallback jika parameter None

```python
        self.model = model
```
- Set model yang akan digunakan

```python
        if not self.api_key:
            raise ValueError("GROQ_API_KEY tidak ditemukan. Silakan set di environment variables.")
```
- Validate api_key exists
- Jika tidak, raise ValueError dengan helpful message

```python
        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)
```
- Create Groq client instance
- Client ini akan digunakan untuk semua API calls
- Menyimpannya di self.client untuk reuse

```python
    def generate(
        self, 
        query: str, 
        context: str,
        system_prompt: str = SYSTEM_PROMPT,
        max_tokens: int = MAX_TOKENS,
        temperature: float = TEMPERATURE
    ) -> str:
        """
        Generate response menggunakan Groq dengan retry logic
        
        Args:
            query: Query dari user
            context: Konteks yang diambil dari vector store
            system_prompt: System prompt untuk model
            max_tokens: Maksimal token yang di-generate
            temperature: Temperature sampling
            
        Returns:
            Teks response yang di-generate
        """
```
- Main method untuk generate response dengan konteks RAG
- Dengan default values dari settings tapi bisa di-override

```python
        # Construct user message with context
        user_message = CONTEXT_PROMPT_TEMPLATE.format(context=context, query=query)
```
- Format user message menggunakan template
- `.format()`: Replace placeholders dengan actual values
- `{context}` → context string dari retriever
- `{query}` → user question
- Template sudah di-define di settings.py

```python
        # Call Groq API with retry logic
        for attempt in range(MAX_RETRIES):
```
- Loop untuk retry logic
- `range(MAX_RETRIES)`: iterate 0, 1, 2 (total 3 attempts)
- Ini membantu handle temporary API errors

```python
            try:
```
- Start try block untuk API call yang mungkin gagal

```python
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=API_TIMEOUT
                )
```
- Make API call ke Groq
- `chat.completions.create()`: Endpoint untuk chat completion
- Parameters:
  - `messages`: List of message objects dengan role dan content
    - System message: Set behavior/instruction untuk model
    - User message: Query dengan konteks
  - `model`: Nama model yang digunakan
  - `max_tokens`: Max output length
  - `temperature`: Randomness/creativity level
  - `timeout`: Max waktu tunggu response
- Returns: ChatCompletion object dengan response

```python
                response = chat_completion.choices[0].message.content
```
- Extract text response dari response object
- Structure:
  - `chat_completion.choices`: List of response choices (biasanya 1)
  - `[0]`: First choice
  - `.message`: Message object
  - `.content`: The actual text response

```python
                return response
```
- Return response dan exit function (skip retry loop)

```python
            except RateLimitError as e:
                logger.warning(f"Rate limit exceeded (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
```
- Catch RateLimitError specific exception
- Log warning dengan attempt number dan error details

```python
                if attempt < MAX_RETRIES - 1:
                ```
                - Check jika masih ada retries available
                - condition: attempt < 2 (jika ini adalah attempt 0, 1, atau 2)

```python
                    wait_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
```
- Calculate wait time menggunakan exponential backoff
- `2 ** attempt`: 2 pangkat attempt number
  - Attempt 0: 2^0 = 1 → 2 * 1 = 2 detik
  - Attempt 1: 2^1 = 2 → 2 * 2 = 4 detik
  - Attempt 2: 2^2 = 4 → 2 * 4 = 8 detik
- Exponential backoff membagi beban ke server saat error

```python
                    logger.info(f"Menunggu {wait_time} detik sebelum mencoba lagi...")
                    time.sleep(wait_time)
```
- Log info dan tunggu sebentar
- `time.sleep()`: Pause execution untuk specified seconds

```python
                else:
                    return "Maaf, terlalu banyak permintaan. Silakan coba lagi nanti."
```
- If semua retries exhausted, return error message ke user
- Tidak raise exception, tapi return friendly message

```python
            except APIError as e:
                logger.error(f"Groq API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
```
- Catch API errors (but not rate limit)
- Log error details

```python
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    logger.info(f"Menunggu {wait_time} detik sebelum mencoba lagi...")
                    time.sleep(wait_time)
```
- Same retry logic seperti RateLimitError

```python
                else:
                    return "Maaf, terjadi kesalahan pada API. Silakan coba lagi nanti."
```
- Return friendly error message jika semua retries gagal

```python
            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}/{MAX_RETRIES}): {e}", exc_info=True)
```
- Catch semua exceptions lainnya
- `exc_info=True`: Include stack trace di log untuk debugging

```python
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    logger.info(f"Menunggu {wait_time} detik sebelum mencoba lagi...")
                    time.sleep(wait_time)
```
- Retry logic lainnya

```python
                else:
                    return f"Error: {str(e)}"
```
- Return error message untuk unexpected errors

```python
        return "Maaf, gagal menghasilkan respons setelah beberapa percobaan."
```
- Fallback return jika loop selesai tanpa return
- Should not reach here tapi ada sebagai safety

```python
    def generate_simple(self, prompt: str, max_tokens: int = MAX_TOKENS) -> str:
        """
        Generate sederhana tanpa konteks RAG dengan retry logic
        
        Args:
            prompt: Prompt langsung ke model
            max_tokens: Maksimal token yang di-generate
            
        Returns:
            Teks yang di-generate
        """
```
- Alternative method untuk generate tanpa konteks RAG
- Lebih simple, langsung pass prompt ke model
- Useful untuk testing atau non-RAG scenarios

```python
        for attempt in range(MAX_RETRIES):
```
- Same retry loop structure

```python
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    max_tokens=max_tokens,
                    timeout=API_TIMEOUT
                )
```
- Simpler API call dengan hanya user message
- Tidak ada system prompt atau context

```python
                return chat_completion.choices[0].message.content
```
- Extract dan return response

```python
            except RateLimitError as e:
                logger.warning(f"Rate limit exceeded (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    logger.info(f"Menunggu {wait_time} detik sebelum mencoba lagi...")
                    time.sleep(wait_time)
                else:
                    return "Maaf, terlalu banyak permintaan. Silakan coba lagi nanti."
```
- Same retry handling seperti generate()

```python
            except APIError as e:
                logger.error(f"Groq API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    logger.info(f"Menunggu {wait_time} detik sebelum mencoba lagi...")
                    time.sleep(wait_time)
                else:
                    return "Maaf, terjadi kesalahan pada API. Silakan coba lagi nanti."
```
- Same API error handling

```python
            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}/{MAX_RETRIES}): {e}", exc_info=True)
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    logger.info(f"Menunggu {wait_time} detik sebelum mencoba lagi...")
                    time.sleep(wait_time)
                else:
                    return f"Error: {str(e)}"
```
- Same general exception handling

```python
        return "Maaf, gagal menghasilkan respons setelah beberapa percobaan."
```
- Fallback return

---

## reingest.py

File ini adalah script untuk ingest data ke ChromaDB, biasanya dijalankan saat setup pertama atau saat ada update data.

```python
import shutil
```
- Mengimpor shutil (shell utilities) module
- `shutil.rmtree()` digunakan untuk menghapus directory dan semua isinya

```python
from pathlib import Path
```
- Mengimpor Path untuk file operations

```python
from src.ingest import DataIngestor
```
- Mengimpor DataIngestor class untuk melakukan ingest

```python
from config.settings import VECTOR_STORE_DIR, PROCESSED_DATA_DIR
```
- Mengimpat paths yang dibutuhkan dari settings

```python
def reingest_data():
    """Ingest data Sahabat AI"""
```
- Main function untuk reingest process
- Dipanggil saat script dijalankan langsung

```python
    print("=" * 60)
    print("Ingest Data Sahabat AI ke ChromaDB")
    print("=" * 60)
    print()
```
- Print header dengan separator line
- Menampilkan informasi apa yang sedang dilakukan
- Empty print untuk spacing

```python
    # 1. Hapus vector store lama (optional)
    if VECTOR_STORE_DIR.exists():
```
- Cek apakah vector store directory exists
- Jika ada, kita akan menghapusnya untuk fresh start

```python
        print(f"Menghapus vector store lama...")
```
- Print pesan progress

```python
        shutil.rmtree(VECTOR_STORE_DIR)
```
- `shutil.rmtree()`: Hapus directory dan semua isi secara rekursif
- Ini akan menghapus:
  - ChromaDB SQLite database file
  - Semua embedding vectors
  - Semua metadata
- Membuat clean slate untuk fresh ingest

```python
        print("✓ Vector store lama berhasil dihapus")
        print()
```
- Print konfirmasi dan spacing

```python
    # 2. Ingest data
    csv_path = PROCSESSED_DATA_DIR / "extracted_data_sahabatai.csv"
```
- Build path ke CSV file data
- `/` operator di Path object untuk join paths
- Full path: `data/processed/extracted_data_sahabatai.csv`

```python
    if not csv_path.exists():
        print(f"❌ File tidak ditemukan: {csv_path}")
        return
```
- Validate CSV file exists
- Jika tidak, print error dan return keluar dari function
- `return`: Exit function early
- Prevents dari proceed dengan error

```python
    try:
```
- Start try block untuk error handling

```python
        ingestor = DataIngestor()
```
- Create instance DataIngestor
- Ini akan:
  - Load embedding model
  - Prepare vector store directory
  - Setup embedding function

```python
        ingestor.load_and_ingest_csv(str(csv_path))
```
- Call method untuk load CSV dan ingest ke ChromaDB
- `str(csv_path)`: Convert Path object ke string
- Method ini akan:
  - Load CSV file
  - Validate columns
  - Clean data
  - Build content strings
  - Generate embeddings
  - Save to ChromaDB

```python
        print()
        print("=" * 60)
        print("✓ Ingest selesai!")
        print("=" * 60)
```
- Print konfirmasi sukses dengan separator line

```python
    except Exception as e:
        print(f"❌ Error: {e}")
```
- Catch any exception
- Print error message
- Tidak raise exception jadi script tidak crash
- User bisa baca error dan fix issue

```python
if __name__ == "__main__":
    reingest_data()
```
- `__name__ == "__main__"`: True jika script dijalankan langsung
- False jika di-import sebagai module
- Ini memungkinkan script di-import tanpa auto-run
- Cara run: `python reingest.py`

---

## app.py

File ini adalah entry point utama untuk aplikasi RAG dengan mode interaktif CLI.

```python
import os
```
- Mengimpor os untuk environment variables dan file operations

```python
from dotenv import load_dotenv
load_dotenv()
```
- Mengimpor load_dotenv dari python-dotenv library
- `load_dotenv()`: Load environment variables dari file .env
- .env file biasanya berisi: `GROQ_API_KEY=your_key_here`
- Ini memudahkan management sensitive data

```python
import sys
```
- Mengimpor sys untuk system operations
- Digunakan untuk sys.exit() untuk terminate program

```python
import logging
```
- Mengimpor logging untuk messages dan error tracking

```python
from src.retriever import Retriever
```
- Mengimpor Retriever class untuk dokumen retrieval

```python
from src.generator import Generator
```
- Mengimpor Generator class untuk generate response

```python
import os
import logging
import warnings
```
- Import duplikat (belum terhapus di code)
- `import os` dan `import logging` sudah ada di atas
- Tidak masalah karena Python ignore duplicate imports

```python
warnings.filterwarnings("ignore", category=UserWarning)
```
- Filter UserWarning jangan ditampilkan
- Menyingkat output dan fokus penting info saja

```python
warnings.filterwarnings("ignore", category=DeprecationWarning)
```
- Filter DeprecationWarning jangan ditampilkan
- Deprecation warnings biasanya tidak critical untuk run

```python
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
```
- Set logging level untuk sentence_transformers logger ke ERROR
- Jadi hanya ERROR yang akan ditampilkan dari library ini
- Mengurangi noise log dari library third-party

```python
logging.getLogger("transformers").setLevel(logging.ERROR)
```
- Set logging level untuk transformers library ke ERROR
- Transformer is heavy library with lots of logs
- Filter untuk cleaner output

```python
logging.getLogger("httpx").setLevel(logging.WARNING)
```
- Set logging level untuk httpx (HTTP library) ke WARNING
- httpx shows INFO logs untuk setiap HTTP request
- Set ke WARNING untuk hanya menampilkan issues

```python
logging.getLogger("chromadb").setLevel(logging.ERROR)
```
- Set logging level untuk ChromaDB ke ERROR
- ChromaDB bisa verbose di logging
- Filter untuk cleaner output

```python
os.environ["ANONYMIZED_TELEMETRY"] = "False"
```
- Set environment variable untuk disable telemetri yang di-anonymize
- Beberapa library mengirim telemetri saat initialization
- "False" mencegah pengiriman data

```python
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
```
- Disable telemetri Hugging Face Hub
- "1" = True (disable)
- Mencegah Hugging Face mengirim usage data

```python
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
```
- Set verbosity level transformers library ke "error"
- Hanya error yang akan ditampilkan dari transformers

```python
os.environ["TOKENIZERS_PARALLELISM"] = "false"
```
- Disable parallelism di tokenizers
- "false" = disable
- Mencegah warning tentang parallel tokenization
- Membantu dengan compatibility on certain systems

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```
- Configure default logging untuk seluruh aplikasi
- `level=logging.INFO`: Set minimum level ke INFO (DEBUG tidak ditampilkan)
- `format`: Format string untuk setiap log message:
  - `%(asctime)s`: Timestamp
  - `%(name)s`: Logger name (nama file/module)
  - `%(levelname)s`: Level (INFO, WARNING, ERROR)
  - `%(message)s`: Log message
- Example output: `2024-02-18 10:30:45 - src.retriever - INFO - Vector store loaded`

```python
logger = logging.getLogger(__name__)
```
- Create logger untuk file app.py
- Logger name akan menjadi "__main__" karena ini adalah main script

```python
class RAGApp:
    """Aplikasi RAG Sederhana"""
```
- Class utama untuk aplikasi RAG
- Encapsulate semua fungsi yang dibutuhkan

```python
    def __init__(self):
        """Inisialisasi aplikasi RAG"""
```
- Constructor untuk RAGApp

```python
        print("=" * 60)
        print("Sistem RAG Coffee Shop")
        print()
```
- Print header aplikasi
- 60 tanda sama dengan sebagai separator
- Empty print untuk spacing

```python
        self.retriever = Retriever()
```
- Create instance Retriever
- Ini akan:
  - Load embedding model
  - Load vector store dari disk
  - Siap untuk handle queries

```python
        self.generator = Generator()
```
- Create instance Generator
- Ini akan:
  - Initialize Groq client
  - Validate API key
  - Siap untuk generate responses

```python
        print()
```
- Spacing untuk clean output

```python
    def query(self, question: str) -> dict:
        """
        Query ke sistem RAG
        
        Args:
            question: Pertanyaan dari user
            
        Returns:
            Dictionary dengan jawaban dan sumber
        """
```
- Main method untuk query sistem RAG
- Input: user question
- Output: dictionary dengan answer dan sources

```python
        print(f"Query: {question}")
        print("-" * 60)
```
- Print query dengan separator untuk feedback ke user

```python
        # Retrieve relevant documents
        documents = self.retriever.retrieve(question)
```
- Call retriever untuk mendapatkan dokumen relevan
- Input: user question
- Output: list of document dictionaries
- Method ini akan:
  - Embed query
  - Search vector database
  - Return top-k relevant documents

```python
        if not documents:
            return {
                "answer": "Maaf, tidak ada informasi yang relevan ditemukan.",
                "sources": []
            }
```
- Check jika tidak ada dokumen found
- Return dictionary dengan error message dan empty sources list
- Early return jika tidak ada data

```python
        # Format context
        context = self.retriever.format_context(documents)
```
- Format retrieved documents ke string yang bisa diberikan ke LLM
- Call format_context method dari retriever
- Output: formatted string dengan semua relevant documents

```python
        # Generate response
        answer = self.generator.generate(question, context)
```
- Generate response dari LLM dengan context
- Call method generate dari Generator
- Input: original question + context from retriever
- Output: LLM-generated response

```python
        # Extract sources
        sources = []
```
- Initialize empty list untuk menyimpan sources

```python
        for doc in documents:
            metadata = doc["metadata"]
            sources.append({
                "nama": metadata.get("source", "Unknown"),
                "lokasi": metadata.get("lokasi", "Unknown")
            })
```
- Extract source information dari setiap document
- `doc["metadata"]`: Get metadata dictionary
- `.get("source", "Unknown")`: Safe access, return "Unknown" jika tidak ada
- `.get("lokasi", "Unknown")`: Safe access, return "Unknown" jika tidak ada
- Append ke sources list dengan format:
  ```python
  {"nama": "@coffee1", "lokasi": "Jakarta Selatan"}
  ```

```python
        return {
            "answer": answer,
            "sources": sources
        }
```
- Return dictionary dengan response lengkap
- Format:
  ```python
  {
    "answer": "Berdasarkan informasi...",
    "sources": [
      {"nama": "@coffee1", "lokasi": "Jakarta Selatan"},
      {"nama": "@coffee2", "lokasi": "Jakarta Barat"}
    ]
  }
  ```

```python
    def print_response(self, response: dict):
        """
        Print response dalam format yang rapi
        
        Args:
            response: Dictionary response dari query()
        """
```
- Method untuk format dan print response ke user
- Input: dictionary dari query() method

```python
        print()
        print("Jawaban:")
        print("=" * 60)
        print(response["answer"])
        print()
```
- Print answer dengan formatting:
  - Empty print untuk spacing
  - Header "Jawaban:"
  - Separator line
  - The answer itself
  - Empty print untuk spacing

```python
        if response["sources"]:
            print("Sumber informasi:")
            print("-" * 60)
            for i, source in enumerate(response["sources"], 1):
                print(f"{i}. {source['nama']} - {source['lokasi']}")
        print()
```
- Print sources jika ada
- `if response["sources"]`: Check jika list not empty
- Print header dan separator
- Iterate sources dengan enumerated index (starting from 1)
- Print format: "1. @coffee1 - Jakarta Selatan"
- Empty print untuk spacing

```python
def main():
    """Fungsi utama - Mode interaktif"""
```
- Main function yang menangani interactive CLI mode

```python
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY tidak ditemukan!")
        print("Silakan set Groq API key Anda:")
        print("  export GROQ_API_KEY='your_api_key_here'  # Linux/Mac")
        print("  set GROQ_API_KEY=your_api_key_here       # Windows CMD")
        print("  $env:GROQ_API_KEY='your_api_key_here'    # Windows PowerShell")
        print()
        print("Dapatkan API key dari: https://console.groq.com/")
        sys.exit(1)
```
- Check if GROQ_API_KEY exists di environment variables
- `os.getenv("GROQ_API_KEY")`: Get environment variable, returns None jika not exists
- Jika tidak ada API key:
  - Print error message
  - Print instructions untuk set API key di different OS:
    - Linux/Mac: export command
    - Windows CMD: set command
    - Windows PowerShell: $env syntax
  - Print URL untuk get API key
  - `sys.exit(1)`: Terminate program dengan exit code 1 (error)
- Exit code 1 menandakan abnormal termination

```python
    try:
        app = RAGApp()
```
- Create RAGApp instance
- Ini akan initialize retriever dan generator
- Wrapped in try block untuk handle initialization errors

```python
    except FileNotFoundError as e:
        logger.error(f"Error saat inisialisasi: {e}")
        print(f"Error: {e}")
        sys.exit(1)
```
- Catch FileNotFoundError (biasanya saat vector store tidak ada)
- Log error dengan details
- Print error ke user
- Exit dengan exit code 1

```python
    except Exception as e:
        logger.error(f"Error tak terduga saat inisialisasi: {e}", exc_info=True)
        print(f"Error tak terduga: {e}")
        sys.exit(1)
```
- Catch semua exceptions lainnya
- Log error dengan stack trace (`exc_info=True`)
- Print user-friendly error message
- Exit dengan exit code 1

```python
    print("=" * 60)
    print("Ketik pertanyaan tentang coffee shop")
    print("Ketik 'exit' atau 'quit' untuk keluar")
    print("=" * 60)
    print()
```
- Print instructions untuk mode interaktif
- Separator lines untuk visual clarity
- Spacing di end

```python
    while True:
```
- Infinite loop untuk interactive prompt
- Akan terus berjalan sampai user type "exit" atau "quit"
- Atau sampai KeyboardInterrupt (Ctrl+C)

```python
        try:
```
- Try block untuk handle user input dan processing errors

```python
            question = input(">> ").strip()
```
- Get input dari user dengan prompt ">> "
- `.strip()`: Remove leading/trailing whitespace
- Stores user input in variable question

```python
            if question.lower() in ["exit", "quit"]:
                break
```
- Check jika user wants to exit
- `.lower()`: Convert ke lowercase untuk case-insensitive comparison
- Check jika "exit" atau "quit" (case-insensitive)
- `break`: Exit while loop, ending the program

```python
            if not question:
                continue
```
- Check jika question is empty
- `continue`: Skip to next iteration, prompt user again
- This handles Enter tanpa typing apa-apa

```python
            # Input sanitization
            if len(question) > 1000:
                print("Pertanyaan terlalu panjang. Maksimal 1000 karakter.")
                continue
```
- Validate panjang question
- `len(question) > 1000`: Check jika lebih dari 1000 karakter
- Print error message jika terlalu panjang
- `continue`: Skip processing, prompt user again
- Ini mencegah abuse/misuse

```python
            response = app.query(question)
```
- Call query method dengan user question
- Ini akan:
  - Retrieve relevant documents
  - Generate answer
  - Return dictionary dengan answer dan sources

```python
            app.print_response(response)
```
- Print hasil response ke user dengan formatting
- Menampilkan jawaban dan sumber informasi

```python
        except KeyboardInterrupt:
            print("\n\nSampai jumpa")
            break
```
- Catch KeyboardInterrupt (Ctrl+C)
- Print goodbye message
- `break`: Exit loop and end program gracefully
- `\n\n`: Newline untuk formatting

```python
        except Exception as e:
            logger.error(f"Error saat memproses query: {e}", exc_info=True)
            print(f"Error: {e}")
            print("Silakan coba lagi.")
```
- Catch semua exceptions lainnya
- Log error dengan stack trace
- Print user-friendly error message
- Print instruction untuk try again
- Loop continues, prompting user again

```python
if __name__ == "__main__":
    main()
```
- Entry point saat script dijalankan langsung
- `python app.py` akan menjalankan main()
- Jika di-import sebagai module, main() tidak akan dijalankan
- Standard Python pattern

---

## Ringkasan Flow Aplikasi

### Flow Inisialisasi
```
1. Load environment variables dari .env
2. Setup logging dan filter warnings
3. Check GROQ_API_KEY exists
4. Create RAGApp:
   a. Initialize Retriever
      - Load embedding model
      - Load vector store dari ChromaDB
   b. Initialize Generator
      - Create Groq client
5. Masuk ke interactive loop
```

### Flow Query
```
1. User input → question
2. Validate input (not empty, not too long)
3. app.query(question):
   a. retriever.retrieve(question)
      - Embed query
      - Search ChromaDB dengan MMR
      - Return top-k documents
   b. retriever.format_context(documents)
      - Format documents untuk LLM
   c. generator.generate(question, context)
      - Build prompt dengan context
      - Call Groq API dengan retry logic
      - Return LLM response
   d. Extract sources dari metadata
   e. Return {answer, sources}
4. app.print_response(response)
   - Print jawaban dan sources
5. Back to prompt for next question
```

### Flow Exit
```
User types "exit" or "quit"
→ Break loop
→ Program ends
```

---

## Catatan Penting

1. **Embedding Consistency**: Embedding model harus SAMA antara ingest dan retrieval
2. **Retry Logic**: Generator menangani rate limits dengan exponential backoff
3. **Error Handling**: Semua critical paths punya error handling yang baik
4. **Input Validation**: User input di-sanitize (length check, empty check)
5. **Logging**: Comprehensive logging untuk debugging dan monitoring
6. **Modularity**: Setiap komponen terpisah dengan clear responsibilities
