"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Settings, Database, Key, ShieldCheck } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function SettingsPage() {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && (!user || user.role !== "admin")) {
      router.replace("/overview");
    }
  }, [user, loading, router]);

  if (loading || (!user || user.role !== "admin")) {
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
        <Header title="Settings" />
        <main className="p-8 max-w-7xl mx-auto w-full space-y-6 flex-1">
          <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs space-y-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center">
                <Settings className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">System Configuration & Integration Settings</h1>
                <p className="text-xs text-slate-500">Manage Supabase database credentials, Pinecone vectors, and Groq LLM settings</p>
              </div>
            </div>

            <div className="space-y-4 max-w-2xl">
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/60 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Database className="w-5 h-5 text-blue-600" />
                  <div>
                    <div className="font-bold text-slate-900 text-sm">Supabase PostgreSQL Connection</div>
                    <div className="text-xs text-slate-500">Credential Auth & RLS Row Security</div>
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">Connected</span>
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/60 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Key className="w-5 h-5 text-indigo-600" />
                  <div>
                    <div className="font-bold text-slate-900 text-sm">Pinecone Cloud Vector Index</div>
                    <div className="text-xs text-slate-500">Index: contract-rag-index (2048-dim)</div>
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">Active</span>
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/60 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <ShieldCheck className="w-5 h-5 text-emerald-600" />
                  <div>
                    <div className="font-bold text-slate-900 text-sm">Groq LLM & OpenRouter Embeddings</div>
                    <div className="text-xs text-slate-500">Model: openai/gpt-oss-20b</div>
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">Operational</span>
              </div>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </div>
  );
}
