"use client";

import React from "react";
import { X, Sparkles, FileText, Calendar, Building2, ShieldCheck } from "lucide-react";
import { SearchResultItem } from "@/services/api";

interface PassageDetailModalProps {
  item: SearchResultItem | null;
  onClose: () => void;
}

export default function PassageDetailModal({ item, onClose }: PassageDetailModalProps) {
  if (!item) return null;

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 overflow-y-auto"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="bg-white rounded-3xl max-w-2xl w-full p-6 shadow-2xl border border-slate-100 relative animate-in fade-in zoom-in-95 duration-200 space-y-5 max-h-[90vh] flex flex-col"
      >
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-slate-600 p-1.5 rounded-full hover:bg-slate-100 transition-colors z-10"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-start gap-4 pr-8">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-xl font-bold text-slate-900">{item.document_title}</h2>
              <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold">
                {item.document_type}
              </span>
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-500 mt-1">
              <span className="flex items-center gap-1">
                <Building2 className="w-3.5 h-3.5 text-slate-400" />
                {item.supplier}
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                Executed: {item.execution_date}
              </span>
            </div>
          </div>
        </div>

        {/* Confidence Badge */}
        <div className="flex items-center justify-between p-3 rounded-2xl bg-emerald-50/80 border border-emerald-100 shrink-0">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span className="text-sm font-semibold text-emerald-900">AI Citation Confidence</span>
          </div>
          <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
            {item.confidence_percentage}% AI confidence
          </span>
        </div>

        {/* Complete Passage Box */}
        <div className="space-y-2 flex-1 overflow-y-auto pr-1">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
            <Sparkles className="w-4 h-4 text-blue-600" />
            <span>Complete Indexed Passage ({item.section_title})</span>
          </div>
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/70 text-slate-700 text-sm leading-relaxed whitespace-pre-wrap font-sans max-h-[50vh] overflow-y-auto">
            {item.passage_text}
          </div>
        </div>

        {/* Footer info */}
        <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400 shrink-0">
          <span>Chunk Reference ID: <strong className="font-mono text-slate-600">{item.chunk_id}</strong></span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-900 text-white font-semibold text-xs hover:bg-slate-800 transition-colors"
          >
            Close Passage
          </button>
        </div>
      </div>
    </div>
  );
}
