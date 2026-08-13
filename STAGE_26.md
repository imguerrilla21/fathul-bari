# Stage 26 — Islamic Text Intelligence & Arabic NLP Engine

Stage 26 membangun **lapisan kecerdasan teks Arab** untuk aplikasi Syarah *Fathul Bari*. Tujuannya adalah membuat sistem tidak hanya mencari berdasarkan embedding, tetapi memahami **lafaz, lemma, akar kata, morfologi, nama perawi, kitab, bab, istilah hadis, dan hubungan antar-teks**.

> Prinsip utama: **Arabic NLP menjadi lapisan pendukung RAG, bukan pengganti teks sumber.** Semua hasil analisis NLP harus dapat ditelusuri kembali ke teks asli.

---

# 26.1 Posisi Stage 26

```text
                    USER QUERY
                         │
                         ▼
              ┌─────────────────────┐
              │ Arabic NLP Engine   │
              ├─────────────────────┤
              │ Normalization       │
              │ Tokenization        │
              │ Lemmatization       │
              │ Root Analysis       │
              │ Entity Recognition  │
              │ Morphology          │
              └──────────┬──────────┘
                         │
             ┌───────────┼────────────┐
             ▼           ▼            ▼
         Keyword      Semantic     Knowledge
          Search       Search        Graph
             │           │            │
             └───────────┼────────────┘
                         ▼
                        RAG
                         │
                         ▼
                     Evidence
                         │
                         ▼
                  Citation Engine
```

---

# 26.2 Sasaran Utama

Stage ini harus menghasilkan kemampuan:

```text
[✓] Arabic Unicode normalization
[✓] Diacritics handling
[✓] Tokenization
[✓] Lemma mapping
[✓] Root mapping
[✓] Morphological metadata
[✓] Arabic named entity recognition
[✓] Narrator detection
[✓] Book detection
[✓] Hadith terminology detection
[✓] Phrase matching
[✓] Exact Arabic search
[✓] Root search
[✓] Lemma search
[✓] Semantic search
[✓] Hybrid search
[✓] Arabic-aware highlighting
[✓] NLP provenance
```

---

# 26.3 Mengapa Tidak Cukup Embedding?

Misalnya user mencari:

```text
النية
```

Embedding mungkin menemukan:

```text
الأعمال بالنيات
```

Tetapi NLP dapat mengetahui bahwa:

```text
النية
النيات
نيته
نوى
ينوي
```

berhubungan secara linguistik.

Kita ingin:

```text
Query
  ↓
النية
  ↓
Lemma: نية
  ↓
Root: نوي
  ↓
Morphological variants
  ↓
Exact + lexical + semantic retrieval
```

---

# 26.4 Arabic Text Pipeline

```text
Raw Arabic
    │
    ▼
Unicode Normalizer
    │
    ▼
Diacritics Processor
    │
    ▼
Character Normalizer
    │
    ▼
Sentence Splitter
    │
    ▼
Tokenizer
    │
    ▼
Morphological Analyzer
    │
    ├── Lemma
    ├── Root
    ├── POS
    ├── Features
    └── Pattern
    │
    ▼
Entity Recognizer
    │
    ├── Person
    ├── Book
    ├── Place
    ├── Hadith
    └── Scholar
    │
    ▼
Index
```

---

# 26.5 Arabic Normalization

Buat modul:

```text
app/nlp/arabic/normalizer.py
```

Contoh:

```python
import re
import unicodedata


TATWEEL = "\u0640"


def normalize_arabic(text: str) -> str:
    text = unicodedata.normalize("NFC", text)

    # Remove tatweel
    text = text.replace(TATWEEL, "")

    # Normalize alef variants
    text = re.sub(r"[إأٱآ]", "ا", text)

    # Normalize ya / alef maqsura
    text = text.replace("ى", "ي")

    # Normalize ta marbuta only when appropriate:
    # DO NOT globally convert ة to ه.
    
    return text
```

**Penting:** jangan melakukan normalisasi agresif yang mengubah makna.

---

# 26.6 Diacritics

Pisahkan:

```text
النِّيَّةُ
```

menjadi:

```text
النِّيَّةُ
```

dan normalized search form:

```text
النية
```

Simpan keduanya.

```json
{
  "original": "النِّيَّةُ",
  "normalized": "النية"
}
```

Jangan menghapus harakat dari sumber asli.

---

# 26.7 Diacritics Function

```python
import re

ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)


def remove_diacritics(text: str) -> str:
    return ARABIC_DIACRITICS.sub("", text)
```

---

# 26.8 Tokenization

Contoh:

```text
إنما الأعمال بالنيات وإنما لكل امرئ ما نوى
```

menjadi:

```json
[
  "إنما",
  "الأعمال",
  "بالنيات",
  "وإنما",
  "لكل",
  "امرئ",
  "ما",
  "نوى"
]
```

Tetapi untuk Arabic NLP kita membutuhkan **tokenization yang lebih kaya**.

---

# 26.9 Clitic-Aware Tokenization

Kata:

```text
وبالنيات
```

secara linguistik dapat dipandang sebagai:

```text
و + ب + ال + نيات
```

Simpan dua representasi:

```text
surface:
وبالنيات

segmented:
و | ب | ال | نيات
```

Ini akan sangat membantu pencarian.

---

# 26.10 Token Model

```sql
CREATE TABLE arabic_tokens (
    id UUID PRIMARY KEY,

    document_id UUID NOT NULL,

    page_id UUID,

    chunk_id UUID,

    token_index INTEGER NOT NULL,

    surface TEXT NOT NULL,

    normalized TEXT NOT NULL,

    lemma TEXT,

    root TEXT,

    pos VARCHAR(40),

    morphology JSONB DEFAULT '{}',

    start_char INTEGER,

    end_char INTEGER
);
```

---

# 26.11 Token Provenance

Setiap token harus tahu asalnya:

```text
source
 ↓
page
 ↓
chunk
 ↓
token
```

Contoh:

```json
{
  "source_id": "fb_001",
  "page_id": "page_45",
  "chunk_id": "chunk_003",
  "token_index": 17,
  "surface": "بالنيات"
}
```

---

# 26.12 Lemmatization

Contoh:

```text
النية
النيات
نيته
نيتهم
نية
```

dapat dipetakan ke lemma:

```text
نية
```

Tetapi jangan membuat lemma hanya dengan string replacement.

Gunakan **morphological analyzer** yang dapat dikonfigurasi.

---

# 26.13 Root

Contoh konseptual:

```text
نية
نوى
ينوي
```

berkaitan dengan root:

```text
ن و ي
```

Database:

```sql
CREATE TABLE arabic_lexemes (
    id UUID PRIMARY KEY,

    lemma TEXT NOT NULL,

    root TEXT,

    language VARCHAR(10) DEFAULT 'ar',

    metadata JSONB DEFAULT '{}',

    UNIQUE(lemma, root)
);
```

---

# 26.14 Jangan Terlalu Mengandalkan Root

Ini penting.

Root extraction dalam bahasa Arab tidak selalu cukup untuk menentukan makna.

Contoh:

```text
علم
```

dapat memiliki berbagai konteks:

```text
عِلْم
عَلَم
عَلِمَ
```

Karena itu ranking retrieval:

```text
exact phrase
    >
lemma
    >
morphological relation
    >
root
    >
semantic similarity
```

bukan:

```text
root = everything
```

---

# 26.15 Morphological Features

Simpan:

```json
{
  "pos": "NOUN",
  "gender": "FEM",
  "number": "SINGULAR",
  "case": "NOMINATIVE",
  "definiteness": "DEFINITE"
}
```

Untuk verba:

```json
{
  "pos": "VERB",
  "aspect": "PERFECT",
  "person": "3",
  "gender": "MASC",
  "number": "SINGULAR"
}
```

Tidak semua analyzer menghasilkan fitur yang sama. Karena itu gunakan:

```text
morphology JSONB
```

---

# 26.16 NLP Provider Abstraction

Jangan mengunci aplikasi pada satu library.

Buat:

```python
class ArabicNLPProvider:

    def normalize(self, text):
        ...

    def tokenize(self, text):
        ...

    def analyze(self, token):
        ...

    def lemmatize(self, token):
        ...

    def root(self, token):
        ...
```

Kemudian:

```text
ArabicNLPProvider
├── LocalArabicAnalyzer
├── ExternalArabicAnalyzer
└── HybridArabicAnalyzer
```

---

# 26.17 Mengapa Abstraction Ini Penting?

Model/library NLP dapat berubah.

Arsitektur kita tetap:

```text
Application
      ↓
ArabicNLPProvider
      ↓
Implementation
```

bukan:

```text
Application
      ↓
hard-coded NLP library
```

---

# 26.18 Entity Recognition

Stage 26 memperkenalkan entity types:

```text
PERSON
SCHOLAR
NARRATOR
BOOK
HADITH_COLLECTION
CHAPTER
PLACE
TRIBE
EVENT
TERM
SCHOOL
```

Contoh:

```text
قال ابن حجر في فتح الباري
```

deteksi:

```text
PERSON:
ابن حجر

BOOK:
فتح الباري
```

---

# 26.19 Entity Model

```sql
CREATE TABLE text_entities (
    id UUID PRIMARY KEY,

    entity_type VARCHAR(40) NOT NULL,

    canonical_name TEXT NOT NULL,

    arabic_name TEXT,

    normalized_name TEXT,

    metadata JSONB DEFAULT '{}'
);
```

Mention:

```sql
CREATE TABLE entity_mentions (
    id UUID PRIMARY KEY,

    entity_id UUID NOT NULL
        REFERENCES text_entities(id),

    chunk_id UUID NOT NULL,

    surface TEXT NOT NULL,

    start_char INTEGER,

    end_char INTEGER,

    confidence NUMERIC(6,5)
);
```

---

# 26.20 Person Authority

Untuk ulama:

```json
{
  "entity_type": "SCHOLAR",
  "canonical_name": "Ibn Hajar al-Asqalani",
  "arabic_name": "ابن حجر العسقلاني",
  "aliases": [
    "ابن حجر",
    "الحافظ ابن حجر",
    "أحمد بن علي بن حجر"
  ]
}
```

Hubungkan dengan `authors` dari Stage 24.

Jangan membuat dua entitas berbeda hanya karena variasi nama.

---

# 26.21 Narrator Detection

Kita perlu mengenali:

```text
حدثنا
حدثني
أخبرنا
عن
قال
سمعت
```

tetapi **jangan menyimpulkan bahwa setiap nama setelah `عن` pasti narrator chain yang valid**.

NLP hanya memberi:

```text
candidate narrator
```

Kemudian hadith parser dan database sanad melakukan verifikasi.

---

# 26.22 Sanad Parser

Pipeline:

```text
Hadith Text
    ↓
Narrator Trigger Detection
    ↓
Name Candidate Detection
    ↓
Entity Linking
    ↓
Chain Construction
    ↓
Hadith Knowledge Graph
```

Output:

```json
{
  "narrators": [
    {
      "surface": "مالك",
      "entity_id": "person_001"
    },
    {
      "surface": "نافع",
      "entity_id": "person_002"
    },
    {
      "surface": "ابن عمر",
      "entity_id": "person_003"
    }
  ]
}
```

---

# 26.23 Hadith Terminology

Buat lexicon khusus:

```text
صحيح
حسن
ضعيف
موضوع
مرفوع
موقوف
مقطوع
مرسل
منقطع
معضل
معلق
متواتر
غريب
عزيز
مشهور
```

Tetapi istilah yang ditemukan dalam teks harus disimpan sebagai:

```text
TERM_MENTION
```

bukan otomatis menjadi status hukum hadis.

---

# 26.24 Context-Sensitive Classification

Misalnya:

```text
هذا حديث صحيح
```

berbeda dengan:

```text
وقيل إنه حديث صحيح
```

dan:

```text
ليس بصحيح
```

Maka:

```text
term detection ≠ hadith grading
```

Grading memerlukan layer khusus.

---

# 26.25 Book Detection

Lexicon:

```text
صحيح البخاري
صحيح مسلم
فتح الباري
شرح النووي
السنن الكبرى
سنن أبي داود
```

Entity linking:

```text
"فتح الباري"
      ↓
bibliographic_source_id
```

Dengan demikian NLP terhubung langsung ke Citation Engine.

---

# 26.26 Phrase Index

Buat index khusus untuk frasa Arab.

```sql
CREATE TABLE arabic_phrases (
    id UUID PRIMARY KEY,

    chunk_id UUID NOT NULL,

    phrase TEXT NOT NULL,

    normalized_phrase TEXT NOT NULL,

    token_start INTEGER,

    token_end INTEGER
);
```

---

# 26.27 Exact Search

Query:

```text
إنما الأعمال بالنيات
```

harus memberikan:

```text
EXACT MATCH
```

dengan ranking tertinggi.

---

# 26.28 Fuzzy Search

Jika user mengetik:

```text
انما الاعمال بالنيات
```

tanpa harakat:

```text
إنما الأعمال بالنيات
```

tetap ditemukan.

---

# 26.29 Arabic Search Normalization Pipeline

```text
User Query
   ↓
Unicode Normalize
   ↓
Remove Optional Diacritics
   ↓
Alef Normalize
   ↓
Ya Normalize
   ↓
Tokenize
   ↓
Lemma/Root Expansion
   ↓
Search
```

---

# 26.30 Hybrid Retrieval

Ini peningkatan penting untuk RAG.

Gunakan:

```text
Final Score =
Exact Score
+
Lexical Score
+
Lemma Score
+
Root Score
+
Semantic Score
+
Entity Score
+
Source Priority
```

Contoh bobot awal:

```text
Exact phrase       0.30
Lexical/BM25       0.20
Lemma              0.15
Semantic           0.20
Entity             0.10
Source priority    0.05
```

Bobot ini **harus dikalibrasi dengan dataset evaluasi**, bukan dianggap final.

---

# 26.31 Retrieval Pipeline

```text
QUERY
 │
 ├── Exact Search
 │
 ├── BM25
 │
 ├── Lemma Search
 │
 ├── Root Search
 │
 ├── Entity Search
 │
 └── Embedding Search
       │
       ▼
    Candidate Pool
       │
       ▼
     Reranker
       │
       ▼
    Evidence
```

---

# 26.32 Query Expansion

User:

```text
"niat dalam ibadah"
```

sistem dapat menghasilkan:

```text
النية
النيات
نوى
نية
عمل
عبادة
قصد
```

Tetapi expansion harus diberi label:

```text
ORIGINAL_QUERY
EXPANDED_QUERY
```

agar audit dapat mengetahui bagaimana hasil diperoleh.

---

# 26.33 Query Expansion Audit

```json
{
  "original": "niat dalam ibadah",

  "expanded": [
    "النية",
    "النيات",
    "قصد"
  ],

  "method": "LEXICAL_EXPANSION"
}
```

---

# 26.34 Arabic Highlighting

Source Viewer:

```text
إنما الأعمال بالنيات وإنما لكل امرئ ما نوى
^^^^^
```

Highlight berdasarkan:

```text
exact
lemma
root
semantic
```

Gunakan warna UI berbeda jika diperlukan:

```text
EXACT
LEMMA
ROOT
SEMANTIC
```

Tetapi jangan bergantung hanya pada warna; tambahkan label/accessibility.

---

# 26.35 Root Search UI

User klik:

```text
نوى
```

menu:

```text
┌────────────────────────────┐
│ Root: ن و ي                │
├────────────────────────────┤
│ Lemmas                     │
│ نية                        │
│ نوى                        │
│ ينوي                       │
│                            │
│ Occurrences: 1,247         │
│                            │
│ [Search All]               │
└────────────────────────────┘
```

---

# 26.36 Lemma Explorer

Route:

```text
/nlp/lemma/{lemma}
```

Contoh:

```text
النية

Root:
ن و ي

Occurrences:
1,247

Books:
Fathul Bari
Sahih Bukhari
...
```

---

# 26.37 Term Concordance

Fitur penting untuk penelitian.

User mencari:

```text
النية
```

sistem menampilkan:

```text
CONCORDANCE

1. إنما الأعمال بالنيات...
2. وإنما لكل امرئ ما نوى...
3. النية محلها القلب...
4. ...
```

Dengan konteks:

```text
± 30 tokens
```

---

# 26.38 Concordance Database

Tidak perlu menyimpan semua context sebagai copy baru.

Gunakan:

```text
chunk_id
token_start
token_end
```

kemudian render dari source.

Ini menjaga provenance.

---

# 26.39 Semantic Concordance

Selain exact:

```text
النية
```

dapat mencari konsep terkait.

Namun hasil semantic harus diberi label:

```text
SEMANTICALLY_RELATED
```

bukan:

```text
SAME_TERM
```

---

# 26.40 Arabic NLP + Knowledge Graph

Graph:

```text
TERM
 │
 ├── lemma
 ├── root
 ├── occurrence
 │
 ▼
CHUNK
 │
 ├── HADITH
 ├── SHARH
 ├── SCHOLAR
 └── BOOK
```

Contoh:

```text
النية
 ↓
نية
 ↓
ن و ي
 ↓
Fathul Bari
 ↓
Ibn Hajar
 ↓
Hadith #1
```

---

# 26.41 Entity Linking

Jika NLP menemukan:

```text
البخاري
```

resolver mencari:

```text
محمد بن إسماعيل البخاري
```

dan menghubungkannya dengan:

```text
author_id
```

Jika ambigu:

```text
MATCH_STATUS = AMBIGUOUS
```

Jangan auto-link secara membabi buta.

---

# 26.42 Entity Confidence

```text
0.98
```

boleh menjadi:

```text
AUTO_LINK_CANDIDATE
```

tetapi:

```text
0.63
```

masuk:

```text
REVIEW_QUEUE
```

Threshold sebaiknya configurable.

---

# 26.43 NLP Review Dashboard

```text
┌─────────────────────────────────────────────┐
│ NLP REVIEW                                  │
├─────────────────────────────────────────────┤
│ Entity candidates                           │
│                                             │
│ ابن حجر                                     │
│ → Ibn Hajar al-Asqalani       98%           │
│ [Accept] [Reject] [Change]                  │
│                                             │
│ البخاري                                     │
│ → Muhammad ibn Ismail          99%           │
│ [Accept]                                    │
└─────────────────────────────────────────────┘
```

---

# 26.44 NLP Job Queue

NLP jangan dijalankan synchronous untuk seluruh kitab.

Gunakan:

```text
INGEST
 ↓
OCR
 ↓
NORMALIZE
 ↓
TOKENIZE
 ↓
MORPHOLOGY
 ↓
ENTITY EXTRACTION
 ↓
INDEX
 ↓
EMBEDDING
```

Setiap tahap menjadi job.

---

# 26.45 Job Model

```sql
CREATE TABLE nlp_jobs (
    id UUID PRIMARY KEY,

    source_id UUID,

    job_type VARCHAR(40) NOT NULL,

    status VARCHAR(30) NOT NULL,

    progress NUMERIC(6,3) DEFAULT 0,

    error_message TEXT,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ
);
```

Status:

```text
QUEUED
RUNNING
COMPLETED
FAILED
CANCELLED
```

---

# 26.46 Pipeline Idempotency

Jika job:

```text
TOKENIZE page 45
```

dijalankan dua kali, hasil tidak boleh menggandakan token.

Gunakan:

```text
source_version
pipeline_version
content_hash
```

sebagai identity.

```text
(source_version, page_id, pipeline_version, content_hash)
```

---

# 26.47 NLP Versioning

Simpan:

```json
{
  "normalizer_version": "1.2",
  "tokenizer_version": "1.1",
  "morphology_version": "2.0",
  "ner_version": "1.0"
}
```

Karena hasil NLP dapat berubah ketika model diperbarui.

---

# 26.48 Reproducibility

Jika hasil retrieval tahun 2026 dipertanyakan:

```text
Source hash
+
NLP version
+
Embedding version
+
Reranker version
+
Query
```

dapat direkonstruksi.

Ini sangat penting untuk platform riset.

---

# 26.49 API

### Analyze Arabic

```http
POST /api/v1/nlp/arabic/analyze
```

Request:

```json
{
  "text": "إنما الأعمال بالنيات"
}
```

Response:

```json
{
  "tokens": [
    {
      "surface": "إنما",
      "normalized": "إنما",
      "lemma": "إنما"
    },
    {
      "surface": "الأعمال",
      "normalized": "الاعمال",
      "lemma": "عمل",
      "root": "ع م ل"
    },
    {
      "surface": "بالنيات",
      "normalized": "بالنيات",
      "lemma": "نية",
      "root": "ن و ي"
    }
  ]
}
```

---

# 26.50 Search API

```http
GET /api/v1/search/arabic
```

Parameter:

```text
?q=النية
&mode=hybrid
&source=fathul_bari
```

Response:

```json
{
  "query": "النية",
  "results": [
    {
      "chunk_id": "FB-V1-P45-C003",
      "match_type": "LEMMA",
      "score": 0.94
    }
  ]
}
```

---

# 26.51 Concordance API

```http
GET /api/v1/nlp/concordance
```

```text
?lemma=نية
```

Response:

```json
{
  "lemma": "نية",
  "root": "ن و ي",
  "occurrences": 1247
}
```

---

# 26.52 Entity API

```http
GET /api/v1/entities/search
```

```text
?q=ابن حجر
&type=SCHOLAR
```

---

# 26.53 RAG Integration

RAG query sekarang:

```text
User:
Apa penjelasan Ibn Hajar tentang niat?
```

Pipeline:

```text
                QUERY
                  │
                  ▼
             Arabic NLP
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
     lemma       root      entity
       │          │          │
       └──────────┼──────────┘
                  ▼
           Hybrid Retrieval
                  │
                  ▼
               Reranker
                  │
                  ▼
               Evidence
                  │
                  ▼
               LLM Answer
                  │
                  ▼
              Citation
```

---

# 26.54 Source Priority

Untuk pertanyaan:

> Apa kata Ibnu Hajar?

ranking source:

```text
1. Fathul Bari
2. sumber yang secara eksplisit mengutip Fathul Bari
3. kitab syarah terkait
4. kitab hadis
5. sumber sekunder
```

Jangan mencampur sumber sekunder sebagai seolah-olah teks asli Fathul Bari.

---

# 26.55 Evidence Type

Tambahkan:

```text
PRIMARY_TEXT
SECONDARY_SOURCE
DERIVED_ANALYSIS
SEMANTIC_MATCH
LEXICAL_MATCH
```

RAG harus mengetahui perbedaannya.

---

# 26.56 Answer Provenance

Jawaban AI:

```text
Menurut Ibn Hajar, ...
```

harus mempunyai:

```json
{
  "claim": "...",
  "evidence": [
    {
      "chunk_id": "FB-V1-P45-C003",
      "match": "LEXICAL + SEMANTIC"
    }
  ],
  "citation_id": "cit_001"
}
```

---

# 26.57 Evaluation Dataset

Sebelum menganggap NLP "akurat", buat dataset evaluasi.

Minimal:

```text
1,000 Arabic sentences
500 named entities
500 lemma mappings
500 root mappings
500 search queries
```

Untuk domain kitab hadis, lebih baik dibuat:

```text
Hadith corpus
Fathul Bari corpus
Arabic scholarly corpus
```

---

# 26.58 Retrieval Evaluation

Ukur:

```text
Recall@5
Recall@10
MRR
nDCG
Precision@k
```

Contoh:

```text
Hybrid Search
Recall@10 = 0.91

Embedding only
Recall@10 = 0.78
```

Angka di atas hanya contoh; jangan dimasukkan sebagai benchmark aktual sebelum pengujian.

---

# 26.59 Human Evaluation

Buat 100 pertanyaan:

```text
Q1: Apa makna النية?
Q2: Bagaimana Ibn Hajar menjelaskan...
...
```

Reviewer menilai:

```text
0 = salah
1 = sebagian benar
2 = benar
```

---

# 26.60 Definition of Done

Stage 26 selesai apabila:

```text
[ ] Arabic normalizer
[ ] Diacritics processor
[ ] Arabic tokenizer
[ ] Clitic-aware tokenization
[ ] Lemmatization layer
[ ] Root layer
[ ] Morphological metadata
[ ] Arabic entity extraction
[ ] Scholar entity linking
[ ] Narrator candidates
[ ] Hadith terminology lexicon
[ ] Book detection
[ ] Exact Arabic search
[ ] Fuzzy search
[ ] Lemma search
[ ] Root search
[ ] Hybrid retrieval
[ ] Arabic highlighting
[ ] Concordance
[ ] NLP job queue
[ ] NLP versioning
[ ] Provenance
[ ] RAG integration
[ ] Evaluation dataset
[ ] Retrieval benchmarks
```

---

# 26.61 Struktur Folder

Tambahkan:

```text
backend/
└── app/
    ├── nlp/
    │   ├── arabic/
    │   │   ├── normalizer.py
    │   │   ├── diacritics.py
    │   │   ├── tokenizer.py
    │   │   ├── morphology.py
    │   │   ├── lemmatizer.py
    │   │   ├── roots.py
    │   │   ├── entities.py
    │   │   └── provider.py
    │   │
    │   ├── hadith/
    │   │   ├── sanad_parser.py
    │   │   ├── terminology.py
    │   │   └── book_detector.py
    │   │
    │   ├── indexing/
    │   │   ├── token_index.py
    │   │   ├── lemma_index.py
    │   │   ├── phrase_index.py
    │   │   └── entity_index.py
    │   │
    │   └── jobs/
    │       ├── pipeline.py
    │       └── tasks.py
    │
    ├── retrieval/
    │   ├── lexical.py
    │   ├── semantic.py
    │   ├── hybrid.py
    │   └── reranker.py
    │
    └── api/
        └── nlp.py
```

---

# 26.62 Arsitektur Final Setelah Stage 26

Sekarang platform sudah memiliki tujuh lapisan utama:

```text
┌──────────────────────────────────────────────────────┐
│                 PUBLICATION                          │
├──────────────────────────────────────────────────────┤
│ Research Document · Review · Citation · Export       │
├──────────────────────────────────────────────────────┤
│                    RAG                               │
├──────────────────────────────────────────────────────┤
│ Hybrid Retrieval · Reranking · Evidence              │
├──────────────────────────────────────────────────────┤
│              ARABIC NLP                              │
├──────────────────────────────────────────────────────┤
│ Token · Lemma · Root · Entity · Morphology           │
├──────────────────────────────────────────────────────┤
│             KNOWLEDGE GRAPH                          │
├──────────────────────────────────────────────────────┤
│ Hadith · Narrator · Scholar · Book · Concept         │
├──────────────────────────────────────────────────────┤
│               SOURCE LAYER                           │
├──────────────────────────────────────────────────────┤
│ Ahmad Sanusi API · Fathul Bari · Other Sources       │
└──────────────────────────────────────────────────────┘
```
