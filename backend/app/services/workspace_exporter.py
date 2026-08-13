import json
from datetime import datetime
from typing import Any

from app.models.workspace import (
    ResearchAnnotation,
    ResearchCitation,
    ResearchNote,
    ResearchProject,
)


def export_project_to_markdown(
    project: ResearchProject,
    notes: list[ResearchNote],
    annotations: list[ResearchAnnotation],
    citations: list[ResearchCitation],
) -> str:
    """Menghasilkan monograf penelitian ilmiah lengkap dalam format Markdown."""
    created_date = project.created_at.strftime("%d %B %Y") if project.created_at else "-"
    
    md_lines = [
        f"# {project.title}",
        f"**Peneliti / Muhaqqiq**: {project.created_by}  ",
        f"**Tanggal Riset**: {created_date}  ",
        f"**Status Proyek**: {project.status.upper()}  ",
        "",
        "---",
        "",
        "## 1. Deskripsi & Latar Belakang Penelitian",
        project.description or "Tidak ada deskripsi latar belakang penelitian.",
        "",
        "---",
        "",
        "## 2. Catatan & Analisis Riset (*Research Notes*)",
        "",
    ]

    if not notes:
        md_lines.append("_Belum ada catatan analisis dalam proyek riset ini._\n")
    else:
        for idx, note in enumerate(notes, start=1):
            tags_str = ""
            if note.tags_json:
                try:
                    tags = json.loads(note.tags_json)
                    if tags:
                        tags_str = f" `[Tags: {', '.join(tags)}]`"
                except Exception:
                    pass

            note_date = note.created_at.strftime("%d/%m/%Y %H:%M") if note.created_at else "-"
            md_lines.append(f"### Catatan #{idx} ({note_date}){tags_str}")
            md_lines.append(note.content)
            md_lines.append("")

    md_lines.extend([
        "---",
        "",
        "## 3. Anotasi & Telaah Teks (*Text Highlights & Annotations*)",
        "",
    ])

    if not annotations:
        md_lines.append("_Belum ada anotasi teks dalam proyek riset ini._\n")
    else:
        for idx, ann in enumerate(annotations, start=1):
            ann_date = ann.created_at.strftime("%d/%m/%Y %H:%M") if ann.created_at else "-"
            md_lines.append(f"### Anotasi #{idx} [{ann.annotation_type}] — {ann_date}")
            md_lines.append("> **Kutipan Teks Asli / Matan**:")
            md_lines.append(f"> \"{ann.selected_text}\"")
            md_lines.append("")
            md_lines.append(f"**Telaah Peneliti**: {ann.comment}")
            md_lines.append("")

    md_lines.extend([
        "---",
        "",
        "## 4. Daftar Pustaka & Sitasi Dokumen Primer (*Bibliography*)",
        "",
    ])

    if not citations:
        md_lines.append("_Belum ada catatan sitasi terdaftar dalam proyek ini._\n")
    else:
        for idx, cit in enumerate(citations, start=1):
            vol_str = f", Jilid {cit.volume}" if cit.volume else ""
            page_str = f", Halaman {cit.printed_page}" if cit.printed_page else ""
            pdf_str = f" (PDF Hal. {cit.pdf_page})" if cit.pdf_page else ""
            
            md_lines.append(
                f"{idx}. {cit.author}. ({cit.work_title}). {cit.edition or 'Dar al-Ma\'rifah'}{vol_str}{page_str}{pdf_str}."
            )
            if cit.citation_text:
                md_lines.append(f"   - _Format Sitasi_: `{cit.citation_text}`")
            md_lines.append("")

    md_lines.extend([
        "---",
        "_Dokumen monograf ini diekspor secara otomatis oleh **Fathul Bari Research Workspace Studio (Tahap 10)**._"
    ])

    return "\n".join(md_lines)


def export_project_to_bibtex(
    project: ResearchProject,
    citations: list[ResearchCitation],
) -> str:
    """Menghasilkan file sitasi format BibTeX standar untuk Zotero/Mendeley."""
    bib_entries = []

    for idx, cit in enumerate(citations, start=1):
        clean_key = f"fathul_bari_{cit.volume or 1}_{cit.printed_page or idx}"
        
        pub = cit.edition or "Dar al-Ma'rifah"
        entry = [
            f"@incollection{{{clean_key},",
            f"  author    = {{{cit.author or 'Ibn Hajar al-Asqalani'}}},",
            f"  title     = {{{cit.work_title or 'Fathul Bari Syarah Shahih al-Bukhari'}}},",
            f"  booktitle = {{{cit.work_title or 'Fathul Bari'}}},",
            f"  publisher = {{{pub}}},",
            f"  volume    = {{{cit.volume or 1}}},",
            f"  pages     = {{{cit.printed_page or 1}}},",
            f"  year      = {{852}},",
            f"  note      = {{PDF Page: {cit.pdf_page or cit.printed_page or 1}; Project: {project.title}}},",
            f"}}",
        ]
        bib_entries.append("\n".join(entry))

    if not bib_entries:
        bib_entries.append(
            f"@book{{fathul_bari_general,\n  author = {{Ibn Hajar al-Asqalani}},\n  title = {{Fathul Bari Syarah Shahih al-Bukhari}},\n  publisher = {{Dar al-Ma'rifah}},\n  year = {{852}},\n  note = {{Project: {project.title}}}\n}}"
        )

    return "\n\n".join(bib_entries)


def export_project_to_ris(
    project: ResearchProject,
    citations: list[ResearchCitation],
) -> str:
    """Menghasilkan format RIS untuk aplikasi manajer referensi (EndNote, Zotero, Mendeley)."""
    ris_entries = []

    for cit in citations:
        entry = [
            "TY  - CHAP",
            f"AU  - {cit.author or 'Ibn Hajar al-Asqalani'}",
            f"TI  - {cit.work_title or 'Fathul Bari Syarah Shahih al-Bukhari'}",
            f"T2  - Shahih al-Bukhari",
            f"PB  - {cit.edition or 'Dar al-Ma\'rifah'}",
            f"VL  - {cit.volume or 1}",
            f"SP  - {cit.printed_page or 1}",
            f"N1  - PDF Page: {cit.pdf_page or cit.printed_page or 1}; Project: {project.title}",
            "ER  - ",
        ]
        ris_entries.append("\n".join(entry))

    if not ris_entries:
        ris_entries.append(
            f"TY  - BOOK\nAU  - Ibn Hajar al-Asqalani\nTI  - Fathul Bari Syarah Shahih al-Bukhari\nPB  - Dar al-Ma'rifah\nN1  - Project: {project.title}\nER  - "
        )

    return "\n\n".join(ris_entries)


def export_project_to_json(
    project: ResearchProject,
    notes: list[ResearchNote],
    annotations: list[ResearchAnnotation],
    citations: list[ResearchCitation],
) -> dict[str, Any]:
    """Menghasilkan arsip riset terstruktur lengkap dalam format JSON."""
    return {
        "project": {
            "id": str(project.id),
            "title": project.title,
            "description": project.description,
            "created_by": project.created_by,
            "status": project.status,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        },
        "notes": [
            {
                "id": str(n.id),
                "content": n.content,
                "hadith_id": str(n.hadith_id) if n.hadith_id else None,
                "sharh_section_id": str(n.sharh_section_id) if n.sharh_section_id else None,
                "source_page_id": n.source_page_id,
                "tags": json.loads(n.tags_json) if n.tags_json else [],
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notes
        ],
        "annotations": [
            {
                "id": str(a.id),
                "selected_text": a.selected_text,
                "annotation_type": a.annotation_type,
                "comment": a.comment,
                "hadith_id": str(a.hadith_id) if a.hadith_id else None,
                "sharh_section_id": str(a.sharh_section_id) if a.sharh_section_id else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in annotations
        ],
        "citations": [
            {
                "id": str(c.id),
                "citation_text": c.citation_text,
                "work_title": c.work_title,
                "author": c.author,
                "edition": c.edition,
                "volume": c.volume,
                "printed_page": c.printed_page,
                "pdf_page": c.pdf_page,
                "source_file": c.source_file,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in citations
        ],
        "exported_at": datetime.utcnow().isoformat(),
    }
