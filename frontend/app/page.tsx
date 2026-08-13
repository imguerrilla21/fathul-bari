"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  BookOpen,
  Bot,
  ShieldCheck,
  Search,
  ArrowRight,
  Sparkles,
  BookMarked,
  CheckCircle2,
  Cpu,
  Layers,
} from "lucide-react";
import { getCollectionsSummary, getHadith, getSharhByHadith } from "@/lib/api";
import { CollectionSummary, Hadith, SharhSectionWithEvidence } from "@/lib/types";

export default function HomePage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [featuredHadith, setFeaturedHadith] = useState<Hadith | null>(null);
  const [featuredSharh, setFeaturedSharh] = useState<SharhSectionWithEvidence | null>(null);
  const [collections, setCollections] = useState<CollectionSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [hadithData, sharhData, colsData] = await Promise.all([
          getHadith("shahih_bukhari", 1).catch(() => null),
          getSharhByHadith("shahih_bukhari", 1).catch(() => null),
          getCollectionsSummary().catch(() => []),
        ]);

        if (hadithData) setFeaturedHadith(hadithData);
        if (sharhData && sharhData.sharh_sections && sharhData.sharh_sections.length > 0) {
          setFeaturedSharh(sharhData.sharh_sections[0]);
        }
        setCollections(colsData);
      } catch (err) {
        console.error("Error loading homepage data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadInitialData();
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const quickPrompts = [
    {
      title: "Hadis Niat & Ikhlas",
      query: "Jelaskan makna hadis Innamal a'malu bin-niyyat dan penjelasan Ibnu Hajar di Fathul Bari?",
      hadith: 1,
    },
    {
      title: "Turunnya Wahyu Seperti Lonceng",
      query: "Bagaimana penjelasan Fathul Bari mengenai suara gemerincing lonceng saat wahyu turun?",
      hadith: 2,
    },
    {
      title: "Mimpi Kenabian di Gua Hira",
      query: "Jelaskan tentang mimpi yang benar dan ibadah tahannuts di Gua Hira menurut Syarah Fathul Bari.",
      hadith: 3,
    },
  ];

  return (
    <div className="space-y-12 animate-fade-in">
      
      {/* Hero Section */}
      <section className="relative rounded-3xl bg-gradient-to-b from-[#0b221a] via-[#0f2c22] to-[#05130e] border border-[#1a4a39] p-8 md:p-12 overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#10b981]/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-[#f59e0b]/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#f59e0b]/15 border border-[#f59e0b]/30 text-[#f59e0b] text-xs font-bold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Platform Riset Turats Modern</span>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-[#ecfdf5] tracking-tight leading-tight">
            Penelitian Hadis <span className="text-[#10b981]">Shahih Bukhari</span> & Syarah <span className="text-[#f59e0b]">Fathul Bari</span>
          </h1>

          <p className="text-[#94a3b8] text-base sm:text-lg leading-relaxed">
            Eksplorasi matan hadis Arab, terjemahan Indonesia resmi Ahmad Sanusi API, serta penjelasan mendalam karya Al-Hafizh Ibnu Hajar al-Asqalani yang terintegrasi dengan <b>RAG AI Assistant</b> dan <b>Review Dashboard Ilmiah</b>.
          </p>

          {/* Search Bar in Hero */}
          <form onSubmit={handleSearchSubmit} className="flex gap-2 max-w-xl">
            <div className="relative flex-1">
              <Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-[#94a3b8]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Cari hadis atau topik (contoh: niat, wahyu, iman)..."
                className="w-full pl-12 pr-4 py-3.5 rounded-2xl bg-[#081a13] border border-[#1a4a39] text-[#ecfdf5] placeholder-[#94a3b8] focus:border-[#10b981] focus:outline-none focus:ring-2 focus:ring-[#10b981]/20 text-sm font-medium transition-all"
              />
            </div>
            <button
              type="submit"
              className="px-6 py-3.5 rounded-2xl bg-[#10b981] hover:bg-[#0d9468] text-white font-bold text-sm shadow-lg shadow-[#10b981]/25 flex items-center gap-2 transition-all hover:scale-105"
            >
              <span>Cari</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick AI Prompts */}
          <div className="pt-2">
            <span className="text-xs font-semibold text-[#94a3b8] block mb-2">
              💡 Pertanyaan Riset Cepat ke Syarah AI Assistant:
            </span>
            <div className="flex flex-wrap gap-2">
              {quickPrompts.map((p, idx) => (
                <Link
                  key={idx}
                  href={`/ai?q=${encodeURIComponent(p.query)}&n=${p.hadith}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#081a13] border border-[#1a4a39] text-xs font-medium text-[#ecfdf5] hover:border-[#f59e0b] hover:bg-[#0f2c22] transition-all"
                >
                  <Bot className="w-3.5 h-3.5 text-[#f59e0b]" />
                  <span>{p.title}</span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Metrics Ribbon */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-6 rounded-2xl bg-[#0b221a] border border-[#1a4a39] flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#94a3b8] mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Koleksi Primer</span>
            <BookOpen className="w-4 h-4 text-[#10b981]" />
          </div>
          <div className="text-2xl font-extrabold text-[#ecfdf5]">
            Shahih al-Bukhari
          </div>
          <div className="text-xs text-[#6ee7b7] mt-1">
            Target 7.008 Hadis Terindeks
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-[#0b221a] border border-[#1a4a39] flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#94a3b8] mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Syarah Utama</span>
            <BookMarked className="w-4 h-4 text-[#f59e0b]" />
          </div>
          <div className="text-2xl font-extrabold text-[#ecfdf5]">
            Fathul Bari
          </div>
          <div className="text-xs text-[#fde68a] mt-1">
            Al-Hafizh Ibnu Hajar al-Asqalani
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-[#0b221a] border border-[#1a4a39] flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#94a3b8] mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">AI Assistant (RAG)</span>
            <Bot className="w-4 h-4 text-[#38bdf8]" />
          </div>
          <div className="text-2xl font-extrabold text-[#ecfdf5]">
            Anti-Hallucination
          </div>
          <div className="text-xs text-[#38bdf8] mt-1">
            Validasi Sitasi Turats 100%
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-[#0b221a] border border-[#1a4a39] flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#94a3b8] mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Review Dashboard</span>
            <ShieldCheck className="w-4 h-4 text-[#10b981]" />
          </div>
          <div className="text-2xl font-extrabold text-[#ecfdf5]">
            Tahap 5 Ready
          </div>
          <div className="text-xs text-[#6ee7b7] mt-1">
            Human Verification Studio
          </div>
        </div>
      </section>

      {/* Featured Hadith & Fathul Bari Commentary */}
      <section className="p-8 rounded-3xl bg-[#0b221a] border border-[#1a4a39] space-y-6 shadow-xl">
        <div className="flex items-center justify-between flex-wrap gap-4 pb-4 border-b border-[#1a4a39]">
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 rounded-full bg-[#10b981]/20 text-[#10b981] font-bold text-xs border border-[#10b981]/30">
              Hadis Pilihan #1
            </span>
            <h2 className="text-xl font-bold text-[#ecfdf5]">
              Shahih al-Bukhari: Bab Permulaan Wahyu & Niat
            </h2>
          </div>

          <Link
            href="/hadith/1"
            className="inline-flex items-center gap-2 text-sm font-semibold text-[#10b981] hover:text-[#6ee7b7] transition-colors"
          >
            <span>Buka Pembaca Lengkap</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Arabic Matan */}
        <div className="p-6 rounded-2xl bg-[#081a13] border-r-4 border-[#f59e0b] border border-[#1a4a39]">
          <p className="font-arabic text-2xl sm:text-3xl text-right leading-loose text-[#fef3c7]" dir="rtl">
            {featuredHadith?.arab ||
              "حَدَّثَنَا الْحُمَيْدِيُّ عَبْدُ اللَّهِ بْنُ الزُّبَيْرِ قَالَ حَدَّثَنَا سُفْيَانُ قَالَ حَدَّثَنَا يَحْيَى بْنُ سَعِيدٍ الأَنْصَارِيُّ ... إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى"}
          </p>
        </div>

        {/* Translation */}
        <div className="text-sm sm:text-base text-[#ecfdf5] leading-relaxed">
          <p className="italic text-[#94a3b8] mb-1 font-semibold text-xs uppercase">Terjemahan Indonesia (Ahmad Sanusi API):</p>
          <p>
            {featuredHadith?.terjemah ||
              "Semua perbuatan tergantung niatnya, dan (balasan) bagi tiap-tiap orang (tergantung) apa yang diniatkan; Barangsiapa niat hijrahnya karena dunia yang ingin digapainya atau karena seorang perempuan yang ingin dinikahinya, maka hijrahnya adalah kepada apa dia diniatkan."}
          </p>
        </div>

        {/* Syarah Fathul Bari Excerpt Card */}
        <div className="p-6 rounded-2xl bg-gradient-to-b from-[#0f2c22] to-[#081a13] border border-[#f59e0b]/40 space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <span className="text-lg">📚</span>
              <h3 className="font-bold text-base text-[#f59e0b]">
                Syarah Fathul Bari — Al-Hafizh Ibnu Hajar al-Asqalani
              </h3>
              <span className="px-2 py-0.5 rounded-md bg-[#f59e0b]/20 text-[#f59e0b] text-xs font-semibold">
                Jilid {featuredSharh?.volume || 1} • Hal. {featuredSharh?.page || 9}
              </span>
            </div>

            <span className="px-2.5 py-1 rounded-full bg-[#10b981]/20 text-[#10b981] text-xs font-bold border border-[#10b981]/30 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Terverifikasi Peneliti</span>
            </span>
          </div>

          <div className="font-arabic text-lg text-right text-[#fde68a] leading-relaxed pt-2" dir="rtl">
            {featuredSharh?.arabic_text ||
              "قَوْلُهُ (إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ) أَيْ صِحَّةُ الأَعْمَالِ أَوْ كَمَالُهَا أَوْ قَبُولُهَا مَشْرُوطٌ بِالنِّيَّةِ. وَالنِّيَّةُ فِي اللُّغَةِ الْقَصْدُ..."}
          </div>

          <p className="text-xs sm:text-sm text-[#94a3b8] leading-relaxed pt-1">
            {featuredSharh?.translation ||
              "Perkataan beliau 'Sesungguhnya amal-amal itu bergantung pada niat': Maksudnya sahnya amal, atau kesempurnaannya, atau diterimanya amal disyaratkan dengan adanya niat. Niat secara bahasa bermakna 'maksud/tujuan'..."}
          </p>

          <div className="pt-2 flex justify-end">
            <Link
              href="/ai?q=Jelaskan+hadis+niat+menurut+Ibnu+Hajar&n=1"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#10b981]/20 hover:bg-[#10b981]/30 text-[#10b981] text-xs font-bold border border-[#10b981]/40 transition-colors"
            >
              <Bot className="w-4 h-4" />
              <span>Tanyakan Lebih Dalam ke Syarah AI</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Exploration Grid */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          href="/hadith"
          className="p-6 rounded-2xl bg-[#0b221a] border border-[#1a4a39] hover:border-[#10b981] transition-all hover:-translate-y-1 shadow-lg group block"
        >
          <div className="w-12 h-12 rounded-xl bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <BookOpen className="w-6 h-6" />
          </div>
          <h3 className="font-bold text-lg text-[#ecfdf5] mb-2 group-hover:text-[#10b981] transition-colors">
            Pembaca Hadis & Syarah
          </h3>
          <p className="text-xs text-[#94a3b8] leading-relaxed">
            Membaca hadis per nomor dengan slider font Arab, terjemahan Indonesia, dan penjelasan Fathul Bari per bab.
          </p>
        </Link>

        <Link
          href="/ai"
          className="p-6 rounded-2xl bg-[#0b221a] border border-[#1a4a39] hover:border-[#f59e0b] transition-all hover:-translate-y-1 shadow-lg group block"
        >
          <div className="w-12 h-12 rounded-xl bg-[#f59e0b]/15 text-[#f59e0b] border border-[#f59e0b]/30 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <Bot className="w-6 h-6" />
          </div>
          <h3 className="font-bold text-lg text-[#ecfdf5] mb-2 group-hover:text-[#f59e0b] transition-colors">
            Syarah AI Assistant (RAG)
          </h3>
          <p className="text-xs text-[#94a3b8] leading-relaxed">
            Asisten riset cerdas yang mensintesis pemahaman hadis dan syarah dengan aturan anti-halusinasi dan sitasi turats.
          </p>
        </Link>

        <Link
          href="/review"
          className="p-6 rounded-2xl bg-[#0b221a] border border-[#1a4a39] hover:border-[#38bdf8] transition-all hover:-translate-y-1 shadow-lg group block"
        >
          <div className="w-12 h-12 rounded-xl bg-[#38bdf8]/15 text-[#38bdf8] border border-[#38bdf8]/30 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h3 className="font-bold text-lg text-[#ecfdf5] mb-2 group-hover:text-[#38bdf8] transition-colors">
            Tahap 5 Review Dashboard
          </h3>
          <p className="text-xs text-[#94a3b8] leading-relaxed">
            Studio verifikasi manusia untuk memeriksa tautan Hadis ↔ Syarah, skor sinyal bukti, dan menyalin sitasi akademik.
          </p>
        </Link>
      </section>

    </div>
  );
}
