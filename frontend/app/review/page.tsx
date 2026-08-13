"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  Search,
  Filter,
  ArrowRight,
  BookOpen,
  Quote,
  Check,
  ChevronRight,
  Sparkles,
  FileText,
} from "lucide-react";
import {
  getReviewQueue,
  verifyReviewLink,
  rejectReviewLink,
} from "@/lib/api";
import { ReviewQueueItem, ReviewStats } from "@/lib/types";
import { useToast } from "@/components/Toast";
import CitationModal from "@/components/CitationModal";

export default function ReviewDashboardPage() {
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [activeItem, setActiveItem] = useState<ReviewQueueItem | null>(null);
  const [statusFilter, setStatusFilter] = useState("pending");
  const [minConfFilter, setMinConfFilter] = useState("0.75");
  const [volumeFilter, setVolumeFilter] = useState("");
  const [searchFilter, setSearchFilter] = useState("");
  const [reviewerName, setReviewerName] = useState("Dr. Ahmad Sanusi (Muhaqqiq)");
  const [reviewNotes, setReviewNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [isCitationOpen, setIsCitationOpen] = useState(false);

  const { showToast } = useToast();

  const loadQueue = async () => {
    setLoading(true);
    try {
      const res = await getReviewQueue(
        statusFilter,
        parseFloat(minConfFilter) || 0.0,
        volumeFilter || undefined,
        searchFilter || undefined
      );
      setQueue(res.queue || []);
      setStats(res.stats || null);

      if (res.queue && res.queue.length > 0) {
        if (!activeItem || !res.queue.find((q) => q.link_id === activeItem.link_id)) {
          setActiveItem(res.queue[0]);
        }
      } else {
        setActiveItem(null);
      }
    } catch (err: any) {
      showToast(`Gagal memuat antrean review: ${err.message}`, "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [statusFilter, minConfFilter, volumeFilter]);

  const handleVerify = async () => {
    if (!activeItem) return;
    setActionLoading(true);
    try {
      await verifyReviewLink(activeItem.link_id, reviewNotes || undefined, reviewerName || undefined);
      showToast(`Kandidat Hadis #${activeItem.hadith_number} berhasil disetujui (Audit Log Recorded)!`);
      setReviewNotes("");
      loadQueue();
    } catch (err: any) {
      showToast(`Gagal memverifikasi: ${err.message}`, "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!activeItem) return;
    setActionLoading(true);
    try {
      await rejectReviewLink(activeItem.link_id, reviewNotes || undefined, reviewerName || undefined);
      showToast(`Kandidat Hadis #${activeItem.hadith_number} ditolak!`, "warning");
      setReviewNotes("");
      loadQueue();
    } catch (err: any) {
      showToast(`Gagal menolak: ${err.message}`, "error");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      
      {/* Overview Stats Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <div className="p-5 rounded-2xl bg-[#0b221a] border border-[#1a4a39]">
          <div className="text-xs font-bold text-[#94a3b8] uppercase tracking-wider mb-1">
            Total Antrean
          </div>
          <div className="text-2xl font-extrabold text-[#ecfdf5]">
            {stats?.total_links || 0}
          </div>
          <div className="text-xs text-[#94a3b8] mt-1">Kandidat Hadis–Syarah</div>
        </div>

        <div className="p-5 rounded-2xl bg-[#0b221a] border border-[#1a4a39]">
          <div className="text-xs font-bold text-[#f59e0b] uppercase tracking-wider mb-1">
            Menunggu Review
          </div>
          <div className="text-2xl font-extrabold text-[#f59e0b]">
            {stats?.pending_count || 0}
          </div>
          <div className="text-xs text-[#fde68a] mt-1">Perlu Keputusan Peneliti</div>
        </div>

        <div className="p-5 rounded-2xl bg-[#0b221a] border border-[#1a4a39]">
          <div className="text-xs font-bold text-[#10b981] uppercase tracking-wider mb-1">
            Disetujui
          </div>
          <div className="text-2xl font-extrabold text-[#10b981]">
            {stats?.verified_count || 0}
          </div>
          <div className="text-xs text-[#6ee7b7] mt-1">Human Verified</div>
        </div>

        <div className="p-5 rounded-2xl bg-[#0b221a] border border-[#1a4a39]">
          <div className="text-xs font-bold text-[#f43f5e] uppercase tracking-wider mb-1">
            Ditolak
          </div>
          <div className="text-2xl font-extrabold text-[#f43f5e]">
            {stats?.rejected_count || 0}
          </div>
          <div className="text-xs text-[#f43f5e] mt-1">Kandidat Tidak Sesuai</div>
        </div>

        <div className="p-5 rounded-2xl bg-[#0b221a] border border-[#1a4a39] col-span-2 sm:col-span-1">
          <div className="text-xs font-bold text-[#38bdf8] uppercase tracking-wider mb-1">
            Rata-Rata Confidence
          </div>
          <div className="text-2xl font-extrabold text-[#38bdf8]">
            {stats?.avg_confidence_percent || 0}%
          </div>
          <div className="text-xs text-[#38bdf8] mt-1">Skor Mesin Deterministic</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39] shadow-xl">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
          
          <div>
            <label className="text-xs font-bold text-[#94a3b8] uppercase tracking-wider block mb-2">
              Status Antrean:
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full p-2.5 rounded-xl bg-[#081a13] border border-[#1a4a39] text-xs font-semibold text-[#ecfdf5] focus:border-[#10b981] focus:outline-none"
            >
              <option value="pending">Menunggu Review (Pending)</option>
              <option value="verified">Disetujui (Verified)</option>
              <option value="rejected">Ditolak (Rejected)</option>
              <option value="all">Semua Status</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-bold text-[#94a3b8] uppercase tracking-wider block mb-2">
              Min. Confidence:
            </label>
            <select
              value={minConfFilter}
              onChange={(e) => setMinConfFilter(e.target.value)}
              className="w-full p-2.5 rounded-xl bg-[#081a13] border border-[#1a4a39] text-xs font-semibold text-[#ecfdf5] focus:border-[#10b981] focus:outline-none"
            >
              <option value="0.0">0.0 (Semua)</option>
              <option value="0.50">≥ 0.50 (Lemah & Kuat)</option>
              <option value="0.75">≥ 0.75 (Standar Review)</option>
              <option value="0.90">≥ 0.90 (Auto Candidate)</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-bold text-[#94a3b8] uppercase tracking-wider block mb-2">
              Jilid Fathul Bari:
            </label>
            <select
              value={volumeFilter}
              onChange={(e) => setVolumeFilter(e.target.value)}
              className="w-full p-2.5 rounded-xl bg-[#081a13] border border-[#1a4a39] text-xs font-semibold text-[#ecfdf5] focus:border-[#10b981] focus:outline-none"
            >
              <option value="">Semua Jilid</option>
              <option value="1">Jilid 1 (Wahyu & Iman)</option>
              <option value="2">Jilid 2 (Ilmu & Wudhu)</option>
              <option value="3">Jilid 3 (Shalat)</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-bold text-[#94a3b8] uppercase tracking-wider block mb-2">
              Cari Teks / Judul:
            </label>
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && loadQueue()}
              placeholder="No. hadis atau kata kunci..."
              className="w-full p-2.5 rounded-xl bg-[#081a13] border border-[#1a4a39] text-xs font-medium text-[#ecfdf5] placeholder-[#94a3b8] focus:border-[#10b981] focus:outline-none"
            />
          </div>

          <div>
            <button
              onClick={loadQueue}
              className="w-full py-2.5 rounded-xl bg-[#10b981] hover:bg-[#0d9468] text-white font-bold text-xs shadow-md shadow-[#10b981]/20 transition-all flex items-center justify-center gap-2"
            >
              <Filter className="w-3.5 h-3.5" />
              <span>Terapkan Filter</span>
            </button>
          </div>

        </div>
      </div>

      {/* Master-Detail Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: Queue List */}
        <div className="lg:col-span-4 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-sm text-[#ecfdf5] flex items-center gap-2">
              <span>📋</span> Daftar Antrean Review
            </h3>
            <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-[#10b981]/15 text-[#10b981]">
              {queue.length} item
            </span>
          </div>

          <div className="space-y-3 max-h-[75vh] overflow-y-auto pr-1">
            {loading ? (
              <div className="py-20 text-center text-[#94a3b8] space-y-2">
                <div className="w-6 h-6 rounded-full border-2 border-[#10b981] border-t-transparent animate-spin mx-auto" />
                <p className="text-xs">Memuat antrean...</p>
              </div>
            ) : queue.length === 0 ? (
              <div className="p-8 rounded-2xl bg-[#0b221a] border border-[#1a4a39] text-center text-[#94a3b8] space-y-2">
                <p className="text-sm font-semibold text-[#ecfdf5]">Tidak ada antrean yang cocok.</p>
                <p className="text-xs">Ubah filter status atau confidence untuk melihat kandidat lain.</p>
              </div>
            ) : (
              queue.map((item) => {
                const isActive = activeItem?.link_id === item.link_id;
                return (
                  <button
                    key={item.link_id}
                    onClick={() => setActiveItem(item)}
                    className={`w-full text-left p-4 rounded-2xl border transition-all block relative ${
                      isActive
                        ? "bg-[#0f2c22] border-[#10b981] shadow-lg shadow-[#10b981]/10 border-l-4 border-l-[#10b981]"
                        : "bg-[#0b221a] border-[#1a4a39] hover:border-[#10b981]/50 hover:bg-[#0f2c22]/50"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-xs text-[#10b981]">
                        Shahih Bukhari #{item.hadith_number}
                      </span>
                      <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/30">
                        {item.confidence_percent}%
                      </span>
                    </div>

                    <div className="text-xs font-bold text-[#ecfdf5] line-clamp-1 mb-1">
                      {item.sharh_title}
                    </div>

                    <div className="text-[11px] text-[#94a3b8] line-clamp-2 leading-relaxed">
                      {item.sharh_translation_snippet || item.hadith_translation_snippet}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Deep Inspector & Action Station */}
        <div className="lg:col-span-8 space-y-6">
          {!activeItem ? (
            <div className="p-16 rounded-3xl bg-[#0b221a] border border-[#1a4a39] text-center text-[#94a3b8] space-y-3 shadow-xl">
              <div className="text-4xl">🔍</div>
              <h3 className="font-bold text-base text-[#ecfdf5]">
                Pilih Kandidat dari Antrean
              </h3>
              <p className="text-xs max-w-md mx-auto leading-relaxed">
                Klik salah satu item antrean di sebelah kiri untuk memeriksa hubungan Matan Hadis ↔ Syarah Fathul Bari, rincian skor bukti, dan melakukan verifikasi.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              
              {/* Header & Score Card */}
              <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39] shadow-xl space-y-4">
                <div className="flex items-center justify-between flex-wrap gap-3 pb-4 border-b border-[#1a4a39]">
                  <div>
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#10b981]/20 text-[#10b981] border border-[#10b981]/30">
                        Shahih al-Bukhari #{activeItem.hadith_number}
                      </span>
                      <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/30">
                        Fathul Bari Jilid {activeItem.sharh_volume} • Hal. {activeItem.sharh_page}
                      </span>
                      <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#38bdf8]/20 text-[#38bdf8]">
                        Status: {activeItem.review_status.toUpperCase()}
                      </span>
                    </div>

                    <h2 className="text-lg font-bold text-[#f59e0b]">
                      {activeItem.sharh_title}
                    </h2>
                  </div>

                  <div className="text-right">
                    <div className="text-xs text-[#94a3b8]">Skor Confidence:</div>
                    <div className="text-3xl font-extrabold text-[#10b981]">
                      {activeItem.confidence_percent}%
                    </div>
                  </div>
                </div>

                {/* Evidence Signal Breakdown */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 rounded-xl bg-[#081a13] border border-[#1a4a39]">
                    <div className="text-[10px] font-bold text-[#94a3b8] uppercase">Number Match</div>
                    <div className="text-lg font-extrabold text-[#10b981]">
                      {(((activeItem.evidence?.number_score || 0) * 100)).toFixed(0)}%
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-[#081a13] border border-[#1a4a39]">
                    <div className="text-[10px] font-bold text-[#94a3b8] uppercase">Text Match</div>
                    <div className="text-lg font-extrabold text-[#f59e0b]">
                      {(((activeItem.evidence?.text_score || 0) * 100)).toFixed(0)}%
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-[#081a13] border border-[#1a4a39]">
                    <div className="text-[10px] font-bold text-[#94a3b8] uppercase">Context Match</div>
                    <div className="text-lg font-extrabold text-[#38bdf8]">
                      {(((activeItem.evidence?.context_score || 0) * 100)).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Matan Hadis Bukhari */}
              <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39] shadow-xl space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-[#1a4a39]/70">
                  <h3 className="font-bold text-sm text-[#ecfdf5] flex items-center gap-2">
                    <span>📖</span> 2. Matan Hadis Shahih al-Bukhari #{activeItem.hadith_number}
                  </h3>
                </div>

                <div className="p-4 rounded-xl bg-[#081a13] border border-[#1a4a39] border-r-4 border-r-[#f59e0b]">
                  <p className="font-arabic text-xl text-right leading-loose text-[#fef3c7]" dir="rtl">
                    {activeItem.hadith_arabic_snippet}
                  </p>
                </div>

                <div className="text-xs sm:text-sm text-[#ecfdf5] leading-relaxed">
                  <p className="font-semibold text-xs text-[#94a3b8] uppercase mb-1">Terjemahan:</p>
                  <p>{activeItem.hadith_translation_snippet}</p>
                </div>
              </div>

              {/* Syarah Fathul Bari Section */}
              <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39] shadow-xl space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-[#1a4a39]/70">
                  <h3 className="font-bold text-sm text-[#f59e0b] flex items-center gap-2">
                    <span>📚</span> 3. Teks Syarah Fathul Bari (Jilid {activeItem.sharh_volume} Hal. {activeItem.sharh_page})
                  </h3>
                </div>

                <div className="p-4 rounded-xl bg-[#081a13] border border-[#1a4a39]">
                  <p className="font-arabic text-xl text-right leading-loose text-[#fde68a]" dir="rtl">
                    {activeItem.sharh_arabic_snippet}
                  </p>
                </div>

                <div className="text-xs sm:text-sm text-[#ecfdf5] leading-relaxed">
                  <p className="font-semibold text-xs text-[#94a3b8] uppercase mb-1">Uraian Makna:</p>
                  <p>{activeItem.sharh_translation_snippet}</p>
                </div>
              </div>

              {/* Action Station */}
              <div className="p-6 rounded-3xl bg-gradient-to-br from-[#0f2c22] to-[#081a13] border border-[#10b981] shadow-2xl space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-sm text-[#ecfdf5] flex items-center gap-2">
                    <span>🛡️</span> 4. Stasiun Keputusan Reviewer Peneliti
                  </h3>

                  <div className="flex items-center gap-2">
                    <Link
                      href="/source"
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#10b981]/15 text-[#6ee7b7] border border-[#10b981]/30 text-xs font-bold hover:bg-[#10b981]/25 transition-colors"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Buka Naskah & Audit (Tahap 6)</span>
                    </Link>

                    <button
                      onClick={() => setIsCitationOpen(true)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#f59e0b]/15 text-[#f59e0b] border border-[#f59e0b]/30 text-xs font-bold hover:bg-[#f59e0b]/25 transition-colors"
                    >
                      <Quote className="w-3.5 h-3.5" />
                      <span>Salin Sitasi Akademik</span>
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-bold text-[#94a3b8] uppercase block mb-1.5">
                      Identitas Reviewer (X-Reviewer):
                    </label>
                    <input
                      type="text"
                      value={reviewerName}
                      onChange={(e) => setReviewerName(e.target.value)}
                      placeholder="Nama peneliti / verifikator..."
                      className="w-full p-3 rounded-xl bg-[#081a13] border border-[#1a4a39] text-xs text-[#ecfdf5] placeholder-[#94a3b8] focus:border-[#10b981] focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-[#94a3b8] uppercase block mb-1.5">
                      Catatan Verifikasi Peneliti (Opsional):
                    </label>
                    <input
                      type="text"
                      value={reviewNotes}
                      onChange={(e) => setReviewNotes(e.target.value)}
                      placeholder="Contoh: Diverifikasi sesuai cetakan Darul Kutub al-Ilmiyyah hal. 9..."
                      className="w-full p-3 rounded-xl bg-[#081a13] border border-[#1a4a39] text-xs text-[#ecfdf5] placeholder-[#94a3b8] focus:border-[#10b981] focus:outline-none"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <button
                    onClick={handleVerify}
                    disabled={actionLoading}
                    className="flex-1 py-3 rounded-xl bg-[#10b981] hover:bg-[#0d9468] disabled:opacity-50 text-white font-bold text-sm shadow-lg shadow-[#10b981]/25 flex items-center justify-center gap-2 transition-all hover:scale-105"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Setujui (Verify / Audit Log)</span>
                  </button>

                  <button
                    onClick={handleReject}
                    disabled={actionLoading}
                    className="px-6 py-3 rounded-xl bg-[#f43f5e]/15 hover:bg-[#f43f5e]/25 text-[#f43f5e] border border-[#f43f5e]/40 font-bold text-sm transition-all"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Tolak (Reject)</span>
                  </button>
                </div>
              </div>

            </div>
          )}
        </div>

      </div>

      {/* Citation Modal */}
      {activeItem && (
        <CitationModal
          isOpen={isCitationOpen}
          onClose={() => setIsCitationOpen(false)}
          hadithNumber={activeItem.hadith_number}
          collectionName="Shahih al-Bukhari"
          volume={activeItem.sharh_volume}
          page={activeItem.sharh_page}
          sharhTitle={activeItem.sharh_title}
          arabicExcerpt={activeItem.hadith_arabic_snippet?.slice(0, 80)}
        />
      )}

    </div>
  );
}
