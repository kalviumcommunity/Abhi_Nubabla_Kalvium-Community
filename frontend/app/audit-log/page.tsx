"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { ShieldAlert, FileText, Sparkles, Search, MessageSquare, ChevronDown, ChevronUp, RefreshCw } from "lucide-react";
import { fetchOverviewData, fetchAiQueryLogsApi, ActivityItem, AiQueryLogItem } from "@/services/api";
import { useAuth } from "@/context/AuthContext";

export default function AuditLogPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  
  const [activeTab, setActiveTab] = useState<"ai_logs" | "system_logs">("ai_logs");
  const [systemLogs, setSystemLogs] = useState<ActivityItem[]>([]);
  const [aiLogs, setAiLogs] = useState<AiQueryLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const [overviewRes, aiRes] = await Promise.all([
        fetchOverviewData(),
        fetchAiQueryLogsApi()
      ]);
      setSystemLogs(overviewRes.recent_activities || []);
      setAiLogs(aiRes.logs || []);
    } catch (err) {
      console.error("Error fetching logs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "admin")) {
      router.replace("/overview");
      return;
    }

    if (user && user.role === "admin") {
      loadLogs();
    }
  }, [user, authLoading, router]);

  if (authLoading || (!user || user.role !== "admin")) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex items-center gap-3 text-slate-600 font-medium">
          <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span>Verifying administrator privileges...</span>
        </div>
      </div>
    );
  }

  const toggleExpand = (id: string) => {
    setExpandedLogId(expandedLogId === id ? null : id);
  };

  return (
    <div className="flex min-h-screen bg-[#f8fafc]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Header title="Audit Log" />
        <main className="p-6 sm:p-8 max-w-7xl mx-auto w-full space-y-6 flex-1">
          {/* Page Header Banner */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="w-11 h-11 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Admin Inspection & Audit Logs</h1>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  Track AI search prompts, questions asked, generated answers, and system contract events
                </p>
              </div>
            </div>

            <button
              onClick={loadLogs}
              disabled={loading}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition-colors shrink-0 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh Logs</span>
            </button>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-200/80 pb-1">
            <button
              onClick={() => setActiveTab("ai_logs")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === "ai_logs"
                  ? "bg-blue-600 text-white shadow-sm shadow-blue-600/20"
                  : "bg-white text-slate-600 hover:bg-slate-100/70 border border-slate-200/80"
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>AI Search & Q&A Logs ({aiLogs.length})</span>
            </button>

            <button
              onClick={() => setActiveTab("system_logs")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === "system_logs"
                  ? "bg-blue-600 text-white shadow-sm shadow-blue-600/20"
                  : "bg-white text-slate-600 hover:bg-slate-100/70 border border-slate-200/80"
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>System Activity Audit ({systemLogs.length})</span>
            </button>
          </div>

          {/* Tab 1: AI Search & Question Logs */}
          {activeTab === "ai_logs" && (
            <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-blue-600" />
                  AI Questions & Search Query Trail
                </h2>
                <span className="text-xs text-slate-500 font-medium">
                  Recorded in real-time
                </span>
              </div>

              {aiLogs.length === 0 ? (
                <div className="py-12 text-center text-slate-500 text-sm">
                  No AI search or question logs recorded yet. Ask a question on the Overview page to generate logs!
                </div>
              ) : (
                <div className="space-y-3">
                  {aiLogs.map((log) => {
                    const isExpanded = expandedLogId === log.id;
                    return (
                      <div
                        key={log.id}
                        className="rounded-2xl border border-slate-200/80 bg-slate-50/50 hover:bg-slate-50 transition-all overflow-hidden"
                      >
                        {/* Log Summary Row */}
                        <div
                          onClick={() => toggleExpand(log.id)}
                          className="p-4 flex items-start justify-between cursor-pointer gap-4"
                        >
                          <div className="flex items-start gap-3 min-w-0">
                            <div className="w-9 h-9 rounded-xl bg-blue-100/80 text-blue-700 flex items-center justify-center shrink-0 mt-0.5">
                              {log.query_type === "AI Intelligent Search" ? (
                                <Search className="w-4.5 h-4.5" />
                              ) : (
                                <Sparkles className="w-4.5 h-4.5" />
                              )}
                            </div>
                            <div className="min-w-0 space-y-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 text-[11px] font-bold">
                                  {log.query_type}
                                </span>
                                <span className="px-2 py-0.5 rounded-full bg-slate-200/70 text-slate-700 text-[11px] font-semibold">
                                  {log.sources_count} source match{log.sources_count !== 1 ? "es" : ""}
                                </span>
                              </div>
                              <h3 className="font-bold text-slate-900 text-sm leading-snug">
                                Prompt / Question: "{log.question}"
                              </h3>
                            </div>
                          </div>

                          <div className="flex items-center gap-3 shrink-0">
                            <span className="text-xs text-slate-400 font-medium whitespace-nowrap">
                              {log.date}
                            </span>
                            <div className="text-slate-400">
                              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </div>
                          </div>
                        </div>

                        {/* Expanded Full AI Answer Details */}
                        {isExpanded && (
                          <div className="p-4 bg-white border-t border-slate-200/80 text-xs sm:text-sm space-y-2 animate-in fade-in duration-150">
                            <div className="font-bold text-blue-900 flex items-center gap-2 text-xs">
                              <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                              <span>Generated AI Answer & Synthesis:</span>
                            </div>
                            <p className="whitespace-pre-wrap text-slate-800 leading-relaxed font-medium bg-blue-50/50 p-3.5 rounded-xl border border-blue-100">
                              {log.answer}
                            </p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Tab 2: System Activity Audit Logs */}
          {activeTab === "system_logs" && (
            <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-600" />
                  System Activity & Contract Audit Trail
                </h2>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-600">
                  <thead>
                    <tr className="border-b border-slate-100 text-xs text-slate-400 font-bold uppercase tracking-wider">
                      <th className="pb-3 font-bold">Document / Item</th>
                      <th className="pb-3 font-bold">Action</th>
                      <th className="pb-3 font-bold">Initiated By</th>
                      <th className="pb-3 font-bold text-right">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {systemLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                        <td className="py-3.5 pr-4 font-bold text-slate-900 flex items-center gap-2">
                          <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                          <span>{log.document_name}</span>
                        </td>
                        <td className="py-3.5 px-2 text-slate-600 font-medium">{log.action}</td>
                        <td className="py-3.5 px-2">
                          <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold">
                            {log.initiated_by}
                          </span>
                        </td>
                        <td className="py-3.5 pl-2 text-right text-slate-400 text-xs">{log.date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
        <Footer />
      </div>
    </div>
  );
}
