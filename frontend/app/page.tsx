"use client";

import React from "react";
import Link from "next/link";
import { LogIn, UserPlus, ShieldCheck, ArrowRight, Database } from "lucide-react";

export default function Home() {
  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center bg-[#f8fafc] px-4 py-16 overflow-hidden">
      {/* Dot Grid Background */}
      <div 
        className="absolute inset-0 z-0 opacity-40 pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(#cbd5e1 1.5px, transparent 1.5px)`,
          backgroundSize: '24px 24px'
        }}
      />

      <div className="relative z-10 w-full max-w-4xl mx-auto text-center space-y-12">
        {/* Brand Header */}
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-blue-50 border border-blue-200/80 text-blue-700 text-sm font-semibold mb-2">
            <Database className="w-4 h-4 text-blue-600" />
            <span>Supabase PostgreSQL + FastAPI Auth</span>
          </div>

          <div className="flex items-center justify-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-xl shadow-blue-600/30">
              <svg className="w-7 h-7 fill-current" viewBox="0 0 24 24">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </div>
            <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
              Nubabla
            </h1>
          </div>

          <p className="max-w-xl mx-auto text-slate-600 text-base sm:text-lg font-medium leading-relaxed">
            Role-Based Authentication Platform with dedicated User & Admin portals connected to PostgreSQL.
          </p>
        </div>

        {/* Portal Navigation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
          {/* User Sign In Card */}
          <div className="bg-white p-7 rounded-3xl border border-slate-200/80 shadow-lg hover:shadow-xl transition-all duration-300 flex flex-col justify-between group">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <LogIn className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold text-slate-900 mb-2">User Sign In</h2>
              <p className="text-slate-500 text-sm leading-relaxed mb-6">
                Access your standard user workspace and personal dashboard.
              </p>
            </div>
            <Link
              href="/login"
              className="inline-flex items-center justify-center gap-2 w-full py-3.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm shadow-md shadow-blue-600/20 transition-all"
            >
              <span>Go to Sign In</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* User Signup Card */}
          <div className="bg-white p-7 rounded-3xl border border-slate-200/80 shadow-lg hover:shadow-xl transition-all duration-300 flex flex-col justify-between group">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <UserPlus className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold text-slate-900 mb-2">Create Account</h2>
              <p className="text-slate-500 text-sm leading-relaxed mb-6">
                Register a new standard user account stored in Supabase PostgreSQL.
              </p>
            </div>
            <Link
              href="/signup"
              className="inline-flex items-center justify-center gap-2 w-full py-3.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm shadow-md transition-all"
            >
              <span>Create Account</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Admin Console Card */}
          <div className="bg-white p-7 rounded-3xl border border-slate-200/80 shadow-lg hover:shadow-xl transition-all duration-300 flex flex-col justify-between group">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-700 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xl font-bold text-slate-900">Admin Console</h2>
                <span className="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 text-xs font-bold uppercase">
                  ADMIN
                </span>
              </div>
              <p className="text-slate-500 text-sm leading-relaxed mb-6">
                Dedicated administration console route for managing role permissions.
              </p>
            </div>
            <Link
              href="/admin/login"
              className="inline-flex items-center justify-center gap-2 w-full py-3.5 px-4 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 font-semibold text-sm transition-all"
            >
              <span>Admin Console</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
