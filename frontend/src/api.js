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

export const api = {
  // --- projects ---
  listProjects: () => request("/projects").then((d) => d.items),
  createProject: (name, description) =>
    request("/projects", { method: "POST", body: { name, description } }),
  deleteProject: (id) => request(`/projects/${id}`, { method: "DELETE" }),

  // --- members ---
  listMembers: (projectId) => request(`/projects/${projectId}/members`).then((d) => d.items),
  createMember: (projectId, member) =>
    request(`/projects/${projectId}/members`, { method: "POST", body: member }),
  updateMember: (projectId, memberId, patch) =>
    request(`/projects/${projectId}/members/${memberId}`, { method: "PATCH", body: patch }),
  deleteMember: (projectId, memberId) =>
    request(`/projects/${projectId}/members/${memberId}`, { method: "DELETE" }),

  // --- sprints ---
  listSprints: (projectId) => request(`/projects/${projectId}/sprints`).then((d) => d.items),
  createSprint: (projectId, sprint) =>
    request(`/projects/${projectId}/sprints`, { method: "POST", body: sprint }),
  updateSprint: (projectId, sprintId, patch) =>
    request(`/projects/${projectId}/sprints/${sprintId}`, { method: "PATCH", body: patch }),
  deleteSprint: (projectId, sprintId) =>
    request(`/projects/${projectId}/sprints/${sprintId}`, { method: "DELETE" }),

  // --- tasks ---
  listTasks: (projectId, { status, sprintId, assigneeId } = {}) => {
    const q = new URLSearchParams();
    if (status) q.set("status", status);
    if (sprintId) q.set("sprint_id", sprintId);
    if (assigneeId) q.set("assignee_id", assigneeId);
    const qs = q.toString();
    return request(`/projects/${projectId}/tasks${qs ? `?${qs}` : ""}`).then((d) => d.items);
  },
  createTask: (projectId, task) =>
    request(`/projects/${projectId}/tasks`, { method: "POST", body: task }),
  updateTask: (projectId, taskId, patch) =>
    request(`/projects/${projectId}/tasks/${taskId}`, { method: "PATCH", body: patch }),
  addComment: (projectId, taskId, body) =>
    request(`/projects/${projectId}/tasks/${taskId}/comments`, {
      method: "POST",
      body: { body },
    }),
  deleteTask: (projectId, taskId) =>
    request(`/projects/${projectId}/tasks/${taskId}`, { method: "DELETE" }),

  chat: (message, history) =>
    request("/chat", { method: "POST", body: { message, history } }),
};

export const STATUSES = ["todo", "in_progress", "blocked", "done"];
export const PRIORITIES = ["low", "medium", "high", "urgent"];
export const ITEM_TYPES = ["story", "task", "bug"];
export const SPRINT_STATUSES = ["planned", "active", "completed"];

export const STATUS_LABELS = {
  todo: "To Do",
  in_progress: "In Progress",
  blocked: "Blocked",
  done: "Done",
};

export const ITEM_TYPE_META = {
  story: { icon: "📘", label: "Story", color: "text-emerald-600" },
  task: { icon: "✅", label: "Task", color: "text-sky-600" },
  bug: { icon: "🐞", label: "Bug", color: "text-red-600" },
};

export const PRIORITY_STYLES = {
  low: "bg-slate-100 text-slate-600",
  medium: "bg-sky-100 text-sky-700",
  high: "bg-amber-100 text-amber-700",
  urgent: "bg-red-100 text-red-700",
};

// Palette offered when creating a member without an explicit color.
export const AVATAR_COLORS = [
  "#6366f1", "#0ea5e9", "#10b981", "#f59e0b",
  "#ef4444", "#ec4899", "#8b5cf6", "#14b8a6",
];

export function initials(name) {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}
