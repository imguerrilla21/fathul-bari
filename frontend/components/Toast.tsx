"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";
import { CheckCircle2, AlertTriangle, XCircle, Info } from "lucide-react";

type ToastType = "success" | "warning" | "error" | "info";

interface ToastMessage {
  id: number;
  text: string;
  type: ToastType;
}

interface ToastContextValue {
  showToast: (text: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue>({
  showToast: () => {},
});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = (text: string, type: ToastType = "success") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, text, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-2xl border text-sm font-medium animate-fade-in transition-all ${
              toast.type === "success"
                ? "bg-[#0b221a] border-[#10b981] text-[#ecfdf5]"
                : toast.type === "warning"
                ? "bg-[#1e1503] border-[#f59e0b] text-[#fef3c7]"
                : toast.type === "error"
                ? "bg-[#25090f] border-[#f43f5e] text-[#ffe4e6]"
                : "bg-[#081a13] border-[#38bdf8] text-[#f0f9ff]"
            }`}
          >
            {toast.type === "success" && <CheckCircle2 className="w-5 h-5 text-[#10b981]" />}
            {toast.type === "warning" && <AlertTriangle className="w-5 h-5 text-[#f59e0b]" />}
            {toast.type === "error" && <XCircle className="w-5 h-5 text-[#f43f5e]" />}
            {toast.type === "info" && <Info className="w-5 h-5 text-[#38bdf8]" />}
            <span>{toast.text}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
