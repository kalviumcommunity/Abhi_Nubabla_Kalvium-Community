"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import PassageDetailModal from "@/components/PassageDetailModal";
import {
  Search as SearchIcon,
  X,
  Sparkles,
} from "lucide-react";
import { searchIntelligentContracts, SearchResultItem, SearchResponse } from "@/services/api";

function SearchContent() {
  const searchParams = useSearchParams();

  const initialQuery = searchParams.get("q") || "";
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [activeQuery, setActiveQuery] = useState(initialQuery);

  // Filters State
  const [docTypes, setDocTypes] = useState<string[]>([]);
  const [confidence, setConfidence] = useState<string[]>([]);
  const [statusVal, setStatusVal] = useState<string[]>([]);

  const [resultsData, setResultsData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedPassage, setSelectedPassage] = useState<SearchResultItem | null>(null);

  const executeSearch = useCallback(async () => {
    setLoading(true);
    try {
      const typeFilters = docTypes.map((t) => t.toLowerCase());
      const confFilters = confidence.map((c) => {
        if (c.includes(">90%")) return "high";
        if (c.includes("70-90%")) return "medium";
        return "low";
      });
      const statusFilters = statusVal.map((s) => s.toLowerCase());

      const data = await searchIntelligentContracts({
        q: activeQuery,
        docTypes: typeFilters,
        confidence: confFilters,
        status: statusFilters,
      });

      setResultsData(data);
    } catch (err) {
      console.error("Search error:", err);
    } finally {
      setLoading(false);
    }
  }, [activeQuery, docTypes, confidence, statusVal]);

  useEffect(() => {
    executeSearch();
  }, [executeSearch]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setActiveQuery(searchQuery);
  };

  const handleClearQuery = () => {
    setSearchQuery("");
    setActiveQuery("");
  };

  const toggleFilter = (list: string[], setList: (val: string[]) => void, item: string) => {
    if (list.includes(item)) {
      setList(list.filter((i) => i !== item));
    } else {
      setList([...list, item]);
    }
  };

  return (
    <main className="p-8 max-w-7xl mx-auto w-full flex-1">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start">
        {/* Left Sidebar Filters (1 Column) */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs space-y-6">
          <h3 className="font-bold text-slate-900 text-lg">Filters</h3>

          {/* DOCUMENT TYPE */}
          <div className="space-y-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
              DOCUMENT TYPE
            </span>
            <div className="space-y-2.5 text-sm font-medium">
              {[
                { label: "Master Agreements", key: "Master Agreements" },
                { label: "Amendments", key: "Amendments" },
                { label: "SOWs & Order Forms", key: "SOWs & Order Forms" },
                { label: "NDAs", key: "NDAs" },
              ].map((item) => {
                const isChecked = docTypes.includes(item.label);
                const count = resultsData?.counts_by_type?.[item.key] ?? 0;
                return (
                  <label
                    key={item.label}
                    className="flex items-center justify-between text-slate-700 cursor-pointer hover:text-slate-900"
                  >
                    <div className="flex items-center gap-2.5">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggleFilter(docTypes, setDocTypes, item.label)}
                        className="w-4 h-4 rounded-md border-slate-300 text-blue-600 focus:ring-blue-500/20"
                      />
                      <span>{item.label}</span>
                    </div>
                    <span className="text-xs text-slate-400 font-normal">{count}</span>
                  </label>
                );
              })}
            </div>
          </div>

          <div className="border-t border-slate-100" />

          {/* AI CONFIDENCE TARGET */}
          <div className="space-y-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
              AI CONFIDENCE TARGET
            </span>
            <div className="space-y-2.5 text-sm font-medium">
              {[
                { label: "High Match (>90%)", key: "High Match (>90%)" },
                { label: "Medium Match (70-90%)", key: "Medium Match (70-90%)" },
                { label: "Low Match (<70%)", key: "Low Match (<70%)" },
              ].map((item) => {
                const isChecked = confidence.includes(item.label);
                const count = resultsData?.counts_by_confidence?.[item.key] ?? 0;
                return (
                  <label
                    key={item.label}
                    className="flex items-center justify-between text-slate-700 cursor-pointer hover:text-slate-900"
                  >
                    <div className="flex items-center gap-2.5">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggleFilter(confidence, setConfidence, item.label)}
                        className="w-4 h-4 rounded-md border-slate-300 text-blue-600 focus:ring-blue-500/20"
                      />
                      <span>{item.label}</span>
                    </div>
                    <span className="text-xs text-slate-400 font-normal">{count}</span>
                  </label>
                );
              })}
            </div>
          </div>

          <div className="border-t border-slate-100" />

          {/* STATUS */}
          <div className="space-y-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
              STATUS
            </span>
            <div className="space-y-2.5 text-sm font-medium">
              {["Active", "Expiring Soon", "Draft"].map((st) => {
                const isChecked = statusVal.includes(st);
                return (
                  <label
                    key={st}
                    className="flex items-center gap-2.5 text-slate-700 cursor-pointer hover:text-slate-900"
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleFilter(statusVal, setStatusVal, st)}
                      className="w-4 h-4 rounded-md border-slate-300 text-blue-600 focus:ring-blue-500/20"
                    />
                    <span>{st}</span>
                  </label>
                );
              })}
            </div>
          </div>
        </div>

        {/* Main Search Results Area (3 Columns) */}
        <div className="lg:col-span-3 space-y-6">
          {/* Main Search Input Form */}
          <form onSubmit={handleSearchSubmit} className="relative">
            <SearchIcon className="w-5 h-5 text-blue-600 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search contract intelligence, payment terms, clauses..."
              className="w-full bg-white border-2 border-blue-500/40 rounded-2xl pl-12 pr-12 py-3.5 text-sm font-medium text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-4 focus:ring-blue-500/10 focus:border-blue-600 shadow-xs transition-all"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={handleClearQuery}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </form>

          {/* Matches Summary Row */}
          <div className="flex items-center justify-between text-sm text-slate-600 px-1">
            <div>
              {activeQuery ? (
                <>Found <strong className="text-slate-900">{resultsData?.total_matches || 0} intelligence matches</strong> for search &quot;{activeQuery}&quot;</>
              ) : (
                <span className="text-slate-500 font-medium">Type a term or query above to search contract intelligence</span>
              )}
            </div>
          </div>

          {/* Loading Spinner */}
          {loading && (
            <div className="py-12 text-center text-slate-500 flex items-center justify-center gap-3">
              <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <span>Searching contract repository...</span>
            </div>
          )}

          {/* Results Cards List */}
          {!loading && resultsData && (
            <div className="space-y-4">
              {resultsData.results.length === 0 ? (
                <div className="bg-white p-12 rounded-3xl border border-slate-200/80 text-center space-y-3">
                  <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
                    <SearchIcon className="w-6 h-6" />
                  </div>
                  <h3 className="font-bold text-slate-900 text-lg">No Contract Passages Found</h3>
                  <p className="text-sm text-slate-500 max-w-md mx-auto">
                    Upload new contracts or try searching for specific terms like payment schedules, liability, or renewal clauses.
                  </p>
                </div>
              ) : (
                resultsData.results.map((res) => (
                  <div
                    key={res.id}
                    className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs hover:shadow-md transition-all space-y-4"
                  >
                    {/* Result Header */}
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <a
                          href="#"
                          onClick={(e) => {
                            e.preventDefault();
                            setSelectedPassage(res);
                          }}
                          className="text-base font-bold text-blue-600 hover:text-blue-700 hover:underline"
                        >
                          {res.document_title}
                        </a>
                        <div className="text-xs text-slate-500 mt-0.5 font-medium">
                          {res.supplier}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-semibold">
                          {res.document_type}
                        </span>
                        <span className="px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                          {res.confidence_percentage}% AI confidence
                        </span>
                      </div>
                    </div>

                    {/* Sparkle AI Passage Box */}
                    <div className="p-4 rounded-2xl bg-slate-50/80 border border-slate-100 flex items-start gap-3">
                      <Sparkles className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                      <p className="text-slate-700 text-sm leading-relaxed font-sans">
                        {res.passage_text}
                      </p>
                    </div>

                    {/* Execution Date & Link */}
                    <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                      <span>Document executed on: {res.execution_date}</span>
                      <button
                        onClick={() => setSelectedPassage(res)}
                        className="font-bold text-blue-600 hover:text-blue-700 hover:underline"
                      >
                        View complete passage
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* Complete Passage Modal */}
      <PassageDetailModal
        item={selectedPassage}
        onClose={() => setSelectedPassage(null)}
      />
    </main>
  );
}

export default function SearchPage() {
  return (
    <div className="flex min-h-screen bg-[#f8fafc]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Header title="AI Intelligent Search" />
        <Suspense fallback={<div className="p-8 text-slate-500">Loading intelligent search...</div>}>
          <SearchContent />
        </Suspense>
        <Footer />
      </div>
    </div>
  );
}
