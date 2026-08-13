"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Bot,
  Send,
  Sparkles,
  ShieldCheck,
  BookOpen,
  Copy,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Quote,
  Check,
} from "lucide-react";
import { askAIAssistant, getAISuggestions, getAIStatus } from "@/lib/api";
import {
  AIResearchResponse,
  AISuggestionsResponse,
  AIStatusResponse,
} from "@/lib/types";
import { useToast } from "@/components/Toast";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  citations?: any[];
  audit?: any;
  provider?: string;
}

function SyarahAIAssistantContent() {
  const searchParams = useSearchParams();

  const initialQuery = searchParams.get("q") || "";
  const initialHadithNum = searchParams.get("n")
    ? parseInt(searchParams.get("n")!, 10)
    : null;

  const [query, setQuery] = useState(initialQuery);
  const [hadithNumber, setHadithNumber] = useState<number | string>(
    initialHadithNum || ""
  );
  const [mode, setMode] = useState<"syarah_focus" | "fiqh_faedah" | "sanad_matan">(
    "syarah_focus"
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<AISuggestionsResponse | null>(null);
  const [aiStatus, setAiStatus] = useState<AIStatusResponse | null>(null);
  const [copiedCitationIndex, setCopiedCitationIndex] = useState<string | null>(null);

  const { showToast } = useToast();
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function loadMeta() {
      try {
        const [suggData, statusData] = await Promise.all([
          getAISuggestions().catch(() => null),
          getAIStatus().catch(() => null),
        ]);
        if (suggData) setSuggestions(suggData);
        if (statusData) setAiStatus(statusData);
      } catch (err) {
        console.error("Error loading AI meta:", err);
      }
    }

    loadMeta();

    // Auto trigger if initial query provided
    if (initialQuery) {
      handleSend(initialQuery, initialHadithNum);
    }
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (customQ?: string, customNum?: number | null) => {
    const textToSend = (customQ !== undefined ? customQ : query).trim();
    const numToSend =
      customNum !== undefined
        ? customNum
        : typeof hadithNumber === "number"
        ? hadithNumber
        : parseInt(hadithNumber as string, 10) || null;

    if (!textToSend) {
      showToast("Tuliskan pertanyaan riset terlebih dahulu.", "warning");
      return;
    }

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: textToSend,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setQuery("");
    setLoading(true);

    try {
      const response: AIResearchResponse = await askAIAssistant(
        textToSend,
        numToSend,
        mode,
        "shahih_bukhari"
      );

      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer,
        timestamp: new Date().toLocaleTimeString(),
        citations: response.citations,
        audit: response.anti_hallucination_audit,
        provider: response.provider,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      showToast(`Gagal mendapatkan respon AI: ${err.message}`, "error");
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `⚠️ Terjadi kesalahan: ${err.message}. Pastikan backend FastAPI sedang berjalan.`,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCitation = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCitationIndex(id);
    showToast("Sitasi berhasil disalin ke clipboard!");
    setTimeout(() => setCopiedCitationIndex(null), 2500);
  };

  const clearChat = () => {
    setMessages([]);
    showToast("Riwayat percakapan dibersihkan.");
  };

  const formatMarkdown = (text: string) => {
    if (!text) return "";
    return text
      .split("\n\n")
      .map((block, idx) => {
        // Arabic quote in « »
        if (block.includes("«") && block.includes("»")) {
          const parts = block.split(/(«[^»]+»)/g);
          return (
            <div key={idx} className="my-3 space-y-2">
              {parts.map((p, pIdx) => {
                if (p.startsWith("«") && p.endsWith("»")) {
                  const arabicText = p.slice(1, -1).trim();
                  return (
                    <div
                      key={pIdx}
                      className="p-4 rounded-xl bg-black/40 border border-[#f59e0b]/40 border-r-4 border-r-[#f59e0b] my-2"
                    >
                      <p className="font-arabic text-xl sm:text-2xl text-right leading-loose text-[#fde68a]" dir="rtl">
                        {arabicText}
                      </p>
                    </div>
                  );
                }
                return <p key={pIdx}>{p}</p>;
              })}
            </div>
          );
        }

        // Headers ###
        if (block.startsWith("### ")) {
          return (
            <h3 key={idx} className="text-lg font-bold text-[#f59e0b] mt-4 mb-2 flex items-center gap-2">
              <span>📜</span> {block.replace("### ", "")}
            </h3>
          );
        }

        // Headers ####
        if (block.startsWith("#### ")) {
          return (
            <h4 key={idx} className="text-base font-bold text-[#ecfdf5] mt-3 mb-1">
              {block.replace("#### ", "")}
            </h4>
          );
        }

        // Bullet lists
        if (block.includes("\n- ") || block.startsWith("- ")) {
          const items = block.split("\n- ").map((item) => item.replace(/^- /, ""));
          return (
            <ul key={idx} className="list-disc list-inside space-y-1.5 my-2 text-sm text-[#ecfdf5]">
              {items.map((it, itIdx) => (
                <li key={itIdx} dangerouslySetInnerHTML={{ __html: it.replace(/\*\*(.*?)\*\*/g, "<b>$1</b>") }} />
              ))}
            </ul>
          );
        }

        // Blockquotes >
        if (block.startsWith("> ")) {
          return (
            <div
              key={idx}
              className="p-3 rounded-xl bg-[#081a13] border-l-4 border-[#10b981] my-2 text-sm text-[#ecfdf5] italic"
            >
              {block.replace(/^>\s*/gm, "")}
            </div>
          );
        }

        return (
          <p
            key={idx}
            className="text-sm sm:text-base leading-relaxed text-[#ecfdf5]"
            dangerouslySetInnerHTML={{
              __html: block.replace(/\*\*(.*?)\*\*/g, "<b>$1</b>"),
            }}
          />
        );
      });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-fade-in">
      
      {/* Sidebar: Engine Info & Preset Suggestions */}
      <aside className="lg:col-span-4 space-y-6">
        
        {/* Engine Status Card */}
        <div className="p-6 rounded-3xl bg-gradient-to-br from-[#0b221a] to-[#0f2c22] border border-[#10b981]/40 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#94a3b8]">
              RAG Engine Status
            </span>
            <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse-dot" />
          </div>

          <h2 className="text-lg font-bold text-[#10b981]">
            {aiStatus?.active_engine || "Built-in Scholarly Synthesizer"}
          </h2>

          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30 text-xs font-bold">
            <ShieldCheck className="w-4 h-4" />
            <span>Anti-Hallucination Guard Active</span>
          </div>

          <p className="text-xs text-[#94a3b8] leading-relaxed">
            Menjamin setiap kutipan teks Arab, nomor hadis, dan nomor halaman Fathul Bari diverifikasi dari basis data lokal.
          </p>
        </div>

        {/* Preset Prompt Categories */}
        <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39] space-y-4 shadow-xl">
          <div className="flex items-center gap-2 pb-3 border-b border-[#1a4a39]">
            <Sparkles className="w-4 h-4 text-[#f59e0b]" />
            <h3 className="font-bold text-sm text-[#ecfdf5]">
              Topik Riset Rekomendasi
            </h3>
          </div>

          <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-1">
            {suggestions?.categories?.map((cat, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-[#f59e0b] uppercase tracking-wider">
                  <span>{cat.icon}</span>
                  <span>{cat.category}</span>
                </div>

                <div className="space-y-2">
                  {cat.questions.map((q, qIdx) => (
                    <button
                      key={qIdx}
                      onClick={() => {
                        setQuery(q.prompt);
                        if (q.hadith_number) setHadithNumber(q.hadith_number);
                        handleSend(q.prompt, q.hadith_number);
                      }}
                      className="w-full text-left p-3 rounded-2xl bg-[#081a13] border border-[#1a4a39] hover:border-[#f59e0b] hover:bg-[#0f2c22] transition-all group block"
                    >
                      <div className="font-bold text-xs text-[#10b981] group-hover:text-[#6ee7b7] mb-1">
                        {q.title}
                      </div>
                      <div className="text-[11px] text-[#94a3b8] line-clamp-2 leading-relaxed">
                        {q.prompt}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

      </aside>

      {/* Main Research Console & Chat Feed */}
      <main className="lg:col-span-8 space-y-6 flex flex-col min-h-[75vh]">
        
        {/* Research Mode & Console Card */}
        <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39] shadow-xl space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <span className="text-xl">🤖</span>
              <h2 className="font-bold text-base text-[#ecfdf5]">
                Konsol Riset Syarah AI (RAG)
              </h2>
            </div>

            <button
              onClick={clearChat}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#081a13] hover:bg-[#0f2c22] text-[#94a3b8] hover:text-[#ecfdf5] border border-[#1a4a39] text-xs font-semibold transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Reset Chat</span>
            </button>
          </div>

          {/* Mode Selector Chips */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-[#94a3b8] mr-1">Fokus Riset:</span>
            
            <button
              onClick={() => setMode("syarah_focus")}
              className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition-all ${
                mode === "syarah_focus"
                  ? "bg-[#10b981] text-white shadow-md shadow-[#10b981]/25"
                  : "bg-[#081a13] text-[#94a3b8] border border-[#1a4a39] hover:text-[#ecfdf5]"
              }`}
            >
              📖 Syarah Ibnu Hajar
            </button>

            <button
              onClick={() => setMode("fiqh_faedah")}
              className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition-all ${
                mode === "fiqh_faedah"
                  ? "bg-[#f59e0b] text-white shadow-md shadow-[#f59e0b]/25"
                  : "bg-[#081a13] text-[#94a3b8] border border-[#1a4a39] hover:text-[#ecfdf5]"
              }`}
            >
              ⚖️ Faedah Hukum & Fikih
            </button>

            <button
              onClick={() => setMode("sanad_matan")}
              className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition-all ${
                mode === "sanad_matan"
                  ? "bg-[#38bdf8] text-white shadow-md shadow-[#38bdf8]/25"
                  : "bg-[#081a13] text-[#94a3b8] border border-[#1a4a39] hover:text-[#ecfdf5]"
              }`}
            >
              🔍 Teks Arab & Matan
            </button>
          </div>

          {/* Query Input Box */}
          <div className="space-y-3 pt-2">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Tuliskan pertanyaan riset hadis & Syarah Fathul Bari di sini... (Shift + Enter untuk baris baru)"
              rows={3}
              className="w-full p-4 rounded-2xl bg-[#081a13] border border-[#1a4a39] text-[#ecfdf5] placeholder-[#94a3b8] focus:border-[#10b981] focus:outline-none text-sm font-medium resize-none transition-all leading-relaxed"
            />

            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <label className="text-xs font-semibold text-[#94a3b8]">No. Hadis (Opsional):</label>
                <input
                  type="number"
                  placeholder="Auto"
                  value={hadithNumber}
                  onChange={(e) => setHadithNumber(e.target.value)}
                  className="w-20 px-3 py-1.5 rounded-xl bg-[#081a13] border border-[#1a4a39] text-xs font-bold text-center text-[#ecfdf5] focus:border-[#10b981] focus:outline-none"
                />
              </div>

              <button
                onClick={() => handleSend()}
                disabled={loading || !query.trim()}
                className="px-6 py-2.5 rounded-2xl bg-[#10b981] hover:bg-[#0d9468] disabled:opacity-40 text-white font-bold text-sm shadow-lg shadow-[#10b981]/25 flex items-center gap-2 transition-all hover:scale-105"
              >
                <span>{loading ? "Memproses..." : "Kirim Pertanyaan"}</span>
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Conversation Feed */}
        <div className="space-y-6 flex-1">
          {messages.length === 0 ? (
            <div className="p-8 rounded-3xl bg-[#0b221a] border border-[#1a4a39] text-center text-[#94a3b8] space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-[#10b981]/15 text-[#10b981] flex items-center justify-center mx-auto">
                <Bot className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-base text-[#ecfdf5]">
                Selamat Datang di Syarah AI Assistant
              </h3>
              <p className="text-xs max-w-md mx-auto leading-relaxed">
                Silakan ketik pertanyaan Anda atau pilih salah satu topik riset di samping kiri untuk memulai telaah ilmiah Shahih al-Bukhari & Fathul Bari.
              </p>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`p-6 sm:p-8 rounded-3xl border shadow-xl space-y-4 animate-fade-in ${
                  msg.role === "user"
                    ? "bg-[#0b221a] border-[#f59e0b]/40 border-l-4 border-l-[#f59e0b]"
                    : "bg-[#0b221a] border-[#10b981]/40 border-l-4 border-l-[#10b981]"
                }`}
              >
                {/* Message Header */}
                <div className="flex items-center justify-between pb-3 border-b border-[#1a4a39]/60">
                  <div className="flex items-center gap-2">
                    {msg.role === "user" ? (
                      <span className="font-bold text-sm text-[#f59e0b]">
                        Pertanyaan Peneliti
                      </span>
                    ) : (
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-[#10b981]">
                          Syarah AI Assistant
                        </span>
                        {msg.provider && (
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30">
                            {msg.provider}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  <span className="text-xs text-[#94a3b8] font-mono">
                    {msg.timestamp}
                  </span>
                </div>

                {/* Message Body */}
                <div className="space-y-2">
                  {msg.role === "user" ? (
                    <p className="text-base font-semibold text-[#ecfdf5] leading-relaxed">
                      {msg.content}
                    </p>
                  ) : (
                    <div className="space-y-3">{formatMarkdown(msg.content)}</div>
                  )}
                </div>

                {/* Citations Deck for Assistant Message */}
                {msg.role === "assistant" && msg.citations && msg.citations.length > 0 && (
                  <div className="pt-4 border-t border-[#1a4a39]/80 space-y-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-[#f59e0b] uppercase tracking-wider">
                      <Quote className="w-4 h-4" />
                      <span>Rujukan & Sitasi Terverifikasi:</span>
                    </div>

                    <div className="space-y-2">
                      {msg.citations.map((cit: any, cIdx: number) => {
                        const citId = `${msg.id}-${cIdx}`;
                        return (
                          <div
                            key={cIdx}
                            className="p-3 rounded-2xl bg-[#081a13] border border-[#1a4a39] flex items-center justify-between flex-wrap gap-3"
                          >
                            <div className="flex items-center gap-2 flex-1 min-w-[200px]">
                              <span className="text-xs text-[#ecfdf5] leading-relaxed">
                                {cit.standard_citation ||
                                  `Fathul Bari Jilid ${cit.volume} Hal. ${cit.page}`}
                              </span>
                              {cit.verified ? (
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#10b981]/20 text-[#10b981] border border-[#10b981]/30 flex items-center gap-0.5 whitespace-nowrap">
                                  <CheckCircle2 className="w-3 h-3" />
                                  <span>Verified</span>
                                </span>
                              ) : (
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/30 whitespace-nowrap">
                                  Candidate
                                </span>
                              )}
                            </div>

                            <div className="flex items-center gap-2">
                              {cit.related_hadith && (
                                <Link
                                  href={`/hadith/${cit.related_hadith}`}
                                  className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-[#0b221a] hover:bg-[#0f2c22] border border-[#1a4a39] text-xs font-semibold text-[#10b981] transition-colors"
                                >
                                  <BookOpen className="w-3.5 h-3.5" />
                                  <span>Buka Hadis</span>
                                </Link>
                              )}

                              <button
                                onClick={() =>
                                  handleCopyCitation(
                                    cit.standard_citation ||
                                      `Fathul Bari Jilid ${cit.volume} Hal. ${cit.page}`,
                                    citId
                                  )
                                }
                                className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-[#0b221a] hover:bg-[#0f2c22] border border-[#1a4a39] text-xs font-semibold text-[#f59e0b] transition-colors"
                              >
                                {copiedCitationIndex === citId ? (
                                  <Check className="w-3.5 h-3.5 text-[#10b981]" />
                                ) : (
                                  <Copy className="w-3.5 h-3.5" />
                                )}
                                <span>Salin</span>
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Anti-hallucination Audit Badge */}
                {msg.role === "assistant" && (
                  <div className="pt-2">
                    <div className="p-3 rounded-2xl bg-[#10b981]/10 border border-[#10b981]/25 flex items-center justify-between flex-wrap gap-2 text-xs text-[#10b981]">
                      <div className="flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-[#10b981]" />
                        <span className="font-semibold">
                          Audit Anti-Halusinasi:{" "}
                          {msg.audit?.passed
                            ? "Lulus 100% (Semua rujukan hadis & halaman terverifikasi)"
                            : "Peringatan konteks luar database"}
                        </span>
                      </div>
                      <span className="font-mono text-[11px] text-[#6ee7b7]">
                        Provenance: Ahmad Sanusi API ↔ Fathul Bari DB
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}

          {/* Loading Indicator Card */}
          {loading && (
            <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#10b981]/40 shadow-xl flex items-center gap-4 animate-pulse">
              <div className="w-8 h-8 rounded-full border-2 border-[#10b981] border-t-transparent animate-spin" />
              <div>
                <p className="font-bold text-sm text-[#10b981]">
                  Menelusuri Matan Hadis & Syarah Fathul Bari...
                </p>
                <p className="text-xs text-[#94a3b8]">
                  Menjalankan Hybrid RAG Retrieval, sintesis turats, dan audit anti-halusinasi.
                </p>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

      </main>

    </div>
  );
}

export default function SyarahAIAssistantPage() {
  return (
    <Suspense
      fallback={
        <div className="py-20 text-center text-[#94a3b8]">
          <div className="w-8 h-8 rounded-full border-2 border-[#10b981] border-t-transparent animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium">Memuat Syarah AI Assistant...</p>
        </div>
      }
    >
      <SyarahAIAssistantContent />
    </Suspense>
  );
}

