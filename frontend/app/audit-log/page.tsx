"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { ShieldAlert, FileText } from "lucide-react";
import { fetchOverviewData, ActivityItem } from "@/services/api";
import { useAuth } from "@/context/AuthContext";

export default function AuditLogPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [logs, setLogs] = useState<ActivityItem[]>([]);

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "admin")) {
      router.replace("/overview");
      return;
    }

    fetchOverviewData()
      .then((data) => setLogs(data.recent_activities))
      .catch((err) => console.error(err));
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

  return (
    <div className="flex min-h-screen bg-[#f8fafc]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Header title="Audit Log" />
        <main className="p-8 max-w-7xl mx-auto w-full space-y-6 flex-1">
          <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">System Activity & Compliance Audit Logs</h1>
                <p className="text-xs text-slate-500">Immutable trail of contract access, scans, uploads, and AI indexing</p>
              </div>
            </div>

            <div className="overflow-x-auto pt-2">
              <table className="w-full text-left text-sm text-slate-600">
                <thead>
                  <tr className="border-b border-slate-100 text-xs text-slate-400 font-bold uppercase tracking-wider">
                    <th className="pb-3 font-bold">Document</th>
                    <th className="pb-3 font-bold">Action</th>
                    <th className="pb-3 font-bold">Initiated By</th>
                    <th className="pb-3 font-bold text-right">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-4 pr-4 font-bold text-slate-900 flex items-center gap-2">
                        <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                        <span>{log.document_name}</span>
                      </td>
                      <td className="py-4 px-2 text-slate-600 font-medium">{log.action}</td>
                      <td className="py-4 px-2">
                        <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold">
                          {log.initiated_by}
                        </span>
                      </td>
                      <td className="py-4 pl-2 text-right text-slate-400 text-xs">{log.date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </div>
  );
}
