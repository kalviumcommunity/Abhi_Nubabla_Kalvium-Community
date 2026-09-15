"use client";

import React, { useState } from "react";
import { X, Upload, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import { uploadContract } from "@/services/api";

interface UploadContractModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function UploadContractModal({ isOpen, onClose, onSuccess }: UploadContractModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [supplier, setSupplier] = useState("");
  const [documentType, setDocumentType] = useState("Master Agreement");
  const [annualValue, setAnnualValue] = useState("150000");
  const [startDate, setStartDate] = useState("2026-01-01");
  const [endDate, setEndDate] = useState("2027-12-31");
  const [statusVal, setStatusVal] = useState("Active");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a contract document file to upload.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      if (supplier) formData.append("supplier", supplier);
      if (documentType) formData.append("document_type", documentType);
      if (annualValue) formData.append("annual_value", annualValue);
      if (startDate) formData.append("start_date", startDate);
      if (endDate) formData.append("end_date", endDate);
      if (statusVal) formData.append("contract_status", statusVal);

      await uploadContract(formData);
      setSuccessMsg("Contract processed & intelligence indexed successfully!");

      setTimeout(() => {
        setSuccessMsg(null);
        setFile(null);
        onSuccess();
        onClose();
      }, 1200);
    } catch (err: any) {
      setError(err.message || "Failed to upload contract.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
      <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 relative animate-in fade-in zoom-in-95 duration-200">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-slate-600 p-1.5 rounded-full hover:bg-slate-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Upload className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Upload New Contract</h2>
            <p className="text-xs text-slate-500">Extract instantly using AI models & index vector storage</p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-50 text-red-700 text-sm flex items-center gap-2 border border-red-200">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-50 text-emerald-700 text-sm flex items-center gap-2 border border-emerald-200">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-sm">
          {/* File Dropzone */}
          <div>
            <label className="block font-semibold text-slate-700 mb-1.5">Contract File (PDF, DOCX, TXT)</label>
            <div className="border-2 border-dashed border-slate-200 rounded-2xl p-4 text-center hover:border-blue-500/50 bg-slate-50/50 transition-colors cursor-pointer relative">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <FileText className="w-8 h-8 text-blue-500 mx-auto mb-1" />
              {file ? (
                <p className="font-semibold text-slate-900 text-sm">{file.name}</p>
              ) : (
                <p className="text-xs text-slate-500">
                  <span className="font-semibold text-blue-600">Click to upload</span> or drag and drop
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Supplier Name</label>
              <input
                type="text"
                placeholder="e.g. Acme Corp"
                value={supplier}
                onChange={(e) => setSupplier(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-slate-900 focus:ring-2 focus:ring-blue-500/20 focus:outline-hidden"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Document Type</label>
              <select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-slate-900 bg-white focus:ring-2 focus:ring-blue-500/20 focus:outline-hidden"
              >
                <option value="Master Agreement">Master Agreement</option>
                <option value="Service Contract">Service Contract</option>
                <option value="SOW / Order Form">SOW / Order Form</option>
                <option value="Subscription Agreement">Subscription Agreement</option>
                <option value="Amendment">Amendment</option>
                <option value="NDA">NDA</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Annual Value ($)</label>
              <input
                type="number"
                value={annualValue}
                onChange={(e) => setAnnualValue(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-slate-900 focus:ring-2 focus:ring-blue-500/20 focus:outline-hidden"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Status</label>
              <select
                value={statusVal}
                onChange={(e) => setStatusVal(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-slate-900 bg-white focus:ring-2 focus:ring-blue-500/20 focus:outline-hidden"
              >
                <option value="Active">Active</option>
                <option value="Expiring Soon">Expiring Soon</option>
                <option value="Draft">Draft</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-slate-900 focus:ring-2 focus:ring-blue-500/20 focus:outline-hidden"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-slate-900 focus:ring-2 focus:ring-blue-500/20 focus:outline-hidden"
              />
            </div>
          </div>

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-slate-200 text-slate-700 font-semibold hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-md shadow-blue-600/20 flex items-center gap-2 transition-all disabled:opacity-50"
            >
              {loading && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
              <span>{loading ? "Processing..." : "Process & Save"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
