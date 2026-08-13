"use client";

import React, { useState, useEffect } from "react";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Play,
  RefreshCw,
  Layers,
  Database,
  Search,
  BookOpen,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Clock,
  Sparkles,
  FileCheck,
} from "lucide-react";

const API_BASE = "http://localhost:8000/api/v1";

interface IngestionJobItem {
  id: string;
  document_id: string;
  volume: number;
  status: "pending" | "running" | "completed" | "failed";
  progress_pct: number;
  current_stage: string;
  pipeline_version: string;
  error_message: string | null;
  created_at: string;
}

interface ManifestItem {
  id: number;
  work_slug: string;
  edition: string;
  volume: number;
  source_sha256: string;
  processed_pages: number;
  sections_count: number;
  hadith_candidates_count: number;
  verified_links_count: number;
  chunks_count: number;
  embeddings_count: number;
  pipeline_version: string;
  created_at: string;
}

export default function CorpusIngestionPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [volume, setVolume] = useState<number>(1);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadStatus, setUploadStatus] = useState<any>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [jobs, setJobs] = useState<IngestionJobItem[]>([]);
  const [manifests, setManifests] = useState<ManifestItem[]>([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [jRes, mRes] = await Promise.all([
        fetch(`${API_BASE}/admin/ingestion/jobs`).then((r) => r.json()),
        fetch(`${API_BASE}/admin/ingestion/manifests`).then((r) => r.json()),
      ]);

      if (Array.isArray(jRes)) setJobs(jRes);
      if (Array.isArray(mRes)) setManifests(mRes);
    } catch (err) {
      console.error("Error fetching ingestion data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleUploadAndRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      alert("Silakan pilih file PDF atau teks Fathul Bari terlebih dahulu.");
      return;
    }

    setUploading(true);
    setUploadStatus(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("volume", volume.toString());

      const upRes = await fetch(`${API_BASE}/admin/ingestion/upload`, {
        method: "POST",
        body: formData,
      });

      const upData = await upRes.json();
      setUploadStatus(upData);

      if (upData.document_id) {
        // Trigger background ingestion pipeline job
        const jobRes = await fetch(`${API_BASE}/admin/ingestion/start/${upData.document_id}`, {
          method: "POST",
        });
        await jobRes.json();
        fetchData();
      }
    } catch (err) {
      console.error("Upload error:", err);
      alert("Gagal mengunggah file dokumen sumber.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
            <Database className="w-4 h-4" /> Stage 13 — Data Ingestion & Corpus Building
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Fathul Bari Corpus Ingestion & Pipeline Manager
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Ekstraksi Layout PDF, Normalisasi Teks Arab, Deteksi Hadis, Semantic Chunking, dan Reproduksibilitas Manifest.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-xl text-sm font-medium border border-slate-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh Pipeline
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        {/* Upload & Pipeline Registration Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <UploadCloud className="w-6 h-6 text-emerald-400" />
            <div>
              <h2 className="text-xl font-bold text-white">Upload Dokumen Sumber Fathul Bari (PDF / Text)</h2>
              <p className="text-xs text-slate-400">
                Pemeriksaan otomatis SHA-256 Checksum, pemisahan halaman, dan pengolahan pipeline berulang.
              </p>
            </div>
          </div>

          <form onSubmit={handleUploadAndRun} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-2">Pilih File PDF / Text</label>
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-2">Volume / Jilid Fathul Bari</label>
              <select
                value={volume}
                onChange={(e) => setVolume(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                {Array.from({ length: 13 }, (_, i) => i + 1).map((v) => (
                  <option key={v} value={v}>
                    Jilid / Volume {v}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={uploading}
              className="flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-5 py-2.5 rounded-xl shadow-lg transition"
            >
              {uploading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4 fill-white" />
              )}
              {uploading ? "Uploading & Ingesting..." : "Jalankan Ingestion Pipeline"}
            </button>
          </form>

          {/* Upload Status Warning */}
          {uploadStatus && (
            <div
              className={`p-4 rounded-xl text-xs font-medium border flex items-center gap-3 ${
                uploadStatus.status === "duplicate"
                  ? "bg-amber-950/20 border-amber-800/60 text-amber-300"
                  : "bg-emerald-950/20 border-emerald-800/60 text-emerald-300"
              }`}
            >
              <CheckCircle2 className="w-5 h-5 shrink-0" />
              <div>
                <div className="font-bold">{uploadStatus.message}</div>
                <div className="font-mono text-[11px] opacity-80 mt-0.5">
                  SHA-256: {uploadStatus.sha256} | Document ID: {uploadStatus.document_id}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Pipeline Jobs Tracker */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-emerald-400" />
            Active Ingestion Jobs & Pipeline State Tracker
          </h2>

          <div className="space-y-4">
            {jobs.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-sm">
                Belum ada job penyerapan data yang berjalan.
              </div>
            ) : (
              jobs.map((j) => (
                <div
                  key={j.id}
                  className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-slate-200">
                        Volume {j.volume} Ingestion
                      </span>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                          j.status === "completed"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : j.status === "running"
                            ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                            : "bg-red-500/20 text-red-400 border border-red-500/30"
                        }`}
                      >
                        {j.status}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">
                        Stage: {j.current_stage}
                      </span>
                    </div>

                    <div className="text-xs text-slate-400 font-semibold">
                      Progress: <span className="text-emerald-400 font-bold">{j.progress_pct}%</span>
                    </div>
                  </div>

                  <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full transition-all duration-500"
                      style={{ width: `${j.progress_pct}%` }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Corpus Manifests Reproducibility Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <FileCheck className="w-5 h-5 text-emerald-400" />
              Corpus Manifests & Reproducibility Audit
            </h2>
            <span className="text-xs text-slate-400">
              Versi Korpus: <span className="text-emerald-400 font-bold">13.0</span>
            </span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase">
                <tr>
                  <th className="p-3">Work</th>
                  <th className="p-3 text-center">Volume</th>
                  <th className="p-3 text-center">Pages</th>
                  <th className="p-3 text-center">Sections</th>
                  <th className="p-3 text-center">Verified Links</th>
                  <th className="p-3 text-center">Chunks & Embeddings</th>
                  <th className="p-3 text-right">SHA-256 Checksum</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {manifests.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-950/50">
                    <td className="p-3 font-semibold text-slate-200 uppercase">{m.work_slug}</td>
                    <td className="p-3 text-center font-bold text-emerald-400">Vol {m.volume}</td>
                    <td className="p-3 text-center text-slate-300">{m.processed_pages}</td>
                    <td className="p-3 text-center text-blue-400 font-bold">{m.sections_count}</td>
                    <td className="p-3 text-center text-purple-400 font-bold">
                      {m.verified_links_count}
                    </td>
                    <td className="p-3 text-center text-amber-400 font-bold">
                      {m.chunks_count}
                    </td>
                    <td className="p-3 text-right font-mono text-[10px] text-slate-500">
                      {m.source_sha256.substring(0, 16)}...
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
