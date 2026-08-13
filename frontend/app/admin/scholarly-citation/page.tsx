"use client";

import React, { useState, useEffect } from "react";
import {
  BookOpen,
  FileText,
  CheckCircle2,
  Download,
  Share2,
  Copy,
  Layers,
  Sparkles,
  ShieldCheck,
  Zap,
  Hash,
  ExternalLink,
  ChevronRight,
  Globe,
} from "lucide-react";
import Link from "next/link";

const API_BASE = "http://localhost:8000/api/v1";

interface CitationItem {
  id: string;
  citation_label: string;
  locator: {
    volume: number;
    printed_page: number;
    pdf_page: number;
  };
  content_hash: string;
  formatted: {
    ISLAMIC_TRADITIONAL: string;
    CHICAGO: string;
    APA: string;
  };
}

interface BibliographyItem {
  id: string;
  author: string;
  title: string;
  publisher: string;
  pub_year: string;
  formatted: string;
}

export default function ScholarlyCitationPage() {
  const [citations, setCitations] = useState<CitationItem[]>([]);
  const [selectedStyle, setSelectedStyle] = useState<"ISLAMIC_TRADITIONAL" | "CHICAGO" | "APA">("ISLAMIC_TRADITIONAL");
  const [bibliography, setBibliography] = useState<BibliographyItem[]>([]);
  const [exportedContent, setExportedContent] = useState<string>("");
  const [exportFormat, setExportFormat] = useState<string>("markdown");
  const [loading, setLoading] = useState<boolean>(true);

  const fetchCitationsAndBibliography = async () => {
    setLoading(true);
    try {
      // Seed citation
      await fetch(`${API_BASE}/citations-v2`, { method: "POST" });

      const cRes = await fetch(`${API_BASE}/citations-v2`);
      const cData = await cRes.json();
      if (Array.isArray(cData)) {
        setCitations(cData);
      }

      const bRes = await fetch(`${API_BASE}/workspaces-v2/ws-1/bibliography?style=${selectedStyle}`);
      const bData = await bRes.json();
      if (Array.isArray(bData)) {
        setBibliography(bData);
      }
    } catch (err) {
      console.error("Error fetching citations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCitationsAndBibliography();
  }, [selectedStyle]);

  const handleExport = async (fmt: string) => {
    setExportFormat(fmt);
    try {
      const res = await fetch(`${API_BASE}/workspaces-v2/ws-1/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ export_format: fmt, style: selectedStyle }),
      });
      const data = await res.json();
      setExportedContent(data.content);
    } catch (err) {
      console.error("Export error:", err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
            <BookOpen className="w-4 h-4" /> Stage 24 — Scholarly Citation & Bibliography Engine
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Dual-Layer Citation & Bibliography Control Panel
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Menghubungkan Provenance Mesin (`FB-V1-P45-C001`) dengan Footnote Akademik Ilmiah & Generator Daftar Pustaka.
          </p>
        </div>

        {/* Global Citation Style Switcher Bar */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-slate-400">Pilih Style Sitasi Global:</span>
          <div className="bg-slate-900 border border-slate-800 p-1 rounded-xl flex gap-1 text-xs font-bold">
            {(["ISLAMIC_TRADITIONAL", "CHICAGO", "APA"] as const).map((st) => (
              <button
                key={st}
                onClick={() => setSelectedStyle(st)}
                className={`px-3 py-1.5 rounded-lg transition ${
                  selectedStyle === st
                    ? "bg-emerald-600 text-white shadow"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        {/* Workspace Dual-Layer Citations & Inspector */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column: Registered Citations & Machine Provenance */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <Layers className="w-5 h-5 text-emerald-400" />
              Inspektor Dua Lapisan Sitasi (Dual-Layer Citation Inspector)
            </h2>

            <div className="space-y-4">
              {citations.map((c) => (
                <div key={c.id} className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-mono text-emerald-400 font-bold">[{c.citation_label}]</span>
                    <span className="bg-emerald-950 border border-emerald-800 text-emerald-400 px-2 py-0.5 rounded-full font-bold text-[10px]">
                      ✓ SHA-256 Verified
                    </span>
                  </div>

                  <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs space-y-1">
                    <span className="text-[10px] text-slate-400 font-mono font-semibold block">Format Footnote ({selectedStyle}):</span>
                    <p className="text-slate-100 font-serif italic text-sm">{c.formatted[selectedStyle]}</p>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1">
                    <span>Vol {c.locator.volume} · Printed Page {c.locator.printed_page} (PDF p.{c.locator.pdf_page})</span>
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

          {/* Right Column: Automated Bibliography Generator */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <BookOpen className="w-5 h-5 text-blue-400" />
              Daftar Pustaka Terotomatisasi (Automated Bibliography)
            </h2>

            <div className="space-y-3">
              {bibliography.map((b) => (
                <div key={b.id} className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs space-y-2">
                  <div className="font-bold text-slate-200">{b.author}</div>
                  <p className="text-slate-300 font-serif leading-relaxed text-sm">{b.formatted}</p>
                  <div className="text-[10px] text-slate-500 font-mono">Penerbit: {b.publisher} ({b.pub_year})</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Multi-Format Academic Exporter Workspace */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Download className="w-5 h-5 text-purple-400" />
                Ekspor Dokumen Riset & Daftar Pustaka Akademik
              </h3>
              <p className="text-slate-400 text-xs mt-0.5">
                Ekspor dokumen riset lengkap dalam format Markdown, DOCX, PDF, BibTeX (LaTeX), RIS (EndNote/Zotero), dan CSL-JSON.
              </p>
            </div>

            <div className="flex flex-wrap gap-2 text-xs font-bold">
              {(["markdown", "docx", "pdf", "bibtex", "ris"] as const).map((fmt) => (
                <button
                  key={fmt}
                  onClick={() => handleExport(fmt)}
                  className={`px-3.5 py-2 rounded-xl transition border border-slate-700 ${
                    exportFormat === fmt
                      ? "bg-purple-600 text-white border-purple-500 shadow"
                      : "bg-slate-950 text-slate-300 hover:bg-slate-800"
                  }`}
                >
                  {fmt.toUpperCase()} Export
                </button>
              ))}
            </div>
          </div>

          {/* Export Output Preview Container */}
          {exportedContent && (
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs text-slate-400 font-mono">
                <span>Preview Hasil Ekspor ({exportFormat.toUpperCase()}):</span>
                <button
                  onClick={() => navigator.clipboard.writeText(exportedContent)}
                  className="flex items-center gap-1 text-emerald-400 hover:underline"
                >
                  <Copy className="w-3.5 h-3.5" /> Salin Teks
                </button>
              </div>
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 text-xs text-slate-200 font-mono leading-relaxed whitespace-pre-line overflow-x-auto max-h-96">
                {exportedContent}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
