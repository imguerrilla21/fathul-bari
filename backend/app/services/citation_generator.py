"""Citation Generator Service untuk Fathul Bari Research Platform.
Menyediakan pembuatan sitasi ilmiah standar turats, Chicago style, BibTeX, dan Markdown.
"""

from typing import Any


def generate_citations(
    hadith_number: int | None,
    collection_name: str | None,
    volume: int | None,
    page: int | None,
    sharh_title: str | None = None,
    hadith_arabic_excerpt: str | None = None,
    author: str = "Ibnu Hajar al-Asqalani",
    book_title: str = "Fathul Bari Syarah Shahih al-Bukhari",
) -> dict[str, str]:
    """Menghasilkan representasi sitasi dalam berbagai format standar akademik."""
    vol_str = f"Jilid {volume}" if volume is not None else "Jilid -"
    page_str = f"Hal. {page}" if page is not None else "Hal. -"
    coll_str = collection_name or "Shahih al-Bukhari"
    num_str = f"No. {hadith_number}" if hadith_number is not None else "No. -"

    # 1. Standar Turats / Format Indonesia
    standard = f"{author}. {book_title}, {vol_str}, {page_str}. Penjelasan Hadis {coll_str} {num_str}."

    # 2. Format Akademik Chicago (Notes & Bibliography)
    chicago = (
        f"Al-Asqalani, Ahmad bin Ali bin Hajar. {book_title}. "
        f"{vol_str}, hlm. {page if page is not None else '-'}. "
        f"(Syarah terhadap {coll_str} {num_str})."
    )

    # 3. Format BibTeX
    clean_key = f"fathul_bari_v{volume or 1}_p{page or 1}_h{hadith_number or 1}"
    bibtex = f"""@incollection{{{clean_key},
  author    = {{Al-Asqalani, Ahmad ibn Ali ibn Hajar}},
  title     = {{{sharh_title or f'Syarah Hadis {num_str}'}}},
  booktitle = {{{book_title}}},
  volume    = {{{volume or 1}}},
  pages     = {{{page or 1}}},
  note      = {{Syarah terhadap {coll_str} {num_str}}},
  publisher = {{Darul Kutub al-Ilmiyyah}},
  address   = {{Beirut, Lebanon}}
}}"""

    # 4. Format Markdown dengan Blockquote
    excerpt_clean = (hadith_arabic_excerpt or "").strip()
    md_lines = [
        f"> **Sitasi:** {standard}",
    ]
    if excerpt_clean:
        md_lines.append(f"> *Matan:* « {excerpt_clean} »")

    markdown = "\n>\n".join(md_lines)

    return {
        "standard": standard,
        "chicago": chicago,
        "bibtex": bibtex,
        "markdown": markdown,
    }
