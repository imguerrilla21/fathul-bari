"use client";

import React, { useState, useEffect } from "react";
import {
  BookOpen,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Send,
  Sparkles,
  ShieldCheck,
  Zap,
  Globe,
  Layers,
  Bot,
  UserCheck,
  Check,
  X,
  ExternalLink,
  ChevronRight,
  Award,
} from "lucide-react";
import Link from "next/link";

const API_BASE = "http://localhost:8000/api/v1";

interface DocumentBlock {
  id: string;
  type: string;
  text: string;
  origin: "HUMAN" | "AI_DRAFT";
  level?: number;
}

interface OutlineItem {
  id: string;
  title: string;
  type: string;
}

interface DocumentClaim {
  id: string;
  claim_text: string;
  claim_type: string;
  status: string;
  support_level: "DIRECT" | "INDIRECT" | "PARTIAL" | "UNSUPPORTED";
  evidence_code: string;
  confidence: number;
}

interface PublicationData {
  id: string;
  publication_code: string;
  title: string;
  status: string;
  quality_score: number;
}

export default function ScholarlyPublicationPage() {
  const [docId, setDocId] = useState<string>("doc-1");
  const [blocks, setBlocks] = useState<DocumentBlock[]>([]);
  const [outline, setOutline] = useState<OutlineItem[]>([]);
  const [claims, setClaims] = useState<DocumentClaim[]>([]);
  const [publication, setPublication] = useState<PublicationData | null>(null);

  const [activeTab, setActiveTab] = useState<"editor" | "claims" | "review" | "public">("editor");

  const [aiPrompt, setAiPrompt] = useState<string>("Tuliskan analisis Ibnu Hajar mengenai fungsi niat dalam ibadah.");
  const [generatingDraft, setGeneratingDraft] = useState<boolean>(false);

  const fetchDocumentDetail = async () => {
    try {
      // Seed initial doc
      const cRes = await fetch(`${API_BASE}/publications-v2/documents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "Analisis Syarah Niat dalam Fathul Bari" }),
      });
      const cData = await cRes.json();
      const targetId = cData.id || "doc-1";
      setDocId(targetId);

      const res = await fetch(`${API_BASE}/publications-v2/documents/${targetId}`);
      const data = await res.json();
      setBlocks(data.blocks || []);
      setOutline(data.outline || []);
      setClaims(data.claims || []);
    } catch (err) {
      console.error("Fetch document error:", err);
    }
  };

  useEffect(() => {
    fetchDocumentDetail();
  }, []);

  const handleGenerateAIDraft = async () => {
    if (!aiPrompt) return;
    setGeneratingDraft(true);
    try {
      const res = await fetch(`${API_BASE}/publications-v2/documents/${docId}/ai-draft`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: aiPrompt }),
      });
      const newBlock = await res.json();
      setBlocks((prev) => [...prev, newBlock]);
    } catch (err) {
      console.error("AI Draft error:", err);
    } finally {
      setGeneratingDraft(false);
    }
  };

  const handleVerifyClaim = async (claimId: string, approved: boolean) => {
    try {
      await fetch(`${API_BASE}/publications-v2/claims/${claimId}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_approved: approved }),
      });
      setClaims((prev) =>
        prev.map((c) => (c.id === claimId ? { ...c, status: approved ? "SUPPORTED" : "REJECTED" } : c))
      );
    } catch (err) {
      console.error("Verify claim error:", err);
    }
  };

  const handlePublish = async () => {
    try {
      const res = await fetch(`${API_BASE}/publications-v2/documents/${docId}/publish`, {
        method: "POST",
      });
      const data = await res.json();
      setPublication(data);
      setActiveTab("public");
    } catch (err) {
      console.error("Publish error:", err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
            <BookOpen className="w-4 h-4" /> Stage 25 — Research Document & Scholarly Publication Pipeline
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Scholarly Publication Pipeline & Verification Gate
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Lingkungan Penulisan Ilmiah End-to-End dengan Verifikasi Klaim Faktual & Snapshot Publikasi (`PUB-2026-000001`).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handlePublish}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-xl text-xs font-bold shadow-lg transition"
          >
            <Award className="w-4 h-4" /> Publish Manuscript (Snapshot)
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-6">
        {/* Navigation Tabs Bar */}
        <div className="flex border-b border-slate-800 pb-3 gap-3 text-xs font-bold">
          <button
            onClick={() => setActiveTab("editor")}
            className={`px-4 py-2 rounded-xl transition ${
              activeTab === "editor" ? "bg-emerald-600 text-white" : "bg-slate-900 text-slate-400 hover:text-slate-200"
            }`}
          >
            Editor Dokumen Berbasis Blok
          </button>
          <button
            onClick={() => setActiveTab("claims")}
            className={`px-4 py-2 rounded-xl transition ${
              activeTab === "claims" ? "bg-purple-600 text-white" : "bg-slate-900 text-slate-400 hover:text-slate-200"
            }`}
          >
            Matriks Klaim & Bukti ({claims.length})
          </button>
          <button
            onClick={() => setActiveTab("public")}
            className={`px-4 py-2 rounded-xl transition ${
              activeTab === "public" ? "bg-blue-600 text-white" : "bg-slate-900 text-slate-400 hover:text-slate-200"
            }`}
          >
            Tampilan Publikasi Publik {publication ? `(${publication.publication_code})` : ""}
          </button>
        </div>

        {/* Tab 1: Block-Based Editor & Outline Navigator */}
        {activeTab === "editor" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Outline Navigator (3 Cols) */}
            <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
              <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2 border-b border-slate-800 pb-3">
                <Layers className="w-4 h-4 text-emerald-400" /> Navigasi Outline
              </h2>
              <div className="space-y-2 text-xs">
                {outline.map((item) => (
                  <div key={item.id} className="p-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-300 font-semibold truncate">
                    {item.title}
                  </div>
                ))}
              </div>
            </div>

            {/* Document Blocks Area (9 Cols) */}
            <div className="lg:col-span-9 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
              {/* Controlled AI Drafting Assistant Bar */}
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
                <span className="text-xs font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-emerald-400" /> Controlled AI Drafting Assistant
                </span>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    placeholder="Instruksi draf AI..."
                    className="flex-1 bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white"
                  />
                  <button
                    onClick={handleGenerateAIDraft}
                    disabled={generatingDraft}
                    className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1"
                  >
                    {generatingDraft ? <Zap className="w-3.5 h-3.5 animate-spin" /> : <Bot className="w-3.5 h-3.5" />}
                    Draft Paragraf
                  </button>
                </div>
              </div>

              {/* Rendered Document Blocks */}
              <div className="space-y-4">
                {blocks.map((b) => (
                  <div key={b.id} className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2 relative">
                    <div className="flex justify-between items-center text-[10px] font-mono border-b border-slate-800/60 pb-2">
                      <span className="text-slate-500 uppercase">{b.type}</span>
                      <span
                        className={`px-2 py-0.5 rounded font-bold ${
                          b.origin === "HUMAN"
                            ? "bg-blue-950 border border-blue-800 text-blue-400"
                            : "bg-purple-950 border border-purple-800 text-purple-400"
                        }`}
                      >
                        {b.origin} ORIGIN
                      </span>
                    </div>

                    {b.type === "HEADING" && (
                      <h2 className="text-lg font-bold text-emerald-400">{b.text}</h2>
                    )}

                    {b.type === "HADITH" && (
                      <p className="text-base text-slate-100 dir-rtl font-arabic leading-loose bg-slate-900 p-3 rounded-lg border border-slate-800">
                        {b.text}
                      </p>
                    )}

                    {b.type === "PARAGRAPH" && (
                      <p className="text-xs text-slate-200 leading-relaxed font-serif">{b.text}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Claim-Evidence Matrix */}
        {activeTab === "claims" && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <ShieldCheck className="w-5 h-5 text-purple-400" /> Matriks Ekstraksi Klaim Faktis & Dukungan Bukti
            </h2>

            <div className="space-y-3">
              {claims.map((c) => (
                <div key={c.id} className="bg-slate-950 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-purple-400 font-bold">[{c.claim_type}]</span>
                      <span
                        className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                          c.support_level === "DIRECT" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                          c.support_level === "INDIRECT" ? "bg-blue-950 text-blue-400 border border-blue-800" :
                          "bg-amber-950 text-amber-400 border border-amber-800"
                        }`}
                      >
                        ✓ {c.support_level} SUPPORT
                      </span>
                    </div>
                    <p className="text-slate-200 font-serif text-sm">{c.claim_text}</p>
                    <div className="text-[10px] text-slate-500 font-mono">Evidence: {c.evidence_code}</div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleVerifyClaim(c.id, true)}
                      className="bg-emerald-950 border border-emerald-800 hover:bg-emerald-900 text-emerald-300 px-3 py-1.5 rounded-lg font-bold text-xs transition flex items-center gap-1"
                    >
                      <Check className="w-3.5 h-3.5" /> Verify
                    </button>
                    <button
                      onClick={() => handleVerifyClaim(c.id, false)}
                      className="bg-rose-950 border border-rose-800 hover:bg-rose-900 text-rose-300 px-3 py-1.5 rounded-lg font-bold text-xs transition flex items-center gap-1"
                    >
                      <X className="w-3.5 h-3.5" /> Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: Public Publication View Tab */}
        {activeTab === "public" && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl max-w-4xl mx-auto space-y-6">
            <div className="border-b border-slate-800 pb-4 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="bg-emerald-950 border border-emerald-800 text-emerald-400 px-3 py-1 rounded-full font-mono font-bold">
                  {publication?.publication_code || "PUB-2026-000001"}
                </span>
                <span className="text-slate-400 text-xs">Quality Score: <strong className="text-emerald-400">{publication?.quality_score || 94}/100</strong></span>
              </div>
              <h1 className="text-2xl font-bold text-white">Analisis Syarah Niat dalam Fathul Bari</h1>
              <p className="text-xs text-slate-400 font-mono">Diterbitkan oleh Almaktaba Research Team · License CC-BY-NC-4.0</p>
            </div>

            <div className="space-y-4 text-sm text-slate-200 font-serif leading-relaxed">
              <p className="bg-slate-950 border border-slate-800 p-4 rounded-xl text-emerald-300 italic text-xs">
                Abstrak: Kajian ini menganalisis kedudukan hukum niat dalam ibadah berdasarkan penjelasan Al-Hafizh Ibnu Hajar al-Asqalani dalam Fathul Bari.
              </p>

              <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-3">
                <span className="text-xs font-mono text-emerald-400 font-bold block">Teks Hadis Aktivis:</span>
                <p className="text-base text-slate-100 dir-rtl font-arabic leading-loose">
                  عن عمر بن الخطاب رضي الله عنه قال: سمعت رسول الله صلى الله عليه وسلم يقول: "إنما الأعمال بالنيات..."
                </p>
              </div>

              <p>
                Al-Hafizh Ibnu Hajar al-Asqalani menegaskan bahwa niat merupakan rukun utama dan syarat sahnya seluruh amal ibadah.<sup>1</sup>
              </p>

              <div className="border-t border-slate-800 pt-4 text-xs font-sans text-slate-400 space-y-1">
                <div className="font-bold text-slate-200">Catatan Kaki (Footnotes):</div>
                <div>1. Ibn Hajar al-'Asqalani, Fath al-Bari bi-Sharh Sahih al-Bukhari, jil. 1 (Beirut: Dar al-Ma'rifah, 1379 H), 45. [FB-V1-P45-C001]</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
