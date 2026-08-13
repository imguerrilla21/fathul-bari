import argparse
import json
from pathlib import Path

from app.services.hadith_reference_detector import detect_hadith_references


def main():
    parser = argparse.ArgumentParser(description="Deteksi Referensi Hadis dari Teks Fathul Bari")
    parser.add_argument("--input", type=str, default="data/fathul_bari/normalized/pages.json", help="File pages.json hasil normalisasi")
    parser.add_argument("--output", type=str, default="data/fathul_bari/normalized/references.json", help="Output file deteksi referensi")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[!] File {in_path} belum ada. Jalankan scripts/extract_fathul_bari.py terlebih dahulu.")
        return

    pages: list[dict] = json.loads(in_path.read_text(encoding="utf-8"))
    print(f"Mendeteksi referensi hadis dari {len(pages)} halaman...")

    all_refs = []
    for page in pages:
        raw = page.get("text", "")
        norm = page.get("normalized_text", "")
        refs = detect_hadith_references(raw, norm)
        if refs:
            all_refs.append({
                "page": page.get("pdf_page"),
                "references": [r.model_dump() for r in refs],
            })

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(all_refs, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[✓] Berhasil mendeteksi {sum(len(r['references']) for r in all_refs)} referensi pada {len(all_refs)} halaman.")
    print(f"[✓] Disimpan ke {out_path}")


if __name__ == "__main__":
    main()
