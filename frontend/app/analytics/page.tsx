"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  Search,
  BookOpen,
  Database,
  Layers,
  Sparkles,
  Users,
  ShieldCheck,
  RefreshCw,
  Play,
  Check,
  XCircle,
  HelpCircle,
  TrendingUp,
} from "lucide-react";

const API_BASE = "http://localhost:8000/api/v1";

interface OverviewData {
  total_hadith: number;
  total_sharh: number;
  total_sources: number;
  total_links: number;
  verified_links: number;
  pending_links: number;
  rejected_links: number;
  hadith_coverage_pct: number;
  sharh_coverage_pct: number;
  verification_pct: number;
}

interface VolumeData {
  volume: number;
  total_sections: number;
  verified_sections: number;
  pending_sections: number;
  coverage_pct: number;
}

interface ConfidenceData {
  distribution: {
    high_confidence_pct90: number;
    mid_confidence_pct70_89: number;
    low_confidence_below70: number;
  };
  calibration_curve: Array<{
    range: string;
    total_count: number;
    verified_count: number;
    predicted_conf_pct: number;
    actual_verification_pct: number;
  }>;
}

interface EvaluationResult {
  run_id: number;
  timestamp: string;
  query_count: number;
  recall_at_1: number;
  recall_at_5: number;
  recall_at_10: number;
  mrr: number;
  ndcg: number;
  precision_k: number;
  groundedness_score: number;
  citation_integrity_score: number;
}

interface GoldenQuery {
  id: number;
  query: string;
  category: string;
  expected_hadith_ids: number[];
  expected_sharh_ids: number[];
}

interface QualityIssueItem {
  id: string;
  issue_type: string;
  severity: "critical" | "warning" | "review";
  title: string;
  description: string;
  target_type: string;
  target_id: number;
  status: "open" | "resolved" | "ignored";
}

interface ReviewerItem {
  reviewer: string;
  verified_count: number;
  rejected_count: number;
  total_reviewed: number;
  approval_rate_pct: number;
}

interface InterRaterItem {
  cohens_kappa: number;
  agreement_level: string;
  observed_agreement_pct: number;
  sample_size: number;
}

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<
    "overview" | "calibration" | "rag_eval" | "issues" | "reviewers"
  >("overview");

  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [volumes, setVolumes] = useState<VolumeData[]>([]);
  const [confidence, setConfidence] = useState<ConfidenceData | null>(null);
  const [queries, setQueries] = useState<GoldenQuery[]>([]);
  const [evalResult, setEvalResult] = useState<EvaluationResult | null>(null);
  const [runningEval, setRunningEval] = useState(false);
  const [issues, setIssues] = useState<QualityIssueItem[]>([]);
  const [reviewers, setReviewers] = useState<ReviewerItem[]>([]);
  const [interRater, setInterRater] = useState<InterRaterItem | null>(null);

  const [severityFilter, setSeverityFilter] = useState<string>("all");

  const fetchData = async () => {
    setLoading(true);
    try {
      const [ovRes, covRes, confRes, qRes, issRes, revRes, irRes] = await Promise.all([
        fetch(`${API_BASE}/analytics/overview`).then((r) => r.json()),
        fetch(`${API_BASE}/analytics/coverage`).then((r) => r.json()),
        fetch(`${API_BASE}/analytics/confidence`).then((r) => r.json()),
        fetch(`${API_BASE}/evaluation/queries`).then((r) => r.json()),
        fetch(`${API_BASE}/analytics/issues`).then((r) => r.json()),
        fetch(`${API_BASE}/analytics/reviewer-performance`).then((r) => r.json()),
        fetch(`${API_BASE}/analytics/inter-rater-agreement`).then((r) => r.json()),
      ]);

      setOverview(ovRes);
      if (covRes && covRes.volumes) setVolumes(covRes.volumes);
      setConfidence(confRes);
      if (Array.isArray(qRes)) setQueries(qRes);
      if (Array.isArray(issRes)) setIssues(issRes);
      if (Array.isArray(revRes)) setReviewers(revRes);
      setInterRater(irRes);
    } catch (err) {
      console.error("Error fetching analytics data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunEvaluation = async () => {
    setRunningEval(true);
    try {
      const res = await fetch(`${API_BASE}/evaluation/run`, {
        method: "POST",
      });
      const data = await res.json();
      setEvalResult(data);
    } catch (err) {
      console.error("Error running evaluation:", err);
    } finally {
      setRunningEval(false);
    }
  };

  const handleResolveIssue = async (id: string, status: "resolved" | "ignored") => {
    try {
      await fetch(`${API_BASE}/analytics/issues/${id}/resolve?status=${status}`, {
        method: "POST",
      });
      setIssues((prev) =>
        prev.map((item) => (item.id === id ? { ...item, status } : item))
      );
    } catch (err) {
      console.error("Error resolving issue:", err);
    }
  };

  const filteredIssues = issues.filter((iss) => {
    if (severityFilter === "all") return true;
    return iss.severity === severityFilter;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
            <ShieldCheck className="w-4 h-4" /> Stage 11 — Quality Control & Analytics
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Research Analytics & Quality Control
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Executive Metrics, Dataset Coverage, RAG Evaluation, Calibration Curve & Quality Flags.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-xl text-sm font-medium border border-slate-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh Metrics
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        {/* Executive Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
              <span>HADIS IMPOR</span>
              <BookOpen className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-white">
              {overview ? overview.total_hadith.toLocaleString() : "..."}
            </div>
            <div className="mt-3 flex items-center justify-between text-xs">
              <span className="text-slate-400">Hadith Coverage</span>
              <span className="font-semibold text-emerald-400">
                {overview?.hadith_coverage_pct}%
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
              <div
                className="bg-emerald-500 h-full rounded-full"
                style={{ width: `${overview?.hadith_coverage_pct || 0}%` }}
              />
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
              <span>BAGIAN SYARAH</span>
              <Layers className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-white">
              {overview ? overview.total_sharh.toLocaleString() : "..."}
            </div>
            <div className="mt-3 flex items-center justify-between text-xs">
              <span className="text-slate-400">Sharh Coverage</span>
              <span className="font-semibold text-blue-400">
                {overview?.sharh_coverage_pct}%
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
              <div
                className="bg-blue-500 h-full rounded-full"
                style={{ width: `${overview?.sharh_coverage_pct || 0}%` }}
              />
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
              <span>VERIFIKASI MANUSIA</span>
              <CheckCircle2 className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-white">
              {overview ? overview.verified_links.toLocaleString() : "..."}
            </div>
            <div className="mt-3 flex items-center justify-between text-xs">
              <span className="text-slate-400">Verification Rate</span>
              <span className="font-semibold text-purple-400">
                {overview?.verification_pct}%
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
              <div
                className="bg-purple-500 h-full rounded-full"
                style={{ width: `${overview?.verification_pct || 0}%` }}
              />
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
              <span>SUMBER KITAB</span>
              <Database className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-white">
              {overview ? overview.total_sources.toLocaleString() : "..."}
            </div>
            <div className="mt-3 flex items-center justify-between text-xs">
              <span className="text-slate-400">Pending Review</span>
              <span className="font-semibold text-amber-400">
                {overview?.pending_links}
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
              <div
                className="bg-amber-500 h-full rounded-full"
                style={{
                  width: `${
                    overview
                      ? Math.min(
                          100,
                          (overview.pending_links / Math.max(1, overview.total_links)) * 100
                        )
                      : 0
                  }%`,
                }}
              />
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2 ${
              activeTab === "overview"
                ? "bg-emerald-600 text-white shadow-lg"
                : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <BarChart3 className="w-4 h-4" /> Coverage & Volumes
          </button>

          <button
            onClick={() => setActiveTab("calibration")}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2 ${
              activeTab === "calibration"
                ? "bg-emerald-600 text-white shadow-lg"
                : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <TrendingUp className="w-4 h-4" /> Calibration Curve
          </button>

          <button
            onClick={() => setActiveTab("rag_eval")}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2 ${
              activeTab === "rag_eval"
                ? "bg-emerald-600 text-white shadow-lg"
                : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <Sparkles className="w-4 h-4" /> RAG & Retrieval Benchmark
          </button>

          <button
            onClick={() => setActiveTab("issues")}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2 ${
              activeTab === "issues"
                ? "bg-emerald-600 text-white shadow-lg"
                : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <AlertTriangle className="w-4 h-4" /> Quality Issues ({issues.length})
          </button>

          <button
            onClick={() => setActiveTab("reviewers")}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2 ${
              activeTab === "reviewers"
                ? "bg-emerald-600 text-white shadow-lg"
                : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <Users className="w-4 h-4" /> Reviewers & Inter-Rater
          </button>
        </div>

        {/* TAB 1: Coverage & Volumes */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Layers className="w-5 h-5 text-emerald-400" />
                Cakupan Verifikasi Per Volume Fathul Bari
              </h2>

              <div className="space-y-4">
                {volumes.map((vol) => (
                  <div
                    key={vol.volume}
                    className="bg-slate-950 border border-slate-800/80 rounded-xl p-4"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-slate-200">
                        Jilid / Volume {vol.volume}
                      </span>
                      <div className="flex items-center gap-4 text-xs">
                        <span className="text-slate-400">
                          {vol.verified_sections} / {vol.total_sections} Terverifikasi
                        </span>
                        <span className="font-bold text-emerald-400 text-sm">
                          {vol.coverage_pct}%
                        </span>
                      </div>
                    </div>
                    <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden flex">
                      <div
                        className="bg-emerald-500 h-full transition-all"
                        style={{ width: `${vol.coverage_pct}%` }}
                        title="Verified"
                      />
                      <div
                        className="bg-amber-500/60 h-full transition-all"
                        style={{
                          width: `${
                            vol.total_sections > 0
                              ? (vol.pending_sections / vol.total_sections) * 100
                              : 0
                          }%`,
                        }}
                        title="Pending"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: Calibration Curve */}
        {activeTab === "calibration" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <div className="mb-6">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-emerald-400" />
                  Confidence Calibration Curve
                </h2>
                <p className="text-slate-400 text-sm mt-1">
                  Membandingkan prediksi confidence score model AI dengan persentase verifikasi riil manusia.
                </p>
              </div>

              {confidence && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {/* Distribution list */}
                  <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
                      Distribusi Confidence Level
                    </h3>
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-emerald-400 font-medium">&gt; 90% Confidence</span>
                        <span className="font-bold text-white">
                          {confidence.distribution.high_confidence_pct90} links
                        </span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-blue-400 font-medium">70% - 90% Confidence</span>
                        <span className="font-bold text-white">
                          {confidence.distribution.mid_confidence_pct70_89} links
                        </span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-amber-400 font-medium">&lt; 70% Confidence</span>
                        <span className="font-bold text-white">
                          {confidence.distribution.low_confidence_below70} links
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Calibration Bins Table */}
                  <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
                      Kalibrasi Prediction vs Actual
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-950 text-slate-400 uppercase">
                          <tr>
                            <th className="p-3">Bin Range</th>
                            <th className="p-3 text-center">Pred. Conf</th>
                            <th className="p-3 text-center">Actual Verifiability</th>
                            <th className="p-3 text-right">Count</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {confidence.calibration_curve.map((row, idx) => (
                            <tr key={idx} className="hover:bg-slate-950/50">
                              <td className="p-3 font-medium text-slate-200">{row.range}</td>
                              <td className="p-3 text-center text-blue-400 font-semibold">
                                {row.predicted_conf_pct}%
                              </td>
                              <td className="p-3 text-center font-bold text-emerald-400">
                                {row.actual_verification_pct}%
                              </td>
                              <td className="p-3 text-right text-slate-400">{row.total_count}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: RAG & Retrieval Benchmark */}
        {activeTab === "rag_eval" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-emerald-400" />
                    Golden Dataset Retrieval & RAG Benchmark
                  </h2>
                  <p className="text-slate-400 text-sm mt-1">
                    Evaluasi akurasi pencarian (Recall@K, MRR, NDCG) dan tingkat groundedness AI.
                  </p>
                </div>

                <button
                  onClick={handleRunEvaluation}
                  disabled={runningEval}
                  className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-5 py-2.5 rounded-xl shadow-lg transition"
                >
                  {runningEval ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4 fill-white" />
                  )}
                  {runningEval ? "Running Benchmark..." : "Run Evaluation Benchmark"}
                </button>
              </div>

              {/* Benchmark Results */}
              {evalResult && (
                <div className="mb-8 grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="bg-slate-950 p-4 rounded-xl border border-emerald-900/50 text-center">
                    <span className="text-slate-400 text-xs font-semibold">RECALL @ 5</span>
                    <div className="text-2xl font-bold text-emerald-400 mt-1">
                      {Math.round(evalResult.recall_at_5 * 100)}%
                    </div>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-xl border border-blue-900/50 text-center">
                    <span className="text-slate-400 text-xs font-semibold">MRR SCORE</span>
                    <div className="text-2xl font-bold text-blue-400 mt-1">
                      {evalResult.mrr}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-xl border border-purple-900/50 text-center">
                    <span className="text-slate-400 text-xs font-semibold">NDCG SCORE</span>
                    <div className="text-2xl font-bold text-purple-400 mt-1">
                      {evalResult.ndcg}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-xl border border-amber-900/50 text-center">
                    <span className="text-slate-400 text-xs font-semibold">GROUNDEDNESS</span>
                    <div className="text-2xl font-bold text-amber-400 mt-1">
                      {Math.round(evalResult.groundedness_score * 100)}%
                    </div>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-xl border border-cyan-900/50 text-center">
                    <span className="text-slate-400 text-xs font-semibold">CITATION INTEGRITY</span>
                    <div className="text-2xl font-bold text-cyan-400 mt-1">
                      {Math.round(evalResult.citation_integrity_score * 100)}%
                    </div>
                  </div>
                </div>
              )}

              {/* Queries Table */}
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Golden Dataset Queries ({queries.length})
              </h3>
              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 uppercase">
                    <tr>
                      <th className="p-3">ID</th>
                      <th className="p-3">Query Evaluation</th>
                      <th className="p-3">Category</th>
                      <th className="p-3">Expected Hadiths</th>
                      <th className="p-3">Expected Sharh</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {queries.map((q) => (
                      <tr key={q.id} className="hover:bg-slate-950/50">
                        <td className="p-3 text-slate-500 font-mono">#{q.id}</td>
                        <td className="p-3 font-medium text-slate-200">{q.query}</td>
                        <td className="p-3">
                          <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full text-[10px] font-semibold">
                            {q.category}
                          </span>
                        </td>
                        <td className="p-3 text-emerald-400 font-mono">
                          {q.expected_hadith_ids.join(", ") || "-"}
                        </td>
                        <td className="p-3 text-blue-400 font-mono">
                          {q.expected_sharh_ids.join(", ") || "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: Quality Issues */}
        {activeTab === "issues" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                    Data Quality Issues & Automated Flags
                  </h2>
                  <p className="text-slate-400 text-sm mt-1">
                    Daftar isu kualitas data otomatis yang perlu ditinjau atau diperbaiki.
                  </p>
                </div>

                <div className="flex items-center gap-2 bg-slate-950 p-1.5 rounded-xl border border-slate-800">
                  {["all", "critical", "warning", "review"].map((sev) => (
                    <button
                      key={sev}
                      onClick={() => setSeverityFilter(sev)}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold uppercase transition ${
                        severityFilter === sev
                          ? "bg-emerald-600 text-white"
                          : "text-slate-400 hover:text-white"
                      }`}
                    >
                      {sev}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                {filteredIssues.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <CheckCircle2 className="w-10 h-10 mx-auto text-emerald-500 mb-2 opacity-50" />
                    Tidak ada isu kualitas data terbuka pada filter ini.
                  </div>
                ) : (
                  filteredIssues.map((iss) => (
                    <div
                      key={iss.id}
                      className={`bg-slate-950 border rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 transition ${
                        iss.status !== "open"
                          ? "opacity-50 border-slate-800"
                          : iss.severity === "critical"
                          ? "border-red-900/60 bg-red-950/10"
                          : iss.severity === "warning"
                          ? "border-amber-900/60 bg-amber-950/10"
                          : "border-slate-800"
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              iss.severity === "critical"
                                ? "bg-red-500/20 text-red-400 border border-red-500/30"
                                : iss.severity === "warning"
                                ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                                : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                            }`}
                          >
                            {iss.severity}
                          </span>
                          <h3 className="font-semibold text-slate-200 text-sm">{iss.title}</h3>
                        </div>
                        <p className="text-xs text-slate-400">{iss.description}</p>
                      </div>

                      {iss.status === "open" ? (
                        <div className="flex items-center gap-2 self-end md:self-auto">
                          <button
                            onClick={() => handleResolveIssue(iss.id, "resolved")}
                            className="flex items-center gap-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition"
                          >
                            <Check className="w-3.5 h-3.5" /> Resolve
                          </button>
                          <button
                            onClick={() => handleResolveIssue(iss.id, "ignored")}
                            className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold px-3 py-1.5 rounded-lg transition"
                          >
                            Ignore
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs text-emerald-400 font-semibold uppercase">
                          ✓ {iss.status}
                        </span>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: Reviewers & Inter-Rater */}
        {activeTab === "reviewers" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Inter Rater Agreement Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-1">
                    Inter-Rater Agreement
                  </h3>
                  <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <ShieldCheck className="w-6 h-6 text-emerald-400" />
                    Cohen's Kappa Score
                  </h2>
                  <p className="text-xs text-slate-400 mt-2">
                    Mengukur tingkat konsistensi persetujuan antar verifikator independen.
                  </p>
                </div>

                {interRater && (
                  <div className="my-6 space-y-3">
                    <div className="text-4xl font-extrabold text-emerald-400">
                      {interRater.cohens_kappa}
                    </div>
                    <div className="inline-block bg-emerald-950 text-emerald-300 border border-emerald-800 text-xs px-3 py-1 rounded-full font-semibold">
                      {interRater.agreement_level}
                    </div>
                    <div className="text-xs text-slate-400">
                      Observed Agreement:{" "}
                      <span className="text-white font-bold">
                        {interRater.observed_agreement_pct}%
                      </span>
                    </div>
                  </div>
                )}

                <div className="text-[11px] text-slate-500 border-t border-slate-800 pt-3">
                  Score &gt; 0.8 mengindikasikan tingkat keselarasan peninjauan yang sangat tinggi.
                </div>
              </div>

              {/* Reviewer Performance Table */}
              <div className="md:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
                  Beban Kerja & Performa Reviewer
                </h3>

                <div className="overflow-x-auto rounded-xl border border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 uppercase">
                      <tr>
                        <th className="p-3">Reviewer</th>
                        <th className="p-3 text-center">Verified</th>
                        <th className="p-3 text-center">Rejected</th>
                        <th className="p-3 text-center">Total</th>
                        <th className="p-3 text-right">Approval Rate</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {reviewers.map((rev, idx) => (
                        <tr key={idx} className="hover:bg-slate-950/50">
                          <td className="p-3 font-medium text-slate-200">{rev.reviewer}</td>
                          <td className="p-3 text-center text-emerald-400 font-bold">
                            {rev.verified_count}
                          </td>
                          <td className="p-3 text-center text-red-400 font-bold">
                            {rev.rejected_count}
                          </td>
                          <td className="p-3 text-center text-slate-300">{rev.total_reviewed}</td>
                          <td className="p-3 text-right font-semibold text-purple-400">
                            {rev.approval_rate_pct}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
