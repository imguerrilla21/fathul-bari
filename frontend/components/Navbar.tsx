"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  BookOpen,
  Bot,
  ShieldCheck,
  Search,
  BarChart3,
  Moon,
  Sun,
  Home,
  FileText,
  Network,
  Cpu,
  Sparkles,
  Database,
  Layers,
} from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const saved = localStorage.getItem("theme") as "dark" | "light" | null;
    if (saved) {
      setTheme(saved);
      document.documentElement.setAttribute("data-theme", saved);
    } else {
      document.documentElement.setAttribute("data-theme", "dark");
    }
  }, []);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
  };

  const navItems = [
    { href: "/", label: "Beranda", icon: Home },
    { href: "/hadith", label: "Pembaca Hadis", icon: BookOpen },
    { href: "/admin/scholarly-publication", label: "Scholarly Publication", icon: FileText, badge: "Tahap 25" },
    { href: "/admin/scholarly-citation", label: "Scholarly Citation", icon: FileText, badge: "Tahap 24" },
    { href: "/admin/research-workspace", label: "Research Workspace", icon: BookOpen, badge: "Tahap 23" },
    { href: "/admin/rag-evidence", label: "RAG Evidence", icon: Sparkles, badge: "Tahap 22" },
    { href: "/admin/fathul-bari-corpus", label: "Source Viewer", icon: FileText, badge: "Tahap 21" },
    { href: "/admin/matching-engine", label: "Hadith Matcher", icon: Layers, badge: "Tahap 20" },
    { href: "/admin/hadith-data-layer", label: "Hadith Data Layer", icon: Database, badge: "Tahap 19" },
    { href: "/graph", label: "Knowledge Graph", icon: Network, badge: "Tahap 9" },
    { href: "/admin/production-deployment", label: "Production Topology", icon: ShieldCheck, badge: "Tahap 17" },
    { href: "/admin/research-rag", label: "Research RAG", icon: Bot, badge: "Tahap 16" },
    { href: "/ai", label: "Syarah AI", icon: Bot, badge: "RAG" },
    { href: "/admin/nlp-matching", label: "Arabic NLP", icon: Sparkles, badge: "Tahap 15" },
    { href: "/admin/corpus-engine", label: "Corpus Engine", icon: Cpu, badge: "Tahap 14" },
    { href: "/admin/ingestion", label: "Corpus Ingestion", icon: FileText, badge: "Tahap 13" },
    { href: "/analytics", label: "Analytics & QA", icon: BarChart3, badge: "Tahap 11" },
    { href: "/admin", label: "Admin & Security", icon: ShieldCheck, badge: "Tahap 12" },
    { href: "/review", label: "Review Dashboard", icon: ShieldCheck, badge: "Tahap 5" },
    { href: "/source", label: "Source & Audit", icon: FileText, badge: "Tahap 6" },
    { href: "/search", label: "Pencarian", icon: Search },
    { href: "/dashboard", label: "Sinkronisasi", icon: BarChart3 },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[#1a4a39] bg-[#0b221a]/90 backdrop-blur-md transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo Brand */}
          <Link href="/" className="flex items-center gap-3.5 group">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#10b981] to-[#064e3b] border border-[#f59e0b]/40 flex items-center justify-center text-white font-extrabold text-xl shadow-lg shadow-[#10b981]/20 group-hover:scale-105 transition-transform">
              ف
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-[#ecfdf5] tracking-tight">
                  Fathul Bari Research
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/30">
                  Next.js App
                </span>
              </div>
              <p className="text-xs text-[#94a3b8]">
                Shahih al-Bukhari & Syarah Al-Hafizh Ibnu Hajar
              </p>
            </div>
          </Link>

          {/* Nav Links */}
          <nav className="hidden md:flex items-center gap-1.5 overflow-x-auto py-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-semibold transition-all whitespace-nowrap ${
                    isActive
                      ? "bg-gradient-to-r from-[#047857] to-[#10b981] text-white shadow-md shadow-[#10b981]/20 border border-[#10b981]"
                      : "text-[#94a3b8] hover:text-[#ecfdf5] hover:bg-[#0f2c22] border border-transparent"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                  {item.badge && (
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded-md font-bold uppercase ${
                        isActive
                          ? "bg-white/20 text-white"
                          : "bg-[#f59e0b]/20 text-[#f59e0b]"
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Actions & Theme Toggle */}
          <div className="flex items-center gap-3">
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#10b981]/10 border border-[#10b981]/25 text-[#10b981] text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse-dot" />
              <span>Backend Connected</span>
            </div>

            <button
              onClick={toggleTheme}
              className="p-2.5 rounded-xl border border-[#1a4a39] bg-[#0f2c22] text-[#ecfdf5] hover:border-[#10b981] transition-colors"
              title="Ganti Tema"
              aria-label="Ganti Tema"
            >
              {theme === "dark" ? (
                <Sun className="w-4 h-4 text-[#f59e0b]" />
              ) : (
                <Moon className="w-4 h-4 text-[#38bdf8]" />
              )}
            </button>
          </div>

        </div>

        {/* Mobile Navigation Row */}
        <div className="md:hidden flex items-center gap-1 overflow-x-auto pb-3 border-t border-[#1a4a39]/60 pt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap ${
                  isActive
                    ? "bg-[#10b981] text-white"
                    : "text-[#94a3b8] hover:bg-[#0f2c22]"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

      </div>
    </header>
  );
}
