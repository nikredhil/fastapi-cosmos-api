import { getToken } from "./auth";

export const BASE = (import.meta.env.VITE_API_BASE || "http://localhost:8000").replace(/\/$/, "");

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) headers["Authorization"] = `Bearer ${await getToken()}`;
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

// multipart upload (no Content-Type so the browser sets the boundary)
async function upload(path, file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${await getToken()}` },
    body: form,
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

const qs = (params) => {
  const q = new URLSearchParams();
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") q.set(k, v);
  });
  const s = q.toString();
  return s ? `?${s}` : "";
};

export const api = {
  // --- local accounts (unauthenticated) ---
  register: (email, password, displayName) =>
    request("/auth/register", {
      method: "POST",
      auth: false,
      body: { email, password, display_name: displayName || null },
    }),
  loginLocal: (email, password) =>
    request("/auth/login", { method: "POST", auth: false, body: { email, password } }),

  // --- dashboard ---
  dashboard: (period) => request(`/dashboard${qs({ period })}`),

  // --- buildings ---
  listBuildings: () => request("/buildings").then((d) => d.items),
  getBuilding: (id) => request(`/buildings/${id}`),
  createBuilding: (body) => request("/buildings", { method: "POST", body }),
  updateBuilding: (id, patch) => request(`/buildings/${id}`, { method: "PATCH", body: patch }),
  deleteBuilding: (id) => request(`/buildings/${id}`, { method: "DELETE" }),

  // --- units ---
  listUnits: (bid) => request(`/buildings/${bid}/units`).then((d) => d.items),
  createUnit: (bid, body) => request(`/buildings/${bid}/units`, { method: "POST", body }),
  updateUnit: (bid, id, patch) =>
    request(`/buildings/${bid}/units/${id}`, { method: "PATCH", body: patch }),
  deleteUnit: (bid, id) => request(`/buildings/${bid}/units/${id}`, { method: "DELETE" }),

  // --- tenants ---
  listTenants: (bid) => request(`/buildings/${bid}/tenants`).then((d) => d.items),
  getTenant: (bid, id) => request(`/buildings/${bid}/tenants/${id}`),
  createTenant: (bid, body) => request(`/buildings/${bid}/tenants`, { method: "POST", body }),
  updateTenant: (bid, id, patch) =>
    request(`/buildings/${bid}/tenants/${id}`, { method: "PATCH", body: patch }),
  deleteTenant: (bid, id) => request(`/buildings/${bid}/tenants/${id}`, { method: "DELETE" }),

  // --- leases ---
  listLeases: (bid) => request(`/buildings/${bid}/leases`).then((d) => d.items),
  createLease: (bid, body) => request(`/buildings/${bid}/leases`, { method: "POST", body }),
  updateLease: (bid, id, patch) =>
    request(`/buildings/${bid}/leases/${id}`, { method: "PATCH", body: patch }),
  deleteLease: (bid, id) => request(`/buildings/${bid}/leases/${id}`, { method: "DELETE" }),

  // --- bills ---
  listBills: (bid, filters) =>
    request(`/buildings/${bid}/bills${qs(filters)}`).then((d) => d.items),
  createBill: (bid, body) => request(`/buildings/${bid}/bills`, { method: "POST", body }),
  updateBill: (bid, id, patch) =>
    request(`/buildings/${bid}/bills/${id}`, { method: "PATCH", body: patch }),
  deleteBill: (bid, id) => request(`/buildings/${bid}/bills/${id}`, { method: "DELETE" }),
  generateBills: (bid, body) =>
    request(`/buildings/${bid}/bills/generate`, { method: "POST", body }).then((d) => d.items),
  recordPayment: (bid, id, body) =>
    request(`/buildings/${bid}/bills/${id}/payments`, { method: "POST", body }),
  setRentStatus: (bid, body) =>
    request(`/buildings/${bid}/bills/rent-status`, { method: "POST", body }),

  // --- contracts / documents ---
  parseContract: (bid, file) => upload(`/buildings/${bid}/contracts/parse`, file),
  uploadImage: (bid, file) => upload(`/buildings/${bid}/contracts/upload`, file),
  contractImageUrl: (bid, imageId) => `${BASE}/buildings/${bid}/contracts/${imageId}`,

  // --- chat ---
  chat: (message, history) => request("/chat", { method: "POST", body: { message, history } }),
};

// ---------- shared constants & helpers ----------

export const BILL_TYPES = ["rent", "water", "electricity", "maintenance", "other"];
export const BILL_STATUSES = ["unpaid", "partial", "paid", "overdue"];

export const BILL_TYPE_META = {
  rent: { label: "Rent", icon: "🏠", color: "#2563eb" },
  water: { label: "Water", icon: "💧", color: "#0ea5e9" },
  electricity: { label: "Electricity", icon: "⚡", color: "#f59e0b" },
  maintenance: { label: "Maintenance", icon: "🔧", color: "#7c3aed" },
  other: { label: "Other", icon: "📄", color: "#64748b" },
};

export const STATUS_STYLES = {
  unpaid: "bg-slate-100 text-slate-600",
  partial: "bg-amber-100 text-amber-700",
  paid: "bg-emerald-100 text-emerald-700",
  overdue: "bg-red-100 text-red-700",
};

export const AVATAR_COLORS = [
  "#2563eb", "#0ea5e9", "#0d9488", "#7c3aed",
  "#db2777", "#ea580c", "#16a34a", "#475569",
];

export function rupees(amount) {
  const n = Number(amount || 0);
  return `₹${n.toLocaleString("en-IN")}`;
}

export function initials(name) {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export function currentPeriod() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export function formatPeriod(period) {
  if (!period) return "";
  const [y, m] = period.split("-");
  const idx = Number(m) - 1;
  return MONTH_NAMES[idx] ? `${MONTH_NAMES[idx]} ${y}` : period;
}

// Last N months as { value: "2026-06", label: "June 2026" }, newest first.
export function recentPeriods(n = 12) {
  const out = [];
  const d = new Date();
  for (let i = 0; i < n; i++) {
    const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    out.push({ value, label: formatPeriod(value) });
    d.setMonth(d.getMonth() - 1);
  }
  return out;
}
