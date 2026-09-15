"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import AddSupplierModal from "@/components/AddSupplierModal";
import { Users, Plus, Building2, CheckCircle2 } from "lucide-react";
import { fetchSuppliersApi } from "@/services/api";

export default function SuppliersPage() {
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadSuppliers = async () => {
    try {
      setLoading(true);
      const data = await fetchSuppliersApi();
      if (data.suppliers) setSuppliers(data.suppliers);
    } catch (e) {
      console.error("Failed to load suppliers:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSuppliers();
  }, []);

  return (
    <div className="flex min-h-screen bg-[#f8fafc]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Header title="Vetted Suppliers" />
        <main className="p-8 max-w-7xl mx-auto w-full space-y-6 flex-1">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Vetted Suppliers Portfolio</h1>
              <p className="text-sm text-slate-500">Manage vendor compliance and SLA targets</p>
            </div>
            <button
              onClick={() => setIsAddOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 text-white font-semibold text-sm shadow-md hover:bg-emerald-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Add Supplier</span>
            </button>
          </div>

          {loading ? (
            <div className="py-12 text-center text-slate-400">Loading suppliers portfolio...</div>
          ) : suppliers.length === 0 ? (
            <div className="bg-white p-12 rounded-3xl border border-slate-200/80 text-center space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto">
                <Building2 className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-slate-900 text-lg">No Vetted Suppliers Recorded</h3>
              <p className="text-sm text-slate-500 max-w-md mx-auto">
                Upload contracts or click &quot;Add Supplier&quot; to begin building your vendor portfolio.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {suppliers.map((s) => (
                <div key={s.id} className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                      <Building2 className="w-5 h-5" />
                    </div>
                    <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Vetted
                    </span>
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">{s.name}</h3>
                    <p className="text-xs text-slate-500 font-medium">{s.category}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
        <Footer />
      </div>

      <AddSupplierModal
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        onSuccess={loadSuppliers}
      />
    </div>
  );
}
