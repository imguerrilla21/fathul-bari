# Stage 42 — Scholarly Citation & Attribution Engine

Stage 42 membangun lapisan **atribusi ilmiah** di atas Multimodal Source Intelligence.

Tujuan utamanya:

> **Setiap klaim yang dihasilkan aplikasi harus dapat diketahui: siapa yang mengatakannya, dari kitab mana, pada halaman mana, apakah merupakan kutipan langsung, kutipan dari pihak ketiga, parafrasa, atau inferensi AI.**

Ini sangat penting untuk aplikasi *Syarah Fathul Bari*. Kesalahan paling berbahaya bukan hanya hallucination, tetapi **false attribution**—misalnya pendapat al-Khattabi dianggap sebagai pendapat Ibn Hajar hanya karena Ibn Hajar sedang mengutipnya.

---

# 42.1 Masalah Utama yang Diselesaikan

Misalnya dalam *Fath al-Bari* terdapat struktur:

```text
قال الخطابي:
...

وقال النووي:
...

قال ابن حجر:
...
```

AI harus mengetahui:

```text
al-Khattabi → AUTHOR_OF → Opinion A

al-Nawawi → AUTHOR_OF → Opinion B

Ibn Hajar → COMMENTARY_ON → Opinion A/B
```

Bukan:

```text
Ibn Hajar → AUTHOR_OF → semua teks
```

---

# 42.2 Arsitektur Stage 42

```text
                 SOURCE CORPUS
                      │
                      ▼
              TEXT / OCR / PAGE
                      │
                      ▼
             ATTRIBUTION PARSER
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
     Speaker       Quotation       Citation
     Detection      Detection       Detection
        │             │             │
        └─────────────┼─────────────┘
                      ▼
              CLAIM EXTRACTION
                      │
                      ▼
             CITATION RESOLVER
                      │
                      ▼
              SCHOLAR GRAPH
                      │
                      ▼
             EVIDENCE VALIDATOR
                      │
                      ▼
                  RAG AI
                      │
                      ▼
             ATTRIBUTED ANSWER
```

---

# 42.3 Empat Lapisan Atribusi

Sistem harus membedakan:

```text
1. SOURCE
2. SPEAKER
3. CLAIM
4. INTERPRETATION
```

Contoh:

```text
Source:
Fath al-Bari Vol. 1 p. 184

Speaker:
Ibn Hajar

Claim:
Niat berkaitan dengan tujuan amal.

Interpretation:
AI menyimpulkan hubungan tersebut dengan konsep X.
```

---

# 42.4 Attribution Types

Gunakan enum:

```text
DIRECT_QUOTE
INDIRECT_QUOTE
PARAPHRASE
ATTRIBUTED_OPINION
COMMENTARY
INFERENCE
SUMMARY
EDITORIAL_NOTE
UNKNOWN
```

---

# 42.5 Direct Quote

Contoh struktur:

```text
قال ابن حجر: ...
```

Representasi:

```json
{
  "speaker": "Ibn Hajar",
  "type": "DIRECT_QUOTE"
}
```

---

# 42.6 Indirect Quote

Contoh:

```text
ذكر النووي أن...
```

Sistem mengenali:

```text
speaker = al-Nawawi
type = INDIRECT_QUOTE
```

---

# 42.7 Reported Opinion

Contoh:

```text
ذهب الشافعي إلى...
```

Maknanya:

```text
speaker = al-Shafi'i
claim_author = al-Shafi'i
reporter = Ibn Hajar
```

Ini berbeda dari:

```text
Ibn Hajar believes...
```

---

# 42.8 Nested Attribution

Kasus yang lebih sulit:

```text
قال ابن حجر:
ذكر الخطابي عن بعض العلماء أن...
```

Graph:

```text
Ibn Hajar
   │
   └── REPORTS
          │
          ▼
      al-Khattabi
          │
          └── REPORTS
                 │
                 ▼
             Some scholars
```

Jangan flatten menjadi:

```text
Ibn Hajar said X.
```

---

# 42.9 Attribution Graph

Graph utama:

```text
PERSON
BOOK
PASSAGE
CLAIM
HADITH
VERSE
OPINION
```

Relationship:

```text
PERSON ──AUTHORED──> BOOK

PERSON ──SAID──> CLAIM

PERSON ──QUOTED──> PERSON

PASSAGE ──CONTAINS──> CLAIM

CLAIM ──SUPPORTED_BY──> PASSAGE

PASSAGE ──LOCATED_ON──> PAGE

CLAIM ──REFERS_TO──> HADITH
```

---

# 42.10 New Knowledge Graph Relations

Tambahkan:

```text
REPORTS
QUOTES
ATTRIBUTES
EXPLAINS
CRITIQUES
AGREES_WITH
DISAGREES_WITH
SUMMARIZES
TRANSMITS
REFERS_TO
```

---

# 42.11 Citation Entity

Buat objek:

```json
{
  "citation_id": "C-001",
  "source_type": "BOOK",
  "author": "Ibn Hajar",
  "title": "Fath al-Bari",
  "volume": 1,
  "page": 184,
  "passage_id": "P88421"
}
```

---

# 42.12 Citation Granularity

Citation tidak selalu berhenti pada halaman.

Level:

```text
DOCUMENT
VOLUME
CHAPTER
PAGE
REGION
BLOCK
PASSAGE
SENTENCE
TOKEN
```

Untuk AI answer, idealnya:

```text
PASSAGE
+
PAGE
+
REGION
```

---

# 42.13 Citation Precision

Contoh buruk:

> Ibn Hajar mengatakan X.
> *(Fath al-Bari, Vol. 1)*

Lebih baik:

> Ibn Hajar menjelaskan X.
> *(Fath al-Bari, Vol. 1, hlm. 184, region R184-07)*

---

# 42.14 Citation Resolver

Jika AI menyebut:

```text
Fath al-Bari, 1/184
```

resolver mencari:

```text
edition
volume
page
passage
region
```

dan menghasilkan canonical citation.

---

# 42.15 Canonical Citation ID

Format internal:

```text
CIT:
FB-ED-001
V1
P184
R184-07
P88421
```

Contoh:

```text
FB-ED-001:1:184:R184-07:P88421
```

---

# 42.16 Citation Deduplication

Satu passage dapat disebut berkali-kali.

Jangan membuat:

```text
C001
C002
C003
```

untuk source yang sama.

Gunakan:

```text
canonical_source_id
```

---

# 42.17 Citation Chain

Contoh:

```text
AI Claim
   ↓
Passage P88421
   ↓
Fath al-Bari
   ↓
Ibn Hajar
   ↓
Hadith Bukhari #1
```

UI dapat menampilkan:

```text
Claim
  └─ Ibn Hajar
      └─ Fath al-Bari
          └─ Bukhari #1
```

---

# 42.18 Secondary Citation

Jika Ibn Hajar mengutip al-Nawawi:

```text
AI Claim
 ↓
Ibn Hajar's passage
 ↓
quoted source
 ↓
al-Nawawi
```

Citation harus dapat menunjukkan:

```text
Primary citation:
Fath al-Bari

Quoted authority:
al-Nawawi
```

---

# 42.19 Direct vs Secondary Evidence

Buat:

```text
PRIMARY_EVIDENCE
SECONDARY_EVIDENCE
TERTIARY_EVIDENCE
```

Contoh:

```text
Fath al-Bari passage
= PRIMARY evidence for what Ibn Hajar wrote

Al-Nawawi text quoted by Ibn Hajar
= SECONDARY evidence for al-Nawawi's view
```

---

# 42.20 Important Rule

Jika pengguna bertanya:

> Apa pendapat al-Nawawi?

dan aplikasi hanya menemukan kutipan Ibn Hajar terhadap al-Nawawi:

Jawaban harus:

> "Dalam *Fath al-Bari*, Ibn Hajar mengutip pendapat yang dinisbatkan kepada al-Nawawi..."

bukan:

> "Al-Nawawi mengatakan..."

kecuali sumber langsung al-Nawawi tersedia atau atribusinya cukup kuat.

---

# 42.21 Attribution Confidence

Gunakan:

```text
VERIFIED
HIGH
MEDIUM
LOW
UNCERTAIN
```

Contoh:

```json
{
  "speaker": "al-Nawawi",
  "confidence": "HIGH",
  "evidence": "explicit attribution"
}
```

---

# 42.22 Attribution Evidence

Setiap atribusi harus menyimpan alasan:

```json
{
  "attribution": "al-Nawawi",
  "evidence": {
    "trigger": "قال النووي",
    "passage_id": "P88421",
    "confidence": 0.98
  }
}
```

---

# 42.23 Attribution Trigger Dictionary

Buat kamus:

```text
قال
ذكر
روى
حكى
نقل
أشار
صرح
ذهب
اختار
رجح
قال النووي
قال الخطابي
قال ابن حجر
```

Tetapi trigger saja **tidak cukup**.

---

# 42.24 Arabic Attribution Parsing

Contoh:

```text
وقال النووي: ...
```

parser:

```json
{
  "reporter": "Ibn Hajar",
  "speaker": "al-Nawawi",
  "relation": "QUOTES"
}
```

Jika konteksnya memang Ibn Hajar yang sedang berbicara.

---

# 42.25 Speaker Resolution

Nama dapat memiliki variasi:

```text
النووي
الإمام النووي
أبو زكريا
يحيى بن شرف
```

Semua diarahkan ke:

```text
PERSON-ID: N0001
```

---

# 42.26 Authority Entity

Buat tabel:

```sql
CREATE TABLE scholars (
    id UUID PRIMARY KEY,

    canonical_name TEXT NOT NULL,

    arabic_name TEXT,

    kunyah TEXT,

    nisbah TEXT,

    birth_year INTEGER,

    death_year INTEGER,

    metadata JSONB
);
```

---

# 42.27 Scholar Aliases

```sql
CREATE TABLE scholar_aliases (
    id UUID PRIMARY KEY,

    scholar_id UUID NOT NULL,

    alias TEXT NOT NULL,

    language VARCHAR(10),

    alias_type VARCHAR(40)
);
```

Contoh:

```text
النووي
الإمام النووي
يحيى بن شرف
```

→ satu entity.

---

# 42.28 Book Entities

```sql
CREATE TABLE scholarly_works (
    id UUID PRIMARY KEY,

    title TEXT NOT NULL,

    arabic_title TEXT,

    author_id UUID,

    work_type VARCHAR(50),

    metadata JSONB
);
```

---

# 42.29 Citation Table

```sql
CREATE TABLE scholarly_citations (
    id UUID PRIMARY KEY,

    source_passage_id UUID,

    cited_person_id UUID,

    cited_work_id UUID,

    citation_type VARCHAR(50),

    confidence NUMERIC,

    evidence JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 42.30 Claims

Sekarang kita membutuhkan **claim layer**.

```sql
CREATE TABLE scholarly_claims (
    id UUID PRIMARY KEY,

    passage_id UUID,

    claim_text TEXT NOT NULL,

    claim_type VARCHAR(50),

    speaker_id UUID,

    confidence NUMERIC,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 42.31 Claim Types

```text
HADITH_CLAIM
FIQH_CLAIM
LINGUISTIC_CLAIM
THEOLOGICAL_CLAIM
HISTORICAL_CLAIM
BIOGRAPHICAL_CLAIM
INTERPRETIVE_CLAIM
EDITORIAL_CLAIM
```

---

# 42.32 Claim Provenance

```text
Claim C001
│
├── speaker: Ibn Hajar
│
├── source: Fath al-Bari
│
├── page: 184
│
├── region: R184-07
│
└── attribution:
      verified
```

---

# 42.33 Claim-to-Source

Relationship:

```text
CLAIM
  │
  └──SUPPORTED_BY
          │
          ▼
       PASSAGE
```

Jika tidak ada:

```text
CLAIM
  │
  └── UNSUPPORTED
```

---

# 42.34 AI Claim Extraction

Setelah LLM menghasilkan jawaban:

```text
Answer
 ↓
Claim Extraction
 ↓
Claim #1
Claim #2
Claim #3
```

Contoh:

```json
{
  "claims": [
    "Ibn Hajar menjelaskan...",
    "Beliau mengaitkan...",
    "Hal ini menunjukkan..."
  ]
}
```

---

# 42.35 Claim Classification

Setiap claim:

```text
DIRECT_SOURCE
INFERENCE
GENERAL_KNOWLEDGE
UNCERTAIN
```

---

# 42.36 Critical Rule

Jika:

```text
claim_type = INFERENCE
```

AI harus menggunakan bahasa:

```text
"Ini dapat dipahami sebagai..."
```

bukan:

```text
"Ibn Hajar mengatakan..."
```

---

# 42.37 Attribution Validator

Pipeline:

```text
AI Answer
 ↓
Claim Extraction
 ↓
Speaker Detection
 ↓
Citation Matching
 ↓
Source Verification
 ↓
Attribution Validation
```

Jika gagal:

```text
REGENERATE
```

atau:

```text
REVIEW_REQUIRED
```

---

# 42.38 False Attribution Detector

Kasus:

```text
AI:
"Ibn Hajar berkata X."

Source:
"وقال النووي: X"
```

Detector:

```text
EXPECTED:
al-Nawawi

FOUND:
Ibn Hajar

→ FALSE_ATTRIBUTION
```

---

# 42.39 Attribution Severity

```text
LOW
MEDIUM
HIGH
CRITICAL
```

False attribution of scholar:

```text
HIGH
```

False attribution of Prophet ﷺ:

```text
CRITICAL
```

---

# 42.40 Hadith Attribution Protection

Untuk hadis, tambahkan rule khusus:

```text
Prophetic statement
Companion statement
Tabi'i statement
Scholar commentary
```

Harus dipisahkan.

---

# 42.41 Example

Source:

```text
قال ابن عباس:
...
```

AI tidak boleh menghasilkan:

> Rasulullah ﷺ bersabda...

karena:

```text
speaker = Ibn Abbas
```

---

# 42.42 Hadith Chain Awareness

Jika tersedia sanad:

```text
حدثنا X عن Y عن Z قال رسول الله ﷺ...
```

sistem dapat menyimpan:

```text
Narrator
  ↓
Narrator
  ↓
Narrator
  ↓
Prophet ﷺ
```

Ini akan menjadi dasar fitur takhrij berikutnya.

---

# 42.43 Citation Graph UI

Tambahkan visualisasi:

```text
                    ابن حجر
                       │
                 COMMENTARY
                       │
                       ▼
                  FATH AL-BARI
                       │
                ┌──────┴──────┐
                ▼             ▼
             النووي        الخطابي
                │             │
              QUOTE         QUOTE
                │             │
                └──────┬──────┘
                       ▼
                     HADITH
```

---

# 42.44 Citation Explorer

Ketika user klik:

```text
al-Nawawi
```

tampilkan:

```text
Mentioned by Ibn Hajar: 127
Direct sources: 83
Indirect citations: 44
Verified: 109
Uncertain: 18
```

Angka hanya contoh.

---

# 42.45 Scholar Profile

```text
الإمام النووي

Canonical:
Yahya ibn Sharaf al-Nawawi

Known works:
Sharh Sahih Muslim
Al-Majmu'
Riyad al-Salihin

Mentioned in:
Fath al-Bari
```

---

# 42.46 Citation Timeline

Untuk penelitian historis:

```text
al-Bukhari
   ↓
al-Khattabi
   ↓
al-Nawawi
   ↓
Ibn Hajar
   ↓
Modern scholar
```

Ini bukan berarti semua hubungan tersebut adalah transmisi langsung. UI harus membedakan:

```text
AUTHORED
QUOTED
REFERRED_TO
COMMENTED_ON
```

---

# 42.47 Citation Types

Enum:

```text
AUTHORED
QUOTED
PARAPHRASED
REFERRED
CRITIQUED
SUPPORTED
REJECTED
COMPARED
ATTRIBUTED
```

---

# 42.48 Agreement / Disagreement

Jika source:

```text
قال النووي...
وقال ابن حجر: وفيه نظر...
```

graph:

```text
Ibn Hajar
   │
   └──CRITIQUES──> al-Nawawi
```

AI dapat menjawab:

> Ibn Hajar tidak sekadar mengutip al-Nawawi, tetapi memberikan kritik terhadap pendapat tersebut.

---

# 42.49 Opinion Graph

Buat entity:

```text
OPINION
```

Contoh:

```text
Opinion O001
│
├── held_by → al-Nawawi
├── reported_by → Ibn Hajar
├── source → Fath al-Bari
└── topic → Niyyah
```

---

# 42.50 Opinion Conflict

Jika:

```text
al-Nawawi → Opinion A

Ibn Hajar → rejects Opinion A

al-Khattabi → Opinion B
```

graph menunjukkan:

```text
A
├── HELD_BY → al-Nawawi
└── REJECTED_BY → Ibn Hajar

B
└── HELD_BY → al-Khattabi
```

---

# 42.51 Citation-Aware RAG

Stage 40:

```text
Question
 ↓
Evidence
 ↓
LLM
```

Stage 42:

```text
Question
 ↓
Evidence
 ↓
Attribution Graph
 ↓
LLM
 ↓
Claim Extraction
 ↓
Citation Validator
 ↓
Attributed Answer
```

---

# 42.52 Context Enhancement

LLM context:

```text
SOURCE:
Fath al-Bari Vol 1 p184

SPEAKER:
Ibn Hajar

QUOTED SCHOLAR:
al-Nawawi

CLAIM:
...

RELATION:
Ibn Hajar quotes al-Nawawi

SOURCE IMAGE:
...
```

Dengan demikian model tidak harus menebak siapa yang berbicara.

---

# 42.53 Structured Prompt

```text
Anda adalah asisten penelitian syarah hadis.

Untuk setiap klaim:
1. Identifikasi pembicara.
2. Bedakan ucapan penulis dari kutipan penulis lain.
3. Jangan mengatribusikan kutipan kepada penulis utama.
4. Jangan mengubah inferensi menjadi kutipan.
5. Sertakan citation ID.
6. Jika atribusi tidak pasti, nyatakan ketidakpastian.
```

---

# 42.54 Answer Format

Output internal:

```json
{
  "answer": "...",
  "claims": [
    {
      "text": "...",
      "speaker": "Ibn Hajar",
      "type": "DIRECT_SOURCE",
      "citation_ids": ["C001"]
    },
    {
      "text": "...",
      "speaker": "al-Nawawi",
      "type": "REPORTED_SOURCE",
      "reported_by": "Ibn Hajar",
      "citation_ids": ["C002"]
    }
  ]
}
```

---

# 42.55 User-Facing Answer

Contoh:

> **Ibn Hajar** menjelaskan bahwa ...
>
> Dalam pembahasan tersebut, beliau juga **mengutip al-Nawawi**, yang berpendapat bahwa ...
>
> Jadi, pendapat kedua merupakan pendapat **al-Nawawi yang dinukil oleh Ibn Hajar**, bukan pendapat Ibn Hajar sendiri.

Inilah perilaku yang kita inginkan.

---

# 42.56 Citation UI

```text
Ibn Hajar menjelaskan bahwa niat berkaitan
dengan tujuan amal. [①]

Beliau juga menukil pendapat al-Nawawi... [②]
```

Klik:

```text
① Fath al-Bari 1/184
   Ibn Hajar
   [View Source]

② Fath al-Bari 1/185
   Ibn Hajar quoting al-Nawawi
   [View Source]
```

---

# 42.57 Citation Tooltip

Hover citation:

```text
┌─────────────────────────────┐
│ SOURCE                      │
│ Fath al-Bari                │
│ Vol. 1, p.185               │
│                             │
│ Speaker: Ibn Hajar          │
│ Quoted: al-Nawawi           │
│ Type: INDIRECT_QUOTE        │
│ Confidence: HIGH            │
│                             │
│ [Open source]               │
└─────────────────────────────┘
```

---

# 42.58 Database Audit

Tambahkan:

```sql
CREATE TABLE attribution_audits (
    id UUID PRIMARY KEY,

    claim_id UUID,

    detected_speaker UUID,

    expected_speaker UUID,

    status VARCHAR(30),

    confidence NUMERIC,

    evidence JSONB,

    reviewed_by UUID,

    reviewed_at TIMESTAMPTZ
);
```

---

# 42.59 Attribution Evaluation Dataset

Buat golden dataset:

```json
{
  "passage_id": "P88421",
  "expected": {
    "speaker": "Ibn Hajar",
    "quoted_person": "al-Nawawi",
    "relation": "QUOTES"
  }
}
```

---

# 42.60 Metrics

Gunakan:

```text
Speaker Accuracy
Attribution Precision
Attribution Recall
Citation Precision
Citation Recall
False Attribution Rate
```

Yang paling penting:

```text
False Attribution Rate
```

Target production:

> **serendah mungkin, dan kasus berisiko tinggi harus masuk review.**

---

# 42.61 Attribution Regression Test

Setiap perubahan:

```text
OCR
LLM
prompt
parser
knowledge graph
```

jalankan:

```text
Golden Attribution Dataset
```

---

# 42.62 Critical Regression

Jika sebelumnya:

```text
Ibn Hajar → al-Nawawi → QUOTES
```

setelah update menjadi:

```text
Ibn Hajar → AUTHOR_OF
```

build harus gagal.

---

# 42.63 API

Tambahkan:

```http
POST /api/v1/attribution/analyze

GET /api/v1/attribution/claims/{id}

GET /api/v1/attribution/scholar/{id}

GET /api/v1/attribution/graph/{claim_id}

POST /api/v1/attribution/verify

GET /api/v1/citations/{id}
```

---

# 42.64 Analyze API

Request:

```json
{
  "passage_id": "P88421"
}
```

Response:

```json
{
  "speaker": {
    "id": "SCH-001",
    "name": "Ibn Hajar",
    "confidence": 0.98
  },
  "citations": [
    {
      "scholar_id": "SCH-002",
      "relation": "QUOTES",
      "confidence": 0.94
    }
  ]
}
```

---

# 42.65 Citation Graph API

```http
GET /api/v1/attribution/graph/P88421
```

Response:

```json
{
  "nodes": [
    {
      "id": "SCH-001",
      "type": "PERSON",
      "name": "Ibn Hajar"
    },
    {
      "id": "SCH-002",
      "type": "PERSON",
      "name": "al-Nawawi"
    }
  ],
  "edges": [
    {
      "from": "SCH-001",
      "to": "SCH-002",
      "type": "QUOTES"
    }
  ]
}
```

---

# 42.66 Attribution Review Dashboard

```text
┌────────────────────────────────────────────────┐
│ ATTRIBUTION REVIEW                             │
├────────────────────────────────────────────────┤
│ Passage: P88421                                │
│                                                │
│ Speaker: Ibn Hajar       Confidence: 98%       │
│                                                │
│ Quotes:                                        │
│   al-Nawawi             Confidence: 94%        │
│                                                │
│ Relation: QUOTES                               │
│                                                │
│ Source: Fath al-Bari 1/184                     │
│                                                │
│ [VERIFY] [EDIT] [REJECT]                      │
└────────────────────────────────────────────────┘
```

---

# 42.67 Scholar Identity Resolution

Masalah:

```text
ابن حجر
```

bisa ambigu.

Resolver harus mempertimbangkan:

```text
context
era
work
known aliases
author of current book
```

Untuk *Fath al-Bari*, konteks membantu mengidentifikasi:

```text
ابن حجر
→ Ahmad ibn Ali ibn Hajar al-Asqalani
```

Tetapi confidence tetap disimpan.

---

# 42.68 Disambiguation

Jika:

```text
ابن حجر
```

memiliki beberapa kandidat:

```text
Candidate A 0.91
Candidate B 0.06
Candidate C 0.03
```

dan threshold belum tercapai:

```text
AMBIGUOUS
```

Jangan memaksa entity resolution.

---

# 42.69 Scholarly Entity Resolution Pipeline

```text
Mention
 ↓
Normalization
 ↓
Alias Search
 ↓
Context Search
 ↓
Book/Date Constraint
 ↓
Candidate Ranking
 ↓
Confidence
 ↓
Verified Entity
```

---

# 42.70 Citation Conflict

Jika dua edisi menunjukkan:

```text
Edition A: p.184
Edition B: p.191
```

simpan keduanya:

```text
same passage
different pagination
```

Citation canonical:

```text
passage_id
```

lebih stabil daripada nomor halaman saja.

---

# 42.71 Edition-Aware Citation

```json
{
  "passage_id": "P88421",

  "citations": [
    {
      "edition": "FB-ED-001",
      "volume": 1,
      "page": 184
    },
    {
      "edition": "FB-ED-002",
      "volume": 1,
      "page": 191
    }
  ]
}
```

---

# 42.72 Citation Normalization

User dapat meminta:

```text
"Format citation Chicago"
```

atau:

```text
"Format Arab"
```

atau:

```text
"Format sederhana"
```

Internal source tetap sama.

Presentation layer yang berubah.

---

# 42.73 Citation Styles

Minimal:

```text
SHORT
ACADEMIC
ARABIC
FOOTNOTE
BIBLIOGRAPHY
```

Contoh:

```text
Ibn Hajar al-'Asqalani,
Fath al-Bari, 1:184.
```

---

# 42.74 Citation Export

Tahap ini dapat menghasilkan:

```text
BibTeX
RIS
CSL-JSON
Markdown
Plain Text
```

Untuk peneliti yang ingin memasukkan sumber ke reference manager.

---

# 42.75 Research Notebook Integration

Workspace dapat memiliki:

```text
Claim
 ↓
Citation
 ↓
Note
 ↓
Source
```

Contoh:

```text
NOTE-102

"Perbedaan antara niat dan tujuan..."

Sources:
C001
C002
C005
```

---

# 42.76 Citation-aware Notes

Saat user membuat catatan:

```text
Saya menyimpulkan bahwa...
```

sistem harus membedakan:

```text
USER_NOTE
```

dari:

```text
SOURCE_CLAIM
```

---

# 42.77 User Interpretation

Jika user menulis:

> "Menurut saya, Ibn Hajar cenderung..."

Simpan sebagai:

```text
USER_INTERPRETATION
```

bukan sebagai:

```text
IBN_HAJAR_CLAIM
```

---

# 42.78 Knowledge Graph Expansion

Setelah Stage 42:

```text
Hadith
 │
 ├── appears in → Fath al-Bari
 │
 ├── explained by → Ibn Hajar
 │
 ├── quotes → al-Nawawi
 │
 ├── quotes → al-Khattabi
 │
 ├── references → Quran
 │
 └── discusses → Fiqh Topic
```

Ini mulai membentuk **Scholarly Knowledge Graph** yang sesungguhnya.

---

# 42.79 Full RAG Architecture

Sekarang pipeline aplikasi:

```text
                 USER QUESTION
                       │
                       ▼
                 QUERY ANALYZER
                       │
                       ▼
               HYBRID RETRIEVAL
                  [Stage 40]
                       │
                       ▼
             MULTIMODAL EVIDENCE
                  [Stage 41]
                       │
                       ▼
             ATTRIBUTION GRAPH
                  [Stage 42]
                       │
                       ▼
              CONTEXT ASSEMBLER
                       │
                       ▼
                     LLM
                       │
                       ▼
                CLAIM EXTRACTOR
                       │
                       ▼
             CITATION VALIDATOR
                       │
                       ▼
           ATTRIBUTION VALIDATOR
                       │
                 ┌─────┴─────┐
                 ▼           ▼
              PASS       REVIEW
                 │
                 ▼
          FINAL ANSWER
```

---

# 42.80 Definition of Done

Stage 42 dianggap selesai jika:

```text
[ ] Scholar Entity Model
[ ] Scholar Alias System
[ ] Work Entity Model
[ ] Citation Entity
[ ] Citation Resolver
[ ] Claim Extraction
[ ] Speaker Detection
[ ] Attribution Parsing
[ ] Nested Attribution
[ ] Direct Quote Detection
[ ] Indirect Quote Detection
[ ] Paraphrase Detection
[ ] Opinion Model
[ ] Citation Graph
[ ] Scholar Graph
[ ] Attribution Confidence
[ ] Attribution Evidence
[ ] False Attribution Detection
[ ] Hadith Speaker Protection
[ ] Primary/Secondary Evidence
[ ] Citation Validation
[ ] Claim Validation
[ ] Edition-Aware Citation
[ ] Citation Deduplication
[ ] Citation Styles
[ ] Citation Export
[ ] Attribution Review UI
[ ] Citation Explorer
[ ] Scholar Explorer
[ ] Golden Attribution Dataset
[ ] Attribution Regression Tests
[ ] Attribution Metrics
[ ] Attribution API
```

---

# 42.81 Prinsip Ilmiah yang Harus Dikunci

Untuk aplikasi Anda, saya sarankan menetapkan **7 aturan permanen**:

### Rule 1 — Jangan menganggap semua teks di *Fathul Bari* adalah ucapan Ibn Hajar.

```text
Author ≠ every quoted statement
```

### Rule 2 — Kutipan harus memiliki provenance.

```text
Quote → Passage → Page → Scan
```

### Rule 3 — Pendapat yang dinukil harus ditandai sebagai dinukil.

```text
Ibn Hajar quotes al-Nawawi
```

bukan:

```text
Ibn Hajar says what al-Nawawi said
```

### Rule 4 — Inferensi AI harus diberi label.

```text
SOURCE
vs
INFERENCE
```

### Rule 5 — Nomor halaman bukan identitas sumber utama.

Gunakan:

```text
passage_id
```

sebagai identifier internal.

### Rule 6 — AI tidak boleh memperbaiki sumber secara diam-diam.

```text
OCR correction ≠ source alteration
```

### Rule 7 — Semua jawaban ilmiah harus dapat ditelusuri.

```text
ANSWER
 ↓
CLAIM
 ↓
CITATION
 ↓
PASSAGE
 ↓
REGION
 ↓
PAGE
 ↓
ORIGINAL SCAN
```

---

# 42.82 Posisi Aplikasi Setelah Stage 42

Aplikasi Anda sekarang telah memiliki empat lapisan inti:

```text
┌─────────────────────────────────────────────┐
│              RESEARCH AI                    │
├─────────────────────────────────────────────┤
│ Citation & Attribution Engine  ← Stage 42  │
├─────────────────────────────────────────────┤
│ Multimodal Source Intelligence ← Stage 41  │
├─────────────────────────────────────────────┤
│ Hybrid RAG & Evidence          ← Stage 40  │
├─────────────────────────────────────────────┤
│ Corpus / Edition Management    ← Stage 39  │
├─────────────────────────────────────────────┤
│ Knowledge Graph                ← Stage 9+   │
├─────────────────────────────────────────────┤
│ Hadith ↔ Fathul Bari Alignment             │
├─────────────────────────────────────────────┤
│ Ahmad Sanusi Hadits API                    │
└─────────────────────────────────────────────┘
```

Dengan demikian, aplikasi sudah bergerak dari **"chatbot hadis"** menjadi **platform penelitian syarah hadis berbasis sumber**.
