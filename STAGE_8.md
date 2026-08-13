## Tahap 8 — Hybrid Search Engine

Arsitektur:

```text
                    PERTANYAAN USER
                           │
                           ▼
                  Query Normalization
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       Lexical Search             Vector Search
       (Arabic/BM25)              (Embedding)
              │                         │
              └────────────┬────────────┘
                           ▼
                    Candidate Fusion
                           │
                           ▼
                       Reranker
                           │
                           ▼
                Verified Evidence Only
                           │
                           ▼
                    RAG Assistant
```

### Mengapa hybrid?

Misalnya pengguna bertanya:

> Apa hubungan niat dengan amal menurut Ibnu Hajar?

Sementara teks sumber:

> إنما الأعمال بالنيات وإنما لكل امرئ ما نوى

**Keyword search** mungkin kuat untuk istilah Arab tertentu.

**Embedding search** lebih kuat untuk memahami kesamaan makna:

```text
"niat dan amal"
        ↓
إنما الأعمال بالنيات
```

Keduanya kemudian digabung.

---

# 1. Struktur data baru

Tambahkan:

```text
document_chunks
├── id
├── sharh_section_id
├── hadith_id
├── text
├── normalized_text
├── language
├── volume
├── pdf_page
├── printed_page
├── verified
└── embedding
```

Kemudian:

```text
retrieval_logs
├── id
├── query
├── query_language
├── retrieved_chunks
├── reranked_chunks
├── latency_ms
└── created_at
```

Ini penting untuk mengevaluasi apakah mesin pencarian kita benar-benar membaik.

---

# 2. PostgreSQL + pgvector

Untuk production, saya menyarankan:

```text
PostgreSQL
├── Full Text Search
├── pg_trgm
└── pgvector
```

Jadi tidak perlu langsung memperkenalkan database vector terpisah.

Arsitektur:

```text
                  PostgreSQL
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
     FTS           pg_trgm        pgvector
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                Hybrid Retrieval
```

---

# 3. Embedding

Untuk setiap chunk Fathul Bari:

```text
النص العربي
      ↓
Embedding Model
      ↓
Vector
      ↓
pgvector
```

Tetapi karena pengguna bisa bertanya dalam Bahasa Indonesia, **model embedding harus mendukung multilingual Arabic ↔ Indonesian semantic retrieval**.

Jangan menggunakan embedding English-only.

---

# 4. Query pipeline

Misalnya:

> Jelaskan mengapa seseorang mendapatkan pahala berdasarkan niatnya.

Pipeline:

```text
Query
 │
 ▼
Detect language
 │
 ▼
Normalize query
 │
 ├───────────────┐
 ▼               ▼
BM25/FTS       Embedding
 │               │
 ▼               ▼
50 candidates   50 candidates
 │               │
 └───────┬───────┘
         ▼
    Reciprocal Rank
       Fusion
         │
         ▼
     Top 20
         │
         ▼
      Reranker
         │
         ▼
       Top 5
         │
         ▼
Verified filter
         │
         ▼
RAG
```

---

# 5. Reciprocal Rank Fusion

Daripada sekadar:

```text
BM25 score + vector score
```

lebih aman menggunakan **RRF**.

Secara sederhana:

```text
RRF(d) =
Σ 1 / (k + rank(d))
```

Contohnya:

```text
Candidate       BM25     Vector
--------------------------------
Hadis #1          1         2
Hadis #45         4         1
Hadis #100        2        15
```

RRF memungkinkan kedua mesin memberikan kontribusi.

---

# 6. Reranker

Setelah mendapatkan 20 kandidat:

```text
Query
 +
Candidate
       ↓
Reranker
       ↓
Relevance score
```

Kemudian:

```text
20 candidates
       ↓
reranker
       ↓
5 terbaik
```

Baru lima evidence ini diberikan kepada LLM.

Ini jauh lebih hemat token dibanding memberikan puluhan halaman Fathul Bari kepada model.

---

# 7. Verified-first policy

Ini bagian yang **sangat penting** untuk aplikasi kita.

Retrieval tidak boleh:

```text
Top similarity
     ↓
langsung ke LLM
```

Tetapi:

```text
Top similarity
       ↓
Check hadith_sharh_links
       ↓
verified?
   ┌───┴───┐
   │       │
  YES      NO
   │       │
   ▼       ▼
RAG      fallback
```

Dengan prioritas:

```text
1. Verified Fathul Bari
2. Verified Hadith
3. Unverified candidate
4. External knowledge
```

Untuk mode **Research**, saya bahkan menyarankan nomor 4 **dimatikan**.

---

# 8. Tiga mode AI Assistant

### Research Mode

```text
ONLY VERIFIED SOURCES
```

Jika tidak menemukan sumber:

> Tidak ditemukan evidence terverifikasi.

### Study Mode

```text
Verified sources
+
unverified candidates
```

Tetapi sumber unverified harus diberi label jelas.

### General Mode

Boleh menggunakan knowledge umum model, tetapi harus mengatakan bahwa jawaban tersebut **bukan kutipan langsung dari Fathul Bari**.

Untuk aplikasi Anda, default sebaiknya:

> **Research Mode**

---

# 9. UI Search

Tambahkan search bar:

```text
┌─────────────────────────────────────────────────────┐
│ 🔎 Cari dalam Fathul Bari...                       │
│                                                     │
│ "Apa maksud Ibnu Hajar tentang niat?"              │
│                                                     │
│ [Research Mode ▼]                    [Search]       │
└─────────────────────────────────────────────────────┘
```

Hasil:

```text
┌─────────────────────────────────────────────────────┐
│ #1 — Bukhari 1                                      │
│                                                     │
│ إنما الأعمال بالنيات...                             │
│                                                     │
│ Fathul Bari · Vol. 1 · hlm. 12                     │
│                                                     │
│ Relevance 94% · VERIFIED ✓                          │
│                                                     │
│ [Buka Syarah] [Buka Source]                        │
└─────────────────────────────────────────────────────┘
```

---

# 10. Citation

Jawaban AI harus menghasilkan citation inline:

> Ibnu Hajar menjelaskan bahwa hadis ini berkaitan dengan pertimbangan niat dalam amal seseorang **[Fathul Bari, Vol. 1, hlm. 12]**.

Klik citation:

```text
        ↓
Source Viewer
        ↓
PDF page 45
```

Jadi pengguna bisa melakukan:

**Jawaban → Evidence → Syarah → PDF asli**

tanpa kehilangan jejak.

---

# 11. Evaluasi kualitas

Sebelum kita naik ke tahap Knowledge Graph, kita perlu membuat **golden dataset**.

Contoh:

```text
Query:
"Apa hubungan niat dengan amal?"

Expected:
Hadith #1
Fathul Bari Vol 1
Section X
```

Kemudian ukur:

```text
Recall@5
Recall@10
MRR
NDCG
Precision@5
```

Target awal:

```text
Recall@5  > 90%
MRR        > 0.80
```

Angka ini adalah **target engineering**, bukan klaim performa sebelum diuji.

---

# 12. Tahap 8B — Multilingual Arabic Retrieval

Setelah hybrid search dasar bekerja, kita optimalkan:

```text
Indonesia
    ↕
Arabic
    ↕
English
```

Contoh:

```text
"amal tergantung niat"
          ↕
"إنما الأعمال بالنيات"
          ↕
"actions are judged by intentions"
```

Ketiga query tersebut idealnya menemukan evidence yang sama.

---

# 13. Roadmap sekarang

Kita sudah memiliki:

```text
✓ Stage 1  Foundation
✓ Stage 2  Hadith API Integration
✓ Stage 3  Hadith/Syarah Data Model
✓ Stage 4  Matching Engine
✓ Stage 5  Review Dashboard
✓ Stage 6  Source Viewer + Audit Trail
✓ Stage 7  RAG/Syarah Assistant
```

Berikutnya:

```text
▶ Stage 8  Hybrid Arabic Search
            │
            ▼
▶ Stage 9  Knowledge Graph
            │
            ▼
▶ Stage 10 Multi-volume Fathul Bari
            │
            ▼
▶ Stage 11 Research Analytics
            │
            ▼
▶ Stage 12 Production + Security
```

