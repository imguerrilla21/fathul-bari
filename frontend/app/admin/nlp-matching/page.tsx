"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Search,
  CheckCircle2,
  AlertTriangle,
  Layers,
  BookOpen,
  Cpu,
  BarChart3,
  HelpCircle,
  ArrowRight,
  ShieldAlert,
  UserCheck,
  FileText,
  Activity,
  Zap,
} from "lucide-react";

const API_BASE = "http://localhost:8000/api/v1";

interface NLPAnalysisResult {
  raw_text: string;
  normalized_text_v2: string;
  tokens: string[];
  lemmas: string[];
  entities: {
    entity_text: string;
    entity_type: string;
    confidence: number;
  }[];
  sanad_chain_graph: {
    source: string;
    target: string;
    term: string;
  }[];
  matn_fingerprint: string[];
}

interface MatchExplanation {
  candidate_id: string;
  hadith_number: number;
  target_hadith_title: string;
  final_confidence_pct: number;
  rationale_bullets: string[];
  potential_issues: string[];
}

interface NLPEvaluationMetrics {
  evaluation_metrics: {
    recall_at_1: number;
    recall_at_5: number;
    mrr_score: number;
    ndcg_score: number;
    precision_at_1: number;
  };
  active_learning: {
    queue_size: number;
    priority_samples: any[];
  };
  total_candidates_evaluated: number;
}

export default function NLPMatchingPage() {
  const [inputText, setInputText] = useState<string>(
    "حدثنا عبد الله بن يوسف قال أخبرنا مالك عن ابن شهاب عن محمد بن جبير عن أبيه عن أبي هريرة رضي الله عنه قال: قال رسول الله صلى الله عليه وسلم: إنما الأعمال بالنيات. وقد تقدم حديث رقم 1 كما سيأتي في كتاب البيوع وفي رواية لمسلم."
  );
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysis, setAnalysis] = useState<NLPAnalysisResult | null>(null);

  const [loadingMetrics, setLoadingMetrics] = useState<boolean>(true);
  const [metrics, setMetrics] = useState<NLPEvaluationMetrics | null>(null);
  const [selectedExplanation, setSelectedExplanation] = useState<MatchExplanation | null>(null);

  const handleAnalyze = async () => {
    if (!inputText) return;
    setAnalyzing(true);
    try {
      const res = await fetch(`${API_BASE}/nlp/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: inputText }),
      });
      const data = await res.json();
      setAnalysis(data);
    } catch (err) {
      console.error("NLP analysis error:", err);
    } finally {
      setAnalyzing(false);
    }
  };

  const fetchMetrics = async () => {
    setLoadingMetrics(true);
    try {
      const res = await fetch(`${API_BASE}/evaluation/matcher`);
      const data = await res.json();
      setMetrics(data);
    } catch (err) {
      console.error("Metrics fetch error:", err);
    } finally {
      setLoadingMetrics(false);
    }
  };

  const fetchExplanation = async (candidateId: string = "dummy-id") => {
    try {
      const res = await fetch(`${API_BASE}/matching/${candidateId}/explanation`);
      const data = await res.json();
      setSelectedExplanation(data);
    } catch (err) {
      console.error("Explanation error:", err);
    }
  };

  useEffect(() => {
    handleAnalyze();
    fetchMetrics();
    fetchExplanation();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-1">
            <Sparkles className="w-4 h-4" /> Stage 15 — Arabic NLP & Advanced Hadith Matching
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Arabic NLP Analyzer & Explainable Matcher
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Lematisasi, Pengenal Entitas Teks (NER), Parser Sanad Graph, Explainable Rationale ("Why This Match?"), dan Metrik Evaluasi NLP.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        {/* Arabic Text Analyzer Workspace */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-emerald-400" />
                Arabic Text NLP Analyzer Workspace
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Uji coba instan pemrosesan Bahasa Arab v2, deteksi entitas, dan mata rantai sanad.
              </p>
            </div>

            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-4 py-2 rounded-xl text-sm transition shadow-lg"
            >
              {analyzing ? <Zap className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              {analyzing ? "Analyzing NLP..." : "Analisa Teks Arab"}
            </button>
          </div>

          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-100 font-arabic text-right leading-relaxed dir-rtl focus:outline-none focus:border-emerald-500 h-28"
          />

          {/* Analysis Results Display */}
          {analysis && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
              {/* NER Entities & Lemmas */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <UserCheck className="w-4 h-4 text-emerald-400" /> Entitas Teks (NER) & Rujukan Relatif
                </h3>

                <div className="flex flex-wrap gap-2">
                  {analysis.entities.map((e, idx) => (
                    <span
                      key={idx}
                      className={`px-3 py-1 rounded-full text-xs font-bold border ${
                        e.entity_type === "NARRATOR"
                          ? "bg-purple-950/40 border-purple-800 text-purple-300"
                          : e.entity_type === "PROPHET"
                          ? "bg-emerald-950/40 border-emerald-800 text-emerald-300"
                          : "bg-blue-950/40 border-blue-800 text-blue-300"
                      }`}
                    >
                      [{e.entity_type}] {e.entity_text}
                    </span>
                  ))}
                </div>

                <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs space-y-1">
                  <div className="font-semibold text-slate-400">Lemmas Ditemukan:</div>
                  <div className="flex flex-wrap gap-1.5 font-arabic dir-rtl">
                    {analysis.lemmas.map((l, i) => (
                      <span key={i} className="bg-slate-900 px-2 py-0.5 rounded text-emerald-400">
                        {l}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Sanad Transmission Graph */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-blue-400" /> Sanad Transmission Chain Graph
                </h3>

                <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2">
                  {analysis.sanad_chain_graph.length === 0 ? (
                    <div className="text-xs text-slate-500">Mata rantai perawi tidak terdeteksi.</div>
                  ) : (
                    analysis.sanad_chain_graph.map((link, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-xs font-arabic dir-rtl text-slate-300">
                        <span className="font-bold text-emerald-400">{link.source}</span>
                        <span className="text-slate-500 font-mono text-[10px]">[{link.term}] ➔</span>
                        <span className="font-bold text-blue-400">{link.target}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Explainable Match Rationale Card */}
        {selectedExplanation && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-amber-400" />
                Explainable Match Rationale Card ("Why This Match?")
              </h2>
              <span className="text-xs font-bold text-emerald-400 bg-emerald-950 border border-emerald-800 px-3 py-1 rounded-full">
                Confidence: {selectedExplanation.final_confidence_pct}%
              </span>
            </div>

            <div className="space-y-3">
              <div className="text-sm font-semibold text-slate-200">
                Target Hadis: <span className="text-slate-400 dir-rtl font-arabic">{selectedExplanation.target_hadith_title}</span>
              </div>

              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2">
                <div className="text-xs font-bold text-emerald-400">Bukti Kesesuaian (Evidence Bullets):</div>
                {selectedExplanation.rationale_bullets.map((b, idx) => (
                  <div key={idx} className="text-xs text-slate-300 flex items-center gap-2">
                    <span>{b}</span>
                  </div>
                ))}
              </div>

              {selectedExplanation.potential_issues.length > 0 && (
                <div className="bg-amber-950/20 border border-amber-800/60 rounded-xl p-3 text-xs text-amber-300">
                  {selectedExplanation.potential_issues[0]}
                </div>
              )}
            </div>
          </div>
        )}

        {/* NLP Evaluation Metrics & Active Learning Queue */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Metrics Breakdown */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-blue-400" />
                NLP Evaluation Benchmark Metrics
              </h2>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className="text-xs text-slate-400">Recall@5 Score</div>
                  <div className="text-2xl font-bold text-emerald-400 mt-1">
                    {metrics.evaluation_metrics.recall_at_5}%
                  </div>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className="text-xs text-slate-400">Mean Reciprocal Rank (MRR)</div>
                  <div className="text-2xl font-bold text-blue-400 mt-1">
                    {metrics.evaluation_metrics.mrr_score}
                  </div>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className="text-xs text-slate-400">NDCG Score</div>
                  <div className="text-2xl font-bold text-purple-400 mt-1">
                    {metrics.evaluation_metrics.ndcg_score}
                  </div>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className="text-xs text-slate-400">Precision@1 Score</div>
                  <div className="text-2xl font-bold text-amber-400 mt-1">
                    {metrics.evaluation_metrics.precision_at_1}%
                  </div>
                </div>
              </div>
            </div>

            {/* Active Learning Queue */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Zap className="w-5 h-5 text-amber-400" />
                  Active Learning Priority Queue
                </h2>
                <span className="text-xs text-amber-400 font-bold bg-amber-950 border border-amber-800 px-2.5 py-0.5 rounded-full">
                  {metrics.active_learning.queue_size} Samples
                </span>
              </div>

              <div className="space-y-2">
                {metrics.active_learning.priority_samples.map((item, idx) => (
                  <div key={idx} className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs flex justify-between items-center">
                    <div>
                      <div className="font-bold text-slate-200">Kandidat Hadis #{item.reference_number || "?"}</div>
                      <div className="text-slate-400 text-[11px] mt-0.5">{item.narrator || "Sanad"}</div>
                    </div>
                    <div className="text-amber-400 font-mono font-bold">
                      {(item.confidence * 100).toFixed(1)}%
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
