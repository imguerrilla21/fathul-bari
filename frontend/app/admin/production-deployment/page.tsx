"use client";

import React, { useState, useEffect } from "react";
import {
  Server,
  Database,
  Cpu,
  RefreshCw,
  Activity,
  CheckCircle2,
  AlertCircle,
  HardDrive,
  ShieldCheck,
  Zap,
  BarChart2,
  Clock,
  Layers,
  FileText,
  Play,
  RotateCcw,
  Sparkles,
} from "lucide-react";

const API_BASE = "http://localhost:8000/api/v1";

interface SystemStatus {
  overall_status: string;
  timestamp: string;
  services: {
    api_fastapi: { status: string; latency_ms: number };
    postgres_pgvector: { status: string; latency_ms: number };
    redis_cache: { status: string; hit_ratio: string };
    s3_object_storage: { status: string; bucket: string };
    background_worker_queue: { status: string; active_workers: number };
  };
}

interface WorkerJob {
  id: string;
  job_key: string;
  job_type: string;
  status: string;
  progress_pct: number;
  current_stage: string;
  pipeline_version: string;
  error_log: string | null;
  created_at: string;
}

interface ProductionMetrics {
  pipeline_version: string;
  operational_latencies: {
    api_response_avg_ms: number;
    vector_search_latency_ms: number;
    rag_synthesis_latency_ms: number;
    embedding_generation_ms: number;
  };
  scientific_quality_metrics: {
    recall_at_5_score: number;
    mrr_score: number;
    citation_validity_pct: number;
    unsupported_claim_rate_pct: number;
    human_review_acceptance_rate: number;
  };
  infrastructure_stats: {
    total_indexed_sources: number;
    total_extracted_pages: number;
    total_verified_hadith_links: number;
  };
}

interface MigrationLog {
  id: number;
  revision_id: string;
  version_num: string;
  description: string;
  applied_at: string;
}

export default function ProductionDeploymentPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [jobs, setJobs] = useState<WorkerJob[]>([]);
  const [metrics, setMetrics] = useState<ProductionMetrics | null>(null);
  const [migrations, setMigrations] = useState<MigrationLog[]>([]);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [backingUp, setBackingUp] = useState<boolean>(false);
  const [backupResult, setBackupResult] = useState<any>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sRes, jRes, mRes, migRes] = await Promise.all([
        fetch(`${API_BASE}/production/system-status`).then((r) => r.json()),
        fetch(`${API_BASE}/production/worker-jobs`).then((r) => r.json()),
        fetch(`${API_BASE}/production/metrics`).then((r) => r.json()),
        fetch(`${API_BASE}/production/migration-history`).then((r) => r.json()),
      ]);

      if (sRes && sRes.overall_status) setStatus(sRes);
      if (Array.isArray(jRes)) setJobs(jRes);
      if (mRes && mRes.pipeline_version) setMetrics(mRes);
      if (Array.isArray(migRes)) setMigrations(migRes);
    } catch (err) {
      console.error("Error fetching production deployment status:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleBackup = async () => {
    setBackingUp(true);
    setBackupResult(null);
    try {
      const res = await fetch(`${API_BASE}/production/disaster-recovery/backup`, {
        method: "POST",
      });
      const data = await res.json();
      setBackupResult(data);
    } catch (err) {
      console.error("Backup error:", err);
    } finally {
      setBackingUp(false);
    }
  };

  const handleRetryJob = async (jobId: string) => {
    try {
      await fetch(`${API_BASE}/production/worker-jobs/${jobId}/retry`, {
        method: "POST",
      });
      fetchData();
    } catch (err) {
      console.error("Retry error:", err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
            <Server className="w-4 h-4" /> Stage 17 — Production Implementation & Deployment Topology
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Production Operations & Deployment Control Panel
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Probe Kesehatan Layanan, Idempotent Async Worker Queue, Prometheus/OpenTelemetry Metrics, dan Disaster Recovery (RPO ≤ 24h).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-xl text-sm font-medium border border-slate-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh Probes
          </button>

          <button
            onClick={handleBackup}
            disabled={backingUp}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-lg transition"
          >
            <HardDrive className="w-4 h-4" />
            {backingUp ? "Backing up..." : "Trigger Backup Snapshot"}
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        {/* Backup Result Alert */}
        {backupResult && (
          <div className="bg-emerald-950/40 border border-emerald-800 rounded-2xl p-4 text-xs text-emerald-300 flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <div>
              <div className="font-bold">{backupResult.message}</div>
              <div className="font-mono text-[11px] opacity-80 mt-0.5">
                Database: {backupResult.database_snapshot} | Storage: {backupResult.object_storage_snapshot}
              </div>
            </div>
          </div>
        )}

        {/* Infrastructure Readiness & Health Status Probe Grid */}
        {status && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Activity className="w-5 h-5 text-emerald-400" />
                Infrastructure Readiness & Service Probes
              </h2>
              <span className="text-xs font-bold text-emerald-400 bg-emerald-950 border border-emerald-800 px-3 py-1 rounded-full">
                System Status: {status.overall_status}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-1">
                <div className="text-xs font-semibold text-slate-400 flex justify-between">
                  <span>FastAPI REST Server</span>
                  <span className="text-emerald-400 font-bold">{status.services.api_fastapi.status}</span>
                </div>
                <div className="text-lg font-bold text-white mt-1">{status.services.api_fastapi.latency_ms} ms</div>
                <div className="text-[10px] text-slate-500">FastAPI Async Uvicorn</div>
              </div>

              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-1">
                <div className="text-xs font-semibold text-slate-400 flex justify-between">
                  <span>PostgreSQL + pgvector</span>
                  <span className="text-emerald-400 font-bold">{status.services.postgres_pgvector.status}</span>
                </div>
                <div className="text-lg font-bold text-white mt-1">{status.services.postgres_pgvector.latency_ms} ms</div>
                <div className="text-[10px] text-slate-500">Vector HNSW Index</div>
              </div>

              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-1">
                <div className="text-xs font-semibold text-slate-400 flex justify-between">
                  <span>Redis Cache</span>
                  <span className="text-emerald-400 font-bold">{status.services.redis_cache.status}</span>
                </div>
                <div className="text-lg font-bold text-white mt-1">{status.services.redis_cache.hit_ratio}</div>
                <div className="text-[10px] text-slate-500">Ahmad Sanusi API Cache</div>
              </div>

              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-1">
                <div className="text-xs font-semibold text-slate-400 flex justify-between">
                  <span>S3 Object Storage</span>
                  <span className="text-emerald-400 font-bold">{status.services.s3_object_storage.status}</span>
                </div>
                <div className="text-xs font-bold text-slate-300 mt-1 truncate">{status.services.s3_object_storage.bucket}</div>
                <div className="text-[10px] text-slate-500">PDF & WebP Page Storage</div>
              </div>

              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-1">
                <div className="text-xs font-semibold text-slate-400 flex justify-between">
                  <span>Worker Queue</span>
                  <span className="text-emerald-400 font-bold">{status.services.background_worker_queue.status}</span>
                </div>
                <div className="text-lg font-bold text-white mt-1">{status.services.background_worker_queue.active_workers} Workers</div>
                <div className="text-[10px] text-slate-500">Celery Async Workers</div>
              </div>
            </div>
          </div>
        )}

        {/* Prometheus / OpenTelemetry Operational Metrics */}
        {metrics && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <BarChart2 className="w-5 h-5 text-blue-400" />
              Prometheus & OpenTelemetry Operational & Quality Telemetry
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                <div className="text-xs text-slate-400">RAG Synthesis Latency</div>
                <div className="text-2xl font-bold text-emerald-400 mt-1">
                  {metrics.operational_latencies.rag_synthesis_latency_ms} ms
                </div>
                <div className="text-[10px] text-slate-500 mt-1">Vector Search: {metrics.operational_latencies.vector_search_latency_ms} ms</div>
              </div>

              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                <div className="text-xs text-slate-400">Recall@5 Scientific Score</div>
                <div className="text-2xl font-bold text-blue-400 mt-1">
                  {metrics.scientific_quality_metrics.recall_at_5_score}%
                </div>
                <div className="text-[10px] text-slate-500 mt-1">MRR Score: {metrics.scientific_quality_metrics.mrr_score}</div>
              </div>

              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                <div className="text-xs text-slate-400">Citation Validity %</div>
                <div className="text-2xl font-bold text-purple-400 mt-1">
                  {metrics.scientific_quality_metrics.citation_validity_pct}%
                </div>
                <div className="text-[10px] text-slate-500 mt-1">Unsupported Claim Rate: 0.0%</div>
              </div>

              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                <div className="text-xs text-slate-400">Human Review Acceptance</div>
                <div className="text-2xl font-bold text-amber-400 mt-1">
                  {metrics.scientific_quality_metrics.human_review_acceptance_rate}%
                </div>
                <div className="text-[10px] text-slate-500 mt-1">Verified Links: {metrics.infrastructure_stats.total_verified_hadith_links}</div>
              </div>
            </div>
          </div>
        )}

        {/* Async Background Worker Jobs Tracker */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
            <Cpu className="w-5 h-5 text-amber-400" />
            Async Background Worker Jobs & Pipeline State Tracker
          </h2>

          <div className="space-y-3">
            {jobs.length === 0 ? (
              <div className="text-center py-6 text-slate-500 text-xs">
                Tidak ada job worker latar belakang yang aktif.
              </div>
            ) : (
              jobs.map((job) => (
                <div key={job.id} className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2 text-xs">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-200">{job.job_type}</span>
                      <span className="text-[10px] font-mono text-slate-500">[{job.job_key}]</span>
                      <span className="bg-emerald-950 text-emerald-400 text-[10px] font-bold px-2 py-0.5 rounded-full border border-emerald-800 uppercase">
                        {job.status}
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-slate-400">Stage: <strong className="text-emerald-400">{job.current_stage}</strong></span>
                      {job.status === "FAILED" && (
                        <button
                          onClick={() => handleRetryJob(job.id)}
                          className="flex items-center gap-1 bg-amber-950 border border-amber-800 text-amber-300 text-[11px] px-2 py-1 rounded transition"
                        >
                          <RotateCcw className="w-3 h-3" /> Retry Job
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-emerald-500 h-full transition-all duration-300" style={{ width: `${job.progress_pct}%` }} />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Database Migration Log (Alembic Versioning) */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
            <Layers className="w-5 h-5 text-purple-400" />
            Alembic Database Schema Migration History
          </h2>

          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase">
                <tr>
                  <th className="p-3">Revision ID</th>
                  <th className="p-3 text-center">Version</th>
                  <th className="p-3">Description</th>
                  <th className="p-3 text-right">Applied At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {migrations.map((mig) => (
                  <tr key={mig.id} className="hover:bg-slate-950/50">
                    <td className="p-3 font-mono font-bold text-slate-300">{mig.revision_id}</td>
                    <td className="p-3 text-center font-bold text-emerald-400">{mig.version_num}</td>
                    <td className="p-3 text-slate-300">{mig.description}</td>
                    <td className="p-3 text-right text-slate-500 font-mono">{mig.applied_at}</td>
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
