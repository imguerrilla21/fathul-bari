# Stage 15 — Arabic NLP & Advanced Hadith Matching

## 15.1 Target utama

Setelah Stage 15, sistem mampu menghadapi pola seperti:

```text
Hadis #1571
        │
        ▼
Exact Match
```

tetapi juga:

```text
"قال المصنف..."
        │
        ▼
Contextual Reference
        │
        ▼
Hadith Candidate
```

atau:

```text
جزء من المتن
        │
        ▼
Partial Matn
        │
        ▼
Full Hadith
```

atau:

```text
عن أبي هريرة...
        │
        ▼
Sanad Pattern
        │
        ▼
Multiple Candidates
        │
        ▼
Reranking
```

---

# 15.2 Masalah yang harus diselesaikan

Fathul Bari dapat merujuk hadis dengan berbagai cara:

### A. Nomor hadis

```text
الحديث رقم 1571
```

### B. Potongan matan

```text
قوله: إنما الأعمال بالنيات
```

### C. Perawi

```text
عن أبي هريرة
```

### D. Lafaz awal

```text
حديث أبي هريرة
```

### E. Rujukan sebelumnya

```text
وقد تقدم
```

### F. Rujukan kitab/bab

```text
كما سيأتي في كتاب...
```

### G. Kutipan sebagian

```text
وفي رواية...
```

### H. Variasi redaksi

```text
قال رسول الله ﷺ...
```

dengan redaksi yang berbeda tetapi merujuk hadis yang sama.

---

# 15.3 Arsitektur NLP

```text
                  ARABIC TEXT
                       │
                       ▼
              ┌─────────────────┐
              │ Arabic NLP      │
              └────────┬────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   Tokenization     Entities       References
        │              │              │
        ▼              ▼              ▼
    Lemmatization   Narrators      Hadith IDs
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                Candidate Engine
                       │
                       ▼
                 Hybrid Matcher
                       │
                       ▼
                   Reranker
                       │
                       ▼
                 Confidence
```

---

# 15.4 Arabic Normalization v2

Stage 13 sudah memiliki normalisasi dasar.

Sekarang kita tambahkan:

```text
RAW
 ↓
Unicode normalization
 ↓
Diacritic handling
 ↓
Alef normalization
 ↓
Ya/Alef Maqsurah normalization
 ↓
Ta Marbuta handling
 ↓
Tatweel removal
 ↓
Punctuation normalization
 ↓
Whitespace normalization
 ↓
SEARCH FORM
```

Tetapi:

> **Raw text tidak pernah diubah.**

---

# 15.5 Tiga bentuk teks

Database menyimpan:

```text
raw_text
normalized_text
search_text
```

Contoh:

```text
RAW:
إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ

NORMALIZED:
إنما الأعمال بالنيات

SEARCH:
انما الاعمال بالنيات
```

---

# 15.6 Tokenization

Arab perlu dipisahkan menjadi token.

```text
قال رسول الله ﷺ
```

menjadi:

```text
قال
رسول
الله
ﷺ
```

Kemudian kita bisa menghapus token tertentu dari pencarian tanpa menghilangkannya dari sumber.

---

# 15.7 Stopword Layer

Jangan menghapus stopword secara permanen.

Buat:

```text
raw_tokens
search_tokens
```

Contoh:

```text
في
من
عن
إلى
على
```

dapat diberi bobot rendah dalam retrieval.

Namun tetap dipertahankan dalam source text.

---

# 15.8 Morphological Normalization

Kata:

```text
الأعمال
للأعمال
وأعمال
بالأعمال
```

memiliki hubungan morfologis.

Search engine perlu mampu mengenali kedekatan tersebut.

Konsep:

```text
Surface Form
      ↓
Morphological Features
      ↓
Lemma / Root-aware Representation
```

Namun **jangan menggunakan akar kata sebagai satu-satunya matching mechanism**.

Misalnya kata dengan akar sama belum tentu memiliki makna atau referensi hadis yang sama.

---

# 15.9 Lemma Representation

Simpan:

```json
{
  "surface": "بالنيات",
  "normalized": "بالنيات",
  "lemma": "نية"
}
```

Sehingga:

```text
بالنيات
للنيات
نية
```

dapat menjadi kandidat lexical similarity.

---

# 15.10 Entity Extraction

Kita membutuhkan entity berikut:

```text
PERSON
NARRATOR
PROPHET
COMPANION
SCHOLAR
BOOK
CHAPTER
HADITH
LOCATION
REFERENCE
```

Contoh:

```text
عن أبي هريرة رضي الله عنه قال
```

menjadi:

```text
PERSON:
أبو هريرة

TYPE:
COMPANION
```

---

# 15.11 Narrator Knowledge Base

Buat tabel:

```text
narrators
```

Contoh:

```text
id
canonical_name
arabic_name
aliases
kunya
nisbah
generation
notes
```

Contoh:

```json
{
  "canonical_name": "Abu Hurairah",
  "arabic_name": "أبو هريرة",
  "aliases": [
    "أبي هريرة",
    "أبو هريرة رضي الله عنه"
  ]
}
```

---

# 15.12 Kenapa alias penting?

Fathul Bari mungkin menggunakan:

```text
أبو هريرة
```

sementara dataset hadis menggunakan:

```text
أبي هريرة
```

atau:

```text
عن هريرة
```

Sistem harus memahami bahwa ketiganya dapat merujuk kepada entitas yang sama.

---

# 15.13 Sanad Extraction

Kita membuat:

```text
Sanad Parser
```

Contoh:

```text
حدثنا عبد الله بن يوسف
قال أخبرنا مالك
عن ابن شهاب
عن محمد بن جبير
عن أبيه
```

menjadi graph:

```text
عبد الله بن يوسف
        ↓
مالك
        ↓
ابن شهاب
        ↓
محمد بن جبير
        ↓
جبير بن مطعم
```

---

# 15.14 Sanad Graph

Database:

```text
narrator_a
    │
    └── TRANSMITS_TO
            ↓
        narrator_b
```

Contoh:

```text
Malik
  ↓
Ibn Shihab
  ↓
Muhammad ibn Jubair
```

Ini dapat menjadi signal tambahan dalam matching.

---

# 15.15 Sanad Similarity

Misalnya:

```text
Candidate A
Malik → Ibn Shihab → Abu Salamah

Candidate B
Malik → Ibn Shihab → Muhammad ibn Jubair
```

Jika Fathul Bari memiliki:

```text
Malik → Ibn Shihab → Muhammad ibn Jubair
```

Candidate B mendapatkan skor sanad lebih tinggi.

---

# 15.16 Matn Extraction

Pisahkan:

```text
SANAD
```

dan:

```text
MATN
```

Contoh:

```text
حدثنا مالك عن نافع عن ابن عمر قال:
نهى رسول الله ﷺ عن بيع...
```

menjadi:

```text
SANAD:
مالك → نافع → ابن عمر

MATN:
نهى رسول الله ﷺ عن بيع...
```

---

# 15.17 Masalah "قال"

Kata:

```text
قال
```

tidak selalu berarti awal matan.

Bisa berarti:

```text
قال ابن حجر
```

atau:

```text
قال رسول الله ﷺ
```

atau:

```text
قال الراوي
```

Karena itu parser harus menggunakan konteks.

---

# 15.18 Hadith Boundary Detection

Pipeline:

```text
Text
 ↓
Potential sanad
 ↓
Potential matn
 ↓
Boundary classifier
 ↓
Hadith object
```

Output:

```json
{
  "sanad_start": 120,
  "sanad_end": 165,
  "matn_start": 166,
  "matn_end": 310
}
```

---

# 15.19 Partial Matn Matching

Ini salah satu fitur paling penting.

Misalnya Fathul Bari hanya mengutip:

```text
إنما الأعمال بالنيات
```

sedangkan database memiliki hadis panjang:

```text
إنما الأعمال بالنيات وإنما لكل امرئ ما نوى...
```

Exact matching gagal.

Tetapi:

```text
substring similarity
+
semantic similarity
+
sequence alignment
```

akan menemukan hubungan tersebut.

---

# 15.20 Matn Fingerprint

Buat fingerprint:

```text
Hadith
 ↓
Normalize
 ↓
Remove low-value tokens
 ↓
N-grams
 ↓
Fingerprint
```

Contoh:

```text
إنما الأعمال بالنيات
```

menghasilkan beberapa n-gram.

Kemudian dapat dicari dengan cepat.

---

# 15.21 Lexical Similarity

Gunakan beberapa signal:

```text
BM25
Jaccard
Cosine TF-IDF
N-gram overlap
Edit distance
```

Tidak perlu satu algoritma saja.

---

# 15.22 Semantic Similarity

Gunakan embedding:

```text
Fathul Bari reference
       ↓
Embedding
       ↓
Vector search
       ↓
Hadith candidates
```

Tetapi semantic similarity **tidak boleh menjadi satu-satunya bukti**.

---

# 15.23 Hybrid Scoring v2

Sekarang score menjadi:

```text
Final Score
=
Reference
+
Matn
+
Semantic
+
Narrator
+
Sanad
+
Chapter
+
Context
```

Contoh struktur:

```json
{
  "reference": 1.00,
  "matn": 0.94,
  "semantic": 0.91,
  "narrator": 0.98,
  "sanad": 0.96,
  "chapter": 0.87,
  "context": 0.92
}
```

Bobot final sebaiknya dipelajari dari **golden corpus**, bukan ditetapkan permanen sejak awal.

---

# 15.24 Context Window

Jangan hanya melihat satu kalimat.

Jika kandidat ditemukan pada:

```text
Page 120
```

ambil context:

```text
Page 119
+
Page 120
+
Page 121
```

atau:

```text
previous section
+
current paragraph
+
next paragraph
```

Kemudian lakukan contextual matching.

---

# 15.25 Chapter-aware Matching

Misalnya hadis berada dalam:

```text
كتاب الصلاة
```

maka kandidat dari hadis-hadis dalam konteks yang sama diberi prioritas.

Namun jangan membuat:

```text
chapter = hard filter
```

karena Fathul Bari sering melakukan cross-reference.

Jadikan chapter sebagai **ranking signal**.

---

# 15.26 Cross-reference Resolution

Kita perlu resolver untuk:

```text
تقدم
سيأتي
كما سبق
مر
تقدم قريبا
سيأتي في كتاب...
```

Contoh:

```text
كما سيأتي في كتاب البيوع
```

sistem mencari:

```text
current position
       ↓
future section
       ↓
Kitab al-Buyu'
```

---

# 15.27 Relative Reference Engine

Buat entity:

```text
references
```

dengan:

```text
reference_type
source_section
target_section
target_hadith
resolution_confidence
status
```

Contoh:

```json
{
  "type": "FUTURE_REFERENCE",
  "text": "كما سيأتي في كتاب البيوع",
  "target_book": "كتاب البيوع",
  "status": "CANDIDATE"
}
```

---

# 15.28 "وفي رواية"

Ini sangat penting.

Jika teks:

```text
وفي رواية لمسلم...
```

maka sistem jangan membuat hadis baru secara otomatis.

Model data:

```text
Hadith A
   │
   ├── VARIANT_OF ──► Hadith B
   │
   └── REPORTED_IN ──► Muslim
```

---

# 15.29 Hadith Variant Graph

```text
                    HADITH
                       │
           ┌───────────┼───────────┐
           ▼           ▼           ▼
       Bukhari       Muslim      Tirmidhi
           │           │
           ▼           ▼
       Variant A    Variant B
           │
           └──── SAME_EVENT ────┐
                                ▼
                         Hadith Concept
```

Perlu hati-hati membedakan:

```text
same wording
same narration
same event
same legal topic
```

Keempatnya bukan hal yang sama.

---

# 15.30 Hadith Identity

Buat tiga level:

```text
Hadith Record
Narration Variant
Hadith Concept
```

Contoh:

```text
Concept
│
├── Bukhari narration
│
├── Muslim narration
│
└── Other narration
```

Ini akan sangat membantu Knowledge Graph.

---

# 15.31 Advanced Matching Pipeline

```text
                    FATHUL BARI
                         │
                         ▼
                 Arabic NLP
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
    Matn              Sanad           References
       │                 │                 │
       ▼                 ▼                 ▼
   Fingerprint       Narrator KG      Ref Resolver
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                 Candidate Retrieval
                         │
                         ▼
                  Hybrid Scoring
                         │
                         ▼
                     Reranker
                         │
                         ▼
                   Confidence
                         │
                         ▼
                  HUMAN REVIEW
```

---

# 15.32 Reranker

Setelah top 20 candidate:

```text
Top 20
  ↓
Cross-encoder / reranker
  ↓
Top 5
```

Input:

```text
Fathul Bari passage
+
Candidate hadith
+
Metadata
```

Output:

```text
relevance score
```

Reranker membantu membedakan kandidat yang secara embedding sama-sama dekat.

---

# 15.33 Candidate Explanation

Sistem harus menjelaskan kepada reviewer:

```text
WHY THIS MATCH?
```

Contoh:

```text
MATCH EXPLANATION

✓ Hadith number matches
✓ Narrator matches
✓ 87% matn overlap
✓ Sanad structure compatible
✓ Chapter context compatible
✓ Semantic similarity: 0.93

Potential issue:
⚠ Fathul Bari quotes abbreviated matn
```

Ini jauh lebih berguna daripada:

```text
Confidence: 94%
```

---

# 15.34 Explainable Confidence

Database:

```json
{
  "final_score": 0.94,
  "evidence": {
    "reference": 1.0,
    "matn_overlap": 0.87,
    "narrator": 1.0,
    "sanad": 0.91,
    "semantic": 0.93,
    "chapter": 0.89
  }
}
```

---

# 15.35 Hard Rules

Beberapa kondisi dapat menjadi **negative signal kuat**.

Contoh:

```text
Explicit hadith number mismatch
```

Jika nomor hadis eksplisit berbeda, jangan menaikkan confidence hanya karena semantic similarity tinggi.

Demikian pula:

```text
different narrator chain
```

tidak selalu berarti hadis berbeda, tetapi harus memicu pemeriksaan.

---

# 15.36 Confidence Calibration

Setelah mendapatkan Golden Corpus:

```text
Predicted score
       │
       ▼
Actual reviewer decision
       │
       ▼
Calibration
```

Kita dapat mengevaluasi:

```text
Precision
Recall
F1
Precision@K
Recall@K
MRR
NDCG
```

---

# 15.37 Target Evaluation

Misalnya:

```text
Task:
Retrieve correct hadith in Top-5
```

metric:

```text
Recall@5
```

Kemudian:

```text
Rank correct hadith
```

metric:

```text
MRR
```

Untuk sistem reviewer:

```text
Precision@1
Precision@5
```

lebih relevan daripada sekadar accuracy.

---

# 15.38 Golden Dataset

Buat:

```text
evaluation/
├── gold_hadith_matches.jsonl
├── gold_references.jsonl
├── gold_narrators.jsonl
└── gold_variants.jsonl
```

Contoh:

```json
{
  "source": "fathul_bari_v1_p45",
  "expected_hadith": "bukhari_1",
  "expected": true
}
```

---

# 15.39 Regression Test

Setiap kali matcher berubah:

```text
git commit
    ↓
Run Golden Corpus
    ↓
Compare metrics
```

Contoh:

```text
Before:
Recall@5 = 91.2%

After:
Recall@5 = 93.7%

PASS
```

Tetapi:

```text
Before:
Precision@1 = 96%

After:
Precision@1 = 89%

FAIL
```

Pipeline tidak boleh langsung dipromosikan.

---

# 15.40 Dataset untuk Machine Learning

Jika nanti jumlah review sudah cukup banyak:

```text
Reviewer decisions
       ↓
Training data
       ↓
Match classifier
```

Contoh:

```text
positive:
verified match

negative:
rejected match
```

Model dapat belajar dari:

```text
matn overlap
narrator overlap
sanad similarity
chapter similarity
reference pattern
embedding similarity
```

---

# 15.41 Active Learning

Ini akan menghemat pekerjaan reviewer.

```text
Model
 ↓
Uncertain candidates
 ↓
Human reviewer
 ↓
New labels
 ↓
Model improvement
```

Prioritaskan kandidat yang:

```text
confidence ≈ 0.50
```

karena paling informatif untuk model.

---

# 15.42 Reviewer Feedback Loop

```text
                MATCHER
                   │
                   ▼
             CANDIDATE
                   │
                   ▼
                REVIEW
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
     VERIFY                 REJECT
        │                     │
        └──────────┬──────────┘
                   ▼
              TRAIN DATA
                   │
                   ▼
              NEW MODEL
                   │
                   ▼
                MATCHER
```

---

# 15.43 Knowledge Graph Enhancement

Setelah Stage 15 graph kita menjadi:

```text
Hadith Concept
      │
      ├── HAS_VARIANT
      │
      ├── TRANSMITTED_BY
      │
      ├── EXPLAINED_BY
      │
      ├── REFERENCED_BY
      │
      ├── LOCATED_IN
      │
      └── REPORTED_IN
```

Sedangkan:

```text
Sharh Section
      │
      ├── EXPLAINS
      ├── REFERENCES
      ├── COMPARES
      └── RESPONDS_TO
```

---

# 15.44 Contoh Knowledge Graph

```text
                   Bukhari #1
                       │
                 EXPLAINED_BY
                       │
                       ▼
                Fathul Bari §1
                  /     |      \
                 /      |       \
                ▼       ▼        ▼
          References  Explains  Located
              │                    │
              ▼                    ▼
        Muslim Variant         Vol 1 p.45
```

Ini mulai menjadi **research graph**, bukan sekadar database hadis.

---

# 15.45 RAG menjadi lebih cerdas

Sebelumnya:

```text
Question
 ↓
Vector Search
 ↓
Answer
```

Sekarang:

```text
Question
 ↓
Intent Detection
 ↓
Hadith Entity Detection
 ↓
Knowledge Graph
 ↓
Hybrid Retrieval
 ↓
Reranker
 ↓
Evidence Assembly
 ↓
LLM
 ↓
Citation Validation
 ↓
Answer
```

---

# 15.46 Contoh pertanyaan

User:

> "Apa penjelasan Ibnu Hajar tentang makna niat dalam hadis إنما الأعمال بالنيات?"

Pipeline:

```text
Question
   ↓
Detect hadith phrase
   ↓
Bukhari #1
   ↓
Graph
   ↓
Fathul Bari sections
   ↓
Retrieve relevant chunks
   ↓
Source pages
   ↓
Answer
```

Jawaban AI kemudian wajib menunjuk:

```text
Fathul Bari
Volume
Page
Section
Hadith
```

---

# 15.47 Citation Guard

Sebelum jawaban dikirim:

```text
AI Answer
   ↓
Citation Validator
   ↓
Every factual claim
   ↓
Evidence?
 ┌──┴──┐
Yes    No
│       │
Pass   Rewrite / flag
```

Tujuannya mengurangi hallucination.

---

# 15.48 "Tidak ditemukan"

Sistem harus memiliki jawaban resmi:

```text
EVIDENCE_NOT_FOUND
```

Jika evidence tidak cukup:

> "Saya belum menemukan bagian Fathul Bari yang cukup kuat untuk mendukung kesimpulan tersebut."

Ini lebih baik daripada AI mengarang.

---

# 15.49 API baru

### NLP analyze

```http
POST /api/v1/nlp/analyze
```

### Detect hadith

```http
POST /api/v1/nlp/hadith-detect
```

### Find candidates

```http
POST /api/v1/matching/hadith
```

### Explain match

```http
GET /api/v1/matching/{id}/explanation
```

### Cross-reference

```http
GET /api/v1/references/{id}
```

### Evaluation

```http
GET /api/v1/evaluation/matcher
```

---

# 15.50 Database tambahan

Stage 15 menambahkan:

```text
narrators
narrator_aliases
sanad_chains
sanad_links

hadith_variants
hadith_concepts

text_entities
hadith_mentions
cross_references

match_features
match_scores
match_explanations

evaluation_datasets
evaluation_results
```

---

# 15.51 Folder Structure

```text
backend/
└── app/
    ├── nlp/
    │   ├── arabic_normalizer.py
    │   ├── tokenizer.py
    │   ├── lemmatizer.py
    │   ├── ner.py
    │   ├── narrator_extractor.py
    │   ├── sanad_parser.py
    │   ├── matn_extractor.py
    │   └── reference_resolver.py
    │
    ├── matching/
    │   ├── lexical.py
    │   ├── semantic.py
    │   ├── narrator.py
    │   ├── sanad.py
    │   ├── context.py
    │   ├── reranker.py
    │   ├── scorer.py
    │   └── explanation.py
    │
    └── evaluation/
        ├── dataset.py
        ├── metrics.py
        ├── evaluator.py
        └── regression.py
```

---

# 15.52 Definition of Done

```text
[ ] Arabic normalization v2
[ ] Arabic tokenizer
[ ] Lemma representation
[ ] Narrator entity extraction
[ ] Narrator alias database
[ ] Sanad extraction
[ ] Sanad graph
[ ] Matn extraction
[ ] Partial matn matching
[ ] Matn fingerprint
[ ] Lexical matching
[ ] Semantic matching
[ ] Context-aware matching
[ ] Chapter-aware ranking
[ ] Cross-reference resolver
[ ] Hadith variant model
[ ] Hadith concept model
[ ] Hybrid scoring v2
[ ] Candidate reranker
[ ] Explainable confidence
[ ] Reviewer feedback capture
[ ] Golden corpus
[ ] Recall@K
[ ] MRR
[ ] NDCG
[ ] Regression testing
[ ] Active-learning foundation
```

---

# Posisi arsitektur sekarang

```text
STAGE 01  Foundation                    ✓
STAGE 02  Ahmad Sanusi API              ✓
STAGE 03  Data Model                    ✓
STAGE 04  Matching Engine               ✓
STAGE 05  Review Dashboard              ✓
STAGE 06  Source + Audit                ✓
STAGE 07  RAG Assistant                 ✓
STAGE 08  Hybrid Search                 ✓
STAGE 09  Knowledge Graph               ✓
STAGE 10  Research Workspace            ✓
STAGE 11  Analytics + Quality Control   ✓
STAGE 12  Production Hardening          ✓
STAGE 13  Corpus Ingestion              ✓
STAGE 14  Corpus Processing              ✓
STAGE 15  Arabic NLP + Advanced Match   ← KITA
```
