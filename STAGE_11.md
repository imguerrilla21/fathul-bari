**Stage 11 — Research Analytics & Quality Control*

Tahap ini penting sebelum aplikasi masuk ke production, karena kita perlu bisa menjawab:

* Seberapa banyak hadis yang sudah terhubung dengan Fathul Bari?
* Berapa yang sudah diverifikasi manusia?
* Bagian mana yang masih memiliki confidence rendah?
* Seberapa akurat retrieval RAG?
* Sumber mana yang belum memiliki halaman yang jelas?
* Berapa banyak jawaban AI yang benar-benar memiliki citation?

# Stage 11 — Research Analytics & Quality Control

```text
                    KNOWLEDGE BASE
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Hadith       Sharh       Sources
             │           │           │
             └─────┬─────┴─────┬─────┘
                   ▼           ▼
               Matching     Knowledge
                   │          Graph
                   ▼           │
               Review         │
                   │           │
                   └─────┬─────┘
                         ▼
                 QUALITY ENGINE
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
    Coverage         Retrieval        Citation
    Metrics          Metrics          Metrics
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                 RESEARCH ANALYTICS
```

---

## 1. Executive Dashboard

Dashboard utama:

```text
┌─────────────────────────────────────────────────────────────┐
│ FATHUL BARI — RESEARCH ANALYTICS                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ HADIS          SYARAH          VERIFIED        SOURCES      │
│ 7,563          8,921           6,482           12,430       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Coverage                 Verification                       │
│ ████████████████ 84%     █████████████ 73%                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Matching Quality                                            │
│                                                             │
│ >90% confidence       5,231                                │
│ 70–90%                1,482                                │
│ <70%                  850                                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ RAG QUALITY                                                 │
│                                                             │
│ Recall@5     92%                                           │
│ MRR          0.87                                           │
│ Citation     96%                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Angka di atas hanya contoh UI, **bukan data aktual**.

---

# 2. Dataset Coverage

Kita perlu mengetahui cakupan database.

Contoh:

```text
Hadis Bukhari
    │
    ├── Imported
    ├── Normalized
    ├── Matched
    ├── Verified
    └── Rejected
```

Metric:

```text
coverage =
verified_hadith / total_hadith
```

Tetapi kita juga perlu:

```text
sharh_coverage =
sharh_sections_with_verified_links
/
total_sharh_sections
```

---

# 3. Verification Analytics

Dashboard:

```text
VERIFICATION STATUS

Verified       ███████████████  73%
Pending        █████             22%
Rejected       ██                 5%
```

Filter:

```text
Collection
Volume
Chapter
Confidence
Reviewer
Date
```

Contoh:

```text
Volume 1
 ├── Verified  91%
 ├── Pending    7%
 └── Rejected   2%
```

Ini membantu menentukan bagian mana yang harus diprioritaskan untuk review.

---

# 4. Confidence Distribution

Jangan hanya menyimpan satu confidence score.

Simpan:

```text
semantic_score
lexical_score
reranker_score
final_confidence
```

Contoh:

```json
{
  "semantic_score": 0.91,
  "lexical_score": 0.84,
  "reranker_score": 0.96,
  "final_confidence": 0.93
}
```

Dengan begitu kita dapat mengetahui **mengapa** sebuah matching memperoleh confidence tinggi.

---

# 5. Confidence Calibration

Ini fitur yang sangat penting.

Misalnya:

```text
confidence 0.90–1.00
```

ternyata hanya:

```text
82% verified
```

maka confidence model terlalu optimistis.

Kita ingin:

```text
Predicted confidence
        ≈
Actual verification probability
```

Gunakan calibration curve:

```text
Confidence
1.0 ┤                         ●
0.8 ┤                   ●
0.6 ┤             ●
0.4 ┤       ●
0.2 ┤ ●
    └──────────────────────────
      Actual verification rate
```

Kemudian kita bisa menggunakan:

* Platt scaling
* isotonic regression

untuk calibration.

---

# 6. Retrieval Evaluation

Stage 8 membuat retrieval engine.

Sekarang kita ukur.

Buat tabel:

```text
evaluation_queries
evaluation_expected_results
evaluation_runs
```

Contoh:

```json
{
  "query": "Apa maksud Ibnu Hajar tentang niat?",
  "expected": [
    "hadith-1",
    "sharh-1"
  ]
}
```

Kemudian:

```text
Recall@1
Recall@5
Recall@10
MRR
NDCG
Precision@K
```

---

# 7. Golden Dataset

Ini akan menjadi salah satu aset paling berharga aplikasi.

Contoh:

```text
Question
Expected Hadith
Expected Sharh
Expected Source
```

Minimal buat:

```text
100 queries
```

Kemudian berkembang menjadi:

```text
500
1,000
5,000
```

Kategori:

```text
Direct Hadith
Conceptual
Arabic
Indonesian
Cross-reference
Multi-hop
Ambiguous
```

---

# 8. RAG Evaluation

Tidak cukup mengukur retrieval.

Jawaban AI juga harus dievaluasi.

Metric:

```text
Groundedness
Citation correctness
Citation completeness
Answer relevance
Faithfulness
```

Contoh:

```text
Question
   ↓
Retrieved Evidence
   ↓
AI Answer
   ↓
Evaluator
```

Output:

```json
{
  "groundedness": 0.94,
  "citation_correctness": 1.0,
  "citation_completeness": 0.91,
  "answer_relevance": 0.95
}
```

---

# 9. Citation Integrity

Kita buat aturan otomatis:

```text
AI Answer
   │
   ▼
Extract citations
   │
   ▼
Check citation IDs
   │
   ├── valid
   └── invalid
```

Jika AI menghasilkan:

> Fathul Bari, jilid 2, halaman 123.

sistem harus memastikan:

```text
Volume 2 exists?
Page 123 exists?
Section exists?
Source exists?
Evidence actually contains claim?
```

Kalau tidak:

```text
INVALID CITATION
```

Jawaban tidak boleh langsung dianggap valid.

---

# 10. AI Answer Audit

Simpan setiap sesi:

```text
assistant_sessions
assistant_messages
assistant_evidence
assistant_citations
```

Contoh:

```text
Question
   │
   ▼
Retrieved evidence
   │
   ▼
Prompt
   │
   ▼
LLM response
   │
   ▼
Citations
   │
   ▼
User feedback
```

Dengan ini kita dapat melakukan audit penuh.

---

# 11. Hallucination Monitor

Buat classifier:

```text
CLAIM
 │
 ├── Supported
 ├── Partially Supported
 └── Unsupported
```

Misalnya AI mengatakan:

> Ibnu Hajar menyatakan X.

Sistem mencari evidence:

```text
X ditemukan?
   │
   ├── YES → Supported
   │
   └── NO → Flag
```

Dashboard:

```text
AI QUALITY

Supported claims       94.2%
Partial claims          4.1%
Unsupported claims      1.7%
```

Angka tersebut tentunya baru akan diketahui setelah sistem dijalankan.

---

# 12. Research Analytics

Untuk setiap project:

```text
Project: Konsep Niat dalam Fathul Bari

Hadith studied: 17
Sharh sections: 31
Volumes: 3
Sources: 47

Notes: 82
Citations: 63
AI questions: 129
```

Visual:

```text
Topic
 │
 ├── 17 Hadith
 ├── 31 Sharh
 ├── 47 Sources
 └── 63 Citations
```

---

# 13. Research Timeline

Tambahkan:

```text
2026-08-01
│
├── Created project
│
├── Added Bukhari #1
│
├── Added Sharh §1
│
├── Verified source
│
├── Added note
│
└── Generated analysis
```

Ini berguna untuk menjaga histori penelitian.

---

# 14. Reviewer Performance

Karena kita memiliki Audit Trail:

```text
Reviewer
   │
   ├── reviewed
   ├── verified
   ├── rejected
   └── average review time
```

Dashboard:

```text
Reviewer            Verified    Rejected
─────────────────────────────────────────
Reviewer A            842          37
Reviewer B            611          29
Reviewer C            492          41
```

Jangan menggunakan metric ini untuk "menghukum" reviewer; tujuannya untuk mengetahui **beban kerja dan konsistensi proses**.

---

# 15. Inter-Rater Agreement

Untuk data yang penting, dua reviewer dapat memverifikasi independently.

```text
Reviewer A ──┐
             ├──► Agreement
Reviewer B ──┘
```

Metric:

```text
Cohen's Kappa
Fleiss' Kappa
```

Misalnya:

```text
Agreement
0.81
```

Ini jauh lebih kuat daripada hanya mengatakan:

> "Sudah diverifikasi."

---

# 16. Quality Flags

Tambahkan automatic flags:

```text
⚠ Missing source page
⚠ Low confidence
⚠ Conflicting reviewer decisions
⚠ Citation mismatch
⚠ Duplicate section
⚠ Possible duplicate hadith
⚠ Unverified relationship
⚠ OCR quality low
```

Dashboard:

```text
QUALITY ISSUES

🔴 Critical     12
🟠 Warning      47
🟡 Review       183
```

Klik issue:

```text
Issue #1024

Hadith: Bukhari #1571
Sharh: §3821

Problem:
Source PDF page missing.

[Open Review]
[Open Source]
[Resolve]
```

---

# 17. Data Quality Pipeline

Arsitektur lengkap:

```text
                 RAW DATA
                    │
                    ▼
               NORMALIZATION
                    │
                    ▼
                  OCR QA
                    │
                    ▼
                MATCHING QA
                    │
                    ▼
              HUMAN REVIEW
                    │
                    ▼
             KNOWLEDGE GRAPH
                    │
                    ▼
              RAG EVALUATION
                    │
                    ▼
             QUALITY DASHBOARD
```

---

# 18. Quality Score

Kita bisa membuat **Research Quality Score**, tetapi jangan mencampurkan semuanya menjadi satu angka tanpa transparansi.

Lebih baik:

```text
Data Coverage        91%
Verification          84%
Source Integrity      97%
Retrieval Quality     92%
Citation Integrity    96%
RAG Groundedness      94%
```

Daripada:

```text
Overall Score = 93%
```

karena angka tunggal bisa menyesatkan.

---

# 19. Stage 11 API

Tambahkan:

```http
GET /api/v1/analytics/overview

GET /api/v1/analytics/coverage

GET /api/v1/analytics/verification

GET /api/v1/analytics/confidence

GET /api/v1/analytics/retrieval

GET /api/v1/analytics/rag

GET /api/v1/analytics/citations

GET /api/v1/analytics/issues
```

Evaluation:

```http
POST /api/v1/evaluation/query

POST /api/v1/evaluation/run

GET /api/v1/evaluation/results
```

---

# 20. Arsitektur sampai Stage 11

Sekarang sistem kita menjadi:

```text
                   ┌─────────────────────┐
                   │ Ahmad Sanusi API    │
                   └──────────┬──────────┘
                              ▼
                     HADITH DATABASE
                              │
                              ▼
                    FATHUL BARI CORPUS
                              │
                              ▼
                    EXTRACTION / OCR
                              │
                              ▼
                      MATCHING ENGINE
                              │
                              ▼
                      REVIEW DASHBOARD
                              │
                              ▼
                    SOURCE + AUDIT TRAIL
                              │
                              ▼
                    KNOWLEDGE GRAPH
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          HYBRID SEARCH                GRAPHRAG
                 │                         │
                 └────────────┬────────────┘
                              ▼
                     AI SYARAH ASSISTANT
                              │
                              ▼
                    RESEARCH WORKSPACE
                              │
                              ▼
                    QUALITY CONTROL
                              │
                              ▼
                   RESEARCH ANALYTICS
```

