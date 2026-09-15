"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import UploadContractModal from "@/components/UploadContractModal";
import AddSupplierModal from "@/components/AddSupplierModal";
import {
  Sparkles,
  Upload,
  UserPlus,
  ShieldCheck,
  FileText,
  RefreshCw
} from "lucide-react";
import { fetchOverviewData, askContractAI, runAuditApi, OverviewData } from "@/services/api";
import { useAuth } from "@/context/AuthContext";

export default function OverviewPage() {
  const router = useRouter();
  const { user } = useAuth();
  const userName = user?.full_name ? user.full_name.split(" ")[0] : "Marcus";

  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiAnswer, setAiAnswer] = useState<string | null>(null);

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isSupplierOpen, setIsSupplierOpen] = useState(false);
  const [auditLoading, setAuditLoading] = useState(false);

  const loadOverview = async () => {
    try {
      setLoading(true);
      const res = await fetchOverviewData();
      setData(res);
    } catch (err) {
      console.error("Error loading overview data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOverview();
  }, []);

  const handleAskAI = async (promptQuery?: string) => {
    const q = promptQuery || aiPrompt;
    if (!q.trim()) return;

    setAiLoading(true);
    setAiAnswer(null);

    try {
      const res = await askContractAI(q.trim());
      setAiAnswer(res.answer);
    } catch (err: any) {
      setAiAnswer("Could not generate AI answer. Please try again.");
    } finally {
      setAiLoading(false);
    }
  };

  const handleRunAudit = async () => {
    setAuditLoading(true);
    try {
      await runAuditApi();
      await loadOverview();
    } catch (err) {
      console.error("Audit error:", err);
    } finally {
      setAuditLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-[#f8fafc]">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Header title="Overview" />

        <main className="p-6 sm:p-8 space-y-6 sm:space-y-8 max-w-7xl mx-auto w-full flex-1">
          {/* Welcome Header */}
          <div className="shrink-0">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Good morning, {userName}
            </h1>
            <p className="text-slate-500 font-medium text-xs sm:text-sm mt-0.5">
              Search and manage your procurement knowledge with on-demand contract intelligence.
            </p>
          </div>

          {/* AI Search & Prompt Hero Section */}
          <div className="bg-white rounded-2xl p-3.5 sm:p-4 border border-slate-200/80 shadow-xs space-y-2.5 shrink-0">
            <div className="relative flex items-center border border-blue-500/40 rounded-xl bg-white focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-600 transition-all p-1.5 shadow-xs">
              <div className="pl-2.5 pr-2 text-blue-600">
                <Sparkles className="w-4 h-4 sm:w-5 sm:h-5" />
              </div>
              <input
                type="text"
                placeholder='Ask anything about your contracts... (e.g., "Do we have unilateral renewal rights with AWS?")'
                value={aiPrompt}
                onChange={(e) => setAiPrompt(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAskAI()}
                className="w-full bg-transparent border-none text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-hidden px-2"
              />
              <button
                onClick={() => handleAskAI()}
                disabled={aiLoading}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs tracking-wide uppercase transition-all shadow-sm shadow-blue-600/20 shrink-0 disabled:opacity-50"
              >
                {aiLoading ? "Thinking..." : "ASK AI"}
              </button>
            </div>

            {/* AI Answer Display */}
            {aiAnswer && (
              <div className="p-3 rounded-xl bg-blue-50/70 border border-blue-100 text-slate-800 text-xs sm:text-sm leading-relaxed space-y-1 animate-in fade-in duration-200 max-h-24 overflow-y-auto">
                <div className="flex items-center gap-2 font-bold text-blue-900">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  <span>Contract Intelligence Synthesis</span>
                </div>
                <p className="whitespace-pre-wrap">{aiAnswer}</p>
              </div>
            )}

            {/* Suggestion Pills */}
            <div className="flex items-center gap-2 text-xs flex-wrap">
              <span className="text-slate-400 font-semibold text-[11px]">Try asking:</span>
              {[
                "What payment terms do we have with Supplier ABC?",
                "Which contracts expire this quarter?",
                "Show me suppliers with volume discounts."
              ].map((pill) => (
                <button
                  key={pill}
                  onClick={() => {
                    setAiPrompt(pill);
                    handleAskAI(pill);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-100/80 hover:bg-slate-200/70 text-slate-700 text-[11px] font-medium transition-colors"
                >
                  {pill}
                </button>
              ))}
            </div>
          </div>

          {/* 4 Dynamic Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 shrink-0">
            {/* Active Contracts */}
            <div className="bg-white rounded-xl sm:rounded-2xl p-3.5 sm:p-4 border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Active Contracts</span>
              <div className="flex items-baseline justify-between mt-2">
                <span className="text-2xl sm:text-3xl font-extrabold text-slate-900">
                  {loading ? "..." : (data?.active_contracts.count ?? 0)}
                </span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold">
                  {data?.active_contracts.change || "Active in DB"}
                </span>
              </div>
            </div>

            {/* Vetted Suppliers */}
            <div className="bg-white rounded-xl sm:rounded-2xl p-3.5 sm:p-4 border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Vetted Suppliers</span>
              <div className="flex items-baseline justify-between mt-2">
                <span className="text-2xl sm:text-3xl font-extrabold text-slate-900">
                  {loading ? "..." : (data?.vetted_suppliers.count ?? 0)}
                </span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold">
                  {data?.vetted_suppliers.change || "Registered Vendors"}
                </span>
              </div>
            </div>

            {/* Pending Renewals */}
            <div className="bg-white rounded-xl sm:rounded-2xl p-3.5 sm:p-4 border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Pending Renewals</span>
              <div className="flex items-baseline justify-between mt-2">
                <span className="text-2xl sm:text-3xl font-extrabold text-slate-900">
                  {loading ? "..." : (data?.pending_renewals.count ?? 0)}
                </span>
                <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 text-[11px] font-bold">
                  {data?.pending_renewals.badge || "Expiring Soon"}
                </span>
              </div>
            </div>

            {/* Compliance Score */}
            <div className="bg-white rounded-xl sm:rounded-2xl p-3.5 sm:p-4 border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Compliance Score</span>
              <div className="flex items-baseline justify-between mt-2">
                <span className="text-2xl sm:text-3xl font-extrabold text-slate-900">
                  {loading ? "..." : (data?.compliance_score.count ?? "0%")}
                </span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold">
                  {data?.compliance_score.change || "Portfolio Verified"}
                </span>
              </div>
            </div>
          </div>

          {/* Bottom Grid: Recent Intel & Quick Operations */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4 flex-1 min-h-0 overflow-hidden">
            {/* Recent Intel & Activity Table (2 columns) */}
            <div className="lg:col-span-2 bg-white rounded-2xl sm:rounded-3xl p-4 border border-slate-200/80 shadow-xs flex flex-col min-h-0 overflow-hidden">
              <div className="flex items-center justify-between mb-2 shrink-0">
                <h3 className="text-base font-bold text-slate-900">Recent Intel & Activity</h3>
                <button
                  onClick={loadOverview}
                  className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Refresh</span>
                </button>
              </div>

              <div className="flex-1 min-h-0 overflow-y-auto">
                <table className="w-full text-left text-xs sm:text-sm text-slate-600">
                  <thead className="sticky top-0 bg-white z-10">
                    <tr className="border-b border-slate-100 text-[11px] text-slate-400 font-bold uppercase tracking-wider">
                      <th className="pb-2 font-bold">Document</th>
                      <th className="pb-2 font-bold">Action</th>
                      <th className="pb-2 font-bold">Initiated By</th>
                      <th className="pb-2 font-bold text-right">Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100/80">
                    {data?.recent_activities.map((act) => (
                      <tr key={act.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="py-2 pr-4 font-semibold text-slate-900 flex items-center gap-2">
                          <FileText className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                          <span className="truncate max-w-[200px]" title={act.document_name}>
                            {act.document_name}
                          </span>
                        </td>
                        <td className="py-2 px-2 text-slate-500 font-medium text-xs">{act.action}</td>
                        <td className="py-2 px-2">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-semibold text-[11px]">
                            {act.initiated_by}
                          </span>
                        </td>
                        <td className="py-2 pl-2 text-right text-slate-400 text-[11px] font-medium whitespace-nowrap">
                          {act.date}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Quick Operations Column (1 column) */}
            <div className="flex flex-col justify-between space-y-2 sm:space-y-2.5 min-h-0">
              <h3 className="text-base font-bold text-slate-900 shrink-0">Quick Operations</h3>

              {/* Action 1: Upload New Contract */}
              <div
                onClick={() => setIsUploadOpen(true)}
                className="bg-white p-3 sm:p-3.5 rounded-xl sm:rounded-2xl border border-slate-200/80 shadow-xs hover:border-blue-400 hover:shadow-md transition-all cursor-pointer group flex items-center gap-3 flex-1"
              >
                <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                  <Upload className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="font-bold text-slate-900 text-xs sm:text-sm">Upload New Contract</h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">Extract instantly using AI models</p>
                </div>
              </div>

              {/* Action 2: Add New Supplier Profile */}
              <div
                onClick={() => setIsSupplierOpen(true)}
                className="bg-white p-3 sm:p-3.5 rounded-xl sm:rounded-2xl border border-slate-200/80 shadow-xs hover:border-emerald-400 hover:shadow-md transition-all cursor-pointer group flex items-center gap-3 flex-1"
              >
                <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                  <UserPlus className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="font-bold text-slate-900 text-xs sm:text-sm">Add New Supplier Profile</h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">Record vendor details and SLA targets</p>
                </div>
              </div>

              {/* Action 3: Run Compliance Audit */}
              <div
                onClick={handleRunAudit}
                className="bg-white p-3 sm:p-3.5 rounded-xl sm:rounded-2xl border border-slate-200/80 shadow-xs hover:border-amber-400 hover:shadow-md transition-all cursor-pointer group flex items-center gap-3 flex-1"
              >
                <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                  {auditLoading ? (
                    <div className="w-4 h-4 border-2 border-amber-600 border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <ShieldCheck className="w-4 h-4" />
                  )}
                </div>
                <div>
                  <h4 className="font-bold text-slate-900 text-xs sm:text-sm">Run Compliance Audit</h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">Scan entire portfolio against key regs</p>
                </div>
              </div>
            </div>
          </div>
        </main>
        <Footer />
      </div>

      {/* Modals */}
      <UploadContractModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={loadOverview}
      />

      <AddSupplierModal
        isOpen={isSupplierOpen}
        onClose={() => setIsSupplierOpen(false)}
        onSuccess={loadOverview}
      />
    </div>
  );
}
