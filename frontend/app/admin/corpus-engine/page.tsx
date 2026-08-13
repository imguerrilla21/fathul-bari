"use client";

import React, { useState, useEffect } from "react";
import {
  Cpu,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Play,
  RefreshCw,
  Layers,
  FileCheck,
  Award,
  ShieldAlert,
  Sliders,
  Check,
  X,
  HelpCircle,
  BarChart2,
  Sparkles,
} from "lucide-react";

const API_BASE = "http://localhost:8000/api/v1";

interface CandidateItem {
  id: string;
  section_id: string | null;
  reference_text: string | null;
  reference_number: number | null;
  matn_text: string | null;
  narrator: string | null;
  status: string;
  rejection_reason: string | null;
  reviewer_note: string | null;
  score_breakdown: {
    reference_score: number;
    lexical_score: number;
    semantic_score: number;
    narrator_score: number;
    chapter_score: number;
    final_score: number;
  } | null;
}

interface QualityReport {
  volume: number;
  total_pages: number;
  good_ocr_pages: number;
  review_ocr_pages: number;
  sections_detected: number;
  total_hadith_candidates: number;
  confidence_breakdown: {
    high: number;
    medium: number;
    low: number;
  };
  verification_status: {
    verified: number;
    rejected: number;
    pending_review: number;
  };
  pipeline_version: string;
}

export default function CorpusEnginePage() {
  const [volume, setVolume] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);
  const [processing, setProcessing] = useState<boolean>(false);
  
  const [candidates, setCandidates] = useState<CandidateItem[]>([]);
  const [report, setReport] = useState<QualityReport | null>(null);
  const [goldenTestResult, setGoldenTestResult] = useState<any>(null);
  const [testingGolden, setTestingGolden] = useState<boolean>(false);

  // Rejection Modal State
  const [rejectingCandidateId, setRejectingCandidateId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState<string>("WRONG_HADITH");
  const [rejectionNote, setRejectionNote] = useState<string>("");

  const fetchData = async () => {
    setLoading(true);
    try {
      const [cRes, rRes] = await Promise.all([
        fetch(`${API_BASE}/corpus-engine/candidates?volume=${volume}`).then((r) => r.json()),
        fetch(`${API_BASE}/corpus-engine/quality-report/${volume}`).then((r) => r.json()),
      ]);

      if (Array.isArray(cRes)) setCandidates(cRes);
      if (rRes && rRes.volume) setReport(rRes);
    } catch (err) {
      console.error("Error fetching corpus engine data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [volume]);

  const handleRunEngine = async () => {
    setProcessing(true);
    try {
      const res = await fetch(`${API_BASE}/corpus-engine/process-document/doc-vol-${volume}?volume=${volume}`, {
        method: "POST",
      });
      await res.json();
      fetchData();
    } catch (err) {
      console.error("Engine execution error:", err);
    } finally {
      setProcessing(false);
    }
  };

  const handleVerify = async (candidateId: string) => {
    try {
      const res = await fetch(`${API_BASE}/corpus-engine/candidates/${candidateId}/verify`, {
        method: "POST",
      });
      await res.json();
      fetchData();
    } catch (err) {
      console.error("Verification error:", err);
    }
  };

  const handleConfirmReject = async () => {
    if (!rejectingCandidateId) return;
    try {
      const res = await fetch(`${API_BASE}/corpus-engine/candidates/${rejectingCandidateId}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reason: rejectionReason,
          note: rejectionNote,
        }),
      });
      await res.json();
      setRejectingCandidateId(null);
      setRejectionNote("");
      fetchData();
    } catch (err) {
      console.error("Rejection error:", err);
    }
  };

  const handleRunGoldenTest = async () => {
    setTestingGolden(true);
    try {
      const res = await fetch(`${API_BASE}/corpus-engine/golden-corpus/test`, {
        method: "POST",
      });
      const data = await res.json();
      setGoldenTestResult(data);
    } catch (err) {
      console.error("Golden Corpus test error:", err);
    } finally {
      setTestingGolden(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
            <Cpu className="w-4 h-4" /> Stage 14 — Corpus Processing Engine
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Corpus Engine & Candidate Match Verification
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Ekstraksi Penulis/Perawi, Matn Matching, Scoring 5 Komponen, dan Human Verification Workflow.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={volume}
            onChange={(e) => setVolume(Number(e.target.value))}
            className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
          >
            {Array.from({ length: 13 }, (_, i) => i + 1).map((v) => (
              <option key={v} value={v}>
                Fathul Bari Jilid {v}
              </option>
            ))}
          </select>

          <button
            onClick={handleRunEngine}
            disabled={processing}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-lg transition"
          >
            {processing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-white" />}
            {processing ? "Processing Engine..." : "Jalankan Engine"}
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        {/* Quality Audit Summary Cards */}
        {report && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
              <div className="text-xs font-semibold text-slate-400">Total Halaman & OCR Quality</div>
              <div className="text-2xl font-bold text-white mt-1">{report.total_pages} Halaman</div>
              <div className="text-xs text-emerald-400 font-semibold mt-2">
                {report.good_ocr_pages} Good | {report.review_ocr_pages} Review Needed
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
              <div className="text-xs font-semibold text-slate-400">Seksi Syarah Terdeteksi</div>
              <div className="text-2xl font-bold text-blue-400 mt-1">{report.sections_detected} Seksi</div>
              <div className="text-xs text-slate-400 mt-2">Struktur Hirarki Kitab & Bab</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
              <div className="text-xs font-semibold text-slate-400">Peringkat Confidence Kandidat</div>
              <div className="flex items-center gap-3 mt-2">
                <span className="text-emerald-400 font-bold text-sm">HIGH: {report.confidence_breakdown.high}</span>
                <span className="text-amber-400 font-bold text-sm">MED: {report.confidence_breakdown.medium}</span>
                <span className="text-red-400 font-bold text-sm">LOW: {report.confidence_breakdown.low}</span>
              </div>
              <div className="text-xs text-slate-400 mt-2">Pencocokan Hadis Ahmad Sanusi</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
              <div className="text-xs font-semibold text-slate-400">Human Verification Status</div>
              <div className="flex items-center gap-3 mt-2">
                <span className="text-purple-400 font-bold text-sm">VERIFIED: {report.verification_status.verified}</span>
                <span className="text-slate-400 font-bold text-sm">REJECTED: {report.verification_status.rejected}</span>
              </div>
              <div className="text-xs text-slate-400 mt-2">
                {report.verification_status.pending_review} Menunggu Review
              </div>
            </div>
          </div>
        )}

        {/* Candidate Hadith Review Queue */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-emerald-400" />
                Candidate Hadith Review Queue with Multi-Score Breakdown
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                AI menemukan kandidat; pakar manusia menetapkan hubungan terverifikasi ke Knowledge Graph.
              </p>
            </div>

            <button
              onClick={handleRunGoldenTest}
              disabled={testingGolden}
              className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-amber-300 text-xs font-semibold px-3 py-2 rounded-xl border border-slate-700 transition"
            >
              <Award className="w-4 h-4 text-amber-400" />
              {testingGolden ? "Running Test..." : "Uji Golden Corpus"}
            </button>
          </div>

          {/* Golden Test Result Banner */}
          {goldenTestResult && (
            <div className="bg-slate-950 border border-amber-800/60 rounded-xl p-4 text-xs space-y-2">
              <div className="flex items-center justify-between font-bold">
                <span className="text-amber-300 flex items-center gap-2">
                  <Award className="w-4 h-4" /> Golden Corpus Regression Benchmark Result
                </span>
                <span className="text-emerald-400 font-mono">
                  Akurasi: {goldenTestResult.accuracy_pct}% ({goldenTestResult.passed}/{goldenTestResult.total_items} Passed)
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                {goldenTestResult.details.map((d: any, idx: number) => (
                  <div key={idx} className="bg-slate-900 p-2 rounded border border-slate-800 flex justify-between">
                    <span className="text-slate-300">Hadis #{d.hadith_number}</span>
                    <span className={d.status === "PASS" ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                      {d.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Candidate Cards List */}
          <div className="space-y-4">
            {candidates.length === 0 ? (
              <div className="text-center py-12 text-slate-500 text-sm">
                Belum ada kandidat hadis terdeteksi. Silakan klik "Jalankan Engine".
              </div>
            ) : (
              candidates.map((cand) => (
                <div
                  key={cand.id}
                  className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-4 hover:border-slate-700 transition"
                >
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="bg-emerald-950 text-emerald-300 border border-emerald-800 text-xs px-2.5 py-0.5 rounded-full font-bold">
                          Kandidat Hadis #{cand.reference_number || "?"}
                        </span>
                        <span
                          className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${
                            cand.status === "VERIFIED"
                              ? "bg-purple-950/40 border-purple-800 text-purple-300"
                              : cand.status === "REJECTED"
                              ? "bg-red-950/40 border-red-800 text-red-300"
                              : "bg-blue-950/40 border-blue-800 text-blue-300"
                          }`}
                        >
                          {cand.status}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 font-semibold mt-1">
                        Perawi / Sanad: <span className="text-slate-200">{cand.narrator || "Tidak terdeteksi"}</span>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2">
                      {cand.status !== "VERIFIED" && (
                        <button
                          onClick={() => handleVerify(cand.id)}
                          className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg shadow transition"
                        >
                          <Check className="w-4 h-4" /> VERIFY
                        </button>
                      )}

                      {cand.status !== "REJECTED" && (
                        <button
                          onClick={() => setRejectingCandidateId(cand.id)}
                          className="flex items-center gap-1.5 bg-red-950 hover:bg-red-900 border border-red-800 text-red-300 text-xs font-semibold px-3 py-1.5 rounded-lg transition"
                        >
                          <X className="w-4 h-4" /> REJECT
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Matn & Reference Quote */}
                  <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs text-slate-300 font-arabic text-right leading-relaxed dir-rtl">
                    {cand.matn_text || cand.reference_text}
                  </div>

                  {/* Score Component Breakdown */}
                  {cand.score_breakdown && (
                    <div className="bg-slate-900/60 border border-slate-800/80 rounded-lg p-3 space-y-2">
                      <div className="flex items-center justify-between text-xs font-bold text-slate-300">
                        <span>Rincian Skor Pencocokan (Multi-Score Breakdown)</span>
                        <span className="text-emerald-400">
                          Final Score: {(cand.score_breakdown.final_score * 100).toFixed(1)}%
                        </span>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-[11px]">
                        <div>
                          <div className="text-slate-400">Reference</div>
                          <div className="font-bold text-slate-200">
                            {(cand.score_breakdown.reference_score * 100).toFixed(0)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-400">Lexical / BM25</div>
                          <div className="font-bold text-slate-200">
                            {(cand.score_breakdown.lexical_score * 100).toFixed(0)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-400">Semantic</div>
                          <div className="font-bold text-slate-200">
                            {(cand.score_breakdown.semantic_score * 100).toFixed(0)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-400">Narrator</div>
                          <div className="font-bold text-slate-200">
                            {(cand.score_breakdown.narrator_score * 100).toFixed(0)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-400">Chapter</div>
                          <div className="font-bold text-slate-200">
                            {(cand.score_breakdown.chapter_score * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {cand.rejection_reason && (
                    <div className="text-xs text-red-400 font-semibold bg-red-950/20 border border-red-900/40 p-2 rounded-lg">
                      Alasan Penolakan: {cand.rejection_reason} {cand.reviewer_note && `(${cand.reviewer_note})`}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Mandatory Rejection Reason Modal */}
      {rejectingCandidateId && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-red-400" />
              Alasan Penolakan Kandidat Hadis
            </h3>
            <p className="text-xs text-slate-400">
              Pilih alasan penolakan untuk mencatat riwayat audit trail peninjau manusia.
            </p>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Kode Alasan Penolakan</label>
              <select
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-red-500"
              >
                <option value="WRONG_HADITH">WRONG_HADITH (Nomor Hadis Salah)</option>
                <option value="WRONG_MATN">WRONG_MATN (Matn Tidak Cocok)</option>
                <option value="WRONG_NARRATOR">WRONG_NARRATOR (Sanad / Perawi Salah)</option>
                <option value="FALSE_DETECTION">FALSE_DETECTION (Deteksi Palsu AI)</option>
                <option value="OCR_ERROR">OCR_ERROR (Kesalahan Teks OCR)</option>
                <option value="DUPLICATE">DUPLICATE (Kandidat Duplikat)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Catatan Peninjau (Opsional)</label>
              <textarea
                value={rejectionNote}
                onChange={(e) => setRejectionNote(e.target.value)}
                placeholder="Tuliskan catatan rinci untuk analisis kesalahan..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 h-20 focus:outline-none focus:border-red-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setRejectingCandidateId(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
              >
                Batal
              </button>
              <button
                onClick={handleConfirmReject}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-red-600 text-white hover:bg-red-500 transition shadow-lg"
              >
                Konfirmasi Penolakan
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
