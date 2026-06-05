const BASE = (import.meta.env.VITE_API_BASE || "http://localhost:8000").replace(/\/$/, "");

async function request(path, { method = "GET", token, body } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
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
  login: (username) =>
    request("/auth/token", { method: "POST", body: { username } }).then((d) => d.access_token),

  listProjects: (token) => request("/projects", { token }).then((d) => d.items),
  createProject: (token, name, description) =>
    request("/projects", { method: "POST", token, body: { name, description } }),
  deleteProject: (token, id) => request(`/projects/${id}`, { method: "DELETE", token }),

  listTasks: (token, projectId, status) => {
    const q = status ? `?status=${status}` : "";
    return request(`/projects/${projectId}/tasks${q}`, { token }).then((d) => d.items);
  },
  createTask: (token, projectId, task) =>
    request(`/projects/${projectId}/tasks`, { method: "POST", token, body: task }),
  updateTask: (token, projectId, taskId, patch) =>
    request(`/projects/${projectId}/tasks/${taskId}`, { method: "PATCH", token, body: patch }),
  deleteTask: (token, projectId, taskId) =>
    request(`/projects/${projectId}/tasks/${taskId}`, { method: "DELETE", token }),

  chat: (token, message, history) =>
    request("/chat", { method: "POST", token, body: { message, history } }),
};

export const STATUSES = ["todo", "in_progress", "blocked", "done"];
export const PRIORITIES = ["low", "medium", "high", "urgent"];
export const STATUS_LABELS = {
  todo: "To Do",
  in_progress: "In Progress",
  blocked: "Blocked",
  done: "Done",
};
