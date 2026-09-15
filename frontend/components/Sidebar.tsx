"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  FileText,
  Users,
  LineChart,
  ShieldAlert,
  Settings,
  LogOut
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [isHovered, setIsHovered] = useState(false);

  const userName = user?.full_name || "User Profile";
  const isAdmin = user?.role === "admin";
  const userRole = isAdmin ? "Enterprise Admin" : "Standard User";

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const allNavItems = [
    { name: "Overview", href: "/overview", icon: LayoutDashboard },
    { name: "Search", href: "/search", icon: Search },
    { name: "Contracts", href: "/contracts", icon: FileText },
    { name: "Suppliers", href: "/suppliers", icon: Users },
    { name: "Insights", href: "/insights", icon: LineChart },
    { name: "Audit Log", href: "/audit-log", icon: ShieldAlert, adminOnly: true },
  ];

  const allSecondaryNav = [
    { name: "Settings", href: "/settings", icon: Settings, adminOnly: true },
  ];

  const navItems = allNavItems.filter((item) => !item.adminOnly || isAdmin);
  const secondaryNav = allSecondaryNav.filter((item) => !item.adminOnly || isAdmin);

  return (
    <aside
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`bg-white border-r border-slate-200/80 flex flex-col justify-between shrink-0 h-screen transition-all duration-300 ease-in-out ${
        isHovered ? "w-64" : "w-16"
      }`}
    >
      <div>
        {/* Brand Header */}
        <div className={`p-4 flex items-center gap-3 overflow-hidden ${isHovered ? "px-5" : "justify-center"}`}>
          <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20 shrink-0">
            <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          {isHovered && (
            <span className="text-xl font-bold text-slate-900 tracking-tight whitespace-nowrap transition-opacity duration-200">
              Nubabla
            </span>
          )}
        </div>

        {/* Main Navigation */}
        <nav className="px-2 space-y-1.5 mt-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (pathname === "/" && item.href === "/overview") || (pathname.startsWith(item.href) && item.href !== "/");

            return (
              <Link
                key={item.name}
                href={item.href}
                title={!isHovered ? item.name : undefined}
                className={`flex items-center ${
                  isHovered ? "gap-3 px-3.5" : "justify-center px-0"
                } py-2.5 rounded-xl font-medium text-sm transition-all duration-200 ${
                  isActive
                    ? "bg-blue-50 text-blue-600 font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/70"
                }`}
              >
                <Icon className={`w-5 h-5 shrink-0 ${isActive ? "text-blue-600" : "text-slate-400"}`} />
                {isHovered && (
                  <span className="whitespace-nowrap transition-opacity duration-200">
                    {item.name}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Navigation & Profile */}
      <div className="p-2 border-t border-slate-100 space-y-3">
        <div className="space-y-1">
          {secondaryNav.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                title={!isHovered ? item.name : undefined}
                className={`flex items-center ${
                  isHovered ? "gap-3 px-3.5" : "justify-center px-0"
                } py-2.5 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100/70 font-medium text-sm transition-all`}
              >
                <Icon className="w-5 h-5 text-slate-400 shrink-0" />
                {isHovered && (
                  <span className="whitespace-nowrap transition-opacity duration-200">
                    {item.name}
                  </span>
                )}
              </Link>
            );
          })}
        </div>

        {/* User Profile Card & Logout */}
        <div className={`flex items-center ${isHovered ? "justify-between px-2" : "justify-center"} pt-2.5 border-t border-slate-100`}>
          <div className="flex items-center gap-3 min-w-0">
            <div
              className="w-9 h-9 rounded-full bg-slate-800 text-white font-semibold flex items-center justify-center text-sm shadow-sm overflow-hidden shrink-0"
              title={!isHovered ? userName : undefined}
            >
              {userName.charAt(0).toUpperCase()}
            </div>
            {isHovered && (
              <div className="flex flex-col min-w-0 transition-opacity duration-200">
                <span className="text-sm font-semibold text-slate-900 truncate leading-tight">{userName}</span>
                <span className="text-xs text-slate-500 truncate leading-tight">{userRole}</span>
              </div>
            )}
          </div>

          {isHovered && (
            <button
              onClick={handleLogout}
              className="p-2 text-slate-400 hover:text-rose-600 rounded-xl hover:bg-rose-50 transition-colors shrink-0"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
