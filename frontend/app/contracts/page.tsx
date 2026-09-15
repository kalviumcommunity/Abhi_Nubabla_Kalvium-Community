"use client";

import React, { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import UploadContractModal from "@/components/UploadContractModal";
import EditContractModal from "@/components/EditContractModal";
import {
  Download,
  Plus,
  Search,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  FileText,
  Trash2,
  Pencil
} from "lucide-react";
import {
  fetchContractsList,
  deleteContractApi,
  getExportContractsUrl,
  ContractRecord,
  ContractsListResponse
} from "@/services/api";

export default function ContractsPage() {
  const [contractsData, setContractsData] = useState<ContractsListResponse | null>(null);
  const [loading, setLoading] = useState(true);

  // Filters & Pagination
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All Statuses");
  const [typeFilter, setTypeFilter] = useState("All Types");
  const [page, setPage] = useState(1);
  const [limit] = useState(10);

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [editingContract, setEditingContract] = useState<ContractRecord | null>(null);
  const [isEditOpen, setIsEditOpen] = useState(false);

  const loadContracts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchContractsList({
        search: searchTerm,
        status: statusFilter,
        type: typeFilter,
        page,
        limit,
      });
      setContractsData(data);
    } catch (err) {
      console.error("Failed to load contracts:", err);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, statusFilter, typeFilter, page, limit]);

  useEffect(() => {
    loadContracts();
  }, [loadContracts]);

  const handleDelete = async (cid: string) => {
    if (confirm("Are you sure you want to remove this contract record?")) {
      try {
        await deleteContractApi(cid);
        loadContracts();
      } catch (err) {
        alert("Failed to delete contract.");
      }
    }
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(val);
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "Active":
        return "bg-emerald-100 text-emerald-800";
      case "Expiring Soon":
        return "bg-amber-100 text-amber-800";
      case "Expired":
        return "bg-rose-100 text-rose-800";
      case "Draft":
        return "bg-slate-100 text-slate-700";
      default:
        return "bg-blue-100 text-blue-800";
    }
  };

  const totalContracts = contractsData?.total_contracts ?? 0;
  const startCount = (page - 1) * limit + 1;
  const endCount = Math.min(page * limit, totalContracts);

  return (
    <div className="flex min-h-screen bg-[#f8fafc]">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Header title="Contracts Portfolio" />

        <main className="p-8 max-w-7xl mx-auto w-full space-y-6 flex-1">
          {/* Header Row: Title + Total Badge + Action Buttons */}
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Contracts Portfolio</h1>
              <span className="px-3 py-1 rounded-full bg-slate-200/70 text-slate-700 text-xs font-bold">
                {totalContracts} Total
              </span>
            </div>

            <div className="flex items-center gap-3">
              <a
                href={getExportContractsUrl()}
                download="contracts_portfolio.csv"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200/80 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-sm shadow-xs transition-colors"
              >
                <Download className="w-4 h-4 text-slate-500" />
                <span>Export List</span>
              </a>

              <button
                onClick={() => setIsUploadOpen(true)}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm shadow-md shadow-blue-600/20 transition-all"
              >
                <Plus className="w-4 h-4" />
                <span>+ New Contract</span>
              </button>
            </div>
          </div>

          {/* Main Card Container */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-6">
            {/* Filter & Pagination Controls Bar */}
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-4 flex-1 min-w-[280px]">
                {/* Search filter input */}
                <div className="relative flex-1 max-w-xs">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Filter by file name..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full bg-white border border-slate-200 rounded-xl pl-9 pr-4 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 transition-all"
                  />
                </div>

                {/* Status Dropdown */}
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-slate-500 text-xs font-semibold">Status:</span>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="bg-white border border-slate-200 rounded-xl px-3 py-2 text-sm font-semibold text-slate-800 focus:ring-2 focus:ring-blue-500/20 focus:outline-hidden"
                  >
                    <option value="All Statuses">All Statuses</option>
                    <option value="Active">Active</option>
                    <option value="Expiring Soon">Expiring Soon</option>
                    <option value="Expired">Expired</option>
                    <option value="Draft">Draft</option>
                  </select>
                </div>

                {/* Type Dropdown */}
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-slate-500 text-xs font-semibold">Type:</span>
                  <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    className="bg-white border border-slate-200 rounded-xl px-3 py-2 text-sm font-semibold text-slate-800 focus:ring-2 focus:ring-blue-500/20 focus:outline-hidden"
                  >
                    <option value="All Types">All Types</option>
                    <option value="Master Agreement">Master Agreement</option>
                    <option value="Service Contract">Service Contract</option>
                    <option value="SOW / Order Form">SOW / Order Form</option>
                    <option value="Service Terms">Service Terms</option>
                    <option value="Subscription Agreement">Subscription Agreement</option>
                    <option value="Amendment">Amendment</option>
                  </select>
                </div>
              </div>

              {/* Pagination control */}
              <div className="flex items-center gap-3 text-xs text-slate-500 font-medium">
                <span>
                  Showing {startCount}-{endCount} of {totalContracts} contracts
                </span>
                <div className="flex items-center gap-1">
                  <button
                    disabled={page === 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4 text-slate-600" />
                  </button>
                  <button
                    disabled={endCount >= totalContracts}
                    onClick={() => setPage((p) => p + 1)}
                    className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 transition-colors"
                  >
                    <ChevronRight className="w-4 h-4 text-slate-600" />
                  </button>
                </div>
              </div>
            </div>

            {/* Contracts Portfolio Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead>
                  <tr className="border-b border-slate-100 text-xs text-slate-400 font-bold uppercase tracking-wider">
                    <th className="pb-3.5 font-bold">Contract Name</th>
                    <th className="pb-3.5 font-bold">Supplier</th>
                    <th className="pb-3.5 font-bold">Document Type</th>
                    <th className="pb-3.5 font-bold">Annual Value</th>
                    <th className="pb-3.5 font-bold">Start Date</th>
                    <th className="pb-3.5 font-bold">End Date</th>
                    <th className="pb-3.5 font-bold text-center">Status</th>
                    <th className="pb-3.5 font-bold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100/80">
                  {loading ? (
                    <tr>
                      <td colSpan={8} className="py-10 text-center text-slate-400">
                        Loading contract portfolio...
                      </td>
                    </tr>
                  ) : contractsData?.contracts.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-10 text-center text-slate-400">
                        No contracts found matching current filters.
                      </td>
                    </tr>
                  ) : (
                    contractsData?.contracts.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="py-4 pr-4 font-bold text-slate-900 flex items-center gap-2.5">
                          <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                          <span className="truncate max-w-[240px]" title={item.contract_name}>
                            {item.contract_name}
                          </span>
                        </td>
                        <td className="py-4 px-2 text-slate-700 font-medium">{item.supplier}</td>
                        <td className="py-4 px-2 text-slate-500 font-normal">{item.document_type}</td>
                        <td className="py-4 px-2 font-extrabold text-slate-900">
                          {formatCurrency(item.annual_value)}
                        </td>
                        <td className="py-4 px-2 text-slate-500 font-medium whitespace-nowrap">
                          {item.start_date}
                        </td>
                        <td className="py-4 px-2 text-slate-500 font-medium whitespace-nowrap">
                          {item.end_date}
                        </td>
                        <td className="py-4 px-2 text-center">
                          <span
                            className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${getStatusBadgeClass(
                              item.status
                            )}`}
                          >
                            {item.status}
                          </span>
                        </td>
                        <td className="py-4 pl-2 text-right flex items-center justify-end gap-1">
                          <button
                            onClick={() => {
                              setEditingContract(item);
                              setIsEditOpen(true);
                            }}
                            className="p-1.5 text-slate-400 hover:text-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
                            title="Edit Contract"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(item.id)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
                            title="Delete Contract"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </main>
        <Footer />
      </div>

      {/* Upload Contract Modal */}
      <UploadContractModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={loadContracts}
      />

      {/* Edit Contract Modal */}
      <EditContractModal
        contract={editingContract}
        isOpen={isEditOpen}
        onClose={() => {
          setIsEditOpen(false);
          setEditingContract(null);
        }}
        onSuccess={loadContracts}
      />
    </div>
  );
}
