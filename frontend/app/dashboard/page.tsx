"use client";

import { useState, useEffect } from "react";
import {
  BarChart3,
  RefreshCw,
  Zap,
  CheckCircle2,
  AlertCircle,
  Database,
  Globe,
  Clock,
  Layers,
  ArrowRight,
} from "lucide-react";
import {
  getCollectionsSummary,
  getSyncRuns,
  triggerSync,
} from "@/lib/api";
import { CollectionSummary, SyncRun } from "@/lib/types";
import { useToast } from "@/components/Toast";

export default function DashboardSyncPage() {
  const [collections, setCollections] = useState<CollectionSummary[]>([]);
  const [syncRuns, setSyncRuns] = useState<SyncRun[]>([]);
  const [syncStart, setSyncStart] = useState(1);
  const [syncEnd, setSyncEnd] = useState(10);
  const [syncMode, setSyncMode] = useState<"range" | "missing" | "all">("range");
  const [syncing, setSyncing] = useState(false);
  const [syncLog, setSyncLog] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const { showToast } = useToast();

  const loadData = async () => {
    setLoading(true);
    try {
      const [cols, runs] = await Promise.all([
        getCollectionsSummary().catch(() => []),
        getSyncRuns().catch(() => []),
      ]);
      setCollections(cols);
      setSyncRuns(runs);
    } catch (err: any) {
      showToast(`Gagal memuat data: ${err.message}`, "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTriggerSync = async () => {
    setSyncing(true);
    setSyncLog(`Menghubungkan ke Ahmad Sanusi API untuk hadis #${syncStart} s/d #${syncEnd}...`);
    try {
      const res = await triggerSync(syncStart, syncEnd, syncMode, "shahih_bukhari");
      setSyncLog(
        `✓ Sinkronisasi Selesai! Status: ${res.status} | Fetched: ${res.fetched} | Inserted: ${res.inserted} | Failed: ${res.failed}`
      );
      showToast(`Sinkronisasi #${syncStart}-#${syncEnd} berhasil diproses!`);
      loadData();
    } catch (err: any) {
      setSyncLog(`Error: ${err.message}`);
      showToast(`Gagal sinkronisasi: ${err.message}`, "error");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      
      {/* Header */}
      <div className="p-8 rounded-3xl bg-[#0b221a] border border-[#1a4a39] shadow-xl flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-extrabold text-xl text-[#ecfdf5]">
              Dashboard Sinkronisasi & Data
            </h1>
            <p className="text-xs text-[#94a3b8]">
              Integrasi Data Hadis Ahmad Sanusi API & Syarah Fathul Bari
            </p>
          </div>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#081a13] hover:bg-[#0f2c22] border border-[#1a4a39] text-xs font-bold text-[#ecfdf5] transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* Collection Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {collections.map((c) => (
          <div
            key={c.id || c.slug}
            className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39] shadow-xl space-y-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-[#10b981]" />
                <h3 className="font-bold text-base text-[#ecfdf5]">{c.name}</h3>
              </div>
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30">
                {c.slug}
              </span>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs text-[#94a3b8]">
                <span>Kelengkapan Data:</span>
                <span className="font-bold text-[#10b981]">{c.completion_percentage}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-[#081a13] overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-[#047857] to-[#10b981] rounded-full transition-all"
                  style={{ width: `${c.completion_percentage}%` }}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 pt-2 text-center">
              <div className="p-3 rounded-xl bg-[#081a13] border border-[#1a4a39]">
                <div className="text-[10px] text-[#94a3b8] uppercase">Tersimpan</div>
                <div className="text-base font-extrabold text-[#ecfdf5]">{c.total_stored}</div>
              </div>

              <div className="p-3 rounded-xl bg-[#081a13] border border-[#1a4a39]">
                <div className="text-[10px] text-[#94a3b8] uppercase">Target</div>
                <div className="text-base font-extrabold text-[#f59e0b]">{c.total_expected}</div>
              </div>

              <div className="p-3 rounded-xl bg-[#081a13] border border-[#1a4a39]">
                <div className="text-[10px] text-[#94a3b8] uppercase">Belum Ada</div>
                <div className="text-base font-extrabold text-[#38bdf8]">{c.missing_count}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Trigger Sync Panel */}
      <div className="p-8 rounded-3xl bg-gradient-to-br from-[#0b221a] to-[#0f2c22] border border-[#10b981]/40 shadow-xl space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-[#1a4a39]">
          <Zap className="w-5 h-5 text-[#f59e0b]" />
          <div>
            <h2 className="font-bold text-base text-[#ecfdf5]">
              Konsol Pemicu Sinkronisasi (Ahmad Sanusi API)
            </h2>
            <p className="text-xs text-[#94a3b8]">
              Unduh atau perbarui hadis secara live dan simpan ke database PostgreSQL lokal
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
          <div>
            <label className="text-xs font-bold text-[#94a3b8] uppercase block mb-1.5">
              Nomor Mulai:
            </label>
            <input
              type="number"
              min={1}
              max={7008}
              value={syncStart}
              onChange={(e) => setSyncStart(parseInt(e.target.value, 10) || 1)}
              className="w-full p-3 rounded-xl bg-[#081a13] border border-[#1a4a39] text-xs font-bold text-[#ecfdf5] focus:border-[#10b981] focus:outline-none"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-[#94a3b8] uppercase block mb-1.5">
              Nomor Selesai:
            </label>
            <input
              type="number"
              min={1}
              max={7008}
              value={syncEnd}
              onChange={(e) => setSyncEnd(parseInt(e.target.value, 10) || 10)}
              className="w-full p-3 rounded-xl bg-[#081a13] border border-[#1a4a39] text-xs font-bold text-[#ecfdf5] focus:border-[#10b981] focus:outline-none"
            />
          </div>

          <div>
            <button
              onClick={handleTriggerSync}
              disabled={syncing}
              className="w-full py-3 rounded-xl bg-[#10b981] hover:bg-[#0d9468] disabled:opacity-50 text-white font-bold text-xs shadow-lg shadow-[#10b981]/25 transition-all flex items-center justify-center gap-2"
            >
              {syncing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Memproses Sinkronisasi...</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  <span>Mulai Sinkronisasi</span>
                </>
              )}
            </button>
          </div>
        </div>

        {syncLog && (
          <div className="p-4 rounded-xl bg-[#081a13] border border-[#1a4a39] text-xs font-mono text-[#6ee7b7]">
            {syncLog}
          </div>
        )}
      </div>

      {/* Sync Runs History */}
      <div className="p-8 rounded-3xl bg-[#0b221a] border border-[#1a4a39] shadow-xl space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b border-[#1a4a39]">
          <Clock className="w-4 h-4 text-[#38bdf8]" />
          <h3 className="font-bold text-sm text-[#ecfdf5]">
            Riwayat Proses Sinkronisasi Terakhir
          </h3>
        </div>

        {syncRuns.length === 0 ? (
          <div className="p-6 text-center text-xs text-[#94a3b8]">
            Belum ada riwayat sinkronisasi batch yang dicatat.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#1a4a39] text-[#94a3b8]">
                  <th className="pb-3 font-semibold">Waktu</th>
                  <th className="pb-3 font-semibold">Koleksi</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold">Fetched</th>
                  <th className="pb-3 font-semibold">Inserted</th>
                  <th className="pb-3 font-semibold">Failed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a4a39]/50">
                {syncRuns.map((r) => (
                  <tr key={r.id} className="text-[#ecfdf5]">
                    <td className="py-3 font-mono text-[11px]">
                      {new Date(r.started_at).toLocaleString()}
                    </td>
                    <td className="py-3 font-semibold">{r.collection_slug}</td>
                    <td className="py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          r.status === "completed"
                            ? "bg-[#10b981]/20 text-[#10b981]"
                            : "bg-[#f43f5e]/20 text-[#f43f5e]"
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="py-3 font-mono">{r.total_fetched}</td>
                    <td className="py-3 font-mono text-[#10b981]">{r.total_inserted}</td>
                    <td className="py-3 font-mono text-[#f43f5e]">{r.total_failed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
