"use client";

import React, { useState, useEffect } from "react";
import {
  BookOpen,
  Search,
  Database,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  FileCheck,
  Layers,
  Sparkles,
  ShieldCheck,
  Download,
  Link,
  Tag,
  Hash,
} from "lucide-react";

const API_BASE = "http://localhost:8000/api/v1";

interface HadithResult {
  id: string;
  external_id: string;
  hadith_number: string;
  arabic_text: string;
  normalized_text: string;
  narrator_text: string;
  grade: string;
  content_hash: string;
  source_url: string;
}

interface IngestionJobStatus {
  job_id: string;
  provider: string;
  collection: string;
  status: string;
  processed_items: number;
  total_items: number;
  error_message: string | null;
}

export default function HadithDataLayerPage() {
  const [searchQuery, setSearchQuery] = useState<string>("إنما الأعمال بالنيات");
  const [searchResults, setSearchResults] = useState<HadithResult[]>([]);
  const [selectedHadith, setSelectedHadith] = useState<HadithResult | null>(null);

  const [ingesting, setIngesting] = useState<boolean>(false);
  const [jobStatus, setJobStatus] = useState<IngestionJobStatus | null>(null);
  const [searching, setSearching] = useState<boolean>(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery) return;

    setSearching(true);
    try {
      const res = await fetch(`${API_BASE}/hadith-layer/search?q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      if (data && data.results) {
        setSearchResults(data.results);
        if (data.results.length > 0) {
          setSelectedHadith(data.results[0]);
        }
      }
    } catch (err) {
      console.error("Search error:", err);
    } finally {
      setSearching(false);
    }
  };

  const handleTriggerIngestion = async (collectionSlug: string) => {
    setIngesting(true);
    setJobStatus(null);
    try {
      const res = await fetch(`${API_BASE}/hadith-layer/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ collection_slug: collectionSlug, limit: 10 }),
      });
      const data = await res.json();
      setJobStatus(data);
      // Refresh search results
      handleSearch();
    } catch (err) {
      console.error("Ingestion error:", err);
    } finally {
      setIngesting(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
            <Database className="w-4 h-4" /> Stage 19 — Ahmad Sanusi Hadits API + Hadith Data Layer
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Hadith Local Research Index & Provider Control Panel
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Penyedia Hadis Provider-Agnostic, Idempotent Upsert, SHA-256 Content Hashing, dan Arabic Normalizer v2.
          </p>
        </div>

        {/* Collection Trigger Bar */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-slate-400">Import Koleksi:</span>
          {(["bukhari", "muslim", "abu-dawud", "tirmidhi"] as const).map((slug) => (
            <button
              key={slug}
              onClick={() => handleTriggerIngestion(slug)}
              disabled={ingesting}
              className="flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 px-3 py-1.5 rounded-lg text-xs font-medium transition"
            >
              <Download className="w-3.5 h-3.5 text-emerald-400" />
              {slug.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        {/* Ingestion Job Status Alert */}
        {jobStatus && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-2">
            <div className="flex justify-between items-center text-xs">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="font-bold text-white">Job Batch Ingestion Active: [{jobStatus.collection.toUpperCase()}]</span>
                <span className="bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-800 font-bold uppercase text-[10px]">
                  {jobStatus.status}
                </span>
              </div>
              <span className="text-slate-400">
                Processed: <strong className="text-emerald-400">{jobStatus.processed_items}</strong> / {jobStatus.total_items} items
              </span>
            </div>

            <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
              <div
                className="bg-emerald-500 h-full transition-all duration-300"
                style={{ width: `${(jobStatus.processed_items / Math.max(jobStatus.total_items, 1)) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Search Bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <form onSubmit={handleSearch} className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-4 top-3.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Cari hadis lokal berdasarkan teks Arab, nomor, perawi, atau external_id..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <button
              type="submit"
              disabled={searching}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-3 rounded-xl text-sm font-semibold shadow-lg transition"
            >
              <RefreshCw className={`w-4 h-4 ${searching ? "animate-spin" : ""}`} />
              Cari Indeks Lokal
            </button>
          </form>
        </div>

        {/* Search Results & Provenance Explorer */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Results List */}
          <div className="lg:col-span-1 space-y-3">
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider">
              Hasil Indeks Lokal ({searchResults.length})
            </h2>

            {searchResults.length === 0 ? (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center text-slate-500 text-xs">
                Tidak ada hadis ditemukan.
              </div>
            ) : (
              searchResults.map((h) => (
                <div
                  key={h.id}
                  onClick={() => setSelectedHadith(h)}
                  className={`cursor-pointer bg-slate-900 border rounded-2xl p-4 transition space-y-2 ${
                    selectedHadith?.id === h.id
                      ? "border-emerald-500 shadow-lg shadow-emerald-950/20"
                      : "border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="flex justify-between items-center font-mono text-xs">
                    <span className="text-emerald-400 font-bold">[{h.external_id}]</span>
                    <span className="bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded text-[10px] border border-emerald-800 font-bold">
                      {h.grade}
                    </span>
                  </div>

                  <p className="text-xs text-slate-200 dir-rtl font-arabic line-clamp-2 leading-relaxed">
                    {h.arabic_text}
                  </p>

                  <div className="text-[10px] text-slate-500 flex justify-between items-center pt-1 border-t border-slate-800/60">
                    <span>Perawi: {h.narrator_text || "-"}</span>
                    <span>No. {h.hadith_number}</span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Right Detailed Inspector & Data Provenance */}
          <div className="lg:col-span-2 space-y-6">
            {selectedHadith ? (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
                <div className="flex justify-between items-start border-b border-slate-800 pb-4">
                  <div>
                    <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 font-bold mb-1">
                      <Tag className="w-3.5 h-3.5" /> {selectedHadith.external_id}
                    </div>
                    <h3 className="text-xl font-bold text-white">
                      Hadis Shahih Bukhari #{selectedHadith.hadith_number}
                    </h3>
                  </div>

                  <span className="bg-emerald-950 text-emerald-400 text-xs font-bold px-3 py-1 rounded-full border border-emerald-800">
                    Derajat: {selectedHadith.grade}
                  </span>
                </div>

                {/* Original Arabic Text */}
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-400">Teks Arab Asli (Canonical Immutable Text):</span>
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 text-right dir-rtl font-arabic text-lg text-slate-100 leading-loose">
                    {selectedHadith.arabic_text}
                  </div>
                </div>

                {/* Normalized Arabic Text */}
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-400">Teks Arab Ter-normalisasi (Arabic Normalizer v2):</span>
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-right dir-rtl font-arabic text-sm text-slate-300 leading-relaxed">
                    {selectedHadith.normalized_text}
                  </div>
                </div>

                {/* Data Provenance & SHA-256 Hash Card */}
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
                  <h4 className="text-xs font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    Data Provenance & SHA-256 Content Hash
                  </h4>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-slate-500">Provider Sumber:</span>
                      <div className="font-semibold text-slate-200 mt-0.5">Ahmad Sanusi Hadits API</div>
                    </div>

                    <div>
                      <span className="text-slate-500">Sanad / Perawi:</span>
                      <div className="font-semibold text-slate-200 mt-0.5">{selectedHadith.narrator_text || "-"}</div>
                    </div>

                    <div className="md:col-span-2">
                      <span className="text-slate-500 flex items-center gap-1">
                        <Hash className="w-3 h-3 text-emerald-400" /> Content SHA-256 Hash:
                      </span>
                      <div className="font-mono text-[11px] text-emerald-400 bg-slate-900 p-2 rounded border border-slate-800 mt-1 break-all">
                        {selectedHadith.content_hash}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 text-sm">
                Pilih hadis di sebelah kiri untuk melihat detail provenance & varian teks.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
