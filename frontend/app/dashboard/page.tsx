"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { User, LogOut, ShieldCheck, Mail, Calendar, CheckCircle2 } from "lucide-react";

export default function UserDashboard() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex items-center gap-3 text-slate-600 font-medium">
          <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span>Loading user dashboard...</span>
        </div>
      </div>
    );
  }

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
              <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </div>
            <div>
              <span className="text-xl font-bold text-slate-900 tracking-tight">Nubabla</span>
              <span className="ml-2 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600">
                User Portal
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 text-sm text-slate-600 font-medium">
              <div className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>{user.email}</span>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-700 font-semibold text-sm transition-colors"
            >
              <LogOut className="w-4 h-4 text-slate-500" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Container */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Welcome back, {user.full_name || "User"}!
          </h1>
          <p className="text-slate-500 font-medium mt-1">
            You are logged into your standard user account connected to Supabase PostgreSQL.
          </p>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* User Profile Card */}
          <div className="md:col-span-1 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm space-y-6">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 font-bold text-xl">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : "U"}
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-lg leading-snug">
                  {user.full_name || "Standard User"}
                </h3>
                <span className="inline-flex items-center gap-1 mt-1 px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs font-bold uppercase tracking-wider">
                  <User className="w-3 h-3" />
                  {user.role}
                </span>
              </div>
            </div>

            <div className="border-t border-slate-100 pt-4 space-y-3.5 text-sm font-medium">
              <div className="flex items-center justify-between text-slate-600">
                <span className="flex items-center gap-2 text-slate-500">
                  <Mail className="w-4 h-4 text-slate-400" /> Email
                </span>
                <span className="text-slate-900 font-semibold truncate max-w-[160px]">{user.email}</span>
              </div>

              <div className="flex items-center justify-between text-slate-600">
                <span className="flex items-center gap-2 text-slate-500">
                  <ShieldCheck className="w-4 h-4 text-slate-400" /> Auth Status
                </span>
                <span className="text-emerald-600 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" /> Active
                </span>
              </div>

              <div className="flex items-center justify-between text-slate-600">
                <span className="flex items-center gap-2 text-slate-500">
                  <Calendar className="w-4 h-4 text-slate-400" /> Database ID
                </span>
                <span className="text-slate-500 font-mono text-xs truncate max-w-[120px]">{user.id}</span>
              </div>
            </div>
          </div>

          {/* User Feature Section */}
          <div className="md:col-span-2 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-slate-900">User Dashboard Capabilities</h3>
                <span className="text-xs font-semibold px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full border border-emerald-200">
                  Supabase RLS Protected
                </span>
              </div>
              <p className="text-slate-600 text-sm leading-relaxed mb-6">
                Your account is authenticated via your FastAPI backend and synced with Supabase PostgreSQL. As a standard user, you have full access to your personal workspace and profile settings.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60">
                  <div className="font-semibold text-slate-900 text-sm mb-1">Personal Workspace</div>
                  <p className="text-xs text-slate-500">Access your private community documents and standard features.</p>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60">
                  <div className="font-semibold text-slate-900 text-sm mb-1">Role Permissions</div>
                  <p className="text-xs text-slate-500">Assigned role: <strong className="text-blue-600 uppercase">USER</strong>. Read/Write access to owned resources.</p>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-4 border-t border-slate-100 text-xs text-slate-400 flex items-center justify-between">
              <span>Connected Database: PostgreSQL (Supabase)</span>
              <span>FastAPI Backend Server: Active</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
