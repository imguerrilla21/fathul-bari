import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Amiri } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import { ToastProvider } from "@/components/Toast";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-ui",
  display: "swap",
});

const amiri = Amiri({
  subsets: ["arabic", "latin"],
  weight: ["400", "700"],
  variable: "--font-arabic",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Fathul Bari Research — Riset Hadis Shahih Bukhari & Syarah Fathul Bari",
  description:
    "Platform penelitian dan studi hadis Shahih al-Bukhari terintegrasi dengan Syarah Fathul Bari karya Al-Hafizh Ibnu Hajar al-Asqalani, RAG AI Assistant, dan Review Dashboard.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="id"
      data-theme="dark"
      className={`${jakarta.variable} ${amiri.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#05130e] text-[#ecfdf5] transition-colors">
        <ToastProvider>
          <Navbar />
          <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
          
          <footer className="w-full border-t border-[#1a4a39] bg-[#0b221a] py-8 text-center text-sm text-[#94a3b8]">
            <div className="max-w-7xl mx-auto px-4">
              <p className="font-semibold text-[#ecfdf5]">
                Fathul Bari Research Platform — Next.js & FastAPI Architecture
              </p>
              <p className="text-xs text-[#6ee7b7] mt-1">
                Data Hadis: Ahmad Sanusi Hadits API • Syarah: Fathul Bari (Ibnu Hajar al-Asqalani) • RAG Assistant & Review Engine
              </p>
            </div>
          </footer>
        </ToastProvider>
      </body>
    </html>
  );
}
