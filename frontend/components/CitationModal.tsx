"use client";

import React, { useState } from "react";
import { X, Copy, Check, BookOpen } from "lucide-react";
import { useToast } from "./Toast";

interface CitationModalProps {
  isOpen: boolean;
  onClose: () => void;
  hadithNumber?: number | null;
  collectionName?: string;
  volume?: number | null;
  page?: number | null;
  sharhTitle?: string | null;
  arabicExcerpt?: string | null;
}

export default function CitationModal({
  isOpen,
  onClose,
  hadithNumber,
  collectionName = "Shahih al-Bukhari",
  volume = 1,
  page = 9,
  sharhTitle,
  arabicExcerpt,
}: CitationModalProps) {
  const { showToast } = useToast();
  const [copiedFormat, setCopiedFormat] = useState<string | null>(null);

  if (!isOpen) return null;

  const volStr = volume ? `Jilid ${volume}` : "Jilid -";
  const halStr = page ? `Hal. ${page}` : "Hal. -";
  const numStr = hadithNumber ? `No. ${hadithNumber}` : "No. -";

  // 1. Standar Turats / Indonesia
  const standardCitation = `Ibnu Hajar al-Asqalani. Fathul Bari Syarah Shahih al-Bukhari, ${volStr}, ${halStr}. Penjelasan Hadis ${collectionName} ${numStr}.`;

  // 2. Format Chicago
  const chicagoCitation = `Al-Asqalani, Ahmad bin Ali bin Hajar. Fathul Bari Syarah Shahih al-Bukhari. ${volStr}, hlm. ${page || "-"}. (Syarah terhadap ${collectionName} ${numStr}).`;

  // 3. Format BibTeX
  const bibtexKey = `fathul_bari_v${volume || 1}_p${page || 1}_h${hadithNumber || 1}`;
  const bibtexCitation = `@incollection{${bibtexKey},
  author    = {Al-Asqalani, Ahmad ibn Ali ibn Hajar},
  title     = {${sharhTitle || `Syarah Hadis ${numStr}`}},
  booktitle = {Fathul Bari Syarah Shahih al-Bukhari},
  volume    = {${volume || 1}},
  pages     = {${page || 1}},
  note      = {Syarah terhadap ${collectionName} ${numStr}},
  publisher = {Darul Kutub al-Ilmiyyah},
  address   = {Beirut, Lebanon}
}`;

  // 4. Format Markdown
  const markdownCitation = `> **Sitasi:** ${standardCitation}${
    arabicExcerpt ? `\n>\n> *Matan:* « ${arabicExcerpt} »` : ""
  }`;

  const copyToClip = (text: string, formatName: string) => {
    navigator.clipboard.writeText(text);
    setCopiedFormat(formatName);
    showToast(`Sitasi format ${formatName} berhasil disalin!`);
    setTimeout(() => setCopiedFormat(null), 2500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-2xl bg-[#0b221a] border border-[#10b981]/40 rounded-2xl p-6 shadow-2xl relative text-[#ecfdf5]">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#1a4a39] mb-5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-lg text-[#ecfdf5]">
                Sitasi Akademik Terstandar
              </h3>
              <p className="text-xs text-[#94a3b8]">
                Rujukan ilmiah resmi Fathul Bari & Hadis {collectionName} {numStr}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-[#0f2c22] text-[#94a3b8] hover:text-[#ecfdf5] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Citations List */}
        <div className="space-y-4 max-h-[65vh] overflow-y-auto pr-1">
          
          {/* Format 1: Standar Turats */}
          <div className="p-4 rounded-xl bg-[#081a13] border border-[#1a4a39]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-[#f59e0b] uppercase tracking-wider">
                1. Standar Turats (Indonesia)
              </span>
              <button
                onClick={() => copyToClip(standardCitation, "Standar Turats")}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#10b981]/15 text-[#10b981] hover:bg-[#10b981]/25 text-xs font-semibold border border-[#10b981]/30 transition-all"
              >
                {copiedFormat === "Standar Turats" ? (
                  <Check className="w-3.5 h-3.5" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
                <span>Salin</span>
              </button>
            </div>
            <p className="text-sm font-medium text-[#ecfdf5] leading-relaxed select-all">
              {standardCitation}
            </p>
          </div>

          {/* Format 2: Chicago Notes */}
          <div className="p-4 rounded-xl bg-[#081a13] border border-[#1a4a39]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-[#38bdf8] uppercase tracking-wider">
                2. Format Chicago (Notes & Bibliography)
              </span>
              <button
                onClick={() => copyToClip(chicagoCitation, "Chicago")}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#38bdf8]/15 text-[#38bdf8] hover:bg-[#38bdf8]/25 text-xs font-semibold border border-[#38bdf8]/30 transition-all"
              >
                {copiedFormat === "Chicago" ? (
                  <Check className="w-3.5 h-3.5" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
                <span>Salin</span>
              </button>
            </div>
            <p className="text-sm font-medium text-[#ecfdf5] leading-relaxed select-all">
              {chicagoCitation}
            </p>
          </div>

          {/* Format 3: BibTeX */}
          <div className="p-4 rounded-xl bg-[#081a13] border border-[#1a4a39]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-[#a78bfa] uppercase tracking-wider">
                3. Format BibTeX (LaTeX)
              </span>
              <button
                onClick={() => copyToClip(bibtexCitation, "BibTeX")}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#a78bfa]/15 text-[#a78bfa] hover:bg-[#a78bfa]/25 text-xs font-semibold border border-[#a78bfa]/30 transition-all"
              >
                {copiedFormat === "BibTeX" ? (
                  <Check className="w-3.5 h-3.5" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
                <span>Salin</span>
              </button>
            </div>
            <pre className="text-xs text-[#94a3b8] font-mono bg-black/40 p-3 rounded-lg overflow-x-auto select-all">
              {bibtexCitation}
            </pre>
          </div>

          {/* Format 4: Markdown Blockquote */}
          <div className="p-4 rounded-xl bg-[#081a13] border border-[#1a4a39]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-[#ec4899] uppercase tracking-wider">
                4. Markdown Blockquote
              </span>
              <button
                onClick={() => copyToClip(markdownCitation, "Markdown")}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#ec4899]/15 text-[#ec4899] hover:bg-[#ec4899]/25 text-xs font-semibold border border-[#ec4899]/30 transition-all"
              >
                {copiedFormat === "Markdown" ? (
                  <Check className="w-3.5 h-3.5" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
                <span>Salin</span>
              </button>
            </div>
            <pre className="text-xs text-[#94a3b8] font-mono bg-black/40 p-3 rounded-lg overflow-x-auto select-all whitespace-pre-wrap">
              {markdownCitation}
            </pre>
          </div>

        </div>

        {/* Footer */}
        <div className="mt-5 pt-4 border-t border-[#1a4a39] flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-[#10b981] hover:bg-[#0d9468] text-white font-semibold text-sm shadow-lg shadow-[#10b981]/25 transition-all"
          >
            Tutup
          </button>
        </div>

      </div>
    </div>
  );
}
