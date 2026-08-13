Baik. **Tahap 3** kita fokuskan pada inti aplikasi: **pipeline ekstraksi Fathul Bari → normalisasi teks Arab → segmentasi → deteksi referensi hadis → linking ke hadis Shahih Bukhari**.

Target akhirnya:

```text
PDF Fathul Bari
      │
      ▼
PDF Text / OCR
      │
      ▼
Arabic Normalization
      │
      ▼
Sharh Sections
      │
      ▼
Hadith Reference Detection
      │
      ▼
Hadith–Sharh Linking Engine
      │
      ▼
PostgreSQL
      │
      ├── Hadith
      ├── Sharh Section
      └── Link + Confidence
```

## 1. Struktur project tahap 3

Tambahkan ke starter project:

```text
backend/
├── app/
│   ├── models/
│   │   ├── sharh.py
│   │   └── ...
│   │
│   ├── services/
│   │   ├── pdf_extractor.py
│   │   ├── arabic_normalizer.py
│   │   ├── sharh_segmenter.py
│   │   ├── hadith_reference_detector.py
│   │   └── hadith_linker.py
│   │
│   └── utils/
│       └── arabic.py
│
├── scripts/
│   ├── extract_fathul_bari.py
│   ├── detect_hadith_refs.py
│   └── link_sharh.py
│
└── data/
    └── fathul_bari/
        ├── raw/
        ├── extracted/
        ├── normalized/
        └── review/
```

Saya menyarankan **tidak mengubah PDF asli**. File original tetap disimpan sebagai `raw`.

---

# 2. Prinsip penting: jangan langsung menghubungkan berdasarkan nomor

Kesalahan yang perlu kita hindari:

```text
Fathul Bari halaman 10
        ↓
menemukan "hadis nomor 1"
        ↓
langsung → Bukhari #1
```

Karena dalam syarah klasik:

* hadis dapat disebut dengan berbagai redaksi;
* satu hadis dapat muncul dalam beberapa bab;
* nomor hadis dapat berbeda antar-edisi;
* Ibnu Hajar dapat menggunakan potongan matan;
* beliau sering berkata seperti `قوله` atau `حديث`;
* syarah dapat membahas beberapa riwayat sekaligus.

Karena itu kita menggunakan **multi-signal matching**.

```text
Nomor hadis
     +
Matan Arab
     +
Nama sahabat
     +
Kata pembuka hadis
     +
Bab
     +
Posisi halaman
     +
Konteks
     ↓
Confidence Score
```

---

# 3. Tambahkan dependency PDF

Pada `backend/requirements.txt` tambahkan:

```text
pypdf==6.0.0
pdfplumber==0.11.7
```

Untuk tahap OCR nantinya kita dapat menambahkan:

```text
pytesseract
```

tetapi **jangan langsung menjadikan OCR sebagai default**.

Jika PDF Fathul Bari sudah memiliki text layer, kita jauh lebih baik menggunakan text layer tersebut.

---

# 4. PDF extractor

Buat:

```text
backend/app/services/pdf_extractor.py
```

```python
from pathlib import Path

import pdfplumber


def extract_pdf(
    pdf_path: str,
    output_dir: str,
) -> list[dict]:

    pdf = Path(pdf_path)
    output = Path(output_dir)

    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    pages = []

    with pdfplumber.open(pdf) as document:

        for page_number, page in enumerate(
            document.pages,
            start=1,
        ):

            text = page.extract_text(
                x_tolerance=2,
                y_tolerance=3,
            ) or ""

            record = {
                "page": page_number,
                "text": text,
            }

            pages.append(record)

            page_file = (
                output /
                f"page_{page_number:04d}.txt"
            )

            page_file.write_text(
                text,
                encoding="utf-8",
            )

    return pages
```

Dengan ini:

```text
Fathul-Bari.pdf
       ↓
page_0001.txt
page_0002.txt
page_0003.txt
...
```

---

# 5. Jangan kehilangan nomor halaman PDF

Ini sangat penting untuk penelitian.

Database harus tahu:

```text
volume
PDF page
printed page
section order
```

Karena:

```text
PDF page 150
```

belum tentu:

```text
halaman kitab 150
```

Jadi model `SharhSection` nantinya sebaiknya diperluas.

---

# 6. Upgrade model `SharhSection`

Ubah menjadi:

```python
class SharhSection(Base):

    __tablename__ = "sharh_sections"

    id = ...

    work_slug = ...

    volume = ...

    pdf_page = ...

    printed_page = ...

    section_order = ...

    title = ...

    arabic_text = ...

    normalized_text = ...

    translation = ...

    extraction_status = ...

    created_at = ...
```

Tambahkan juga:

```text
source_file
source_hash
```

sehingga kita bisa membuktikan section berasal dari PDF tertentu.

---

# 7. Arabic Normalizer

Ini bagian sangat penting.

Buat:

```text
backend/app/services/arabic_normalizer.py
```

```python
import re


ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)


def normalize_arabic(text: str) -> str:

    if not text:
        return ""

    # Remove tashkeel
    text = ARABIC_DIACRITICS.sub(
        "",
        text,
    )

    # Normalize Alef
    text = re.sub(
        r"[إأآٱ]",
        "ا",
        text,
    )

    # Normalize Yeh
    text = text.replace(
        "ى",
        "ي",
    )

    # Normalize Persian forms
    text = text.replace(
        "ک",
        "ك",
    )

    text = text.replace(
        "ی",
        "ي",
    )

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()
```

---

# 8. Simpan dua versi teks

Jangan melakukan kesalahan ini:

```text
Original Arabic
      ↓
normalize
      ↓
replace original
```

Kita harus menyimpan:

```text
arabic_text
     │
     └── original

normalized_text
     │
     └── untuk search/matching
```

Karena untuk penelitian, **teks asli harus selalu dipertahankan**.

---

# 9. Segmentasi Fathul Bari

Kita belum boleh menganggap:

```text
1 halaman = 1 syarah
```

Yang lebih tepat:

```text
Volume
  │
  ├── Kitab
  │    ├── Bab
  │    │    ├── Sharh section
  │    │    └── Sharh section
```

Secara sederhana tahap awal:

```text
PDF page
   ↓
paragraph
   ↓
section
```

Kemudian pada tahap berikutnya kita dapat meningkatkan ke:

```text
Kitab → Bab → Hadis → Sharh
```

---

# 10. Deteksi marker syarah

Ibnu Hajar sering menggunakan formula seperti:

```text
قوله
قوله تعالى
قوله باب
حديث
أخرجه
رواه
```

Buat:

```text
backend/app/services/sharh_segmenter.py
```

```python
import re

MARKERS = [
    r"قوله",
    r"قوله تعالى",
    r"حديث",
    r"أخرجه",
    r"رواه",
]


def detect_markers(text: str):

    found = []

    for marker in MARKERS:

        if re.search(marker, text):

            found.append(marker)

    return found
```

Ini **bukan classifier final**.

Ini hanya sinyal.

---

# 11. Hadith Reference Detector

Buat:

```text
backend/app/services/hadith_reference_detector.py
```

Tahap pertama kita cari pola nomor.

```python
import re


ARABIC_DIGITS = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩",
    "0123456789",
)


def normalize_digits(
    text: str,
) -> str:

    return text.translate(
        ARABIC_DIGITS
    )


PATTERNS = [

    r"حديث\s*(\d+)",

    r"الحديث\s*(\d+)",

    r"رقم\s*(\d+)",

]


def detect_numbers(
    text: str,
) -> list[int]:

    text = normalize_digits(
        text
    )

    numbers = []

    for pattern in PATTERNS:

        matches = re.findall(
            pattern,
            text,
        )

        for value in matches:

            numbers.append(
                int(value)
            )

    return sorted(
        set(numbers)
    )
```

---

# 12. Tapi nomor saja belum cukup

Misalnya:

```text
حديث رقم 150
```

bisa berarti:

```text
Bukhari #150
```

tetapi kita tetap harus memberi confidence.

Model:

```text
reference_type:
    explicit_number

confidence:
    0.98
```

Sedangkan:

```text
matan similarity
```

misalnya:

```text
confidence:
    0.87
```

---

# 13. Buat struktur `HadithReference`

Kita dapat memakai Pydantic:

```python
from pydantic import BaseModel


class HadithReference(BaseModel):

    hadith_number: int | None

    matched_text: str | None

    reference_type: str

    confidence: float

    evidence: dict
```

Contoh:

```json
{
  "hadith_number": 150,
  "reference_type": "explicit_number",
  "confidence": 0.98,
  "evidence": {
    "marker": "حديث",
    "number": 150
  }
}
```

---

# 14. Hadith–Sharh Linking Engine

Sekarang kita sampai ke komponen utama.

Buat:

```text
backend/app/services/hadith_linker.py
```

Algoritmanya:

```text
                 Sharh Section
                       │
             ┌─────────┴─────────┐
             │                   │
        Explicit #           Matan text
             │                   │
             ▼                   ▼
       Candidate IDs       Text similarity
             │                   │
             └─────────┬─────────┘
                       ▼
                  Score Engine
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       number        text        context
        0.50         0.35         0.15
          │            │            │
          └────────────┴────────────┘
                       ▼
                 final score
```

---

# 15. Confidence formula

Untuk versi awal:

```text
score =
    number_score × 0.50
  + text_score × 0.35
  + context_score × 0.15
```

Contoh:

```text
number = 1.0
text = 0.91
context = 0.80
```

maka:

```text
0.50
+ 0.3185
+ 0.12

= 0.9385
```

atau:

```text
93.85%
```

---

# 16. Kategori confidence

Saya sarankan:

```text
≥ 0.90
    AUTO VERIFIED CANDIDATE

0.75–0.89
    REVIEW

0.50–0.74
    WEAK MATCH

< 0.50
    REJECT
```

**Penting:** `AUTO VERIFIED CANDIDATE` bukan berarti langsung dianggap sebagai kebenaran ilmiah.

Untuk aplikasi akademik:

```text
AI confidence
      ≠
Human verification
```

---

# 17. Database linking

Kita sudah mempunyai:

```text
hadith_sharh_links
```

Contoh:

```text
hadith_id
    ↓
Bukhari #1

sharh_section_id
    ↓
Fathul Bari Vol 1 Page 45

match_method
    ↓
number + text

confidence
    ↓
0.96

verified
    ↓
false
```

Setelah peneliti memeriksa:

```text
verified = true
```

---

# 18. Tambahkan `review_status`

Saya menyarankan upgrade schema.

```text
pending
auto_candidate
verified
rejected
```

Jadi:

```text
confidence 0.94
        ↓
auto_candidate
        ↓
human review
        ↓
verified
```

---

# 19. Workflow penelitian

Aplikasi nantinya mempunyai:

```text
                 EXTRACT
                    │
                    ▼
                  RAW
                    │
                    ▼
                NORMALIZE
                    │
                    ▼
                SEGMENT
                    │
                    ▼
             DETECT REFERENCES
                    │
                    ▼
              LINK CANDIDATES
                    │
                    ▼
               HUMAN REVIEW
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
       VERIFIED             REJECTED
          │
          ▼
       PUBLISHED
```

Ini jauh lebih aman untuk proyek hadis daripada membuat AI langsung "menebak" hubungan.

---

# 20. Script ekstraksi

Buat:

```text
backend/scripts/extract_fathul_bari.py
```

```python
import argparse
import json
from pathlib import Path

from app.services.pdf_extractor import (
    extract_pdf,
)

from app.services.arabic_normalizer import (
    normalize_arabic,
)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--pdf",
        required=True,
    )

    parser.add_argument(
        "--output",
        default="data/fathul_bari/extracted",
    )

    args = parser.parse_args()

    pages = extract_pdf(
        args.pdf,
        args.output,
    )

    normalized = []

    for page in pages:

        normalized.append({
            "page": page["page"],
            "text": page["text"],
            "normalized_text":
                normalize_arabic(
                    page["text"]
                ),
        })

    output = Path(
        "data/fathul_bari/normalized"
    )

    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    file = (
        output /
        "pages.json"
    )

    file.write_text(
        json.dumps(
            normalized,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"Extracted {len(pages)} pages"
    )


if __name__ == "__main__":
    main()
```

---

# 21. Jalankan

Misalnya Anda mempunyai:

```text
data/fathul_bari/raw/
    fathul_bari_volume_01.pdf
```

Jalankan:

```bash
docker compose exec backend \
python scripts/extract_fathul_bari.py \
--pdf data/fathul_bari/raw/fathul_bari_volume_01.pdf
```

Output:

```text
data/fathul_bari/
├── raw/
│   └── fathul_bari_volume_01.pdf
│
├── extracted/
│   ├── page_0001.txt
│   ├── page_0002.txt
│   └── ...
│
└── normalized/
    └── pages.json
```

---

# 22. Jangan langsung memasukkan seluruh PDF

Gunakan pendekatan:

```text
5 halaman
 ↓
uji extraction

50 halaman
 ↓
uji segmentation

1 volume
 ↓
uji reference detection

seluruh kitab
 ↓
production pipeline
```

Ini akan menghemat banyak waktu debugging.

---

# 23. Tahap 3A — gold sample

Saya sangat menyarankan kita membuat dataset kecil yang diverifikasi manusia:

```text
data/fathul_bari/review/
    gold_links.json
```

Contoh:

```json
[
  {
    "volume": 1,
    "page": 45,
    "hadith_number": 1,
    "verified": true
  },
  {
    "volume": 1,
    "page": 46,
    "hadith_number": 2,
    "verified": true
  }
]
```

Ini nantinya menjadi **ground truth**.

Kemudian algoritma kita dapat diuji:

```text
Predicted:
Bukhari #1

Gold:
Bukhari #1

→ TRUE POSITIVE
```

---

# 24. Metrik yang akan kita gunakan

Bukan sekadar:

> "Kelihatannya cocok."

Tetapi:

```text
Precision
Recall
F1
```

Misalnya:

```text
100 candidate links

90 benar
10 salah
```

Precision:

```text
90%
```

Ini sangat penting jika nanti linking engine dipakai untuk ribuan halaman.

---

# 25. Tahap 3B — pencarian matan

Setelah exact-number detection bekerja, kita tambahkan pencarian teks.

Contohnya syarah menyebut:

```text
إنما الأعمال بالنيات
```

Database Bukhari mempunyai:

```text
إنما الأعمال بالنيات وإنما لكل امرئ ما نوى
```

Engine harus mengetahui bahwa keduanya merupakan potongan matan yang sama.

Tahap ini bisa menggunakan:

```text
exact substring
        ↓
token overlap
        ↓
character similarity
        ↓
Arabic-aware similarity
        ↓
embedding
```

**Embedding jangan menjadi lapisan pertama.**

Kita prioritaskan deterministic matching terlebih dahulu.

---

# 26. Arsitektur final linking engine

```text
             SHARH TEXT
                  │
                  ▼
        Arabic normalization
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
 explicit reference      text clues
        │                   │
        ▼                   ▼
    candidate IDs      candidate search
        │                   │
        └─────────┬─────────┘
                  ▼
             score engine
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
      number     matn     context
        │         │         │
        └─────────┴─────────┘
                  ▼
             confidence
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
    reject      review     candidate
                              │
                              ▼
                         human review
                              │
                         ┌────┴────┐
                         ▼         ▼
                      verified   rejected
```

---

# 27. Yang akan kita dapatkan di UI

Nantinya ketika pengguna membuka:

**Shahih Bukhari #1**

layar akan menjadi:

```text
┌──────────────────────────────────────────────┐
│ SHAHIH AL-BUKHARI #1                         │
├──────────────────────────────────────────────┤
│                                              │
│ إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ ...       │
│                                              │
│ Sesungguhnya amal itu tergantung niat...     │
│                                              │
├──────────────────────────────────────────────┤
│ SYARAH FATHUL BARI                           │
├──────────────────────────────────────────────┤
│                                              │
│ Volume 1 · Halaman 45                        │
│                                              │
│ قوله: إنما الأعمال بالنيات...                │
│                                              │
│ [Tampilkan halaman sumber]                   │
│                                              │
├──────────────────────────────────────────────┤
│ SUMBER                                       │
│ Ahmad Sanusi → Shahih Bukhari                │
│ Fathul Bari → Volume 1, halaman 45           │
└──────────────────────────────────────────────┘
```

Dan yang paling penting:

**setiap klaim mempunyai provenance.**

---

# 28. Tahap 3 selesai jika

Kita jangan menganggap tahap ini selesai hanya karena PDF berhasil diekstrak.

Definition of Done:

```text
[ ] PDF original tersimpan
[ ] Text extraction berhasil
[ ] Arabic normalization berhasil
[ ] Page mapping dipertahankan
[ ] Sharh section berhasil dibuat
[ ] Reference detector berjalan
[ ] Candidate linking berjalan
[ ] Confidence score tersedia
[ ] Human review tersedia
[ ] Provenance tersedia
[ ] Gold dataset tersedia
[ ] Precision/Recall dapat dihitung
```

### Urutan implementasi berikutnya

Saya sarankan setelah ini kita masuk ke **Tahap 3A**, bukan langsung AI/RAG:

**3A. Saya akan membuatkan modul PDF ingestion + database migration + API upload PDF + extraction job secara lengkap**, sehingga Anda tinggal menaruh file PDF Fathul Bari dan sistem otomatis menghasilkan:

```text
PDF
 ↓
Pages
 ↓
Raw text
 ↓
Normalized Arabic
 ↓
Sharh sections
 ↓
Database
```

Setelah pipeline tersebut stabil, **Tahap 4** baru kita bangun **Hadith–Sharh Matching Engine**, termasuk fuzzy Arabic matching dan confidence scoring.
