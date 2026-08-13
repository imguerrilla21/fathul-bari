import json
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Source, Collection, Hadith, SharhSection, HadithSharhLink

db = SessionLocal()

try:
    source = db.scalar(select(Source).where(Source.name == "Ahmad Sanusi Hadits API"))
    if not source:
        source = Source(
            name="Ahmad Sanusi Hadits API",
            source_type="api",
            base_url="https://api.ahmadsanusi.com",
            license="Open API",
            created_at=datetime.now(timezone.utc),
        )
        db.add(source)
        db.flush()
        print("[✓] Source 'Ahmad Sanusi Hadits API' dibuat.")
    else:
        print("[✓] Source 'Ahmad Sanusi Hadits API' sudah ada.")

    collection = db.scalar(select(Collection).where(Collection.slug == "shahih_bukhari"))
    if not collection:
        collection = Collection(
            slug="shahih_bukhari",
            name="Shahih al-Bukhari",
            language="id",
            total_expected=7008,
        )
        db.add(collection)
        db.flush()
        print("[✓] Collection 'Shahih al-Bukhari' dibuat (expected: 7008).")
    else:
        print(f"[✓] Collection '{collection.name}' sudah ada (expected: {collection.total_expected}).")

    # Sample Hadiths
    hadith_data = [
        (
            1,
            "حَدَّثَنَا الْحُمَيْدِيُّ عَبْدُ اللَّهِ بْنُ الزُّبَيْرِ قَالَ حَدَّثَنَا سُفْيَانُ قَالَ حَدَّثَنَا يَحْيَى بْنُ سَعِيدٍ الأَنْصَارِيُّ قَالَ أَخْبَرَنِي مُحَمَّدُ بْنُ إِبْرَاهِيمَ التَّيْمِيُّ أَنَّهُ سَمِعَ عَلْقَمَةَ بْنَ وَقَّاصٍ اللَّيْثِيَّ يَقُولُ سَمِعْتُ عُمَرَ بْنَ الْخَطَّابِ رَضِيَ اللَّهُ عَنْهُ عَلَى الْمِنْبَرِ قَالَ سَمِعْتُ رَسُولَ اللَّهِ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ يَقُولُ إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى فَمَنْ كَانَتْ هِجْرَتُهُ إِلَى دُنْيَا يُصِيبُهَا أَوْ إِلَى امْرَأَةٍ يَنْكِحُهَا فَهِجْرَتُهُ إِلَى مَا هَاجَرَ إِلَيْهِ",
            "Telah menceritakan kepada kami Al Humaidi Abdullah bin Az Zubair berkata, telah menceritakan kepada kami Sufyan yang berkata, telah menceritakan kepada kami Yahya bin Sa'id Al Anshari berkata, telah mengabarkan kepada kami Muhammad bin Ibrahim At Taimi, bahwa dia pernah mendengar Alqamah bin Waqqash Al Laitsi berkata; saya pernah mendengar Umar bin Al Khaththab di atas mimbar berkata; saya mendengar Rasulullah shallallahu 'alaihi wasallam bersabda: \"Semua perbuatan tergantung niatnya, dan (balasan) bagi tiap-tiap orang (tergantung) apa yang diniatkan; Barangsiapa niat hijrahnya karena dunia yang ingin digapainya atau karena seorang perempuan yang ingin dinikahinya, maka hijrahnya adalah kepada apa dia diniatkan.\""
        ),
        (
            2,
            "حَدَّثَنَا عَبْدُ اللَّهِ بْنُ يُوسُفَ قَالَ أَخْبَرَنَا مَالِكٌ عَنْ هِشَامِ بْنِ عُرْوَةَ عَنْ أَبِيهِ عَنْ عَائِشَةَ أُمِّ الْمُؤْمِنِينَ رَضِيَ اللَّهُ عَنْهَا أَنَّ الْحَارِثَ بْنَ هِشَامٍ رَضِيَ اللَّهُ عَنْهُ سَأَلَ رَسُولَ اللَّهِ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ فَقَالَ يَا رَسُولَ اللَّهِ كَيْفَ يَأْتِيكَ الْوَحْيُ فَقَالَ رَسُولُ اللَّهِ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ أَحْيَانًا يَأْتِينِي مِثْلَ صَلْصَلَةِ الْجَرَسِ وَهُوَ أَشَدُّهُ عَلَيَّ فَيُفْصَمُ عَنِّي وَقَدْ وَعَيْتُ عَنْهُ مَا قَالَ وَأَحْيَانًا يَتَمَثَّلُ لِيَ الْمَلَكُ رَجُلاً فَيُكَلِّمُنِي فَأَعِي مَا يَقُولُ",
            "Telah menceritakan kepada kami Abdullah bin Yusuf berkata, telah mengabarkan kepada kami Malik dari Hisyam bin Urwah dari bapaknya dari Aisyah Ummul Mukminin bahwa Al Harits bin Hisyam bertanya kepada Rasulullah: \"Wahai Rasulullah, bagaimana wahyu turun kepadamu?\" Beliau menjawab: \"Kadang datang seperti gemerincing lonceng, dan itu yang paling berat bagiku, lalu terlepas dariku dan aku telah menghafal apa yang disampaikannya. Dan kadang malaikat menjelma sebagai seorang laki-laki lalu berbicara kepadaku dan aku menghafal apa yang dikatakannya.\""
        ),
        (
            3,
            "حَدَّثَنَا يَحْيَى بْنُ بُكَيْرٍ قَالَ حَدَّثَنَا اللَّيْثُ عَنْ عُقَيْلٍ عَنِ ابْنِ شِهَابٍ عَنْ عُرْوَةَ بْنِ الزُّبَيْرِ عَنْ عَائِشَةَ أُمِّ الْمُؤْمِنِينَ أَنَّهَا قَالَتْ أَوَّلُ مَا بُدِئَ بِهِ رَسُولُ اللَّهِ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ مِنَ الْوَحْيِ الرُّؤْيَا الصَّالِحَةُ فِي النَّوْمِ فَكَانَ لاَ يَرَى رُؤْيَا إِلاَّ جَاءَتْ مِثْلَ فَلَقِ الصُّبْحِ ثُمَّ حُبِّبَ إِلَيْهِ الْخَلاَءُ وَكَانَ يَخْلُو بِغَارِ حِرَاءٍ فَيَتَحَنَّثُ فِيهِ",
            "Telah menceritakan kepada kami Yahya bin Bukair berkata, telah menceritakan kepada kami Al Laits dari Uqail dari Ibnu Syihab dari Urwah bin Az Zubair dari Aisyah Ummul Mukminin bahwa dia berkata: \"Awal mula wahyu yang datang kepada Rasulullah adalah mimpi yang benar dalam tidur. Beliau tidak melihat suatu mimpi melainkan datang seperti terangnya fajar subuh. Kemudian beliau dijadikan menyukai menyendiri, dan beliau menyendiri di Gua Hira beribadah di dalamnya beberapa malam...\""
        )
    ]

    for num, arab, trans in hadith_data:
        h = db.scalar(select(Hadith).where(
            Hadith.collection_id == collection.id,
            Hadith.external_number == num,
        ))
        if not h:
            h = Hadith(
                collection_id=collection.id,
                source_id=source.id,
                external_number=num,
                arabic_text=arab,
                translation=trans,
                retrieved_at=datetime.now(timezone.utc),
            )
            db.add(h)
            print(f"[✓] Hadis #{num} dibuat.")

    db.flush()

    # Sample Sharh Sections for Fathul Bari Volume 1
    sharh_sections_data = [
        (
            1, 9,
            "Syarah Hadis Pertama: Innamal A'malu bin-Niyyat (Penjelasan Permulaan Wahyu & Niat)",
            "قَوْلُهُ (إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ) أَيْ صِحَّةُ الأَعْمَالِ أَوْ كَمَالُهَا أَوْ قَبُولُهَا مَشْرُوطٌ بِالنِّيَّةِ. وَالنِّيَّةُ فِي اللُّغَةِ الْقَصْدُ، وَفِي الشَّرْعِ قَصْدُ الشَّيْءِ مُقْتَرِنًا بِفِعْلِهِ. وَقَدْ أَوْرَدَ الْمُصَنِّفُ رَحِمَهُ اللَّهُ هَذَا الْحَدِيثَ فِي صَدْرِ كِتَابِهِ لِيَكُونَ خُطْبَةً لَهُ، إِشَارَةً إِلَى أَنَّ كُلَّ عَمَلٍ لَا يُرَادُ بِهِ وَجْهُ اللَّهِ فَهُوَ بَاطِلٌ.",
            "Perkataan beliau 'Sesungguhnya amal-amal itu bergantung pada niat': Maksudnya sahnya amal, atau kesempurnaannya, atau diterimanya amal disyaratkan dengan adanya niat. Niat secara bahasa bermakna 'maksud/tujuan', sedangkan secara syariat adalah menyengaja suatu hal yang diiringi dengan perbuatannya. Al-Bukhari membawakan hadis ini di awal kitabnya sebagai khutbah (pembuka) kitab, sebagai isyarat bahwa setiap amal yang tidak ditujukan mengharap wajah Allah maka amal itu batil.",
            1, 0.95, "auto_candidate", True, "Diverifikasi secara editorial: Muqaddimah & Bab Permulaan Wahyu Hadis #1 Fathul Bari Jilid 1 hal. 9.",
            {"number_score": 1.0, "text_score": 0.88, "context_score": 0.0, "detected_numbers": [1], "quotes_found": ["إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ"]}
        ),
        (
            1, 24,
            "Syarah Hadis Kedua: Kaifa Ya'tikal Wahyu (Penjelasan Bunyi Gemerincing Lonceng & Rupa Malaikat)",
            "قَوْلُهُ (مِثْلَ صَلْصَلَةِ الْجَرَسِ) الصَّلْصَلَةُ فِي الأَصْلِ صَوْتُ وُقُوعِ الْحَدِيدِ بَعْضِهِ عَلَى بَعْضٍ. وَإِنَّمَا كَانَ أَشَدَّهُ عَلَيْهِ لِأَنَّهُ يَنْزِعُ عَنْهُ صِفَةَ الْبَشَرِيَّةِ وَيَتَّصِلُ بِالْمَلَكُوتِ الأَعْلَى فَيَثْقُلُ عَلَيْهِ ذَلِكَ ثِقَلًا شَدِيدًا. وَقَوْلُهُ (يَتَمَثَّلُ لِيَ الْمَلَكُ رَجُلًا) أَيْ يَصِيرُ عَلَى صُورَةِ رَجُلٍ لِيَسْهُلَ عَلَى النَّبِيِّ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ الأَخْذُ عَنْهُ.",
            "Perkataan beliau 'seperti gemerincing lonceng': Salsalah pada asalnya adalah suara besi yang saling beradu. Hal itu merupakan yang paling berat bagi beliau karena melepaskan sifat kemanusiaan dan terhubung langsung dengan alam malakut tertinggi sehingga terasa sangat berat. Dan sabda beliau 'malaikat menjelma sebagai seorang laki-laki' yaitu berubah menjadi rupa manusia agar memudahkan bagi Nabi mengambil wahyu darinya.",
            2, 0.85, "review", False, "Kandidat Review: Ditemukan kecocokan kutipan matan 'misl salsalatil jaras' dengan skor 85%.",
            {"number_score": 0.0, "text_score": 0.92, "context_score": 0.0, "detected_numbers": [], "quotes_found": ["مِثْلَ صَلْصَلَةِ الْجَرَسِ", "يَتَمَثَّلُ لِيَ الْمَلَكُ رَجُلًا"]}
        ),
        (
            1, 35,
            "Syarah Hadis Ketiga: Awwalu Ma Budi'a bihi ar-Ru'ya ash-Shalihah (Peristiwa Gua Hira & Turunnya Iqra)",
            "قَوْلُهُ (أَوَّلُ مَا بُدِئَ بِهِ) دَلِيلٌ عَلَى أَنَّ الرُّؤْيَا الصَّادِقَةَ كَانَتْ مُقَدِّمَةً لِلْيَقَظَةِ. وَكَانَ ذَلِكَ سِتَّةَ أَشْهُرٍ قَبْلَ نُزُولِ جِبْرِيلَ عَلَيْهِ السَّلَامُ بِالْقُرْآنِ فِي غَارِ حِرَاءٍ. وَالتَّحَنُّثُ هُوَ التَّعَبُّدُ وَهُوَ التَّخَلِّي عَنِ الإِثْمِ.",
            "Perkataan beliau 'Awal mula wahyu yang datang': Bukti bahwa mimpi yang benar merupakan mukadimah bagi wahyu dalam keadaan terjaga. Hal tersebut berlangsung selama enam bulan sebelum turunnya Jibril 'alaihissalam membawa Al-Qur'an di Gua Hira. Dan at-tahannuts maknanya adalah beribadah dan menjauhkan diri dari dosa.",
            3, 0.78, "review", False, "Kandidat Review: Ditemukan kemiripan teks pada mukadimah mimpi kenabian di Gua Hira.",
            {"number_score": 0.0, "text_score": 0.82, "context_score": 0.0, "detected_numbers": [], "quotes_found": ["أَوَّلُ مَا بُدِئَ بِهِ"]}
        ),
        (
            1, 42,
            "Syarah Bab Keutamaan Ilmu dan Kedudukan Sanad Hadis",
            "قَوْلُهُ (بَابُ فَضْلِ الْعِلْمِ) الْمُرَادُ بِهِ الْعِلْمُ الشَّرْعِيُّ الَّذِي يُفِيدُ مَعْرِفَةَ مَا يَجِبُ عَلَى الْمُكَلَّفِ مِنْ أَمْرِ دِينِهِ فِي عِبَادَاتِهِ وَمُعَامَلَاتِهِ، وَالْعِلْمُ بِاللَّهِ وَصِفَاتِهِ وَمَا يَجِبُ لَهُ مِنْ حُقُوقِ التَّوْحِيدِ.",
            "Perkataan beliau 'Bab Keutamaan Ilmu': Yang dimaksud adalah ilmu syar'i yang memberi faidah pemahaman atas apa yang diwajibkan bagi mukallaf menyangkut urusan agamanya dalam ibadah dan muamalah, serta ilmu tentang Allah dan sifat-sifat-Nya.",
            1, 0.58, "weak_match", False, "Kandidat Lemah (Weak Match): Tidak ditemukan penyebutan nomor hadis spesifik.",
            {"number_score": 0.0, "text_score": 0.45, "context_score": 0.0, "detected_numbers": [], "quotes_found": []}
        )
    ]

    for vol, page, title, arab, trans, target_hadith_num, conf, status, verified, notes, evidence in sharh_sections_data:
        sec = db.scalar(select(SharhSection).where(
            SharhSection.work_slug == "fathul_bari",
            SharhSection.volume == vol,
            SharhSection.page == page,
        ))
        if not sec:
            sec = SharhSection(
                work_slug="fathul_bari",
                volume=vol,
                printed_page=page,
                pdf_page=page,
                page=page,
                section_order=1,
                title=title,
                arabic_text=arab,
                translation=trans,
                extraction_status="verified" if verified else "segmented",
                created_at=datetime.now(timezone.utc),
            )
            db.add(sec)
            db.flush()
            print(f"[✓] SharhSection Fathul Bari Jilid {vol} Hal. {page} dibuat.")

        target_hadith = db.scalar(select(Hadith).where(
            Hadith.collection_id == collection.id,
            Hadith.external_number == target_hadith_num,
        ))

        if target_hadith and sec:
            link = db.scalar(select(HadithSharhLink).where(
                HadithSharhLink.hadith_id == target_hadith.id,
                HadithSharhLink.sharh_section_id == sec.id,
            ))
            if not link:
                link = HadithSharhLink(
                    hadith_id=target_hadith.id,
                    sharh_section_id=sec.id,
                    match_method="manual_editorial" if verified else "deterministic_v1",
                    confidence=conf,
                    review_status="verified" if verified else status,
                    verified=verified,
                    evidence=json.dumps(evidence, ensure_ascii=False),
                    notes=notes,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(link)
                print(f"[✓] Tautan Hadis #{target_hadith_num} ↔ Syarah Jilid {vol} Hal. {page} dikonfigurasi (conf: {conf}, status: {link.review_status}).")

    db.commit()
    print("\n[✓] Seed SELESAI dan BERHASIL!")
finally:
    db.close()
