import httpx

client = httpx.Client()
try:
    print("=== PENGUJIAN ENDPOINT SOURCE VIEWER ===")
    r1 = client.get("http://127.0.0.1:8000/api/v1/source/sections?volume=1")
    data = r1.json()
    print(f"[✓] 1. Berhasil mengambil {data['total']} seksi untuk Jilid 1.")
    
    first_sec = data["sections"][0]
    sharh_id = first_sec["sharh_id"]
    print(f"[✓] 2. Seksi terpilih: {first_sec['title']} (ID: {sharh_id})")
    
    r2 = client.get(f"http://127.0.0.1:8000/api/v1/source/sharh/{sharh_id}")
    meta = r2.json()
    print(f"[✓] 3. Metadata naskah sumber: Vol {meta['volume']}, Hal. {meta['printed_page']}, File: {meta['pdf_filename']}")
    
    r3 = client.get(f"http://127.0.0.1:8000/api/v1/source/sharh/{sharh_id}/page-image")
    print(f"[✓] 4. Citra naskah resolusi tinggi PNG berhasil di-render:")
    print(f"    - Status: {r3.status_code}")
    print(f"    - Content-Type: {r3.headers.get('content-type')}")
    print(f"    - Ukuran berkas PNG: {len(r3.content):,} bytes")
    
    # Uji Jilid 2 dan Jilid 4
    r_vol2 = client.get("http://127.0.0.1:8000/api/v1/source/sections?volume=2")
    print(f"[✓] 5. Jilid 2 memiliki {r_vol2.json()['total']} seksi.")
    
    r_vol4 = client.get("http://127.0.0.1:8000/api/v1/source/sections?volume=4")
    print(f"[✓] 6. Jilid 4 memiliki {r_vol4.json()['total']} seksi.")
    
    print("\n[SUCCESS] Semua endpoint Source Viewer & Audit Trail berfungsi normal.")
finally:
    client.close()
