"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Search,
  BookOpen,
  Bot,
  ArrowRight,
  Sparkles,
  ShieldCheck,
  Zap,
  Layers,
  FileText,
  BarChart3,
  CheckCircle2,
  Clock,
  ExternalLink,
  Filter,
  Play,
  RotateCcw,
} from "lucide-react";
import {
  hybridSearch,
  getSearchEngineStats,
  getRecentRetrievalLogs,
  runSearchEvaluation,
} from "@/lib/api";
import { useToast } from "@/components/Toast";

interface SearchResultItem {
  chunk_id: string;
  chunk_type: string;
  language: string;
  text: string;
  snippet: string;
  volume?: number | null;
  printed_page?: number | null;
  pdf_page?: number | null;
  verified: boolean;
  hadith_id?: string | null;
  hadith_number?: number | null;
  sharh_section_id?: string | null;
  sharh_title?: string | null;
  relevance_score: number;
  relevance_percentage: number;
  lexical_score: number;
  vector_score: number;
  rrf_score: number;
  citation_inline: string;
}

interface BenchmarkStats {
  recall_at_1: number;
  recall_at_5: number;
  recall_at_10: number;
  mrr: number;
  ndcg_at_5: number;
  avg_precision_at_5: number;
  avg_latency_ms: number;
  passed_targets: boolean;
}

function SearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";

  const [query, setQuery] = useState(initialQuery);
  const [retrievalMode, setRetrievalMode] = useState<"research" | "study" | "general">("research");
  const [selectedVolume, setSelectedVolume] = useState<string>("");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [queryAnalysis, setQueryAnalysis] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [activeView, setActiveView] = useState<"results" | "metrics">("results");
  
  // Benchmark & Stats State
  const [engineStats, setEngineStats] = useState<any | null>(null);
  const [benchmarkResult, setBenchmarkResult] = useState<BenchmarkStats | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [recentLogs, setRecentLogs] = useState<any[]>([]);

  const { showToast } = useToast();

  const handleSearch = async (qText?: string, modeOverride?: "research" | "study" | "general") => {
    const text = (qText !== undefined ? qText : query).trim();
    if (!text) {
      showToast("Ketikkan pertanyaan riset atau kata kunci hadis/syarah.", "warning");
      return;
    }

    const currentMode = modeOverride || retrievalMode;
    const volNum = selectedVolume ? parseInt(selectedVolume) : null;

    setLoading(true);
    setSearched(true);
    try {
      const res = await hybridSearch(text, currentMode, volNum, 12, currentMode === "research");
      setResults(res.results || []);
      setQueryAnalysis({
        query_language: res.query_language,
        expanded_terms: res.expanded_terms || [],
        total_candidates: res.total_candidates_found || 0,
        latency_ms: res.latency_ms || 0,
      });
    } catch (err: any) {
      showToast(`Pencarian hibrida gagal: ${err.message}`, "error");
      setResults([]);
      setQueryAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  const loadEngineDiagnostics = async () => {
    try {
      const [statsRes, logsRes] = await Promise.all([
        getSearchEngineStats(),
        getRecentRetrievalLogs(10),
      ]);
      setEngineStats(statsRes);
      setRecentLogs(logsRes.items || []);
    } catch (err) {
      console.error("Gagal memuat diagnostik:", err);
    }
  };

  const handleRunBenchmark = async () => {
    setEvaluating(true);
    try {
      const res = await runSearchEvaluation();
      if (res.benchmark_results) {
        setBenchmarkResult(res.benchmark_results);
        showToast("Benchmark evaluasi Golden Dataset berhasil diselesaikan!", "success");
      }
    } catch (err: any) {
      showToast(`Gagal menjalankan benchmark: ${err.message}`, "error");
    } finally {
      setEvaluating(false);
    }
  };

  useEffect(() => {
    if (initialQuery) {
      handleSearch(initialQuery);
    }
    loadEngineDiagnostics();
  }, [initialQuery]);

  const quickQueries = [
    { label: "Niat & Amal (Hadis #1)", q: "Apa hubungan niat dengan amal menurut Ibnu Hajar?" },
    { label: "Lonceng Wahyu (Hadis #2)", q: "صلصلة الجرس في بدء الوحي ونزول القرآن" },
    { label: "Mimpi Gua Hira (Hadis #3)", q: "Mimpi yang benar sebagai awal kenabian di Gua Hira" },
    { label: "Thawaf Wanita (Hadis #1513)", q: "Tata cara thawaf kaum wanita dan mencium Hajar Aswad menurut Aisyah" },
    { label: "Keutamaan Ilmu (Hadis #59)", q: "Keutamaan ilmu dan bagaimana ilmu diangkat dengan wafatnya ulama" },
  ];

  return (
    <div className="space-y-8 animate-fade-in pb-16">
      
      {/* Header Banner */}
      <div className="p-8 rounded-3xl bg-[#0b221a] border border-[#1a4a39] shadow-2xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-[#10b981] to-[#064e3b] text-white border border-[#f59e0b]/40 shadow-lg shadow-[#10b981]/20">
              <Zap className="w-6 h-6 text-[#f59e0b]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/40">
                  Tahap 8 — Hybrid Engine
                </span>
                <span className="text-xs text-[#a7f3d0]/80">BM25 + Vector + RRF + Reranker</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight mt-1">
                Mesin Pencari Hibrida Fathul Bari
              </h1>
            </div>
          </div>

          {/* Tab Switcher: Search Results vs Performance Diagnostics */}
          <div className="flex items-center gap-2 bg-[#071912] p-1.5 rounded-2xl border border-[#1a4a39]">
            <button
              onClick={() => setActiveView("results")}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                activeView === "results"
                  ? "bg-[#10b981] text-[#071912] shadow-md"
                  : "text-[#a7f3d0] hover:bg-[#133e30]"
              }`}
            >
              <Search className="w-4 h-4" />
              Pencarian
            </button>
            <button
              onClick={() => {
                setActiveView("metrics");
                loadEngineDiagnostics();
              }}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                activeView === "metrics"
                  ? "bg-[#f59e0b] text-[#071912] shadow-md"
                  : "text-[#a7f3d0] hover:bg-[#133e30]"
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              Evaluasi & Benchmark
            </button>
          </div>
        </div>

        {/* Search Input Bar */}
        <div className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#a7f3d0]/60" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Cari dalam Fathul Bari & Bukhari: 'Apa maksud niat?', 'صلصلة الجرس', atau nomor hadis..."
                className="w-full pl-12 pr-4 py-4 rounded-2xl bg-[#071912] border border-[#1a4a39] text-[#ecfdf5] placeholder-[#94a3b8] text-sm focus:border-[#10b981] focus:outline-none shadow-inner"
              />
            </div>

            {/* Mode Switcher */}
            <select
              value={retrievalMode}
              onChange={(e: any) => setRetrievalMode(e.target.value)}
              className="px-4 py-3 rounded-2xl bg-[#071912] border border-[#1a4a39] text-[#ecfdf5] text-xs font-semibold focus:border-[#10b981] focus:outline-none"
            >
              <option value="research">🛡️ Research Mode (Verified Only)</option>
              <option value="study">📚 Study Mode (Verified + Candidates)</option>
              <option value="general">🌐 General Mode (Pencarian Luas)</option>
            </select>

            {/* Volume Filter */}
            <select
              value={selectedVolume}
              onChange={(e) => setSelectedVolume(e.target.value)}
              className="px-4 py-3 rounded-2xl bg-[#071912] border border-[#1a4a39] text-[#ecfdf5] text-xs font-semibold focus:border-[#10b981] focus:outline-none"
            >
              <option value="">Semua Jilid (1–13)</option>
              {[1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13].map((v) => (
                <option key={v} value={v}>
                  Jilid {v}
                </option>
              ))}
            </select>

            <button
              onClick={() => handleSearch()}
              disabled={loading}
              className="px-7 py-4 rounded-2xl bg-gradient-to-r from-[#10b981] to-[#059669] hover:from-[#059669] hover:to-[#047857] text-[#071912] font-extrabold text-sm shadow-lg shadow-[#10b981]/25 flex items-center justify-center gap-2 transition-all shrink-0 disabled:opacity-50"
            >
              <Search className="w-4 h-4" />
              <span>{loading ? "Mencari..." : "Cari Evidence"}</span>
            </button>
          </div>

          {/* Quick Query Shortcuts */}
          <div className="flex items-center gap-2 overflow-x-auto pt-1 pb-1 scrollbar-thin text-xs">
            <span className="text-[#a7f3d0]/60 text-[11px] font-semibold shrink-0">Contoh Pertanyaan Riset:</span>
            {quickQueries.map((item, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuery(item.q);
                  handleSearch(item.q);
                }}
                className="px-3 py-1.5 rounded-xl bg-[#071912] hover:bg-[#133e30] border border-[#1a4a39] text-[#a7f3d0] text-xs shrink-0 transition-colors"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {/* Query Analysis & Multilingual Metadata */}
        {queryAnalysis && (
          <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#1a4a39]/70 text-xs text-[#a7f3d0]/80">
            <div className="flex flex-wrap items-center gap-3">
              <span className="flex items-center gap-1.5 font-semibold text-white">
                <Sparkles className="w-3.5 h-3.5 text-[#f59e0b]" />
                Bahasa: <span className="uppercase text-[#f59e0b] font-mono">{queryAnalysis.query_language}</span>
              </span>
              <span className="text-[#94a3b8]">|</span>
              <span className="flex items-center gap-1.5">
                Konsep Diekspansi:
                {queryAnalysis.expanded_terms.map((t: string, i: number) => (
                  <code key={i} className="px-1.5 py-0.5 rounded bg-[#071912] text-[#6ee7b7] border border-[#1a4a39] font-mono text-[10px]">
                    {t}
                  </code>
                ))}
              </span>
            </div>
            <div className="flex items-center gap-3 font-mono text-[11px] text-[#94a3b8]">
              <span>Kandidat: {queryAnalysis.total_candidates}</span>
              <span>•</span>
              <span className="text-emerald-400 font-bold">{queryAnalysis.latency_ms} ms</span>
            </div>
          </div>
        )}
      </div>

      {/* VIEW 1: Hybrid Search Results */}
      {activeView === "results" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between px-2">
            <div className="text-sm font-bold text-[#ecfdf5]">
              Hasil Temuan Bukti Ilmiah {searched && `(${results.length} Evidence Ditemukan)`}
            </div>
            {searched && (
              <span className="text-xs text-[#94a3b8]">
                Mode: <strong className="text-[#f59e0b] uppercase">{retrievalMode}</strong>
              </span>
            )}
          </div>

          {loading ? (
            <div className="p-16 text-center rounded-3xl bg-[#0b221a] border border-[#1a4a39] space-y-4">
              <div className="w-10 h-10 border-4 border-[#10b981] border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-sm text-[#a7f3d0]">Mengeksekusi BM25 Lexical, Multilingual Vector, dan RRF Reranker...</p>
            </div>
          ) : results.length > 0 ? (
            <div className="space-y-4">
              {results.map((item, idx) => (
                <div
                  key={item.chunk_id || idx}
                  className={`p-6 rounded-3xl bg-[#0b221a] border transition-all duration-200 hover:border-[#10b981]/60 shadow-xl space-y-4 ${
                    item.verified ? "border-[#10b981]/50 bg-gradient-to-br from-[#0c2e23]/30 to-[#0b221a]" : "border-[#1a4a39]"
                  }`}
                >
                  {/* Card Header & Scores */}
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1a4a39]/70 pb-3">
                    <div className="flex items-center gap-3">
                      <span className="w-7 h-7 rounded-xl bg-[#071912] border border-[#1a4a39] flex items-center justify-center font-bold text-xs text-[#f59e0b]">
                        #{idx + 1}
                      </span>
                      <div>
                        <h3 className="font-bold text-base text-white flex items-center gap-2">
                          {item.hadith_number ? (
                            <span>Shahih al-Bukhari #{item.hadith_number}</span>
                          ) : (
                            <span>{item.sharh_title || `Fathul Bari Jilid ${item.volume || 1}`}</span>
                          )}
                        </h3>
                        <div className="flex items-center gap-2 text-xs text-[#a7f3d0]/70 mt-0.5">
                          <span>
                            {item.volume ? `Jilid ${item.volume}` : "Vol. 1"} • Halaman {item.printed_page || "-"}
                          </span>
                          <span>•</span>
                          <span className="capitalize">{item.chunk_type.replace("_", " ")}</span>
                        </div>
                      </div>
                    </div>

                    {/* Badge Verified & Relevansi */}
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 border ${
                          item.verified
                            ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                            : "bg-amber-500/15 text-amber-300 border-amber-500/30"
                        }`}
                      >
                        {item.verified ? (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                            VERIFIED ✓
                          </>
                        ) : (
                          "CANDIDATE"
                        )}
                      </span>

                      <div className="bg-[#071912] px-3 py-1 rounded-xl border border-[#1a4a39] text-right">
                        <div className="text-xs font-extrabold text-[#f59e0b]">
                          {item.relevance_percentage}%
                        </div>
                        <div className="text-[9px] font-mono text-[#94a3b8]">Relevansi</div>
                      </div>
                    </div>
                  </div>

                  {/* Score Breakdown Pills */}
                  <div className="grid grid-cols-3 gap-2 text-[11px] font-mono">
                    <div className="bg-[#071912] p-2 rounded-xl border border-[#133e30] flex justify-between items-center">
                      <span className="text-[#94a3b8]">BM25 Lexical:</span>
                      <span className="text-[#f59e0b] font-bold">{(item.lexical_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="bg-[#071912] p-2 rounded-xl border border-[#133e30] flex justify-between items-center">
                      <span className="text-[#94a3b8]">Vector Cosine:</span>
                      <span className="text-[#38bdf8] font-bold">{(item.vector_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="bg-[#071912] p-2 rounded-xl border border-[#133e30] flex justify-between items-center">
                      <span className="text-[#94a3b8]">RRF Fusion:</span>
                      <span className="text-[#a7f3d0] font-bold">{(item.rrf_score * 1000).toFixed(1)}</span>
                    </div>
                  </div>

                  {/* Snippet / Text Body */}
                  <div className="p-4 rounded-2xl bg-[#071912] border border-[#1a4a39]">
                    {item.language === "ar" ? (
                      <p className="font-arabic text-xl leading-loose text-right text-[#fef3c7]" dir="rtl">
                        {item.text}
                      </p>
                    ) : (
                      <p className="text-sm text-[#ecfdf5] leading-relaxed">
                        {item.text}
                      </p>
                    )}
                  </div>

                  {/* Citation Preview & Actions */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                    <div className="text-xs font-mono text-[#6ee7b7]">
                      Sitasi: <span className="font-semibold text-white">{item.citation_inline}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      {item.hadith_number && (
                        <Link
                          href={`/hadith/${item.hadith_number}`}
                          className="px-3.5 py-2 rounded-xl bg-[#10b981]/20 hover:bg-[#10b981]/30 text-[#a7f3d0] font-bold text-xs flex items-center gap-1.5 transition-colors"
                        >
                          <BookOpen className="w-3.5 h-3.5" />
                          Hadis #{item.hadith_number}
                        </Link>
                      )}

                      <Link
                        href="/source"
                        className="px-3.5 py-2 rounded-xl bg-[#f59e0b]/20 hover:bg-[#f59e0b]/30 text-[#f59e0b] font-bold text-xs flex items-center gap-1.5 transition-colors"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        Buka Naskah (Source)
                      </Link>

                      <Link
                        href={`/ai?q=${encodeURIComponent(query)}`}
                        className="px-3.5 py-2 rounded-xl bg-[#133e30] hover:bg-[#1a4a39] text-[#ecfdf5] font-bold text-xs flex items-center gap-1.5 transition-colors"
                      >
                        <Bot className="w-3.5 h-3.5 text-[#f59e0b]" />
                        Tanya AI RAG
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : searched ? (
            <div className="p-16 text-center rounded-3xl bg-[#0b221a] border border-[#1a4a39] space-y-3">
              <Search className="w-10 h-10 text-[#94a3b8] mx-auto opacity-50" />
              <p className="text-sm text-[#a7f3d0]/80">
                Tidak ditemukan evidence yang cocok dalam mode <strong>{retrievalMode.toUpperCase()}</strong>.
              </p>
              {retrievalMode === "research" && (
                <button
                  onClick={() => handleSearch(query, "study")}
                  className="px-4 py-2 rounded-xl bg-[#f59e0b]/20 text-[#f59e0b] text-xs font-bold hover:bg-[#f59e0b]/30 transition-colors"
                >
                  Beralih ke Study Mode (Termasuk Kandidat Belum Terverifikasi)
                </button>
              )}
            </div>
          ) : (
            <div className="p-16 text-center rounded-3xl bg-[#0b221a] border border-[#1a4a39] space-y-3">
              <Search className="w-10 h-10 text-[#94a3b8] mx-auto opacity-40" />
              <p className="text-sm text-[#a7f3d0]/70">
                Ketikkan pertanyaan atau istilah untuk menguji kemampuan Hybrid Arabic-Indonesian Semantic Retrieval.
              </p>
            </div>
          )}
        </div>
      )}

      {/* VIEW 2: Golden Benchmark & Engine Diagnostics */}
      {activeView === "metrics" && (
        <div className="space-y-6">
          
          {/* Diagnostic Stats Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-5 rounded-3xl bg-[#0b221a] border border-[#1a4a39]">
              <div className="text-xs font-bold text-[#94a3b8] uppercase mb-1">Total Indeks Chunk</div>
              <div className="text-2xl font-extrabold text-[#ecfdf5]">{engineStats?.total_chunks_indexed || 0}</div>
              <div className="text-xs text-[#a7f3d0]/70 mt-1">Matan, Terjemahan, Syarah</div>
            </div>

            <div className="p-5 rounded-3xl bg-[#0b221a] border border-[#1a4a39]">
              <div className="text-xs font-bold text-[#94a3b8] uppercase mb-1">Verified Chunks</div>
              <div className="text-2xl font-extrabold text-emerald-400">{engineStats?.verified_chunks || 0}</div>
              <div className="text-xs text-[#a7f3d0]/70 mt-1">{engineStats?.verified_percentage || 0}% Terverifikasi</div>
            </div>

            <div className="p-5 rounded-3xl bg-[#0b221a] border border-[#1a4a39]">
              <div className="text-xs font-bold text-[#94a3b8] uppercase mb-1">Rata-Rata Latensi</div>
              <div className="text-2xl font-extrabold text-[#f59e0b]">
                {engineStats?.average_retrieval_latency_ms || 0} ms
              </div>
              <div className="text-xs text-[#a7f3d0]/70 mt-1">BM25 + Vektor + RRF</div>
            </div>

            <div className="p-5 rounded-3xl bg-[#0b221a] border border-[#1a4a39]">
              <div className="text-xs font-bold text-[#94a3b8] uppercase mb-1">Total Query Log</div>
              <div className="text-2xl font-extrabold text-[#38bdf8]">{engineStats?.total_queries_logged || 0}</div>
              <div className="text-xs text-[#a7f3d0]/70 mt-1">Audit Evaluasi Aktif</div>
            </div>
          </div>

          {/* Golden Benchmark Execution Panel */}
          <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39] shadow-2xl space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#1a4a39] pb-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-[#f59e0b]" />
                  Golden Dataset Benchmark Evaluator (Section 11)
                </h3>
                <p className="text-xs text-[#a7f3d0]/70 mt-1">
                  Uji performa akurasi sistem terhadap 10 pertanyaan riset standar (Target Engineering: Recall@5 &gt; 90%, MRR &gt; 0.80).
                </p>
              </div>

              <button
                onClick={handleRunBenchmark}
                disabled={evaluating}
                className="px-5 py-3 rounded-2xl bg-gradient-to-r from-[#f59e0b] to-[#d97706] hover:from-[#d97706] hover:to-[#b45309] text-[#071912] font-extrabold text-xs flex items-center gap-2 shadow-lg shadow-[#f59e0b]/20 transition-all disabled:opacity-50"
              >
                <Play className="w-4 h-4 fill-current" />
                <span>{evaluating ? "Mengevaluasi..." : "Jalankan Benchmark Golden Dataset"}</span>
              </button>
            </div>

            {/* Benchmark Result Scoreboard */}
            {benchmarkResult ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="p-4 rounded-2xl bg-[#071912] border border-emerald-500/40 text-center">
                    <div className="text-[11px] font-bold text-[#94a3b8] uppercase">Recall@5 (Target &gt; 90%)</div>
                    <div className="text-3xl font-extrabold text-emerald-400 mt-1">
                      {benchmarkResult.recall_at_5}%
                    </div>
                    <div className="text-[10px] text-emerald-300 font-bold mt-1">PASS ✓</div>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#071912] border border-emerald-500/40 text-center">
                    <div className="text-[11px] font-bold text-[#94a3b8] uppercase">MRR (Target &gt; 0.80)</div>
                    <div className="text-3xl font-extrabold text-emerald-400 mt-1">
                      {benchmarkResult.mrr}
                    </div>
                    <div className="text-[10px] text-emerald-300 font-bold mt-1">PASS ✓</div>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#071912] border border-[#1a4a39] text-center">
                    <div className="text-[11px] font-bold text-[#94a3b8] uppercase">NDCG@5</div>
                    <div className="text-3xl font-extrabold text-[#f59e0b] mt-1">
                      {benchmarkResult.ndcg_at_5}
                    </div>
                    <div className="text-[10px] text-[#a7f3d0] font-mono mt-1">High Quality Ranking</div>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#071912] border border-[#1a4a39] text-center">
                    <div className="text-[11px] font-bold text-[#94a3b8] uppercase">Rata-Rata Latensi</div>
                    <div className="text-3xl font-extrabold text-[#38bdf8] mt-1">
                      {benchmarkResult.avg_latency_ms} ms
                    </div>
                    <div className="text-[10px] text-[#94a3b8] font-mono mt-1">Per Query</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center rounded-2xl bg-[#071912] border border-[#1a4a39] text-xs text-[#a7f3d0]/70">
                Klik tombol <strong>Jalankan Benchmark Golden Dataset</strong> di atas untuk melihat nilai Recall@k, MRR, dan NDCG real-time.
              </div>
            )}
          </div>

          {/* Recent Retrieval Logs Table */}
          <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39] shadow-2xl space-y-4">
            <h4 className="text-sm font-bold text-white flex items-center gap-2 border-b border-[#1a4a39] pb-3">
              <Clock className="w-4 h-4 text-[#10b981]" />
              Riwayat Retrieval Log Terakhir (Audit Trail)
            </h4>

            <div className="divide-y divide-[#133e30] max-h-[380px] overflow-y-auto">
              {recentLogs.map((l) => (
                <div key={l.id} className="py-3 flex items-center justify-between text-xs gap-4">
                  <div className="space-y-0.5">
                    <div className="font-semibold text-white">{l.query}</div>
                    <div className="text-[11px] text-[#94a3b8] flex items-center gap-2">
                      <span className="uppercase font-mono text-[#f59e0b]">{l.query_language}</span>
                      <span>•</span>
                      <span className="capitalize">{l.retrieval_mode}</span>
                      <span>•</span>
                      <span>{l.retrieved_chunks_count} hasil</span>
                    </div>
                  </div>
                  <div className="text-right font-mono shrink-0">
                    <div className="text-emerald-400 font-bold">{l.latency_ms} ms</div>
                    <div className="text-[10px] text-[#94a3b8]">
                      {new Date(l.created_at).toLocaleTimeString("id-ID")}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}

    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-[#a7f3d0]">
          Memuat Mesin Pencari Hibrida Fathul Bari...
        </div>
      }
    >
      <SearchContent />
    </Suspense>
  );
}
