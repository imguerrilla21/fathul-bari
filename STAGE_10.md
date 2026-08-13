# Stage 10 — Multi-Volume Fathul Bari & Research Workspace

Tahap ini membuat aplikasi siap menangani **seluruh jilid Fathul Bari**, bukan hanya satu volume atau kumpulan section terpisah.

## 1. Target Stage 10

Kita ingin mencapai:

```text
                FATHUL BARI
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   Volume 1       Volume 2      ... Volume 13
       │             │                 │
       ▼             ▼                 ▼
    Sections       Sections          Sections
       │             │                 │
       └─────────────┼─────────────────┘
                     ▼
              Knowledge Graph
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
     Hybrid Search          GraphRAG
          │                     │
          └──────────┬──────────┘
                     ▼
              Research Workspace
```

---

# 2. Multi-volume data model

Kita perlu memperjelas struktur:

```text
Work
 │
 ├── Edition
 │
 │    ├── Volume
 │    │     ├── Page
 │    │     │     └── Section
 │    │     │
 │    │     └── Section
 │    │
 │    └── Metadata
 │
 └── Source Document
```

Contoh:

```text
Fathul Bari
│
├── Edition A
│
├── Volume 1
│   ├── PDF Page 1
│   ├── PDF Page 2
│   └── ...
│
├── Volume 2
│   └── ...
│
└── Volume 13
```

Ini penting karena **halaman PDF dan halaman cetak tidak selalu sama**.

---

# 3. Source identity

Setiap kutipan harus mempunyai identitas sumber yang lengkap:

```json
{
  "work": "Fathul Bari",
  "author": "Ibn Hajar al-Asqalani",
  "edition": "...",
  "volume": 1,
  "pdf_page": 45,
  "printed_page": 12,
  "section_id": "...",
  "source_document_id": "..."
}
```

Sehingga citation tidak cukup hanya:

> Fathul Bari, jilid 1.

Tetapi:

> Ibn Hajar al-Asqalani, *Fathul Bari*, edisi X, jilid 1, hlm. 12, PDF hlm. 45.

---

# 4. Hadith-to-Sharh Mapping

Ini akan menjadi salah satu fitur terpenting.

Misalnya:

```text
Bukhari #1
     │
     ├── Fathul Bari §001
     ├── Fathul Bari §002
     └── Fathul Bari §003
```

Karena satu hadis bisa memiliki pembahasan yang panjang.

Sebaliknya:

```text
Fathul Bari §050
      │
      ├── Bukhari #20
      ├── Bukhari #21
      └── Bukhari #22
```

Jadi jangan gunakan constraint:

```text
1 Hadis = 1 Syarah
```

Model harus mendukung:

```text
Many-to-many
```

---

# 5. Research Workspace

Kita kemudian membuat workspace khusus peneliti.

```text
┌──────────────────────────────────────────────────────┐
│ FATHUL BARI RESEARCH WORKSPACE                       │
├──────────────────────────────────────────────────────┤
│ Search: [ niat amal                              ] 🔎│
├───────────────┬──────────────────────┬───────────────┤
│ HADIS         │ SYARAH               │ SOURCE        │
│               │                      │               │
│ Bukhari #1    │ Fathul Bari §1       │ Vol 1 p.12    │
│               │                      │               │
│ Arabic text   │ Arabic text          │ PDF viewer    │
│               │                      │               │
│               │ Explanation...       │               │
├───────────────┴──────────────────────┴───────────────┤
│ NOTES                                                 │
│                                                      │
│ [ Tambahkan catatan penelitian... ]                  │
│                                                      │
├──────────────────────────────────────────────────────┤
│ CITATIONS                                             │
│ [1] Bukhari #1                                       │
│ [2] Fathul Bari Vol 1 p.12                           │
└──────────────────────────────────────────────────────┘
```

---

# 6. Research Notes

Tambahkan tabel:

```text
research_projects
research_notes
research_citations
```

### Research project

```text
id
title
description
created_by
created_at
```

### Research note

```text
id
project_id
content
hadith_id
sharh_section_id
source_page_id
created_at
updated_at
```

Dengan demikian pengguna bisa membuat:

> **Penelitian: Konsep Niat dalam Fathul Bari**

dan menyimpan semua evidence di dalam satu workspace.

---

# 7. Annotation

Peneliti juga harus bisa menandai teks:

```text
[TEXT]
   ↓
Highlight
   ↓
Annotation
```

Contoh:

```text
قوله إنما الأعمال بالنيات...

       ↑
       └── [Catatan]
           Ibnu Hajar membahas...
```

Tipe annotation:

```text
NOTE
QUESTION
IMPORTANT
CROSS_REFERENCE
QUOTE
TODO
```

---

# 8. Citation Manager

Setiap evidence dapat dimasukkan ke citation collection:

```text
Research Project
      │
      ├── Citation #1
      │     └── Bukhari #1
      │
      ├── Citation #2
      │     └── Fathul Bari Vol.1 p.12
      │
      └── Citation #3
            └── Fathul Bari Vol.1 p.13
```

Kemudian:

```text
Export citations
```

ke format:

```text
Markdown
BibTeX
RIS
JSON
```

---

# 9. Cross-reference Engine

Ini akan menjadi fitur kuat.

Misalnya Fathul Bari section A menyebut:

```text
انظر حديث رقم 123
```

Engine mendeteksi:

```text
"حديث رقم 123"
```

dan membuat candidate:

```text
Sharh A
   │
   └── REFERENCES
          │
          ▼
      Hadith #123
```

Kemudian masuk ke review jika confidence rendah.

---

# 10. Topic Research

Tambahkan entity:

```text
Topic
```

Contoh:

```text
NIAT
IKHLAS
TAUHID
SHALAT
PUASA
ZAKAT
HAJI
AKHLAK
IMAN
MUAMALAH
```

Hubungan:

```text
Hadith
  │
  └── ABOUT ──► Topic
                   ▲
                   │
              DISCUSSES
                   │
                Sharh
```

Dengan ini pengguna dapat membuka:

> **Semua pembahasan Fathul Bari tentang Niat**

dan mendapatkan:

```text
Hadis
↓
Syarah
↓
Volume
↓
Halaman
↓
Related Hadith
```

---

# 11. Research Graph

Workspace kemudian mempunyai graph sendiri:

```text
                 TOPIC
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
     HADITH     SHARH     PERSON
        │         │
        │         │
        └────┬────┘
             ▼
          SOURCE
             │
             ▼
          PAGE
```

Berbeda dari Knowledge Graph global, **Research Graph hanya berisi entity yang dipilih untuk penelitian tertentu**.

---

# 12. RAG dalam Research Workspace

Sekarang AI dapat bekerja berdasarkan workspace:

```text
User
 │
 ▼
Research Question
 │
 ▼
Workspace Filter
 │
 ├── Selected Hadith
 ├── Selected Sharh
 ├── Selected Topics
 └── Selected Sources
 │
 ▼
GraphRAG
 │
 ▼
Answer
 │
 ▼
Citations
```

Misalnya:

> “Bandingkan penjelasan Ibnu Hajar tentang niat pada tiga hadis berikut.”

AI tidak mencari seluruh internet.

Ia hanya menggunakan:

```text
Research Project
     ↓
3 Hadith
     ↓
Verified Sharh
     ↓
Source pages
```

---

# 13. Export Research

Pada akhirnya:

```text
Research Workspace
        │
        ▼
      Export
        │
 ┌──────┼──────┐
 ▼      ▼      ▼
MD     PDF    DOCX
```

Struktur hasil:

```text
# Penelitian Konsep Niat

## Pertanyaan Penelitian

...

## Hadis

### Hadis 1
...

## Syarah Fathul Bari

...

## Analisis

...

## Evidence

...

## References

...
```

AI hanya membantu menyusun analisis; **citation tetap berasal dari evidence yang tersimpan**.

---

# 14. Arsitektur keseluruhan sekarang

Kita sudah sampai pada arsitektur yang jauh lebih matang:

```text
                 ┌─────────────────────┐
                 │   Ahmad Sanusi API  │
                 └──────────┬──────────┘
                            │
                            ▼
                     Hadith Database
                            │
                            ▼
                   Fathul Bari Dataset
                            │
                            ▼
                    Matching Engine
                            │
                            ▼
                    Review Dashboard
                            │
                       VERIFY
                            │
                            ▼
                    Source + Audit
                            │
                            ▼
                   Knowledge Graph
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
        Hybrid Search                 GraphRAG
              │                           │
              └─────────────┬─────────────┘
                            ▼
                    AI Syarah Assistant
                            │
                            ▼
                   Research Workspace
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
          Notes         Citations       Export
```

---

# 15. Urutan implementasi Stage 10

Saya sarankan jangan langsung mengerjakan semuanya sekaligus.

```text
10A  Multi-volume data model
 ↓
10B  Source/Edition management
 ↓
10C  Hadith ↔ Sharh cross-reference
 ↓
10D  Research Project
 ↓
10E  Notes & annotations
 ↓
10F  Citation manager
 ↓
10G  Research Graph
 ↓
10H  GraphRAG workspace
 ↓
10I  Export
```

### Prioritas pertama

**10A–10C harus selesai terlebih dahulu.**

Karena sebelum membuat workspace penelitian, kita harus memastikan:

```text
Hadis
  ↕
Syarah
  ↕
Volume
  ↕
Halaman
  ↕
Source PDF
  ↕
Audit
```

sudah memiliki **ID dan provenance yang konsisten**.

Setelah itu **10D–10I** bisa dibangun di atas fondasi tersebut.

Dengan Stage 10 ini, aplikasi mulai berubah dari **“AI chatbot Fathul Bari” menjadi research platform Fathul Bari**: pengguna dapat mencari, memverifikasi, menelusuri sumber, membangun penelitian, menyimpan catatan, dan menghasilkan jawaban AI yang tetap terhubung ke sumber primer.
