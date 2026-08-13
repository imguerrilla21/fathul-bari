# Stage 29 — Scholarly Verification & Human-in-the-Loop System

Stage 29 adalah **lapisan kontrol ilmiah** aplikasi. Setelah Stage 28, AI sudah mampu mencari hadis, sanad, variasi matan, dan syarah *Fathul Bari*. Sekarang kita memastikan bahwa **setiap informasi penting dapat diperiksa, diverifikasi, ditolak, dikoreksi, dan dilacak siapa yang memverifikasinya**.

Prinsip utamanya:

> **AI menemukan dan mengusulkan. Reviewer memeriksa. Sumber primer menjadi dasar. Sistem menyimpan seluruh jejak keputusan.**

---

# 29.1 Posisi Stage 29

```text
                    USER QUERY
                        │
                        ▼
                RESEARCH ENGINE
                        │
                        ▼
                 AI / RAG RESULT
                        │
                        ▼
                ┌───────────────┐
                │ CLAIMS        │
                │ EVIDENCE      │
                │ CITATIONS     │
                └───────┬───────┘
                        │
                        ▼
             SCHOLARLY REVIEW ENGINE
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       VERIFY         REJECT         EDIT
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                  VERIFIED DATA
                        │
          ┌─────────────┼──────────────┐
          ▼             ▼              ▼
      Knowledge       RAG          Publication
       Graph        Retrieval
```

---

# 29.2 Masalah yang Diselesaikan

Tanpa Stage 29, sistem dapat menghasilkan:

```text
AI:
"Ibn Hajar mengatakan X."
```

padahal:

```text
Evidence:
tidak ditemukan
```

atau:

```text
Evidence:
ada, tetapi konteks berbeda.
```

Dengan Stage 29:

```text
CLAIM
 ↓
EVIDENCE
 ↓
SOURCE
 ↓
REVIEW
 ↓
VERIFICATION STATUS
```

---

# 29.3 Status Evidence

Gunakan status:

```text
DISCOVERED
        ↓
PENDING_REVIEW
        ↓
┌───────┼────────┐
▼       ▼        ▼
VERIFIED REJECTED NEEDS_EDIT
                  │
                  ▼
             PENDING_REVIEW
```

Tambahkan:

```text
SUPERSEDED
```

jika evidence lama digantikan oleh evidence baru.

---

# 29.4 Status Claim

```text
AI_GENERATED
PENDING_REVIEW
SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED
CONTRADICTED
CORRECTED
VERIFIED
```

Perhatikan:

```text
SUPPORTED ≠ VERIFIED
```

`SUPPORTED` berarti evidence ditemukan.

`VERIFIED` berarti reviewer telah memeriksanya.

---

# 29.5 Verification Levels

Gunakan:

```text
LEVEL_0 = AI_UNVERIFIED
LEVEL_1 = SOURCE_FOUND
LEVEL_2 = SOURCE_CHECKED
LEVEL_3 = SCHOLAR_REVIEWED
LEVEL_4 = PUBLICATION_APPROVED
```

Contoh:

```text
AI menemukan:
LEVEL_0

Source Viewer dibuka:
LEVEL_1

Reviewer mengecek:
LEVEL_2

Ahli memverifikasi:
LEVEL_3

Masuk publikasi:
LEVEL_4
```

---

# 29.6 Jangan Menggunakan Satu Angka Confidence Saja

Ini sangat penting.

Jangan:

```json
{
  "confidence": 0.95
}
```

karena angka itu dapat disalahartikan sebagai "kebenaran ilmiah".

Pisahkan:

```json
{
  "retrieval_score": 0.95,
  "nlp_confidence": 0.91,
  "source_quality": 0.98,
  "human_verification": true
}
```

---

# 29.7 Evidence Object Baru

```python
class ScholarlyEvidence:
    id: str

    source_id: str
    document_id: str
    page_id: str
    chunk_id: str

    evidence_type: str

    text: str

    retrieval_score: float
    nlp_confidence: float

    verification_status: str
    verification_level: int
```

---

# 29.8 Verification Record

Setiap verifikasi harus menjadi record tersendiri.

```sql
CREATE TABLE verification_records (
    id UUID PRIMARY KEY,

    target_type VARCHAR(40) NOT NULL,

    target_id UUID NOT NULL,

    reviewer_id UUID NOT NULL,

    decision VARCHAR(40) NOT NULL,

    reason TEXT,

    notes TEXT,

    previous_status VARCHAR(40),

    new_status VARCHAR(40),

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

`target_type`:

```text
CLAIM
EVIDENCE
ENTITY
ISNAD
HADITH_VARIANT
CITATION
```

---

# 29.9 Reviewer Role

Tidak semua user memiliki hak yang sama.

Buat role:

```text
VIEWER
RESEARCHER
REVIEWER
SCHOLAR
EDITOR
ADMIN
```

Contoh:

```text
VIEWER
→ membaca

RESEARCHER
→ membuat penelitian

REVIEWER
→ memeriksa evidence

SCHOLAR
→ scholarly verification

EDITOR
→ publication approval

ADMIN
→ konfigurasi sistem
```

---

# 29.10 Permission Matrix

```text
┌─────────────────────┬───────┬──────────┬─────────┬────────┐
│ Action              │ User  │ Research │ Scholar │ Admin  │
├─────────────────────┼───────┼──────────┼─────────┼────────┤
│ Read source         │ ✓     │ ✓        │ ✓       │ ✓      │
│ Create research     │       │ ✓        │ ✓       │ ✓      │
│ Verify evidence     │       │          │ ✓       │ ✓      │
│ Verify isnad        │       │          │ ✓       │ ✓      │
│ Approve publication │       │          │         │ ✓      │
│ Edit taxonomy       │       │          │         │ ✓      │
└─────────────────────┴───────┴──────────┴─────────┴────────┘
```

Permission dapat dibuat lebih granular.

---

# 29.11 Reviewer Assignment

Penelitian dapat ditugaskan:

```text
Research
   ↓
Review Queue
   ↓
Assigned Reviewer
   ↓
Review
```

Model:

```sql
CREATE TABLE review_assignments (
    id UUID PRIMARY KEY,

    target_type VARCHAR(40),

    target_id UUID,

    reviewer_id UUID,

    priority VARCHAR(20),

    status VARCHAR(30),

    due_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 29.12 Review Queue

Dashboard:

```text
┌──────────────────────────────────────────────────┐
│ SCHOLARLY REVIEW QUEUE                           │
├──────────────┬───────────┬──────────┬───────────┤
│ Target       │ Type      │ Priority │ Status    │
├──────────────┼───────────┼──────────┼───────────┤
│ Claim #001   │ Claim     │ HIGH     │ Pending   │
│ Isnad #442   │ Isnad     │ HIGH     │ Pending   │
│ Entity #882  │ Narrator  │ MEDIUM   │ Pending   │
│ Citation #31 │ Citation  │ LOW      │ Pending   │
└──────────────┴───────────┴──────────┴───────────┘
```

---

# 29.13 Claim Review Interface

```text
┌─────────────────────────────────────────────────────┐
│ CLAIM REVIEW                                        │
├─────────────────────────────────────────────────────┤
│ Claim                                               │
│                                                     │
│ "Ibn Hajar menjelaskan bahwa..."                   │
│                                                     │
├─────────────────────────────────────────────────────┤
│ EVIDENCE                                            │
│                                                     │
│ Fathul Bari — Page 45                              │
│                                                     │
│ "...النِّيَّة..."                                  │
│                                                     │
├─────────────────────────────────────────────────────┤
│ DECISION                                            │
│                                                     │
│ [✓ Verify] [Partial] [Reject] [Edit]               │
└─────────────────────────────────────────────────────┘
```

---

# 29.14 Source Viewer Terintegrasi

Reviewer tidak boleh dipaksa membuka tab lain.

Klik evidence:

```text
Claim
  ↓
Evidence
  ↓
Source Viewer
  ↓
Page
  ↓
Exact passage
```

Highlight:

```text
██████████████████████
relevant source passage
██████████████████████
```

---

# 29.15 Reviewer Decision

Gunakan:

```text
VERIFY
PARTIALLY_VERIFY
REJECT
CORRECT
NEEDS_MORE_EVIDENCE
```

---

# 29.16 Verify

Reviewer menyatakan:

> Evidence mendukung claim.

```json
{
  "decision": "VERIFY",
  "reason": "Teks sumber mendukung klaim."
}
```

---

# 29.17 Partially Verify

Misalnya AI mengatakan:

> Ibn Hajar menyebut X dan Y.

Evidence hanya mendukung X.

Reviewer:

```text
PARTIALLY_VERIFY
```

Kemudian claim dipecah:

```text
Claim A → VERIFIED
Claim B → UNSUPPORTED
```

---

# 29.18 Reject

Jika AI mengarang:

```text
REJECT
```

dan wajib memberi alasan:

```text
reason:
"Informasi tidak terdapat dalam sumber."
```

---

# 29.19 Correct

Reviewer dapat mengubah:

```text
AI:
"Ibn Hajar mengatakan X."

Reviewer:
"Ibn Hajar menjelaskan X dalam konteks Y."
```

Sistem menyimpan:

```text
original_claim
corrected_claim
reviewer
timestamp
evidence
```

Jangan overwrite tanpa histori.

---

# 29.20 Immutable Review History

```text
Claim v1
   ↓
AI generated

Claim v2
   ↓
Reviewer corrected

Claim v3
   ↓
Scholar verified
```

Semua versi tetap tersimpan.

---

# 29.21 Claim Versioning

```sql
CREATE TABLE claim_versions (
    id UUID PRIMARY KEY,

    claim_id UUID NOT NULL,

    version INTEGER NOT NULL,

    claim_text TEXT NOT NULL,

    author_id UUID,

    change_reason TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 29.22 Verification State Machine

```text
                 ┌──────────────┐
                 │ AI_GENERATED │
                 └──────┬───────┘
                        │
                        ▼
                 PENDING_REVIEW
                   │    │
          ┌────────┘    └─────────┐
          ▼                       ▼
      VERIFIED                 REJECTED
          │
          ▼
      PUBLISHED
```

Dengan cabang:

```text
PENDING
   ↓
PARTIAL
   ↓
CORRECTED
   ↓
REVIEW
```

---

# 29.23 Publication Gate

Ini fitur penting.

Artikel tidak boleh dipublikasikan jika:

```text
critical claims = unverified
```

Policy:

```python
def can_publish(document):
    critical_claims = get_critical_claims(document)

    return all(
        c.verification_status == "VERIFIED"
        for c in critical_claims
    )
```

---

# 29.24 Critical Claim

Tidak semua kalimat memerlukan level verifikasi sama.

Contoh:

```text
CRITICAL:
"Hadis ini diriwayatkan oleh..."

CRITICAL:
"Ibn Hajar berkata..."

CRITICAL:
"Perawi X adalah guru Y."

NON_CRITICAL:
"Secara umum, tema hadis ini..."
```

---

# 29.25 Claim Criticality

```text
CRITICAL
HIGH
MEDIUM
LOW
```

Database:

```sql
ALTER TABLE research_claims
ADD COLUMN criticality VARCHAR(20);
```

---

# 29.26 Automatic Verification Prioritization

Sistem otomatis memberi prioritas:

```text
CRITICAL + LOW CONFIDENCE
        ↓
       HIGH
```

Contoh:

```text
"Ibn Hajar mengatakan..."
confidence 0.54
→ HIGH PRIORITY
```

---

# 29.27 Review Priority Score

```text
Priority =
criticality
× uncertainty
× publication_impact
```

Ini adalah heuristic internal.

---

# 29.28 Isnad Verification

Isnad memiliki UI khusus.

```text
Malik
  │
  ▼
Nafi'
  │
  ▼
Ibn Umar
  │
  ▼
Prophet ﷺ
```

Setiap edge:

```text
[عن]
confidence: 0.94

[Verify]
[Reject]
[Edit]
```

---

# 29.29 Verify Isnad Node

Reviewer dapat memilih:

```text
Surface:
ابن عمر

Resolved:
عبد الله بن عمر

Decision:
✓ Correct
```

atau:

```text
✗ Wrong identity
```

---

# 29.30 Isnad Review Result

```json
{
  "node_id": "node_001",
  "decision": "VERIFY",
  "resolved_entity": "narrator_123",
  "reviewer_id": "user_45"
}
```

---

# 29.31 Graph Update Setelah Verification

Jika reviewer memverifikasi:

```text
Nafi' → narrated_from → Ibn Umar
```

status edge:

```text
UNVERIFIED
    ↓
VERIFIED
```

RAG kemudian dapat memberikan ranking lebih tinggi pada evidence tersebut.

---

# 29.32 Verified Graph

Bedakan:

```text
ALL GRAPH
```

dan:

```text
VERIFIED GRAPH
```

Query RAG dapat memilih:

```text
verified_only=true
```

untuk pertanyaan sensitif.

---

# 29.33 RAG Trust Layer

Tambahkan:

```text
Trust Score
```

Contoh:

```text
Primary verified source:
1.00

Primary unverified:
0.85

Secondary verified:
0.80

Semantic-only:
0.50

AI inference:
0.20
```

Angka hanya initial policy dan harus dikonfigurasi.

---

# 29.34 Trust-Aware Retrieval

Final retrieval:

```text
FinalScore =
Relevance
×
SourceQuality
×
VerificationTrust
```

Dengan demikian evidence terverifikasi diprioritaskan.

---

# 29.35 Reviewer Notes

Reviewer dapat menulis:

```text
Catatan:
"Lafaz pada edisi ini berbeda dengan edisi lainnya.
Perlu dilakukan pemeriksaan terhadap edisi X."
```

Catatan tidak mengubah source.

---

# 29.36 Disagreement System

Reviewer boleh tidak sepakat.

```text
Reviewer A:
VERIFY

Reviewer B:
PARTIALLY_VERIFY
```

Sistem **tidak otomatis memilih mayoritas**.

Status:

```text
DISPUTED
```

---

# 29.37 Disputed Evidence

```text
┌─────────────────────────────────────────────┐
│ ⚠ DISPUTED                                 │
├─────────────────────────────────────────────┤
│ Reviewer A → Verified                       │
│ Reviewer B → Partial                        │
│                                             │
│ [Open Discussion]                           │
└─────────────────────────────────────────────┘
```

---

# 29.38 Scholarly Discussion

Tambahkan:

```sql
CREATE TABLE review_discussions (
    id UUID PRIMARY KEY,

    target_type VARCHAR(40),

    target_id UUID,

    author_id UUID,

    message TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 29.39 Discussion Rules

Diskusi harus tetap terkait evidence.

Komentar:

> "Saya rasa ini benar."

kurang kuat.

Komentar:

> "Pada halaman 132, lafaz tersebut muncul sebagai ..., sehingga identifikasi ini perlu dikoreksi."

lebih berguna.

---

# 29.40 Evidence Annotation

Reviewer dapat menandai:

```text
IMPORTANT
AMBIGUOUS
TYPO
OCR_ERROR
MISSING_PAGE
WRONG_REFERENCE
WRONG_ENTITY
```

---

# 29.41 OCR Error Correction

Jika source OCR:

```text
النية
```

terbaca:

```text
البيه
```

reviewer dapat membuat correction:

```text
OCR:
البيه

Corrected:
النية
```

Tetapi:

```text
original OCR
```

tetap dipertahankan.

---

# 29.42 Correction Layer

```text
Original Source
      │
      ├── OCR Text
      │
      └── Corrected Representation
```

Jangan mengubah file sumber asli.

---

# 29.43 Source Correction Model

```sql
CREATE TABLE source_annotations (
    id UUID PRIMARY KEY,

    source_id UUID,

    page_id UUID,

    chunk_id UUID,

    annotation_type VARCHAR(40),

    original_text TEXT,

    corrected_text TEXT,

    reviewer_id UUID,

    status VARCHAR(30),

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 29.44 Audit Trail

Setiap tindakan:

```text
USER
ACTION
TARGET
OLD STATE
NEW STATE
REASON
TIMESTAMP
```

Contoh:

```json
{
  "actor": "reviewer_01",
  "action": "VERIFY_CLAIM",
  "target": "claim_442",
  "old_status": "PENDING_REVIEW",
  "new_status": "VERIFIED",
  "reason": "Evidence directly supports claim."
}
```

---

# 29.45 Audit Table

Jika Stage 6 sudah memiliki audit system, extend:

```sql
CREATE TABLE audit_events (
    id UUID PRIMARY KEY,

    actor_id UUID,

    action VARCHAR(100),

    entity_type VARCHAR(50),

    entity_id UUID,

    before_state JSONB,

    after_state JSONB,

    reason TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 29.46 Audit Tidak Boleh Mutable

Reviewer tidak boleh menghapus:

```text
Reviewer A verified
```

hanya karena reviewer B tidak setuju.

Sebaliknya:

```text
Event 1:
A → VERIFIED

Event 2:
B → DISPUTED
```

keduanya tetap ada.

---

# 29.47 Review Dashboard

Dashboard utama:

```text
┌──────────────────────────────────────────────────────┐
│ SCHOLARLY REVIEW                                    │
├──────────────────────────────────────────────────────┤
│ Pending          124                                │
│ High Priority     18                                │
│ Disputed           7                                │
│ Verified          892                                │
│ Rejected           43                                │
├──────────────────────────────────────────────────────┤
│ QUEUE                                                │
│                                                      │
│ Claim #123       Ibn Hajar attribution     HIGH      │
│ Isnad #551       Narrator identity        HIGH      │
│ Entity #332      Scholar linking          MEDIUM    │
│ OCR #782         Page correction          LOW       │
└──────────────────────────────────────────────────────┘
```

---

# 29.48 Review Filters

```text
Status
Type
Reviewer
Source
Book
Scholar
Hadith
Priority
Date
```

---

# 29.49 Scholar Dashboard

Untuk reviewer tingkat scholar:

```text
MY REVIEWS

Assigned:
34

Completed:
27

Disputed:
2

Pending:
5
```

---

# 29.50 Verification Statistics

```text
EVIDENCE QUALITY

Total claims                  12,431
Verified                       9,820
Partially verified             1,102
Rejected                         418
Pending                        1,091
```

---

# 29.51 Source Quality Dashboard

```text
SOURCE QUALITY

Fathul Bari
Verified passages: 4,812
OCR corrections:      31
Reference errors:       4

Hadith API
Verified records: 12,932
Pending:             842
```

---

# 29.52 AI Learning dari Review

Jangan langsung melakukan:

```text
Reviewer feedback
 ↓
train model automatically
```

Gunakan terlebih dahulu:

```text
Review feedback
 ↓
Evaluation Dataset
 ↓
Offline Evaluation
 ↓
Model/Prompt Improvement
 ↓
New Version
```

Ini jauh lebih aman.

---

# 29.53 Reviewer Feedback Dataset

Simpan:

```json
{
  "query": "...",
  "prediction": "...",
  "decision": "REJECT",
  "corrected_output": "...",
  "evidence": ["..."]
}
```

Dataset ini menjadi benchmark internal.

---

# 29.54 Evaluation Pipeline

```text
Production Review
      ↓
Feedback Dataset
      ↓
Regression Tests
      ↓
New RAG Version
      ↓
Evaluation
      ↓
Approval
      ↓
Production
```

---

# 29.55 RAG Regression Test

Jika sebelumnya sistem berhasil menemukan:

```text
Fathul Bari Page X
```

versi baru tidak boleh kehilangan hasil tersebut tanpa alasan.

Test:

```python
def test_fathul_bari_retrieval():
    results = research("Apa penjelasan Ibn Hajar tentang niat?")
    assert contains_source(results, "Fathul Bari")
```

---

# 29.56 Golden Questions

Buat dataset:

```text
golden_questions.json
```

Contoh:

```json
[
  {
    "question": "Apa penjelasan Ibn Hajar tentang niat?",
    "required_sources": [
      "Fathul Bari"
    ]
  }
]
```

---

# 29.57 Golden Evidence

Lebih kuat lagi:

```json
{
  "question": "...",
  "golden_evidence": [
    "FB-P45-C03",
    "Bukhari-1"
  ]
}
```

RAG harus menemukan evidence tersebut.

---

# 29.58 Verification API

### Verify claim

```http
POST /api/v1/review/claims/{claim_id}/verify
```

```json
{
  "decision": "VERIFY",
  "notes": "Source supports the claim."
}
```

### Reject

```http
POST /api/v1/review/claims/{claim_id}/reject
```

### Correct

```http
POST /api/v1/review/claims/{claim_id}/correct
```

```json
{
  "corrected_text": "...",
  "reason": "..."
}
```

---

# 29.59 Generic Review API

Lebih baik juga punya:

```http
POST /api/v1/review/{target_type}/{target_id}
```

Request:

```json
{
  "decision": "VERIFY",
  "notes": "..."
}
```

Target:

```text
claim
evidence
isnad
entity
citation
variant
```

---

# 29.60 Review Service

```python
class ReviewService:

    def verify(self, target, reviewer, notes):
        ...

    def reject(self, target, reviewer, reason):
        ...

    def correct(self, target, reviewer, correction):
        ...

    def dispute(self, target, reviewer, reason):
        ...

    def get_history(self, target):
        ...
```

---

# 29.61 Publication Workflow

Sekarang publication pipeline:

```text
Research
  ↓
Draft
  ↓
AI Evidence
  ↓
Human Review
  ↓
Scholar Verification
  ↓
Editorial Review
  ↓
Publication
```

---

# 29.62 Publication State

```text
DRAFT
RESEARCHED
REVIEWING
SCHOLAR_VERIFIED
EDITOR_APPROVED
PUBLISHED
ARCHIVED
```

---

# 29.63 Publication Gate

```python
def publication_status(document):

    if has_unverified_critical_claims(document):
        return "REVIEWING"

    if not scholar_review_completed(document):
        return "SCHOLAR_VERIFIED_REQUIRED"

    return "EDITOR_APPROVED"
```

---

# 29.64 Source Integrity

Sebelum publish:

```text
Source hash
     ↓
Compare
     ↓
No unexpected change
```

Jika source berubah:

```text
SOURCE_CHANGED
```

maka evidence yang bergantung padanya dapat ditandai:

```text
REVALIDATION_REQUIRED
```

---

# 29.65 Revalidation

```text
Source version 1
      ↓
Evidence verified
      ↓
Source version 2
      ↓
Content changed
      ↓
Evidence becomes:
REVALIDATION_REQUIRED
```

Ini sangat penting untuk API yang datanya dapat berubah.

---

# 29.66 Ahmad Sanusi API + Verification

Arsitektur:

```text
Ahmad Sanusi API
       │
       ▼
Raw Record
       │
       ▼
Canonical Hadith
       │
       ▼
NLP
       │
       ▼
AI Analysis
       │
       ▼
Review
       │
       ▼
VERIFIED
```

Jangan:

```text
API → automatically VERIFIED
```

---

# 29.67 Source Trust Policy

Contoh konfigurasi:

```yaml
source_policy:

  primary_book:
    default_trust: high

  verified_local_corpus:
    default_trust: high

  api_import:
    default_trust: medium

  ai_generated:
    default_trust: low
```

Nilai ini hanya **default retrieval policy**, bukan penilaian keaslian kitab.

---

# 29.68 RAG Policy

Untuk pertanyaan:

> "Apa kata Ibn Hajar?"

sistem:

```text
REQUIRED:
Fathul Bari evidence
```

Jika tidak ditemukan:

```text
DO NOT ANSWER AS ATTRIBUTION
```

Jawaban:

> "Saya belum menemukan kutipan Fathul Bari yang cukup untuk memastikan atribusi tersebut."

Ini jauh lebih baik daripada hallucination.

---

# 29.69 Attribution Guard

Implementasikan:

```python
def validate_attribution(claim):

    if claim.attribution == "IBN_HAJAR":
        if not claim.has_fathul_bari_evidence:
            return False

    return True
```

---

# 29.70 Hadith Grading Guard

Jika AI mengatakan:

> "Hadis ini sahih."

validator mengecek:

```text
Does evidence contain explicit grading?
```

Jika tidak:

```text
BLOCK
```

atau ubah menjadi:

> "Hadis ini terdapat dalam ..."

---

# 29.71 Isnad Guard

Jika AI menyebut:

```text
A → B → C
```

validator memastikan chain memang ada di graph:

```python
assert graph.contains_path(A, B, C)
```

Jika tidak:

```text
UNSUPPORTED_ISNAD
```

---

# 29.72 Source Locator Guard

AI tidak boleh menghasilkan:

```text
Fathul Bari, halaman 123
```

jika:

```text
page 123
```

tidak ada dalam source metadata.

Validator:

```python
assert source.has_locator(citation.locator)
```

---

# 29.73 Verification-Aware Answer

Setelah Stage 29, jawaban dapat memiliki badge:

```text
✓ SOURCE VERIFIED
✓ SCHOLAR REVIEWED
⚠ AI INFERENCE
```

Contoh:

```text
Ibn Hajar menjelaskan ...

✓ Fathul Bari — source verified
```

---

# 29.74 Evidence Badge

Gunakan:

```text
[PRIMARY]
[VERIFIED]
[SECONDARY]
[INFERRED]
[DISPUTED]
```

Ini membantu pengguna memahami tingkat evidence.

---

# 29.75 Research Result Example

```text
┌──────────────────────────────────────────────┐
│ JAWABAN                                      │
├──────────────────────────────────────────────┤
│                                              │
│ Ibn Hajar menjelaskan ... [1]                │
│                                              │
│ ✓ Primary source                             │
│ ✓ Scholar verified                           │
│                                              │
│ Hadis diriwayatkan melalui ... [2]           │
│                                              │
│ ✓ Hadith source                              │
│ ⚠ Isnad entity partially verified            │
│                                              │
└──────────────────────────────────────────────┘
```

---

# 29.76 Definition of Done

Stage 29 selesai apabila:

```text
[ ] Review queue
[ ] Reviewer roles
[ ] Permission system
[ ] Claim verification
[ ] Evidence verification
[ ] Isnad verification
[ ] Entity verification
[ ] Citation verification
[ ] Verify / Reject / Correct
[ ] Dispute workflow
[ ] Review discussion
[ ] Immutable audit
[ ] Claim versioning
[ ] Source annotation
[ ] OCR correction
[ ] Verification levels
[ ] Trust-aware RAG
[ ] Attribution guard
[ ] Grading guard
[ ] Isnad guard
[ ] Citation guard
[ ] Publication gate
[ ] Source revalidation
[ ] Reviewer feedback dataset
[ ] Golden questions
[ ] RAG regression testing
```

---

# 29.77 Struktur Folder

Tambahkan:

```text
backend/
└── app/
    ├── review/
    │   ├── service.py
    │   ├── claims.py
    │   ├── evidence.py
    │   ├── isnad.py
    │   ├── entities.py
    │   ├── citations.py
    │   ├── assignments.py
    │   ├── discussions.py
    │   └── permissions.py
    │
    ├── verification/
    │   ├── state_machine.py
    │   ├── validators.py
    │   ├── attribution.py
    │   ├── grading.py
    │   ├── isnad_guard.py
    │   └── source_guard.py
    │
    ├── audit/
    │   ├── events.py
    │   └── history.py
    │
    └── publication/
        ├── gates.py
        ├── approval.py
        └── revalidation.py
```

Frontend:

```text
frontend/
└── src/
    ├── pages/
    │   ├── ReviewDashboard/
    │   └── ResearchReview/
    │
    ├── components/
    │   ├── ClaimReview/
    │   ├── EvidenceReview/
    │   ├── IsnadReview/
    │   ├── VerificationBadge/
    │   ├── ReviewHistory/
    │   ├── ConflictPanel/
    │   └── SourceAnnotation/
    │
    └── services/
        └── reviewApi.ts
```

---

# 29.78 Arsitektur Keseluruhan Setelah Stage 29

Sekarang platform sudah memiliki **kontrol epistemik**:

```text
                         USER
                           │
                           ▼
                  NATURAL LANGUAGE
                    RESEARCH ENGINE
                           │
                           ▼
                         RAG
                           │
          ┌────────────────┼─────────────────┐
          ▼                ▼                 ▼
       HADITH           FATHUL BARI       ISNAD
       ENGINE             ENGINE           GRAPH
          │                │                 │
          └────────────────┼─────────────────┘
                           ▼
                      EVIDENCE
                           │
                           ▼
                        CLAIMS
                           │
                           ▼
                 ┌──────────────────┐
                 │ VERIFICATION     │
                 │                  │
                 │ AI               │
                 │ Reviewer         │
                 │ Scholar          │
                 │ Editor           │
                 └────────┬─────────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          VERIFIED     DISPUTED      REJECTED
             │
             ▼
        TRUSTED GRAPH
             │
             ▼
        TRUSTED RAG
             │
             ▼
         PUBLICATION
```

---

# 29.79 Prinsip Terpenting yang Sekarang Tercapai

Aplikasi tidak lagi hanya menjawab:

> **"Apa yang ditemukan AI?"**

tetapi dapat menjawab:

> **"Apa yang ditemukan AI, dari sumber mana, pada bagian mana, bagaimana hubungan sanadnya, siapa yang memverifikasinya, kapan diverifikasi, apakah ada keberatan, dan apakah klaim tersebut layak dipublikasikan?"**

Itulah yang membuat aplikasi ini mulai mendekati **platform penelitian digital hadis**, bukan sekadar chatbot hadis.

---
