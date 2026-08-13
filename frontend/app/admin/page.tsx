"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Users,
  Key,
  Lock,
  Activity,
  Cpu,
  Database,
  FileCode,
  DollarSign,
  AlertOctagon,
  CheckCircle,
  RefreshCw,
  UserCheck,
  UserPlus,
  Shield,
  Layers,
  Server,
  Zap,
} from "lucide-react";

const API_BASE = "http://localhost:8000/api/v1";

interface UserItem {
  id: string;
  email: string;
  username: string;
  role: "reader" | "researcher" | "reviewer" | "admin";
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

interface SecuritySummary {
  failed_login_attempts: number;
  rate_limit_violations: number;
  suspicious_requests: number;
  unauthorized_api_attempts: number;
  active_users_count: number;
  total_users_count: number;
  security_features: {
    https_ssl: boolean;
    jwt_authentication: boolean;
    role_based_access_control: boolean;
    immutable_audit_logging: boolean;
    api_rate_limiting: boolean;
    security_headers: boolean;
  };
}

interface AIUsageStats {
  total_requests: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_latency_ms: number;
}

interface PromptItem {
  id: number;
  name: string;
  version: string;
  system_prompt: string;
  is_active: boolean;
  created_at: string;
}

interface ReadinessData {
  status: string;
  database: string;
  redis_cache: string;
  vector_store: string;
  object_storage: string;
  hadiths_loaded: number;
  sharh_sections_loaded: number;
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<
    "security" | "users" | "ai_cost" | "prompts" | "readiness"
  >("security");

  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [securitySummary, setSecuritySummary] = useState<SecuritySummary | null>(null);
  const [aiUsage, setAiUsage] = useState<AIUsageStats | null>(null);
  const [prompts, setPrompts] = useState<PromptItem[]>([]);
  const [readiness, setReadiness] = useState<ReadinessData | null>(null);

  const [loginEmail, setLoginEmail] = useState("admin@fathulbari.id");
  const [loginPassword, setLoginPassword] = useState("admin123_change_in_prod");
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<any>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [uRes, secRes, aiRes, pRes, rRes] = await Promise.all([
        fetch(`${API_BASE}/admin/users`).then((r) => r.json()),
        fetch(`${API_BASE}/admin/security-summary`).then((r) => r.json()),
        fetch(`${API_BASE}/admin/ai-usage`).then((r) => r.json()),
        fetch(`${API_BASE}/admin/prompts`).then((r) => r.json()),
        fetch(`http://localhost:8000/ready`).then((r) => r.json()),
      ]);

      if (Array.isArray(uRes)) setUsers(uRes);
      setSecuritySummary(secRes);
      setAiUsage(aiRes);
      if (Array.isArray(pRes)) setPrompts(pRes);
      setReadiness(rRes);
    } catch (err) {
      console.error("Error fetching admin data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });
      const data = await res.json();
      if (data.access_token) {
        setAuthToken(data.access_token);
        setCurrentUser(data.user);
        alert(`Login berhasil sebagai ${data.user.email} (${data.user.role})`);
      } else {
        alert(data.detail || "Login gagal");
      }
    } catch (err) {
      console.error("Login error:", err);
    }
  };

  const handleUpdateRole = async (userId: string, newRole: string) => {
    try {
      await fetch(`${API_BASE}/admin/users/${userId}/role`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: newRole }),
      });
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, role: newRole as any } : u))
      );
    } catch (err) {
      console.error("Update role error:", err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
            <ShieldCheck className="w-4 h-4" /> Stage 12 — Production Hardening & Security
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Admin Security & Governance Center
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            RBAC User Roles, Authentication, AI Token Cost Control, Prompt Versioning & Health Readiness.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-xl text-sm font-medium border border-slate-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        {/* Quick Auth Status & Login Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1">
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">
              Status Otentikasi Pengguna
            </span>
            <div className="flex items-center gap-3">
              <span className="text-lg font-bold text-white">
                {currentUser ? currentUser.email : "Default Guest/Admin"}
              </span>
              <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase">
                {currentUser ? currentUser.role : "ADMIN"}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {authToken ? "JWT Bearer Token Aktif" : "Sistem terkonfigurasi dengan role RBAC."}
            </p>
          </div>

          {!authToken && (
            <form onSubmit={handleLogin} className="flex flex-col sm:flex-row items-center gap-2">
              <input
                type="email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                placeholder="Admin Email"
                className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              />
              <input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                placeholder="Password"
                className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              />
              <button
                type="submit"
                className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-4 py-2 rounded-xl transition"
              >
                Login JWT
              </button>
            </form>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
          <button
            onClick={() => setActiveTab("security")}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2 ${
              activeTab === "security"
                ? "bg-emerald-600 text-white shadow-lg"
                : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <Shield className="w-4 h-4" /> Security Summary
          </button>

          <button
            onClick={() => setActiveTab("users")}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2 ${
              activeTab === "users"
                ? "bg-emerald-600 text-white shadow-lg"
                : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <Users className="w-4 h-4" /> Users & RBAC Roles ({users.length})
          </button>

          <button
            onClick={() => setActiveTab("ai_cost")}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2 ${
              activeTab === "ai_cost"
                ? "bg-emerald-600 text-white shadow-lg"
                : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <DollarSign className="w-4 h-4" /> AI Cost & Token Control
          </button>

          <button
            onClick={() => setActiveTab("prompts")}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2 ${
              activeTab === "prompts"
                ? "bg-emerald-600 text-white shadow-lg"
                : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <FileCode className="w-4 h-4" /> Prompt Versioning
          </button>

          <button
            onClick={() => setActiveTab("readiness")}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2 ${
              activeTab === "readiness"
                ? "bg-emerald-600 text-white shadow-lg"
                : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <Server className="w-4 h-4" /> Health & Readiness Probes
          </button>
        </div>

        {/* TAB 1: Security Summary */}
        {activeTab === "security" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Security Features Checklist */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-400" />
                  Fitur Keamanan Production
                </h2>
                <div className="space-y-3">
                  {securitySummary?.security_features &&
                    Object.entries(securitySummary.security_features).map(
                      ([key, enabled]) => (
                        <div
                          key={key}
                          className="flex items-center justify-between bg-slate-950 p-3 rounded-xl border border-slate-800"
                        >
                          <span className="text-sm font-medium text-slate-300 capitalize">
                            {key.replace(/_/g, " ")}
                          </span>
                          {enabled ? (
                            <span className="flex items-center gap-1 text-xs font-bold text-emerald-400">
                              <CheckCircle className="w-4 h-4" /> ACTIVE
                            </span>
                          ) : (
                            <span className="text-xs text-slate-500">DISABLED</span>
                          )}
                        </div>
                      )
                    )}
                </div>
              </div>

              {/* Security Audit Counters */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Lock className="w-5 h-5 text-emerald-400" />
                  Statistik Audit Keamanan Real-time
                </h2>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                    <span className="text-xs text-slate-400 font-semibold">FAILED LOGINS</span>
                    <div className="text-2xl font-bold text-slate-200 mt-1">
                      {securitySummary?.failed_login_attempts}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                    <span className="text-xs text-slate-400 font-semibold">RATE LIMIT VIOLATIONS</span>
                    <div className="text-2xl font-bold text-slate-200 mt-1">
                      {securitySummary?.rate_limit_violations}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                    <span className="text-xs text-slate-400 font-semibold">UNAUTHORIZED API</span>
                    <div className="text-2xl font-bold text-slate-200 mt-1">
                      {securitySummary?.unauthorized_api_attempts}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                    <span className="text-xs text-slate-400 font-semibold">ACTIVE SESSIONS</span>
                    <div className="text-2xl font-bold text-emerald-400 mt-1">
                      {securitySummary?.active_users_count}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: Users & RBAC Roles */}
        {activeTab === "users" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Users className="w-5 h-5 text-emerald-400" />
                Manajemen Pengguna & Hak Akses (RBAC)
              </h2>

              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 uppercase">
                    <tr>
                      <th className="p-3">Username</th>
                      <th className="p-3">Email</th>
                      <th className="p-3">Current Role</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Ubah Role Access</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {users.map((u) => (
                      <tr key={u.id} className="hover:bg-slate-950/50">
                        <td className="p-3 font-semibold text-slate-200">{u.username}</td>
                        <td className="p-3 text-slate-400">{u.email}</td>
                        <td className="p-3">
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                              u.role === "admin"
                                ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                                : u.role === "reviewer"
                                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                : u.role === "researcher"
                                ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                                : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            {u.role}
                          </span>
                        </td>
                        <td className="p-3">
                          {u.is_active ? (
                            <span className="text-emerald-400 font-semibold">Active</span>
                          ) : (
                            <span className="text-slate-500">Disabled</span>
                          )}
                        </td>
                        <td className="p-3 text-right">
                          <select
                            value={u.role}
                            onChange={(e) => handleUpdateRole(u.id, e.target.value)}
                            className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                          >
                            <option value="reader">Reader</option>
                            <option value="researcher">Researcher</option>
                            <option value="reviewer">Reviewer</option>
                            <option value="admin">Admin</option>
                          </select>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: AI Cost & Token Control */}
        {activeTab === "ai_cost" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-emerald-400" />
                AI Token Consumption & Cost Control
              </h2>

              {aiUsage && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                    <span className="text-xs text-slate-400 font-semibold">TOTAL AI REQUESTS</span>
                    <div className="text-2xl font-bold text-emerald-400 mt-1">
                      {aiUsage.total_requests}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                    <span className="text-xs text-slate-400 font-semibold">TOTAL TOKENS</span>
                    <div className="text-2xl font-bold text-blue-400 mt-1">
                      {aiUsage.total_tokens.toLocaleString()}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                    <span className="text-xs text-slate-400 font-semibold">ESTIMATED COST</span>
                    <div className="text-2xl font-bold text-purple-400 mt-1">
                      ${aiUsage.total_cost_usd} USD
                    </div>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                    <span className="text-xs text-slate-400 font-semibold">AVG LATENCY</span>
                    <div className="text-2xl font-bold text-amber-400 mt-1">
                      {aiUsage.avg_latency_ms} ms
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: Prompt Versioning */}
        {activeTab === "prompts" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <FileCode className="w-5 h-5 text-emerald-400" />
                Prompt Templates & Versioning Engine
              </h2>

              <div className="space-y-3">
                {prompts.map((p) => (
                  <div
                    key={p.id}
                    className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-200">{p.name}</span>
                        <span className="bg-emerald-500/20 text-emerald-400 text-xs px-2 py-0.5 rounded font-mono font-bold">
                          v{p.version}
                        </span>
                      </div>
                      {p.is_active && (
                        <span className="text-xs font-bold text-emerald-400 uppercase">
                          ✓ Active Version
                        </span>
                      )}
                    </div>
                    <pre className="bg-slate-900 p-3 rounded-lg text-xs text-slate-300 font-mono overflow-x-auto">
                      {p.system_prompt}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: Health & Readiness */}
        {activeTab === "readiness" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Server className="w-5 h-5 text-emerald-400" />
                System Health & Readiness Probes
              </h2>

              {readiness && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                    <span className="text-xs text-slate-400 font-semibold">SYSTEM STATUS</span>
                    <div className="text-xl font-bold text-emerald-400 mt-1 uppercase">
                      {readiness.status}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                    <span className="text-xs text-slate-400 font-semibold">DATABASE CONNECTION</span>
                    <div className="text-xl font-bold text-emerald-400 mt-1 uppercase">
                      {readiness.database}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                    <span className="text-xs text-slate-400 font-semibold">VECTOR STORE</span>
                    <div className="text-xl font-bold text-emerald-400 mt-1 uppercase">
                      {readiness.vector_store}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                    <span className="text-xs text-slate-400 font-semibold">OBJECT STORAGE</span>
                    <div className="text-xl font-bold text-emerald-400 mt-1 uppercase">
                      {readiness.object_storage}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
