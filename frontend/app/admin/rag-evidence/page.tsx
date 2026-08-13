"use client";

import React, { useState } from "react";
import {
  Sparkles,
  Search,
  CheckCircle2,
  AlertTriangle,
  FileText,
  BookOpen,
  Layers,
  ArrowRight,
  ShieldCheck,
  Zap,
  HelpCircle,
  Hash,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import Link from "next/link";

const API_BASE = "http://localhost:8000/api/v1";

interface EvidenceItem {
  id: string;
  citation_code: string;
  volume: number;
  printed_page: number;
  pdf_page: number;
  text: string;
  retrieval_score: number;
  rank: number;
  content_hash: string;
}

interface ClaimItem {
  claim_text: string;
  citation_code: string;
  validation_status: "SUPPORTED" | "PARTIALLY_SUPPORTED" | "UNSUPPORTED";
  confidence: number;
}

interface RAGQueryResponse {
  query_id: string;
  question: string;
  intent: string;
  answer: string;
  evidence: EvidenceItem[];
  validation: {
    status: string;
    total_claims: number;
    supported_claims: number;
    claims: ClaimItem[];
  };
}

export default function RAGEvidencePage() {
  const [question, setQuestion] = useState<string>("Apa penjelasan Ibnu Hajar tentang niat dalam hadis إنما الأعمال بالنيات?");
  const [ragResult, setRagResult] = useState<RAGQueryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleRunRAGQuery = async (e?: React.FormEvent, customQ?: string) => {
    if (e) e.preventDefault();
    const queryToRun = customQ || question;
    if (!queryToRun) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/rag-engine/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: queryToRun }),
      });
      const data = await res.json();
      setRagResult(data);
    } catch (err) {
      console.error("RAG Query error:", err);
    } finally {
      setLoading(false);
    }
  };

  const presetQuestions = [
    "Apa penjelasan Ibnu Hajar tentang niat dalam hadis إنما الأعمال بالنيات?",
    "Mengapa Imam Bukhari membuka kitabnya dengan hadis niat?",
    "Apa perbedaan riwayat hadis tentang niat dalam Fathul Bari?",
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
            <Sparkles className="w-4 h-4" /> Stage 22 — RAG Evidence Engine
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Closed-Loop RAG Evidence Engine & Citation Inspector
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Validasi Sitasi Klaim (`✓ SUPPORTED`), Reranker Multi-Fitur, dan Tautan Langsung Sitasi `[FB-V1-P45-C003]` ke Source Viewer.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        {/* Question & Benchmark Input Bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <form onSubmit={handleRunRAGQuery} className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-4 top-3.5" />
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Tanyakan topik riset hadis atau penjelasan syarah Fathul Bari..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-3 rounded-xl text-sm font-semibold shadow-lg transition"
            >
              {loading ? <Zap className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              {loading ? "Menjalankan Pipeline..." : "Jalankan RAG Query"}
            </button>
          </form>

          {/* Benchmark Preset Buttons */}
          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
            <span className="text-slate-400 font-semibold">Pertanyaan Benchmark:</span>
            {presetQuestions.map((pq, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuestion(pq);
                  handleRunRAGQuery(undefined, pq);
                }}
                className="bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 px-3 py-1.5 rounded-lg transition"
              >
                {pq}
              </button>
            ))}
          </div>
        </div>

        {/* Results & RAG Inspector Workspace */}
        {ragResult && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column: Query Analysis & Evidence Ranker */}
            <div className="lg:col-span-1 space-y-6">
              {/* Query Intent Analysis */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Query Analyzer & Intent Breakdown
                </h3>
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Query Intent:</span>
                    <span className="font-bold text-emerald-400">{ragResult.intent}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total Bukti Terambil:</span>
                    <span className="font-bold text-white">{ragResult.evidence.length} Chunks</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Status Validasi Klaim:</span>
                    <span className="font-bold text-emerald-400">{ragResult.validation.status}</span>
                  </div>
                </div>
              </div>

              {/* Ranked Evidence Candidates */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Layers className="w-4 h-4 text-emerald-400" />
                  Paket Bukti Teratas (Ranked Evidence Pack)
                </h3>

                <div className="space-y-3">
                  {ragResult.evidence.map((ev) => (
                    <div key={ev.id} className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs space-y-2">
                      <div className="flex justify-between items-center font-mono">
                        <span className="text-emerald-400 font-bold">#{ev.rank} [{ev.citation_code}]</span>
                        <span className="text-slate-400">Score: {(ev.retrieval_score * 100).toFixed(1)}%</span>
                      </div>
                      <p className="text-slate-200 dir-rtl font-arabic line-clamp-2 leading-relaxed">
                        {ev.text}
                      </p>
                      <div className="flex justify-between items-center text-[10px] text-slate-500 pt-1 border-t border-slate-800/60">
                        <span>Printed Page {ev.printed_page} (PDF p.{ev.pdf_page})</span>
                        <Link
                          href="/admin/fathul-bari-corpus"
                          className="text-emerald-400 hover:underline flex items-center gap-1 font-semibold"
                        >
                          Source Viewer <ChevronRight className="w-3 h-3" />
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column: Generated Answer & Claim Inspector */}
            <div className="lg:col-span-2 space-y-6">
              {/* Generated Answer Box */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-emerald-400" />
                    Jawaban Syarah AI Terverifikasi
                  </h3>
                  <span className="bg-emerald-950 border border-emerald-800 text-emerald-400 px-3 py-1 rounded-full text-xs font-bold">
                    ✓ Closed-Loop Verified
                  </span>
                </div>

                <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 text-slate-200 text-sm leading-relaxed whitespace-pre-line font-mono">
                  {ragResult.answer}
                </div>
              </div>

              {/* Claim-Level Citation Validation Inspector */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Inspektor Validasi Klaim Berbasis Bukti (Claim Citation Inspector)
                </h3>

                <div className="space-y-3">
                  {ragResult.validation.claims.map((cl, idx) => (
                    <div key={idx} className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-slate-200">Klaim #{idx + 1}:</span>
                        <span className="bg-emerald-950 border border-emerald-800 text-emerald-400 px-2.5 py-0.5 rounded-full font-bold text-[10px]">
                          ✓ {cl.validation_status} ({(cl.confidence * 100).toFixed(0)}%)
                        </span>
                      </div>

                      <p className="text-slate-300">{cl.claim_text}</p>

                      <div className="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/60 pt-2">
                        <span className="font-mono text-emerald-400 font-semibold">Sitasi Terhubung: [{cl.citation_code}]</span>
                        <Link
                          href="/admin/fathul-bari-corpus"
                          className="flex items-center gap-1 text-slate-300 hover:text-emerald-400 font-semibold transition"
                        >
                          Buka di Source Viewer <ExternalLink className="w-3 h-3 text-emerald-400" />
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
