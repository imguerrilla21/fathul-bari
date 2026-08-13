"use client";

import React, { useState, useEffect } from "react";
import {
  Layers,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Search,
  BookOpen,
  HelpCircle,
  Sparkles,
  ShieldAlert,
  Play,
  RotateCcw,
  Zap,
} from "lucide-react";

const API_BASE = "http://localhost:8000/api/v1";

interface CandidateMatch {
  id: string;
  hadith: {
    id: string;
    external_id: string;
    number: string;
    arabic_text: string;
  };
  sharh: {
    id: string;
    volume: number;
    page: number;
    arabic_text: string;
  };
  scores: {
    lexical: number;
    semantic: number;
    reference: number;
    context: number;
    confidence: number;
    band: "HIGH" | "MEDIUM" | "LOW" | "VERY_LOW";
  };
  status: "PENDING" | "VERIFIED" | "REJECTED" | "NEEDS_REVIEW" | "RELATED";
  match_type: string;
  matcher_version: string;
}

interface ExplanationData {
  matcher_version: string;
  overall_confidence: number;
  confidence_band: string;
  signals: {
    type: string;
    description: str;
    score: number;
    matched: boolean;
  }[];
  summary: string;
}

export default function MatchingEnginePage() {
  const [candidates, setCandidates] = useState<CandidateMatch[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateMatch | null>(null);
  const [explanation, setExplanation] = useState<ExplanationData | null>(null);

  const [filterBand, setFilterBand] = useState<string>("ALL");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");

  const [loading, setLoading] = useState<boolean>(true);
  const [runningJob, setRunningJob] = useState<boolean>(false);
  const [showExplanationModal, setShowExplanationModal] = useState<boolean>(false);

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/matching-engine/candidates?limit=20`;
      if (filterStatus !== "ALL") url += `&status=${filterStatus}`;
      if (filterBand !== "ALL") url += `&confidence_band=${filterBand}`;

      const res = await fetch(url);
      const data = await res.json();
      if (Array.isArray(data)) {
        setCandidates(data);
        if (data.length > 0) {
          setSelectedCandidate(data[0]);
        }
      }
    } catch (err) {
      console.error("Error fetching match candidates:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, [filterBand, filterStatus]);

  const handleRunMatching = async () => {
    setRunningJob(true);
    try {
      await fetch(`${API_BASE}/matching-engine/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ collection_slug: "bukhari" }),
      });
      fetchCandidates();
    } catch (err) {
      console.error("Run matching error:", err);
    } finally {
      setRunningJob(false);
    }
  };

  const handleVerify = async (matchId: string) => {
    try {
      await fetch(`${API_BASE}/matching-engine/${matchId}/verify`, { method: "POST" });
      fetchCandidates();
    } catch (err) {
      console.error("Verify error:", err);
    }
  };

  const handleReject = async (matchId: string) => {
    try {
      await fetch(`${API_BASE}/matching-engine/${matchId}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rejection_reason: "FALSE_DETECTION" }),
      });
      fetchCandidates();
    } catch (err) {
      console.error("Reject error:", err);
    }
  };

  const handleFetchExplanation = async (matchId: string) => {
    try {
      const res = await fetch(`${API_BASE}/matching-engine/${matchId}/explanation`);
      const data = await res.json();
      setExplanation(data);
      setShowExplanationModal(true);
    } catch (err) {
      console.error("Explanation error:", err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
            <Layers className="w-4 h-4" /> Stage 20 — Hadith ↔ Fathul Bari Matching Engine
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Hadith ↔ Fathul Bari Candidate Matcher & Review Queue
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Multi-Signal Scoring (Leksikal 30%, Semantik 35%, Referensi 20%, Konteks 15%), Rationale Explanation, dan Matcher Version 20.1.0.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunMatching}
            disabled={runningJob}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2.5 rounded-xl text-sm font-semibold shadow-lg transition"
          >
            {runningJob ? <Zap className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {runningJob ? "Matching..." : "Jalankan Matcher Engine"}
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        {/* Filters Bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <span className="text-xs font-semibold text-slate-400">Filter Status:</span>
            <div className="flex gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
              {(["ALL", "PENDING", "VERIFIED", "REJECTED"] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setFilterStatus(st)}
                  className={`px-3 py-1 rounded-lg font-bold transition ${
                    filterStatus === st ? "bg-emerald-600 text-white" : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-xs font-semibold text-slate-400">Filter Band:</span>
            <div className="flex gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
              {(["ALL", "HIGH", "MEDIUM", "LOW"] as const).map((bd) => (
                <button
                  key={bd}
                  onClick={() => setFilterBand(bd)}
                  className={`px-3 py-1 rounded-lg font-bold transition ${
                    filterBand === bd ? "bg-purple-600 text-white" : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {bd}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Candidates List */}
          <div className="lg:col-span-1 space-y-3">
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider">
              Antrean Kandidat Review ({candidates.length})
            </h2>

            {candidates.length === 0 ? (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center text-slate-500 text-xs">
                Tidak ada kandidat pencocokan dalam antrean.
              </div>
            ) : (
              candidates.map((c) => (
                <div
                  key={c.id}
                  onClick={() => setSelectedCandidate(c)}
                  className={`cursor-pointer bg-slate-900 border rounded-2xl p-4 transition space-y-3 ${
                    selectedCandidate?.id === c.id
                      ? "border-emerald-500 shadow-lg shadow-emerald-950/20"
                      : "border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-mono text-emerald-400 font-bold">[{c.hadith.external_id}]</span>
                    <span className={`px-2.5 py-0.5 rounded-full font-bold text-[10px] border ${
                      c.scores.band === "HIGH" ? "bg-emerald-950 text-emerald-400 border-emerald-800" :
                      c.scores.band === "MEDIUM" ? "bg-purple-950 text-purple-400 border-purple-800" :
                      "bg-amber-950 text-amber-400 border-amber-800"
                    }`}>
                      {c.scores.confidence * 100}% ({c.scores.band})
                    </span>
                  </div>

                  <p className="text-xs text-slate-200 dir-rtl font-arabic line-clamp-2 leading-relaxed">
                    {c.hadith.arabic_text}
                  </p>

                  <div className="flex items-center justify-between text-[10px] text-slate-500 border-t border-slate-800/60 pt-2">
                    <span>Fathul Bari Vol {c.sharh.volume}: Hlm {c.sharh.page}</span>
                    <span className="font-bold text-slate-400">{c.status}</span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Right Inspector & Rationale Details */}
          <div className="lg:col-span-2 space-y-6">
            {selectedCandidate ? (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
                <div className="flex justify-between items-start border-b border-slate-800 pb-4">
                  <div>
                    <span className="text-xs font-mono text-emerald-400 font-bold mb-1 block">
                      Matcher Version: {selectedCandidate.matcher_version}
                    </span>
                    <h3 className="text-xl font-bold text-white">
                      Hadis #{selectedCandidate.hadith.number} ↔ Fathul Bari Jilid {selectedCandidate.sharh.volume} Hlm {selectedCandidate.sharh.page}
                    </h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleFetchExplanation(selectedCandidate.id)}
                      className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-700 transition"
                    >
                      <HelpCircle className="w-3.5 h-3.5 text-purple-400" />
                      Why this match?
                    </button>
                  </div>
                </div>

                {/* Side-by-Side Text View */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2">
                    <span className="text-xs font-bold text-emerald-400">Teks Hadis Shahih Bukhari:</span>
                    <p className="text-xs text-slate-200 dir-rtl font-arabic leading-relaxed">
                      {selectedCandidate.hadith.arabic_text}
                    </p>
                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2">
                    <span className="text-xs font-bold text-blue-400">Teks Syarah Fathul Bari (Hlm {selectedCandidate.sharh.page}):</span>
                    <p className="text-xs text-slate-200 dir-rtl font-arabic leading-relaxed">
                      {selectedCandidate.sharh.arabic_text}
                    </p>
                  </div>
                </div>

                {/* 5-Component Signal Scores */}
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-3">
                  <h4 className="text-xs font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-2">
                    <Sparkles className="w-4 h-4 text-emerald-400" />
                    Perincian Skor Multi-Sinyal Hibrida
                  </h4>

                  <div className="space-y-3 text-xs">
                    <div>
                      <div className="flex justify-between text-slate-400 mb-1">
                        <span>Leksikal Arabic Normalization (30% Weight)</span>
                        <span className="font-bold text-slate-200">{(selectedCandidate.scores.lexical * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-emerald-500 h-full" style={{ width: `${selectedCandidate.scores.lexical * 100}%` }} />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-slate-400 mb-1">
                        <span>Semantik Vector HNSW (35% Weight)</span>
                        <span className="font-bold text-slate-200">{(selectedCandidate.scores.semantic * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-blue-500 h-full" style={{ width: `${selectedCandidate.scores.semantic * 100}%` }} />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-slate-400 mb-1">
                        <span>Pola Referensi & Nomor Hadis (20% Weight)</span>
                        <span className="font-bold text-slate-200">{(selectedCandidate.scores.reference * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-purple-500 h-full" style={{ width: `${selectedCandidate.scores.reference * 100}%` }} />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-slate-400 mb-1">
                        <span>Kesesuaian Konteks Bab (15% Weight)</span>
                        <span className="font-bold text-slate-200">{(selectedCandidate.scores.context * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-amber-500 h-full" style={{ width: `${selectedCandidate.scores.context * 100}%` }} />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Review Action Buttons */}
                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    onClick={() => handleReject(selectedCandidate.id)}
                    className="flex items-center gap-2 bg-rose-950 border border-rose-800 hover:bg-rose-900 text-rose-300 px-4 py-2.5 rounded-xl text-xs font-bold transition"
                  >
                    <XCircle className="w-4 h-4" /> Tolak (Reject)
                  </button>

                  <button
                    onClick={() => handleVerify(selectedCandidate.id)}
                    className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2.5 rounded-xl text-xs font-bold shadow-lg transition"
                  >
                    <CheckCircle2 className="w-4 h-4" /> Verifikasi (Verify Match)
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 text-sm">
                Pilih kandidat pencocokan di sebelah kiri untuk meninjau perincian skor multi-sinyal.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Rationale Explanation Modal */}
      {showExplanationModal && explanation && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-purple-400" />
                Why This Match? Rationale Explanation
              </h3>
              <button onClick={() => setShowExplanationModal(false)} className="text-slate-400 hover:text-white text-sm">
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-300">{explanation.summary}</p>

            <div className="space-y-2">
              {explanation.signals.map((sig, idx) => (
                <div key={idx} className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs space-y-1">
                  <div className="flex justify-between font-bold">
                    <span className="text-purple-400">{sig.type}</span>
                    <span className="text-emerald-400">Score: {(sig.score * 100).toFixed(0)}%</span>
                  </div>
                  <p className="text-slate-400 text-[11px]">{sig.description}</p>
                </div>
              ))}
            </div>

            <button
              onClick={() => setShowExplanationModal(false)}
              className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 py-2.5 rounded-xl text-xs font-bold border border-slate-700 transition"
            >
              Tutup Penjelasan
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
