const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: "user" | "admin";
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface MetricCardData {
  count: string | number;
  change?: string;
  badge?: string;
}

export interface ActivityItem {
  id: string;
  document_name: string;
  action: string;
  initiated_by: string;
  date: string;
  timestamp?: string;
}

export interface OverviewData {
  active_contracts: MetricCardData;
  vetted_suppliers: MetricCardData;
  pending_renewals: MetricCardData;
  compliance_score: MetricCardData;
  recent_activities: ActivityItem[];
}

export interface ContractRecord {
  id: string;
  contract_name: string;
  supplier: string;
  document_type: string;
  annual_value: number;
  start_date: string;
  end_date: string;
  status: "Active" | "Expiring Soon" | "Expired" | "Draft" | string;
  created_at?: string;
}

export interface ContractsListResponse {
  total_contracts: number;
  page: number;
  limit: number;
  contracts: ContractRecord[];
}

export interface SearchResultItem {
  id: string;
  document_title: string;
  supplier: string;
  document_type: string;
  confidence_percentage: number;
  confidence_label: string;
  passage_text: string;
  execution_date: string;
  chunk_id: string;
  section_title: string;
  similarity_score: number;
}

export interface SearchResponse {
  query: string;
  total_matches: number;
  results: SearchResultItem[];
  counts_by_type: Record<string, number>;
  counts_by_confidence: Record<string, number>;
}

// Authentication Service Functions
export async function signupUser(fullName: string, email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ full_name: fullName, email, password }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Signup failed.");
  return data;
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Invalid email or password.");
  return data;
}

export async function loginAdmin(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Admin authentication failed.");
  return data;
}

export async function getCurrentUser(token: string): Promise<UserProfile> {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Failed to fetch session.");
  return data.user;
}

// Overview API
export async function fetchOverviewData(): Promise<OverviewData> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/overview`);
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Failed to fetch overview data.");
    }
    return await response.json();
  } catch (err) {
    console.warn("Backend API unreachable during startup, retrying overview fetch...", err);
    try {
      await new Promise((res) => setTimeout(res, 1000));
      const response = await fetch(`${API_BASE_URL}/api/overview`);
      if (response.ok) return await response.json();
    } catch (_) {}

    return {
      active_contracts: { count: 0, change: "Active in DB" },
      vetted_suppliers: { count: 0, change: "Registered Vendors" },
      pending_renewals: { count: 0, badge: "Expiring Soon" },
      compliance_score: { count: "100%", change: "Portfolio Verified" },
      recent_activities: []
    };
  }
}

// Contracts API
export async function fetchContractsList(params?: {
  search?: string;
  status?: string;
  type?: string;
  page?: number;
  limit?: number;
}): Promise<ContractsListResponse> {
  const query = new URLSearchParams();
  if (params?.search) query.append("search", params.search);
  if (params?.status && params.status !== "All Statuses") query.append("status", params.status);
  if (params?.type && params.type !== "All Types") query.append("type", params.type);
  if (params?.page) query.append("page", params.page.toString());
  if (params?.limit) query.append("limit", params.limit.toString());

  const response = await fetch(`${API_BASE_URL}/api/contracts/list?${query.toString()}`);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Failed to fetch contracts.");
  return data;
}

export async function uploadContract(formData: FormData): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/contracts/upload`, {
    method: "POST",
    body: formData,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Contract upload failed.");
  return data;
}

export async function updateContractApi(contractId: string, updateData: Partial<ContractRecord>): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/contracts/${contractId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updateData),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Failed to update contract.");
  return data;
}

export async function deleteContractApi(contractId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/contracts/${contractId}`, {
    method: "DELETE",
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Failed to delete contract.");
  return data;
}

export function getExportContractsUrl(): string {
  return `${API_BASE_URL}/api/contracts/export`;
}

// AI Intelligent Search API
export async function searchIntelligentContracts(params: {
  q?: string;
  docTypes?: string[];
  confidence?: string[];
  status?: string[];
}): Promise<SearchResponse> {
  const query = new URLSearchParams();
  if (params.q) query.append("q", params.q);
  if (params.docTypes && params.docTypes.length > 0) query.append("doc_types", params.docTypes.join(","));
  if (params.confidence && params.confidence.length > 0) query.append("confidence", params.confidence.join(","));
  if (params.status && params.status.length > 0) query.append("contract_status", params.status.join(","));

  const response = await fetch(`${API_BASE_URL}/api/query/search?${query.toString()}`);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Search failed.");
  return data;
}

export async function askContractAI(question: string, contractId?: string, userEmail?: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, contract_id: contractId, user_email: userEmail }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "AI query failed.");
  return data;
}

export async function fetchSuppliersApi(): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/suppliers`);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Failed to fetch suppliers.");
  return data;
}

export async function addSupplierApi(name: string, category: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/suppliers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, category }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Failed to add supplier.");
  return data;
}

export async function runAuditApi(): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/audit/run`, {
    method: "POST",
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Failed to run audit.");
  return data;
}

export interface AiQueryLogItem {
  id: string;
  query_type: string;
  question: string;
  answer: string;
  sources_count: number;
  sources?: any[];
  user_email?: string;
  initiated_by: string;
  date: string;
  timestamp: string;
}

export async function fetchAiQueryLogsApi(): Promise<{ total: number; logs: AiQueryLogItem[] }> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/audit/ai-logs`);
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Failed to fetch AI query logs.");
    }
    return await response.json();
  } catch (err) {
    console.warn("Backend API unreachable during startup, retrying AI logs fetch...", err);
    try {
      await new Promise((res) => setTimeout(res, 1000));
      const response = await fetch(`${API_BASE_URL}/api/audit/ai-logs`);
      if (response.ok) return await response.json();
    } catch (_) {}
    return { total: 0, logs: [] };
  }
}

export async function fetchUserQueryHistoryApi(userEmail?: string): Promise<{ total: number; history: AiQueryLogItem[] }> {
  try {
    const query = userEmail ? `?user_email=${encodeURIComponent(userEmail)}` : "";
    const response = await fetch(`${API_BASE_URL}/api/query/user-history${query}`);
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Failed to fetch user query history.");
    }
    return await response.json();
  } catch (err) {
    console.warn("User query history API connection warning:", err);
    return { total: 0, history: [] };
  }
}

export async function clearUserQueryHistoryApi(userEmail?: string): Promise<{ message: string; cleared_count: number }> {
  try {
    const query = userEmail ? `?user_email=${encodeURIComponent(userEmail)}` : "";
    const response = await fetch(`${API_BASE_URL}/api/query/user-history${query}`, {
      method: "DELETE"
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Failed to clear user query history.");
    }
    return await response.json();
  } catch (error: any) {
    console.warn("Clear query history API error:", error);
    throw error;
  }
}

export async function deleteUserQueryHistoryItemApi(logId: string, userEmail?: string): Promise<{ message: string; id: string }> {
  try {
    const query = userEmail ? `?user_email=${encodeURIComponent(userEmail)}` : "";
    const response = await fetch(`${API_BASE_URL}/api/query/user-history/${encodeURIComponent(logId)}${query}`, {
      method: "DELETE"
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Failed to delete query history item.");
    }
    return await response.json();
  } catch (error: any) {
    console.warn("Delete query history item API error:", error);
    throw error;
  }
}
