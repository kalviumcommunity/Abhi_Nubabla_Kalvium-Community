"use client";

import React from "react";
import Link from "next/link";
import { ShieldCheck, Database, Cpu } from "lucide-react";

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="mt-auto border-t border-slate-200/80 bg-white py-6 px-8 text-slate-500 text-xs">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Left Brand & Copyright */}
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-xs shadow-xs">
            <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <span className="font-bold text-slate-900 text-sm">Nubabla</span>
          <span className="text-slate-300">|</span>
          <span>© {currentYear} Nubabla Procurement & Contract Intelligence. All rights reserved.</span>
        </div>

        {/* Center Navigation Links */}
        <div className="flex items-center gap-5 text-slate-600 font-medium">
          <Link href="/overview" className="hover:text-blue-600 transition-colors">Overview</Link>
          <Link href="/search" className="hover:text-blue-600 transition-colors">AI Search</Link>
          <Link href="/contracts" className="hover:text-blue-600 transition-colors">Contracts</Link>
          <Link href="/suppliers" className="hover:text-blue-600 transition-colors">Suppliers</Link>
          <Link href="/insights" className="hover:text-blue-600 transition-colors">Insights</Link>
        </div>

        {/* Right Status Badge */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200/60 text-emerald-800 font-semibold text-[11px]">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>System Operational</span>
        </div>
      </div>
    </footer>
  );
}
