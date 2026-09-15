"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { LineChart, TrendingUp, PieChart, ShieldCheck } from "lucide-react";
import { fetchContractsList, fetchOverviewData, OverviewData, ContractRecord } from "@/services/api";

export default function InsightsPage() {
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [contracts, setContracts] = useState<ContractRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [ovData, cList] = await Promise.all([
          fetchOverviewData(),
          fetchContractsList({ limit: 100 })
        ]);
        setOverview(ovData);
        setContracts(cList.contracts || []);
      } catch (err) {
        console.error("Error loading insights data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const totalSpend = contracts.reduce((sum, c) => sum + (c.annual_value || 0), 0);
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(val);
  };

  // Compute top category
  const categoryCounts: Record<string, number> = {};
  contracts.forEach((c) => {
    const cat = c.document_type || "General";
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
  });
  const topCategory = Object.keys(categoryCounts).reduce((a, b) => categoryCounts[a] > categoryCounts[b] ? a : b, "No Data");

  return (
    <div className="flex min-h-screen bg-[#f8fafc]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Header title="Procurement Insights" />
        <main className="p-8 max-w-7xl mx-auto w-full space-y-6 flex-1">
          <div className="bg-white p-8 rounded-3xl border border-slate-200/80 shadow-xs space-y-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center">
                <LineChart className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">Contract Analytics & Portfolio Insights</h1>
                <p className="text-sm text-slate-500">Real-time spend distribution, renewal timelines, and liability risk exposure.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/60">
                <div className="flex items-center gap-2 text-slate-700 font-bold mb-2">
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                  <span>Annual Commitment</span>
                </div>
                <div className="text-2xl font-extrabold text-slate-900">
                  {loading ? "..." : formatCurrency(totalSpend)}
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Across {contracts.length} active corporate agreements
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/60">
                <div className="flex items-center gap-2 text-slate-700 font-bold mb-2">
                  <PieChart className="w-4 h-4 text-blue-600" />
                  <span>Top Spend Category</span>
                </div>
                <div className="text-2xl font-extrabold text-slate-900">
                  {loading ? "..." : (contracts.length > 0 ? topCategory : "N/A")}
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  {contracts.length > 0 ? `Most frequent document classification` : "No contracts in database"}
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/60">
                <div className="flex items-center gap-2 text-slate-700 font-bold mb-2">
                  <ShieldCheck className="w-4 h-4 text-indigo-600" />
                  <span>Compliance Rating</span>
                </div>
                <div className="text-2xl font-extrabold text-slate-900">
                  {loading ? "..." : (overview?.compliance_score.count ?? "0%")}
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  {overview?.compliance_score.change || "Portfolio Verified"}
                </p>
              </div>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </div>
  );
}
