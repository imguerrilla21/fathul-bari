"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  FileText,
  ShieldCheck,
  History,
  Download,
  Eye,
  ZoomIn,
  ZoomOut,
  Maximize2,
  CheckCircle2,
  XCircle,
  Clock,
  Layers,
  ArrowRight,
  BookOpen,
  Filter,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Search,
  Hash,
  UserCheck,
  AlertCircle,
  FileCheck,
  RefreshCw,
} from "lucide-react";
import { useToast } from "@/components/Toast";
import {
  getSourceSections,
  getSourceMetadata,
  getSharhAuditTrail,
  getRecentAudits,
} from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface LinkedHadith {
  link_id: string;
  hadith_id: string;
  hadith_number: number;
  confidence: number;
  verified: boolean;
  review_status: string;
  notes?: string;
}

interface SourceMetadata {
  sharh_id: string;
  work_slug: string;
  work_title: string;
  author: string;
  volume: number;
  printed_page: number;
  pdf_page: number;
  page: number;
  section_order: number;
  title: string;
  source_file: string;
  source_hash: string;
  source_document_path?: string;
  page_image_path?: string;
  pdf_available: boolean;
  pdf_filename?: string;
  pdf_size_bytes: number;
  pdf_size_mb: number;
  document_download_url: string;
  page_image_url: string;
  linked_hadiths: LinkedHadith[];
}

interface AuditEvent {
  id: string;
  action: string;
  actor: string;
  request_id?: string;
  before_state?: any;
  after_state?: any;
  notes?: string;
  created_at: string;
}

interface SectionItem {
  sharh_id: string;
  volume: number;
  printed_page: number;
  pdf_page?: number;
  section_order: number;
  title: string;
  arabic_snippet?: string;
  source_file?: string;
  pdf_available: boolean;
  verified: boolean;
  review_status: string;
  linked_hadith_numbers?: number[];
}

function SourceViewerContent() {
  const searchParams = useSearchParams();
  const initialSharhId = searchParams.get("sharh_id") || "";
  const initialVolume = searchParams.get("volume") ? parseInt(searchParams.get("volume")!) : 1;

  const { showToast } = useToast();
  const [sections, setSections] = useState<SectionItem[]>([]);
  const [selectedSectionId, setSelectedSectionId] = useState<string>(initialSharhId);
  const [metadata, setMetadata] = useState<SourceMetadata | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [recentAudits, setRecentAudits] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"image" | "text" | "audit" | "recent">("image");
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [selectedVolume, setSelectedVolume] = useState<number>(initialVolume);
  const [loading, setLoading] = useState<boolean>(true);
  const [imageLoading, setImageLoading] = useState<boolean>(true);
  const [auditLoading, setAuditLoading] = useState<boolean>(false);

  // Custom audit note state
  const [customNote, setCustomNote] = useState<string>("");
  const [customAction, setCustomAction] = useState<string>("CORRECTION");
  const [customActor, setCustomActor] = useState<string>("Dr. Ahmad Sanusi (Muhaqqiq)");
  const [submittingAudit, setSubmittingAudit] = useState<boolean>(false);

  // 1. Fetch available sections by volume
  useEffect(() => {
    async function loadSections() {
      try {
        setLoading(true);
        const data = await getSourceSections(selectedVolume || null, 100);
        if (data.sections && data.sections.length > 0) {
          setSections(data.sections);
          // Jika belum ada seksi terpilih, atau seksi saat ini tidak ada di list volume baru
          const currentExists = data.sections.some((s: SectionItem) => s.sharh_id === selectedSectionId);
          if (!selectedSectionId || !currentExists) {
            setSelectedSectionId(data.sections[0].sharh_id);
          }
        } else {
          setSections([]);
        }
      } catch (err) {
        console.error("Gagal memuat seksi sumber:", err);
      } finally {
        setLoading(false);
      }
    }
    loadSections();
  }, [selectedVolume]);

  // 2. Fetch Source Metadata & Section Audit Trail when selectedSectionId changes
  useEffect(() => {
    if (!selectedSectionId) return;

    async function fetchSourceDetails() {
      try {
        setAuditLoading(true);
        setImageLoading(true);
        const [metaData, auditData] = await Promise.all([
          getSourceMetadata(selectedSectionId),
          getSharhAuditTrail(selectedSectionId),
        ]);

        setMetadata(metaData);
        setAuditEvents(auditData.audit_trail || []);
      } catch (err) {
        console.error("Gagal mengambil metadata naskah sumber:", err);
      } finally {
        setAuditLoading(false);
      }
    }

    fetchSourceDetails();
  }, [selectedSectionId]);

  // 3. Fetch Recent Platform Audit logs
  useEffect(() => {
    async function fetchRecentAudits() {
      try {
        const data = await getRecentAudits(30);
        setRecentAudits(data.items || []);
      } catch (err) {
        console.error("Gagal mengambil log audit terbaru:", err);
      }
    }
    fetchRecentAudits();
  }, []);

  const handleCreateAuditEvent = async (linkId: string) => {
    if (!customNote.trim()) {
      showToast("Silakan isi catatan/alasan koreksi audit.", "error");
      return;
    }

    try {
      setSubmittingAudit(true);
      const res = await fetch(`${API_BASE}/api/v1/source/audit/link/${linkId}/event`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: customAction,
          actor: customActor,
          notes: customNote,
          request_id: crypto.randomUUID(),
        }),
      });

      if (res.ok) {
        showToast("Event audit baru berhasil dicatat (Immutable Trail).", "success");
        setCustomNote("");
        // Refresh audit trail
        const auditData = await getSharhAuditTrail(selectedSectionId);
        setAuditEvents(auditData.audit_trail || []);
        // Refresh recent audits
        const recData = await getRecentAudits(30);
        setRecentAudits(recData.items || []);
      } else {
        showToast("Gagal mencatat event audit.", "error");
      }
    } catch (err) {
      showToast("Terjadi kesalahan jaringan.", "error");
    } finally {
      setSubmittingAudit(false);
    }
  };

  const getActionBadgeColor = (action: string) => {
    switch (action.toUpperCase()) {
      case "VERIFY":
        return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
      case "REJECT":
        return "bg-rose-500/20 text-rose-300 border-rose-500/30";
      case "INGEST":
        return "bg-sky-500/20 text-sky-300 border-sky-500/30";
      case "CORRECTION":
        return "bg-amber-500/20 text-amber-300 border-amber-500/30";
      case "RESET":
        return "bg-purple-500/20 text-purple-300 border-purple-500/30";
      default:
        return "bg-slate-500/20 text-slate-300 border-slate-500/30";
    }
  };

  return (
    <div className="min-h-screen bg-[#071912] text-[#ecfdf5] pb-24">
      {/* Header Banner */}
      <div className="relative border-b border-[#133e30] bg-gradient-to-r from-[#0b281f] via-[#082018] to-[#0b281f] py-10 px-4 sm:px-6 lg:px-8 shadow-xl">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="px-3 py-1 text-xs font-semibold uppercase tracking-wider rounded-full bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/40">
                Tahap 6 — Source Viewer & Audit
              </span>
              <span className="flex items-center gap-1.5 text-xs text-[#6ee7b7]">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                High-Resolution Manuscript & PDF Stream
              </span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white flex items-center gap-3">
              <FileText className="w-9 h-9 text-[#f59e0b]" />
              Dokumen Sumber & Jejak Audit Naskah
            </h1>
            <p className="mt-2 text-sm sm:text-base text-[#a7f3d0]/80 max-w-2xl">
              Verifikasi lembar naskah otentik Fathul Bari (Ibnu Hajar al-Asqalani), inspeksi citra resolusi tinggi per halaman PDF, serta audit trail append-only yang akuntabel.
            </p>
          </div>

          {/* Quick Actions & Links */}
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/review"
              className="px-4 py-2.5 rounded-xl bg-[#10b981]/20 hover:bg-[#10b981]/30 border border-[#10b981]/40 text-[#a7f3d0] font-semibold text-sm transition-all flex items-center gap-2 shadow-lg"
            >
              <ShieldCheck className="w-4 h-4 text-[#10b981]" />
              Review Dashboard
            </Link>
            <Link
              href="/search"
              className="px-4 py-2.5 rounded-xl bg-[#133e30]/80 hover:bg-[#1a4a39] border border-[#2a6a53] text-[#ecfdf5] font-semibold text-sm transition-all flex items-center gap-2"
            >
              <Search className="w-4 h-4 text-[#f59e0b]" />
              Pencarian Hibrida
            </Link>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Sidebar: Section Selector & Metadata */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* Volume Filter & Section Picker */}
            <div className="bg-[#0b221a] border border-[#1a4a39] rounded-2xl p-5 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Layers className="w-5 h-5 text-[#f59e0b]" />
                  Pilih Seksi Naskah
                </h2>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#133e30] text-[#a7f3d0] border border-[#2a6a53]">
                  {sections.length} Halaman / Seksi
                </span>
              </div>

              {/* Volume Filter Buttons */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-2 mb-4 scrollbar-thin">
                {[1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13].map((vol) => (
                  <button
                    key={vol}
                    onClick={() => setSelectedVolume(vol)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all shrink-0 ${
                      selectedVolume === vol
                        ? "bg-[#f59e0b] text-[#071912] shadow-md shadow-[#f59e0b]/30 font-bold"
                        : "bg-[#133e30]/60 hover:bg-[#1a4a39] text-[#a7f3d0] border border-[#1a4a39]"
                    }`}
                  >
                    Jilid {vol}
                  </button>
                ))}
              </div>

              {/* Section List */}
              {loading ? (
                <div className="py-12 text-center text-xs text-[#a7f3d0]/60">
                  <div className="w-6 h-6 border-2 border-[#10b981] border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                  Memuat seksi naskah Jilid {selectedVolume}...
                </div>
              ) : sections.length > 0 ? (
                <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
                  {sections.map((item) => {
                    const isSelected = item.sharh_id === selectedSectionId;
                    return (
                      <button
                        key={item.sharh_id}
                        onClick={() => setSelectedSectionId(item.sharh_id)}
                        className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                          isSelected
                            ? "bg-gradient-to-r from-[#10b981]/25 to-[#064e3b]/40 border-[#10b981] shadow-lg shadow-[#10b981]/15"
                            : "bg-[#081d16] hover:bg-[#102e23] border-[#164233]"
                        }`}
                      >
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="font-semibold text-[#f59e0b]">
                            Jilid {item.volume} • Hal. {item.printed_page}
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              item.verified
                                ? "bg-emerald-500/20 text-emerald-300"
                                : item.review_status === "rejected"
                                ? "bg-rose-500/20 text-rose-300"
                                : "bg-amber-500/20 text-amber-300"
                            }`}
                          >
                            {item.verified ? "Verified ✓" : item.review_status || "Pending"}
                          </span>
                        </div>
                        <div className="text-xs text-[#ecfdf5] font-medium line-clamp-2 leading-relaxed">
                          {item.title}
                        </div>
                        {item.linked_hadith_numbers && item.linked_hadith_numbers.length > 0 && (
                          <div className="mt-2 text-[11px] text-[#6ee7b7] flex items-center gap-1.5">
                            <BookOpen className="w-3.5 h-3.5" />
                            Terkait Hadis #{item.linked_hadith_numbers.join(", #")}
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-[#a7f3d0]/60">
                  Tidak ada naskah untuk Jilid {selectedVolume}.
                </div>
              )}
            </div>

            {/* Primary Source Document Info Card */}
            {metadata && (
              <div className="bg-[#0b221a] border border-[#1a4a39] rounded-2xl p-5 shadow-xl space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-[#1a4a39] pb-3">
                  <FileCheck className="w-4 h-4 text-[#10b981]" />
                  Integritas Dokumen Primer
                </h3>

                <div className="space-y-2.5 text-xs">
                  <div className="flex justify-between py-1 border-b border-[#133e30]">
                    <span className="text-[#a7f3d0]/70">Kitab Rujukan:</span>
                    <span className="font-bold text-[#ecfdf5]">{metadata.work_title}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#133e30]">
                    <span className="text-[#a7f3d0]/70">Penyusun:</span>
                    <span className="text-[#ecfdf5]">{metadata.author}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#133e30]">
                    <span className="text-[#a7f3d0]/70">Volume & Halaman:</span>
                    <span className="font-semibold text-[#f59e0b]">
                      Jilid {metadata.volume} (Hal. Cetak: {metadata.printed_page || metadata.page})
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#133e30]">
                    <span className="text-[#a7f3d0]/70">Status PDF Asli:</span>
                    <span
                      className={`font-semibold flex items-center gap-1 ${
                        metadata.pdf_available ? "text-emerald-400" : "text-amber-400"
                      }`}
                    >
                      {metadata.pdf_available ? "Tersedia di Server" : "Arsip Digital"}
                    </span>
                  </div>
                  {metadata.pdf_filename && (
                    <div className="flex justify-between py-1 border-b border-[#133e30]">
                      <span className="text-[#a7f3d0]/70">Berkas PDF:</span>
                      <span className="font-mono text-[11px] text-[#6ee7b7]">{metadata.pdf_filename} ({metadata.pdf_size_mb} MB)</span>
                    </div>
                  )}
                  <div className="py-1">
                    <span className="text-[#a7f3d0]/70 block mb-1">SHA-256 Content Hash:</span>
                    <span className="font-mono text-[10px] text-[#94a3b8] bg-[#071912] px-2 py-1 rounded block truncate border border-[#133e30]">
                      {metadata.source_hash || "Calculated on Ingest"}
                    </span>
                  </div>
                </div>

                {/* PDF Download Button */}
                <a
                  href={`${API_BASE}${metadata.document_download_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full mt-3 py-2.5 px-4 rounded-xl bg-gradient-to-r from-[#f59e0b] to-[#d97706] text-[#071912] font-bold text-xs flex items-center justify-center gap-2 hover:opacity-95 transition-opacity shadow-lg shadow-[#f59e0b]/20"
                >
                  <Download className="w-4 h-4" />
                  Unduh Dokumen Sumber Asli (PDF/Text)
                </a>
              </div>
            )}

          </div>

          {/* Right Area: Viewer, Tabs, and Audit Trail */}
          <div className="lg:col-span-8 space-y-6">

            {/* Navigation Tabs & Controls */}
            <div className="bg-[#0b221a] border border-[#1a4a39] rounded-2xl p-2 flex flex-wrap items-center justify-between gap-3 shadow-xl">
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => setActiveTab("image")}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                    activeTab === "image"
                      ? "bg-[#10b981] text-[#071912] font-bold shadow-md shadow-[#10b981]/20"
                      : "text-[#a7f3d0] hover:bg-[#133e30]"
                  }`}
                >
                  <Eye className="w-4 h-4" />
                  Citra Naskah Visual (PNG)
                </button>
                <button
                  onClick={() => setActiveTab("text")}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                    activeTab === "text"
                      ? "bg-[#10b981] text-[#071912] font-bold shadow-md shadow-[#10b981]/20"
                      : "text-[#a7f3d0] hover:bg-[#133e30]"
                  }`}
                >
                  <FileText className="w-4 h-4" />
                  Transkripsi Teks Arab
                </button>
                <button
                  onClick={() => setActiveTab("audit")}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                    activeTab === "audit"
                      ? "bg-[#10b981] text-[#071912] font-bold shadow-md shadow-[#10b981]/20"
                      : "text-[#a7f3d0] hover:bg-[#133e30]"
                  }`}
                >
                  <History className="w-4 h-4" />
                  Audit Trail ({auditEvents.length})
                </button>
                <button
                  onClick={() => setActiveTab("recent")}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                    activeTab === "recent"
                      ? "bg-[#f59e0b] text-[#071912] font-bold shadow-md shadow-[#f59e0b]/20"
                      : "text-[#f59e0b] hover:bg-[#133e30]"
                  }`}
                >
                  <Clock className="w-4 h-4" />
                  Log Platform Terbaru
                </button>
              </div>

              {/* Zoom Controls (when image tab active) */}
              {activeTab === "image" && (
                <div className="flex items-center gap-2 bg-[#071912] px-3 py-1.5 rounded-xl border border-[#1a4a39] text-xs">
                  <button
                    onClick={() => setZoomLevel((z) => Math.max(40, z - 20))}
                    className="p-1 text-[#a7f3d0] hover:text-white transition-colors"
                    title="Perkecil"
                  >
                    <ZoomOut className="w-4 h-4" />
                  </button>
                  <span className="font-mono text-xs text-[#f59e0b] w-12 text-center font-bold">
                    {zoomLevel}%
                  </span>
                  <button
                    onClick={() => setZoomLevel((z) => Math.min(220, z + 20))}
                    className="p-1 text-[#a7f3d0] hover:text-white transition-colors"
                    title="Perbesar"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setZoomLevel(100)}
                    className="p-1 text-[#a7f3d0] hover:text-white transition-colors border-l border-[#1a4a39] pl-2"
                    title="Reset Zoom"
                  >
                    <Maximize2 className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            {/* TAB 1: Visual Manuscript Page Image Viewer */}
            {activeTab === "image" && (
              <div className="bg-[#0b221a] border border-[#1a4a39] rounded-2xl p-6 shadow-2xl space-y-4">
                <div className="flex items-center justify-between text-xs text-[#a7f3d0]/80 border-b border-[#1a4a39] pb-3">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span>High-Resolution Manuscript Rendered Engine (Tahap 6)</span>
                  </div>
                  {metadata && (
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-[#f59e0b]">
                        Jilid {metadata.volume} • Halaman {metadata.printed_page || metadata.page}
                      </span>
                      <a
                        href={`${API_BASE}/api/v1/source/sharh/${selectedSectionId}/page-image`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[#6ee7b7] hover:underline flex items-center gap-1"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        Tab Baru
                      </a>
                    </div>
                  )}
                </div>

                {selectedSectionId ? (
                  <div className="relative overflow-auto max-h-[700px] rounded-xl bg-[#071912] p-4 flex items-center justify-center border border-[#133e30] min-h-[480px]">
                    {imageLoading && (
                      <div className="absolute inset-0 bg-[#071912]/80 flex flex-col items-center justify-center text-xs text-[#a7f3d0] z-10 space-y-2">
                        <div className="w-8 h-8 border-3 border-[#10b981] border-t-transparent rounded-full animate-spin"></div>
                        <span>Merender lembar naskah resolusi tinggi...</span>
                      </div>
                    )}

                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      key={selectedSectionId}
                      src={`${API_BASE}/api/v1/source/sharh/${selectedSectionId}/page-image`}
                      alt={`Halaman Fathul Bari Jilid ${metadata?.volume || selectedVolume} Hal ${metadata?.printed_page || ""}`}
                      onLoad={() => setImageLoading(false)}
                      onError={() => {
                        setImageLoading(false);
                      }}
                      style={{ width: `${zoomLevel}%`, maxWidth: "none" }}
                      className="rounded-lg shadow-2xl transition-all duration-200 border border-[#2a6a53]/40"
                    />
                  </div>
                ) : (
                  <div className="h-72 flex flex-col items-center justify-center text-center text-[#a7f3d0]/60 space-y-2">
                    <FileText className="w-12 h-12 text-[#2a6a53]" />
                    <p>Pilih salah satu seksi di bilah kiri untuk menampilkan halaman naskah.</p>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: Arabic Transcribed Text */}
            {activeTab === "text" && metadata && (
              <div className="bg-[#0b221a] border border-[#1a4a39] rounded-2xl p-6 shadow-2xl space-y-6">
                <div>
                  <h3 className="text-base font-bold text-[#f59e0b] mb-1">{metadata.title}</h3>
                  <p className="text-xs text-[#a7f3d0]/70">
                    Fathul Bari Jilid {metadata.volume} Hal. {metadata.printed_page} • Sumber: {metadata.source_file}
                  </p>
                </div>

                {/* Arabic Text Display */}
                <div className="bg-[#071912] border border-[#1a4a39] rounded-xl p-6">
                  <div
                    className="font-arabic text-2xl text-[#fef3c7] leading-[2.6] text-right"
                    dir="rtl"
                  >
                    {sections.find((s) => s.sharh_id === selectedSectionId)?.arabic_snippet ||
                      "Teks ulasan naskah Fathul Bari sedang dimuat..."}
                  </div>
                </div>

                {/* Linked Hadiths */}
                {metadata.linked_hadiths && metadata.linked_hadiths.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-[#a7f3d0]">
                      Tautan Hadis Shahih Bukhari Terkait:
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {metadata.linked_hadiths.map((link) => (
                        <div
                          key={link.link_id}
                          className="bg-[#081d16] border border-[#164233] p-3.5 rounded-xl flex items-center justify-between"
                        >
                          <div>
                            <div className="font-bold text-sm text-white flex items-center gap-2">
                              <BookOpen className="w-4 h-4 text-[#10b981]" />
                              Shahih Bukhari #{link.hadith_number}
                            </div>
                            <div className="text-xs text-[#a7f3d0]/70 mt-1">
                              Confidence: {Math.round((link.confidence || 0) * 100)}%
                            </div>
                          </div>
                          <Link
                            href={`/hadith/${link.hadith_number}`}
                            className="p-2 rounded-lg bg-[#10b981]/20 hover:bg-[#10b981]/30 text-[#a7f3d0] transition-colors"
                            title="Buka Hadis"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </Link>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: Immutable Audit Trail Timeline */}
            {activeTab === "audit" && (
              <div className="space-y-6">
                
                {/* Timeline Header */}
                <div className="bg-[#0b221a] border border-[#1a4a39] rounded-2xl p-6 shadow-2xl">
                  <div className="flex items-center justify-between mb-6 pb-4 border-b border-[#1a4a39]">
                    <div>
                      <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <ShieldCheck className="w-5 h-5 text-emerald-400" />
                        Jejak Audit Seksi Ini ({auditEvents.length} Event)
                      </h3>
                      <p className="text-xs text-[#a7f3d0]/70 mt-1">
                        Catatan audit bersifat append-only; setiap keputusan, modifikasi, dan verifikasi terekam permanen.
                      </p>
                    </div>
                  </div>

                  {/* Audit Event Timeline */}
                  {auditEvents.length === 0 ? (
                    <div className="text-center py-10 text-[#a7f3d0]/60">
                      <History className="w-10 h-10 mx-auto mb-2 text-[#2a6a53]" />
                      <p>Belum ada event audit khusus untuk seksi ini.</p>
                    </div>
                  ) : (
                    <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-[#1a4a39]">
                      {auditEvents.map((ev, idx) => (
                        <div key={ev.id || idx} className="relative group">
                          {/* Dot indicator */}
                          <div className="absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full bg-[#10b981] border-2 border-[#071912]"></div>

                          <div className="bg-[#071912] border border-[#1a4a39] rounded-xl p-4 space-y-2">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`px-2.5 py-0.5 rounded-md text-xs font-bold border ${getActionBadgeColor(
                                    ev.action
                                  )}`}
                                >
                                  {ev.action}
                                </span>
                                <span className="text-xs font-semibold text-white flex items-center gap-1">
                                  <UserCheck className="w-3.5 h-3.5 text-[#f59e0b]" />
                                  {ev.actor}
                                </span>
                              </div>
                              <span className="text-[11px] text-[#94a3b8]">
                                {new Date(ev.created_at).toLocaleString("id-ID", {
                                  dateStyle: "medium",
                                  timeStyle: "medium",
                                })}
                              </span>
                            </div>

                            {ev.notes && (
                              <p className="text-xs text-[#ecfdf5] bg-[#0b221a] p-2.5 rounded-lg border border-[#133e30]">
                                {ev.notes}
                              </p>
                            )}

                            {ev.request_id && (
                              <div className="text-[10px] font-mono text-[#6ee7b7]/60">
                                Request-ID: {ev.request_id}
                              </div>
                            )}

                            {/* Before/After Diff Snapshot */}
                            {(ev.before_state || ev.after_state) && (
                              <details className="mt-2 text-[11px] text-[#a7f3d0]/80">
                                <summary className="cursor-pointer hover:text-[#f59e0b] font-semibold text-[10px] uppercase">
                                  Lihat Snapshot State (JSON)
                                </summary>
                                <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2 bg-[#05140e] p-2.5 rounded border border-[#133e30] font-mono text-[10px]">
                                  <div>
                                    <span className="text-rose-400 font-bold block mb-1">Before State:</span>
                                    <pre className="overflow-x-auto text-[#94a3b8]">
                                      {typeof ev.before_state === "object"
                                        ? JSON.stringify(ev.before_state, null, 2)
                                        : ev.before_state || "(null)"}
                                    </pre>
                                  </div>
                                  <div>
                                    <span className="text-emerald-400 font-bold block mb-1">After State:</span>
                                    <pre className="overflow-x-auto text-[#a7f3d0]">
                                      {typeof ev.after_state === "object"
                                        ? JSON.stringify(ev.after_state, null, 2)
                                        : ev.after_state || "(null)"}
                                    </pre>
                                  </div>
                                </div>
                              </details>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Form to Append New Audit Note / Correction */}
                {metadata?.linked_hadiths && metadata.linked_hadiths.length > 0 && (
                  <div className="bg-[#0b221a] border border-[#1a4a39] rounded-2xl p-6 shadow-2xl space-y-4">
                    <h4 className="text-sm font-bold text-white flex items-center gap-2 border-b border-[#1a4a39] pb-3">
                      <Sparkles className="w-4 h-4 text-[#f59e0b]" />
                      Tambah Catatan Audit / Koreksi Manual (Append-Only)
                    </h4>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-[#a7f3d0] mb-1">
                          Aksi / Kategori Audit:
                        </label>
                        <select
                          value={customAction}
                          onChange={(e) => setCustomAction(e.target.value)}
                          className="w-full bg-[#071912] border border-[#1a4a39] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-[#10b981]"
                        >
                          <option value="CORRECTION">CORRECTION (Koreksi Ilmiah)</option>
                          <option value="NOTE">NOTE (Catatan Tambahan Peneliti)</option>
                          <option value="SUPERSEDE">SUPERSEDE (Penggantian Keputusan)</option>
                          <option value="RE_VERIFY">RE_VERIFY (Verifikasi Ulang)</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-[#a7f3d0] mb-1">
                          Identitas Aktor Reviewer:
                        </label>
                        <input
                          type="text"
                          value={customActor}
                          onChange={(e) => setCustomActor(e.target.value)}
                          placeholder="Nama peneliti / reviewer..."
                          className="w-full bg-[#071912] border border-[#1a4a39] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-[#10b981]"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-[#a7f3d0] mb-1">
                        Catatan Keputusan / Alasan Ilmiah:
                      </label>
                      <textarea
                        rows={3}
                        value={customNote}
                        onChange={(e) => setCustomNote(e.target.value)}
                        placeholder="Tuliskan catatan kajian sanad, koreksi nomor halaman, atau justifikasi ilmiah..."
                        className="w-full bg-[#071912] border border-[#1a4a39] rounded-xl p-3 text-xs text-white focus:outline-none focus:border-[#10b981]"
                      />
                    </div>

                    <div className="flex justify-end">
                      <button
                        onClick={() => handleCreateAuditEvent(metadata.linked_hadiths[0].link_id)}
                        disabled={submittingAudit}
                        className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#10b981] to-[#059669] hover:from-[#059669] hover:to-[#047857] text-[#071912] font-bold text-xs flex items-center gap-2 shadow-lg shadow-[#10b981]/20 transition-all disabled:opacity-50"
                      >
                        <ShieldCheck className="w-4 h-4" />
                        {submittingAudit ? "Mencatat..." : "Simpan ke Audit Trail"}
                      </button>
                    </div>
                  </div>
                )}

              </div>
            )}

            {/* TAB 4: Recent Platform Audit Activity */}
            {activeTab === "recent" && (
              <div className="bg-[#0b221a] border border-[#1a4a39] rounded-2xl p-6 shadow-2xl space-y-4">
                <div className="flex items-center justify-between border-b border-[#1a4a39] pb-4">
                  <div>
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <Clock className="w-5 h-5 text-[#f59e0b]" />
                      Log Audit Platform Terbaru ({recentAudits.length} Event)
                    </h3>
                    <p className="text-xs text-[#a7f3d0]/70 mt-1">
                      Aktivitas seluruh reviewer, proses ingestion otomatis, dan keputusan kurasi penelitian.
                    </p>
                  </div>
                </div>

                <div className="divide-y divide-[#133e30] max-h-[620px] overflow-y-auto">
                  {recentAudits.map((item) => (
                    <div key={item.id} className="py-3.5 flex items-start justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getActionBadgeColor(
                              item.action
                            )}`}
                          >
                            {item.action}
                          </span>
                          <span className="text-xs font-semibold text-white">{item.actor}</span>
                          <span className="text-[11px] text-[#94a3b8]">
                            • Entity: <code className="font-mono text-[#6ee7b7]">{item.entity_type}</code>
                          </span>
                        </div>
                        {item.notes && (
                          <div className="text-xs text-[#ecfdf5]/90 pl-1">{item.notes}</div>
                        )}
                        {item.request_id && (
                          <div className="text-[10px] font-mono text-[#6ee7b7]/60 pl-1">
                            ReqID: {item.request_id}
                          </div>
                        )}
                      </div>
                      <span className="text-[11px] text-[#94a3b8] shrink-0 font-mono">
                        {new Date(item.created_at).toLocaleDateString("id-ID", {
                          day: "numeric",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>

        </div>
      </div>
    </div>
  );
}

export default function SourceViewerPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#071912] p-12 text-center text-[#a7f3d0]">
          Memuat Dokumen Sumber & Audit Trail...
        </div>
      }
    >
      <SourceViewerContent />
    </Suspense>
  );
}
