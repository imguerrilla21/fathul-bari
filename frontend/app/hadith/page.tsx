"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Copy,
  Bot,
  Quote,
  Sparkles,
  Share2,
  CheckCircle2,
  Clock,
  ExternalLink,
} from "lucide-react";
import { getHadith, getSharhByHadith } from "@/lib/api";
import { Hadith, SharhSectionWithEvidence } from "@/lib/types";
import { useToast } from "@/components/Toast";
import CitationModal from "@/components/CitationModal";

function HadithReaderContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialNomor = parseInt(searchParams.get("nomor") || "1", 10) || 1;


  const [nomor, setNomor] = useState(initialNomor);
  const [inputNomor, setInputNomor] = useState(initialNomor.toString());
  const [hadith, setHadith] = useState<Hadith | null>(null);
  const [sharhSections, setSharhSections] = useState<SharhSectionWithEvidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [arabicFontSize, setArabicFontSize] = useState(28);
  const [isCitationOpen, setIsCitationOpen] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    async function loadHadithData() {
      setLoading(true);
      try {
        const [hData, sData] = await Promise.all([
          getHadith("shahih_bukhari", nomor).catch(() => null),
          getSharhByHadith("shahih_bukhari", nomor).catch(() => null),
        ]);

        setHadith(hData);
        setSharhSections(sData?.sharh_sections || []);
      } catch (err: any) {
        showToast(`Gagal memuat hadis #${nomor}: ${err.message}`, "error");
      } finally {
        setLoading(false);
      }
    }

    loadHadithData();
  }, [nomor]);

  const handleNomorSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseInt(inputNomor, 10);
    if (!isNaN(parsed) && parsed >= 1 && parsed <= 7008) {
      setNomor(parsed);
    } else {
      showToast("Nomor hadis harus antara 1 dan 7008", "warning");
    }
  };

  const nextHadith = () => {
    if (nomor < 7008) {
      setNomor(nomor + 1);
      setInputNomor((nomor + 1).toString());
    }
  };

  const prevHadith = () => {
    if (nomor > 1) {
      setNomor(nomor - 1);
      setInputNomor((nomor - 1).toString());
    }
  };

  const copyArabic = () => {
    if (hadith?.arab) {
      navigator.clipboard.writeText(hadith.arab);
      showToast("Teks Arab berhasil disalin!");
    }
  };

  const copyTranslation = () => {
    if (hadith?.terjemah) {
      navigator.clipboard.writeText(hadith.terjemah);
      showToast("Terjemahan berhasil disalin!");
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      
      {/* Navigation Toolbar */}
      <div className="p-6 rounded-2xl bg-[#0b221a] border border-[#1a4a39] flex flex-wrap items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-extrabold text-xl text-[#ecfdf5] flex items-center gap-2">
              <span>Shahih al-Bukhari</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/30">
                Hadis #{nomor}
              </span>
            </h1>
            <p className="text-xs text-[#94a3b8]">
              Kitab Shahih al-Bukhari • Sumber: Ahmad Sanusi Hadits API
            </p>
          </div>
        </div>

        {/* Stepper & Number Search Form */}
        <div className="flex items-center gap-2">
          <button
            onClick={prevHadith}
            disabled={nomor <= 1 || loading}
            className="p-2.5 rounded-xl bg-[#081a13] border border-[#1a4a39] text-[#ecfdf5] hover:border-[#10b981] disabled:opacity-40 transition-colors"
            title="Hadis Sebelumnya"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>

          <form onSubmit={handleNomorSubmit} className="flex items-center gap-1.5">
            <input
              type="number"
              min={1}
              max={7008}
              value={inputNomor}
              onChange={(e) => setInputNomor(e.target.value)}
              className="w-20 px-3 py-2 rounded-xl bg-[#081a13] border border-[#1a4a39] text-center font-bold text-sm text-[#ecfdf5] focus:border-[#10b981] focus:outline-none"
            />
            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-[#10b981] hover:bg-[#0d9468] text-white font-bold text-xs shadow-md shadow-[#10b981]/20 transition-all"
            >
              Buka
            </button>
          </form>

          <button
            onClick={nextHadith}
            disabled={nomor >= 7008 || loading}
            className="p-2.5 rounded-xl bg-[#081a13] border border-[#1a4a39] text-[#ecfdf5] hover:border-[#10b981] disabled:opacity-40 transition-colors"
            title="Hadis Selanjutnya"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Main Hadith Card */}
      <div className="p-8 rounded-3xl bg-[#0b221a] border border-[#1a4a39] space-y-6 shadow-xl relative">
        
        {/* Controls Ribbon */}
        <div className="flex items-center justify-between flex-wrap gap-3 pb-4 border-b border-[#1a4a39]">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-[#94a3b8]">Ukuran Teks Arab:</span>
            <button
              onClick={() => setArabicFontSize(Math.max(20, arabicFontSize - 2))}
              className="px-2.5 py-1 rounded-lg bg-[#081a13] border border-[#1a4a39] text-xs font-bold text-[#ecfdf5] hover:border-[#10b981]"
            >
              A-
            </button>
            <span className="text-xs font-mono text-[#f59e0b] px-1">{arabicFontSize}px</span>
            <button
              onClick={() => setArabicFontSize(Math.min(44, arabicFontSize + 2))}
              className="px-2.5 py-1 rounded-lg bg-[#081a13] border border-[#1a4a39] text-xs font-bold text-[#ecfdf5] hover:border-[#10b981]"
            >
              A+
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={copyArabic}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#081a13] border border-[#1a4a39] text-xs font-semibold text-[#ecfdf5] hover:border-[#10b981] transition-colors"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>Salin Arab</span>
            </button>

            <button
              onClick={copyTranslation}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#081a13] border border-[#1a4a39] text-xs font-semibold text-[#ecfdf5] hover:border-[#10b981] transition-colors"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>Salin Terjemah</span>
            </button>

            <button
              onClick={() => setIsCitationOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#f59e0b]/15 border border-[#f59e0b]/30 text-xs font-bold text-[#f59e0b] hover:bg-[#f59e0b]/25 transition-colors"
            >
              <Quote className="w-3.5 h-3.5" />
              <span>Sitasi Ilmiah</span>
            </button>

            <button
              onClick={() => router.push(`/ai?q=Jelaskan+hadis+nomor+${nomor}&n=${nomor}`)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-[#10b981] hover:bg-[#0d9468] text-white text-xs font-bold shadow-md shadow-[#10b981]/20 transition-all hover:scale-105"
            >
              <Bot className="w-3.5 h-3.5" />
              <span>Tanya Syarah AI</span>
            </button>
          </div>
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="py-20 text-center text-[#94a3b8] space-y-3">
            <div className="w-8 h-8 rounded-full border-2 border-[#10b981] border-t-transparent animate-spin mx-auto" />
            <p className="text-sm font-medium">Memuat Hadis #{nomor} & Syarah Fathul Bari...</p>
          </div>
        ) : hadith ? (
          <>
            {/* Arabic Matan */}
            <div className="p-6 rounded-2xl bg-[#081a13] border border-[#1a4a39] border-r-4 border-r-[#f59e0b]">
              <p
                className="font-arabic text-right leading-loose text-[#fef3c7] select-text"
                dir="rtl"
                style={{ fontSize: `${arabicFontSize}px` }}
              >
                {hadith.arab}
              </p>
            </div>

            {/* Translation */}
            <div className="space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#94a3b8]">
                Terjemahan Bahasa Indonesia:
              </span>
              <p className="text-base text-[#ecfdf5] leading-relaxed select-text font-normal">
                {hadith.terjemah}
              </p>
            </div>

            {/* Provenance Footer */}
            <div className="flex items-center justify-between text-xs text-[#94a3b8] pt-4 border-t border-[#1a4a39] flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-[#10b981]">Sumber Provenance:</span>
                <span>{hadith.source?.type === "ahmad_sanusi" ? "Ahmad Sanusi Hadits API" : "Database Lokal"}</span>
                {hadith.source?.endpoint && <span className="font-mono text-[#6ee7b7]">({hadith.source.endpoint})</span>}
              </div>

              {hadith.source?.retrieved_at && (
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>Diambil: {new Date(hadith.source.retrieved_at).toLocaleDateString()}</span>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="py-16 text-center text-[#94a3b8] space-y-2">
            <p className="text-base font-semibold text-[#ecfdf5]">Hadis #{nomor} belum tersedia di database lokal.</p>
            <p className="text-xs">Sistem akan otomatis mencoba mengunduh dari Ahmad Sanusi API pada permintaan berikutnya.</p>
          </div>
        )}
      </div>

      {/* Syarah Fathul Bari Commentary Section */}
      <div className="p-8 rounded-3xl bg-[#0b221a] border border-[#1a4a39] space-y-6 shadow-xl">
        <div className="flex items-center justify-between flex-wrap gap-3 pb-4 border-b border-[#1a4a39]">
          <div className="flex items-center gap-3">
            <span className="text-2xl">📚</span>
            <div>
              <h2 className="text-lg font-bold text-[#f59e0b]">
                Syarah Fathul Bari (Al-Hafizh Ibnu Hajar al-Asqalani)
              </h2>
              <p className="text-xs text-[#94a3b8]">
                Penjelasan ilmiah dan perbandingan riwayat untuk Hadis #{nomor}
              </p>
            </div>
          </div>

          <span className="text-xs font-bold px-3 py-1 rounded-full bg-[#f59e0b]/15 text-[#f59e0b] border border-[#f59e0b]/30">
            {sharhSections.length} Bagian Syarah Tertaut
          </span>
        </div>

        {sharhSections.length === 0 ? (
          <div className="p-8 rounded-2xl bg-[#081a13] border border-[#1a4a39] text-center text-[#94a3b8] space-y-2">
            <p className="text-sm">Belum ada bagian Syarah Fathul Bari yang diverifikasi untuk Hadis #{nomor}.</p>
            <p className="text-xs text-[#6ee7b7]">
              Anda dapat menggunakan <b>Matching Studio</b> atau <b>Tahap 5 Review Dashboard</b> untuk menghubungkan syarah.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {sharhSections.map((sec, idx) => (
              <div
                key={sec.id || idx}
                className="p-6 rounded-2xl bg-[#081a13] border border-[#1a4a39] hover:border-[#f59e0b]/50 transition-all space-y-4"
              >
                <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-[#1a4a39]/70">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-[#f59e0b]">{sec.title}</span>
                    <span className="px-2 py-0.5 rounded-md bg-[#f59e0b]/20 text-[#f59e0b] text-xs font-semibold">
                      Jilid {sec.volume} • Hal. {sec.page}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {sec.verified ? (
                      <span className="px-2.5 py-0.5 rounded-full bg-[#10b981]/20 text-[#10b981] text-xs font-bold border border-[#10b981]/30 flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Human Verified</span>
                      </span>
                    ) : (
                      <span className="px-2.5 py-0.5 rounded-full bg-[#f59e0b]/20 text-[#f59e0b] text-xs font-bold border border-[#f59e0b]/30">
                        Confidence {((sec.confidence || 0) * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>

                {sec.arabic_text && (
                  <div className="p-4 rounded-xl bg-black/30 border border-[#1a4a39]">
                    <p className="font-arabic text-xl text-right leading-relaxed text-[#fde68a]" dir="rtl">
                      {sec.arabic_text}
                    </p>
                  </div>
                )}

                {sec.translation && (
                  <div className="text-sm text-[#ecfdf5] leading-relaxed">
                    <p className="font-semibold text-xs text-[#94a3b8] uppercase mb-1">Uraian Makna Syarah:</p>
                    <p>{sec.translation}</p>
                  </div>
                )}

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={() => setIsCitationOpen(true)}
                    className="flex items-center gap-1.5 text-xs font-bold text-[#f59e0b] hover:text-[#fef3c7]"
                  >
                    <Quote className="w-3.5 h-3.5" />
                    <span>Salin Sitasi Bagian Ini</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Citation Modal Popup */}
      <CitationModal
        isOpen={isCitationOpen}
        onClose={() => setIsCitationOpen(false)}
        hadithNumber={nomor}
        collectionName="Shahih al-Bukhari"
        volume={sharhSections[0]?.volume || 1}
        page={sharhSections[0]?.page || 9}
        sharhTitle={sharhSections[0]?.title}
        arabicExcerpt={hadith?.arab?.slice(0, 80)}
      />

    </div>
  );
}

export default function HadithReaderPage() {
  return (
    <Suspense
      fallback={
        <div className="py-20 text-center text-[#94a3b8]">
          <div className="w-8 h-8 rounded-full border-2 border-[#10b981] border-t-transparent animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium">Memuat Pembaca Hadis...</p>
        </div>
      }
    >
      <HadithReaderContent />
    </Suspense>
  );
}

