"use client";

import React, { useState, useEffect } from "react";
import {
  BookOpen,
  FileText,
  Edit3,
  Sparkles,
  Search,
  CheckCircle2,
  AlertTriangle,
  GitCompare,
  Highlighter,
  Download,
  Plus,
  Send,
  HelpCircle,
  ExternalLink,
  Layers,
  Zap,
} from "lucide-react";
import Link from "next/link";

const API_BASE = "http://localhost:8000/api/v1";

interface WorkspaceNote {
  id: string;
  title: string;
  content: string;
  note_type: string;
}

interface ResearchFinding {
  id: string;
  title: string;
  statement: string;
  status: string;
  confidence: number;
}

interface HighlightItem {
  id: string;
  selected_text: string;
  color: string;
}

interface DiffToken {
  word: string;
  status: "UNCHANGED" | "ADDED" | "REMOVED";
}

export default function ResearchWorkspacePage() {
  const [workspaceId, setWorkspaceId] = useState<string>("");
  const [notes, setNotes] = useState<WorkspaceNote[]>([]);
  const [findings, setFindings] = useState<ResearchFinding[]>([]);
  const [highlights, setHighlights] = useState<HighlightItem[]>([]);

  const [activeTab, setActiveTab] = useState<"notes" | "findings" | "compare">("notes");

  const [selectedText, setSelectedText] = useState<string>("قوله إنما الأعمال بالنيات");
  const [aiQuestion, setAiQuestion] = useState<string>("Apa maksud bagian ini?");
  const [aiResponse, setAiResponse] = useState<string>("");
  const [askingAi, setAskingAi] = useState<boolean>(false);

  const [newNoteTitle, setNewNoteTitle] = useState<string>("");
  const [newNoteContent, setNewNoteContent] = useState<string>("");

  const [diffTokens, setDiffTokens] = useState<DiffToken[]>([]);

  const fetchWorkspace = async () => {
    try {
      const res = await fetch(`${API_BASE}/workspaces-v2`);
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        const wsId = data[0].id;
        setWorkspaceId(wsId);

        const dRes = await fetch(`${API_BASE}/workspaces-v2/${wsId}`);
        const dData = await dRes.json();
        setNotes(dData.notes || []);
        setFindings(dData.findings || []);
        setHighlights(dData.highlights || []);
      }
    } catch (err) {
      console.error("Error loading workspace:", err);
    }
  };

  useEffect(() => {
    fetchWorkspace();
  }, []);

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNoteTitle || !newNoteContent || !workspaceId) return;

    try {
      await fetch(`${API_BASE}/workspaces-v2/${workspaceId}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: newNoteTitle, content: newNoteContent }),
      });
      setNewNoteTitle("");
      setNewNoteContent("");
      fetchWorkspace();
    } catch (err) {
      console.error("Add note error:", err);
    }
  };

  const handleAddHighlight = async () => {
    if (!selectedText || !workspaceId) return;
    try {
      await fetch(`${API_BASE}/workspaces-v2/${workspaceId}/highlights`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ page_id: "page-1", selected_text: selectedText, color: "yellow" }),
      });
      fetchWorkspace();
    } catch (err) {
      console.error("Highlight error:", err);
    }
  };

  const handleAskAI = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiQuestion || !workspaceId) return;

    setAskingAi(true);
    try {
      const res = await fetch(`${API_BASE}/workspaces-v2/${workspaceId}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: aiQuestion, selected_text: selectedText }),
      });
      const data = await res.json();
      setAiResponse(data.answer);
    } catch (err) {
      console.error("Ask AI error:", err);
    } finally {
      setAskingAi(false);
    }
  };

  const handleRunDiff = async () => {
    if (!workspaceId) return;
    try {
      const res = await fetch(`${API_BASE}/workspaces-v2/${workspaceId}/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text1: "عن عمر بن الخطاب قال سمعت رسول الله يقول إنما الأعمال بالنيات",
          text2: "عن عمر بن الخطاب قال سمعت رسول الله يقول إنما الأعمال بالنية",
        }),
      });
      const data = await res.json();
      setDiffTokens(data.diff_tokens || []);
    } catch (err) {
      console.error("Compare error:", err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
            <BookOpen className="w-4 h-4" /> Stage 23 — Research Workspace & Multi-Source Comparison
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Hadith Research Workspace Platform
          </h1>
          <p className="text-slate-400 text-xs mt-0.5">
            Ruang Kerja Riset 3-Kolom (Hadis, Syarah Fathul Bari, Catatan Markdown & Chat AI Kontekstual).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setActiveTab("compare");
              handleRunDiff();
            }}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-xl text-xs font-bold border border-slate-700 transition"
          >
            <GitCompare className="w-4 h-4 text-purple-400" /> Komparasi Varian Hadis
          </button>
        </div>
      </div>

      {/* 3-Column Resizable Workspace Layout */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Pane (3 Cols): Hadith Reader & Metadata */}
        <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2 border-b border-slate-800 pb-3">
            <BookOpen className="w-4 h-4 text-emerald-400" />
            Hadis Aktif (Left Pane)
          </h2>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex justify-between items-center text-xs">
              <span className="font-mono text-emerald-400 font-bold">Bukhari #1</span>
              <span className="text-[10px] text-slate-500 font-bold">Kitab Bad'ul Wahyi</span>
            </div>

            <p className="text-sm text-slate-100 dir-rtl font-arabic leading-loose">
              عَنْ أَمِيرِ الْمُؤْمِنِينَ أَبِي حَفْصٍ عُمَرَ بْنِ الْخَطَّابِ رَضِيَ اللَّهُ عَنْهُ قَالَ: سَمِعْتُ رَسُولَ اللَّهِ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ يَقُولُ: "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ..."
            </p>

            <p className="text-xs text-slate-300 border-t border-slate-800/60 pt-2 leading-relaxed">
              "Sesungguhnya setiap amalan tergantung pada niatnya..."
            </p>
          </div>

          <div className="text-[11px] text-slate-400 space-y-1 bg-slate-950 p-3 rounded-xl border border-slate-800">
            <div>Perawi: Umar bin Khattab r.a.</div>
            <div>Sumber Data: Ahmad Sanusi Hadits API</div>
          </div>
        </div>

        {/* Middle Pane (5 Cols): Fathul Bari Source Viewer & Highlight Engine */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-400" />
              Syarah Fathul Bari (Middle Pane)
            </h2>
            <span className="text-xs font-mono text-slate-400">Vol 1 · Hlm 45</span>
          </div>

          {/* Text Highlight Tool Bar */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-400 font-semibold">Teks Terpilih:</span>
              <button
                onClick={handleAddHighlight}
                className="flex items-center gap-1 bg-amber-950 border border-amber-800 hover:bg-amber-900 text-amber-300 px-3 py-1 rounded-lg font-bold text-[11px] transition"
              >
                <Highlighter className="w-3.5 h-3.5" /> Highlight Text
              </button>
            </div>
            <input
              type="text"
              value={selectedText}
              onChange={(e) => setSelectedText(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 dir-rtl font-arabic text-emerald-400 focus:outline-none"
            />
          </div>

          {/* Canonical Source Text */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-3">
            <div className="flex justify-between items-center font-mono text-xs">
              <span className="text-emerald-400 font-bold">[FB-V1-P45-C001]</span>
              <span className="text-slate-500">SHA-256 Verified</span>
            </div>
            <p className="text-sm text-slate-100 dir-rtl font-arabic leading-loose">
              قوله (إنما الأعمال بالنيات) قال الحافظ ابن حجر في فتح الباري: النية شرط في صحة العبادات، واشتراطها في الطهارة والصلاة والزكاة ثابت بالإجماع...
            </p>
          </div>

          {/* Highlights List */}
          {highlights.length > 0 && (
            <div className="space-y-2 pt-2">
              <span className="text-xs font-bold text-slate-400">Daftar Highlight Teks Terpenuhi:</span>
              {highlights.map((hl) => (
                <div key={hl.id} className="bg-amber-950/40 border border-amber-800/60 p-2.5 rounded-xl text-xs dir-rtl font-arabic text-amber-200">
                  {hl.selected_text}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Pane (4 Cols): Markdown Notes, Findings & Context-Aware AI */}
        <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex border-b border-slate-800 pb-3 gap-2 text-xs">
            <button
              onClick={() => setActiveTab("notes")}
              className={`px-3 py-1.5 rounded-lg font-bold transition ${
                activeTab === "notes" ? "bg-emerald-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Catatan ({notes.length})
            </button>
            <button
              onClick={() => setActiveTab("findings")}
              className={`px-3 py-1.5 rounded-lg font-bold transition ${
                activeTab === "findings" ? "bg-purple-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Temuan ({findings.length})
            </button>
            <button
              onClick={() => {
                setActiveTab("compare");
                handleRunDiff();
              }}
              className={`px-3 py-1.5 rounded-lg font-bold transition ${
                activeTab === "compare" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Varian Diff
            </button>
          </div>

          {/* Tab 1: Markdown Notes Editor */}
          {activeTab === "notes" && (
            <div className="space-y-4">
              <form onSubmit={handleAddNote} className="bg-slate-950 border border-slate-800 rounded-xl p-3 space-y-2 text-xs">
                <input
                  type="text"
                  placeholder="Judul catatan riset..."
                  value={newNoteTitle}
                  onChange={(e) => setNewNoteTitle(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-white font-bold"
                />
                <textarea
                  rows={3}
                  placeholder="Tulis catatan riset Markdown (misal: Sitasi [FB-V1-P45-C001])..."
                  value={newNoteContent}
                  onChange={(e) => setNewNoteContent(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono"
                />
                <button
                  type="submit"
                  className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-2 rounded-lg font-bold shadow transition"
                >
                  + Tambah Catatan Riset
                </button>
              </form>

              <div className="space-y-3">
                {notes.map((n) => (
                  <div key={n.id} className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs space-y-2">
                    <div className="flex justify-between font-bold">
                      <span className="text-emerald-400">{n.title}</span>
                      <span className="text-[10px] text-slate-500">{n.note_type}</span>
                    </div>
                    <p className="text-slate-300 font-mono whitespace-pre-line leading-relaxed">
                      {n.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 2: Verified Findings Stream */}
          {activeTab === "findings" && (
            <div className="space-y-3 text-xs">
              {findings.map((f) => (
                <div key={f.id} className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-white">{f.title}</span>
                    <span className="bg-emerald-950 border border-emerald-800 text-emerald-400 px-2 py-0.5 rounded-full font-bold text-[10px]">
                      ✓ {f.status} ({(f.confidence * 100).toFixed(0)}%)
                    </span>
                  </div>
                  <p className="text-slate-300">{f.statement}</p>
                </div>
              ))}
            </div>
          )}

          {/* Tab 3: Hadith Variant Sequence Diff */}
          {activeTab === "compare" && (
            <div className="space-y-4 text-xs">
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
                <span className="font-bold text-slate-400 block border-b border-slate-800 pb-2">
                  Komparasi Teks Varian: Shahih Bukhari #1 vs Shahih Muslim #1907
                </span>

                <div className="dir-rtl font-arabic text-base leading-loose flex flex-wrap gap-1 bg-slate-900 p-3 rounded-lg border border-slate-800">
                  {diffTokens.map((tok, idx) => (
                    <span
                      key={idx}
                      className={`px-1 py-0.5 rounded ${
                        tok.status === "ADDED" ? "bg-emerald-950 text-emerald-400 font-bold border border-emerald-800" :
                        tok.status === "REMOVED" ? "bg-rose-950 text-rose-400 line-through border border-rose-800" :
                        "text-slate-200"
                      }`}
                    >
                      {tok.word}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Context-Aware AI Chat Box */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3 text-xs border-t-2 border-t-emerald-500">
            <span className="font-bold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              Ask AI From Selection (Kontekstual)
            </span>

            <form onSubmit={handleAskAI} className="space-y-2">
              <input
                type="text"
                value={aiQuestion}
                onChange={(e) => setAiQuestion(e.target.value)}
                placeholder="Tanyakan analisis AI kontekstual..."
                className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-white"
              />
              <button
                type="submit"
                disabled={askingAi}
                className="w-full bg-purple-600 hover:bg-purple-500 text-white py-2 rounded-lg font-bold shadow transition flex items-center justify-center gap-2"
              >
                {askingAi ? <Zap className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                {askingAi ? "Menganalisis..." : "Tanya AI Workspace"}
              </button>
            </form>

            {aiResponse && (
              <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-slate-200 space-y-2 leading-relaxed">
                <span className="text-[10px] font-mono text-emerald-400 font-bold block">Respon AI Kontekstual:</span>
                <p className="whitespace-pre-line">{aiResponse}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
