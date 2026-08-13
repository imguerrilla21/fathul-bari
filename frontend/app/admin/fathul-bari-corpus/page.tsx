"use client";

import React, { useState, useEffect } from "react";
import {
  FileText,
  BookOpen,
  Search,
  CheckCircle2,
  AlertCircle,
  Hash,
  Download,
  Layers,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  ShieldCheck,
  Tag,
  Sparkles,
} from "lucide-react";

const API_BASE = "http://localhost:8000/api/v1";

interface DocumentVolume {
  id: string;
  volume_number: number;
  title: string;
  page_count: number;
}

interface SourceDocumentData {
  id: string;
  title: string;
  author: string;
  edition: string;
  file_hash: string;
  volumes: DocumentVolume[];
}

interface PageDetail {
  id: string;
  printed_page_number: number;
  pdf_page_number: number;
  image_path: string;
  extracted_text: string;
  normalized_text: string;
  extraction_method: string;
  ocr_confidence: number;
  content_hash: string;
  chunks: {
    id: string;
    citation_code: string;
    original_text: string;
    token_count: number;
    content_hash: string;
  }[];
}

interface SearchResultItem {
  chunk_id: string;
  citation_code: string;
  volume: number;
  printed_page: number;
  pdf_page: number;
  snippet: string;
  content_hash: string;
}

export default function FathulBariCorpusPage() {
  const [documents, setDocuments] = useState<SourceDocumentData[]>([]);
  const [selectedVolume, setSelectedVolume] = useState<number>(1);
  const [pageDetail, setPageDetail] = useState<PageDetail | null>(null);

  const [searchQuery, setSearchQuery] = useState<string>("إنما الأعمال بالنيات");
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [searching, setSearching] = useState<boolean>(false);

  const fetchDocumentsAndPages = async () => {
    try {
      const dRes = await fetch(`${API_BASE}/source-viewer/documents`);
      const dData = await dRes.json();
      if (Array.isArray(dData)) {
        setDocuments(dData);
      }

      const pRes = await fetch(`${API_BASE}/source-viewer/pages/page-1`);
      const pData = await pRes.json();
      if (pData && pData.id) {
        setPageDetail(pData);
      }
    } catch (err) {
      console.error("Error fetching corpus data:", err);
    }
  };

  useEffect(() => {
    fetchDocumentsAndPages();
  }, []);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery) return;

    setSearching(true);
    try {
      const res = await fetch(`${API_BASE}/source-viewer/search?q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      if (data && data.results) {
        setSearchResults(data.results);
      }
    } catch (err) {
      console.error("Search error:", err);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
            <FileText className="w-4 h-4" /> Stage 21 — Fathul Bari Corpus Ingestion & Source Viewer
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Fathul Bari Dual-Pane Source Viewer & Universal Citation Inspector
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Pemisahan 3 Lapisan Teks, Dua Nomor Halaman (Printed Page vs PDF Page), dan Kode Sitasi Universal (`FB-V1-P45-C003`).
          </p>
        </div>

        {/* Volume Switcher Bar */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-400">Pilih Volume:</span>
          <div className="bg-slate-900 border border-slate-800 p-1 rounded-xl flex gap-1">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13].map((v) => (
              <button
                key={v}
                onClick={() => setSelectedVolume(v)}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition ${
                  selectedVolume === v
                    ? "bg-emerald-600 text-white shadow"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Vol {v}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        {/* Corpus Search Bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <form onSubmit={handleSearch} className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-4 top-3.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Cari teks Fathul Bari berdasarkan kata kunci Arab atau Kode Sitasi [FB-V1-P45-C003]..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <button
              type="submit"
              disabled={searching}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-3 rounded-xl text-sm font-semibold shadow-lg transition"
            >
              <Search className="w-4 h-4" /> Cari Korpus
            </button>
          </form>

          {/* Search Snippets Grid */}
          {searchResults.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
              {searchResults.map((sr, idx) => (
                <div key={idx} className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs space-y-1">
                  <div className="flex justify-between font-bold">
                    <span className="text-emerald-400 font-mono">[{sr.citation_code}]</span>
                    <span className="text-slate-400">Printed Page {sr.printed_page} (PDF Page {sr.pdf_page})</span>
                  </div>
                  <p className="text-slate-200 dir-rtl font-arabic line-clamp-2 leading-relaxed">
                    {sr.snippet}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Dual-Pane Source Viewer */}
        {pageDetail && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left Pane: PDF Page Image Preview & Dual Page Numbers */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-emerald-400" />
                  Pratinjau Gambar Halaman PDF (Left Pane)
                </h2>
                <span className="text-xs font-bold text-slate-400 bg-slate-950 border border-slate-800 px-3 py-1 rounded-full">
                  PDF Page: {pageDetail.pdf_page_number}
                </span>
              </div>

              {/* Dual Page Number Indicator */}
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex justify-around text-xs text-slate-300">
                <div>
                  Halaman Cetak (Printed Page): <strong className="text-emerald-400">{pageDetail.printed_page_number}</strong>
                </div>
                <div>
                  Halaman PDF Digital: <strong className="text-blue-400">{pageDetail.pdf_page_number}</strong>
                </div>
              </div>

              {/* PDF Image Simulation Container */}
              <div className="bg-slate-950 border border-slate-800 rounded-xl h-96 flex flex-col items-center justify-center p-6 text-center space-y-3">
                <FileText className="w-16 h-16 text-slate-600" />
                <div className="font-arabic dir-rtl text-lg text-slate-300">
                  فتح الباري شرح صحيح البخاري - الجزء الأول
                </div>
                <div className="text-xs text-slate-500 font-mono">
                  [PDF Page Image Preview: {pageDetail.image_path}]
                </div>
              </div>
            </div>

            {/* Right Pane: Extracted Text & Citation Chunks */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
              <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-emerald-400" />
                  Teks Ekstraksi & Kode Sitasi Universal (Right Pane)
                </h2>
                <span className="text-xs font-bold text-emerald-400 bg-emerald-950 border border-emerald-800 px-3 py-1 rounded-full">
                  Method: {pageDetail.extraction_method} ({pageDetail.ocr_confidence * 100}%)
                </span>
              </div>

              {/* Extracted Original Arabic Text */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-400">Teks Arab Asli Halaman (Canonical Extracted Evidence):</span>
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-right dir-rtl font-arabic text-base text-slate-100 leading-loose">
                  {pageDetail.extracted_text}
                </div>
              </div>

              {/* Chunks & Citation Badges */}
              <div className="space-y-3">
                <span className="text-xs font-bold text-slate-400">Daftar Chunk & Kode Sitasi Universal:</span>
                {pageDetail.chunks.map((c) => (
                  <div key={c.id} className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2 text-xs">
                    <div className="flex justify-between items-center font-mono">
                      <span className="text-emerald-400 font-bold">[{c.citation_code}]</span>
                      <span className="text-slate-500">{c.token_count} Tokens</span>
                    </div>

                    <p className="text-slate-200 dir-rtl font-arabic leading-relaxed">
                      {c.original_text}
                    </p>

                    <div className="text-[10px] text-slate-500 font-mono border-t border-slate-800/60 pt-1 flex items-center gap-1">
                      <Hash className="w-3 h-3 text-emerald-400" /> SHA-256: {c.content_hash}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
