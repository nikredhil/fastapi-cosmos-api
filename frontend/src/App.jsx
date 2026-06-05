import { useState, useEffect, useCallback } from "react";
import { api } from "./api";
import Login from "./components/Login";
import Board from "./components/Board";
import ChatPanel from "./components/ChatPanel";

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("tt_token"));
  const [username, setUsername] = useState(() => localStorage.getItem("tt_user"));
  const [projects, setProjects] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [newProject, setNewProject] = useState("");
  const [error, setError] = useState(null);

  const logout = useCallback(() => {
    localStorage.removeItem("tt_token");
    localStorage.removeItem("tt_user");
    setToken(null);
    setUsername(null);
    setProjects([]);
    setSelectedId(null);
    setTasks([]);
  }, []);

  const guard = useCallback(
    async (fn) => {
      try {
        return await fn();
      } catch (err) {
        if (String(err.message).startsWith("401")) logout();
        else setError(err.message);
      }
    },
    [logout]
  );

  const loadProjects = useCallback(async () => {
    if (!token) return;
    await guard(async () => {
      const items = await api.listProjects(token);
      setProjects(items);
      setSelectedId((cur) => cur ?? items[0]?.id ?? null);
    });
  }, [token, guard]);

  const loadTasks = useCallback(async () => {
    if (!token || !selectedId) {
      setTasks([]);
      return;
    }
    await guard(async () => setTasks(await api.listTasks(token, selectedId)));
  }, [token, selectedId, guard]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);
  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  function onLogin(tok, user) {
    localStorage.setItem("tt_token", tok);
    localStorage.setItem("tt_user", user);
    setToken(tok);
    setUsername(user);
  }

  async function createProject(e) {
    e.preventDefault();
    if (!newProject.trim()) return;
    await guard(async () => {
      const p = await api.createProject(token, newProject.trim());
      setNewProject("");
      await loadProjects();
      setSelectedId(p.id);
    });
  }

  async function refreshAll() {
    await loadProjects();
    await loadTasks();
  }

  const selected = projects.find((p) => p.id === selectedId) || null;

  if (!token) return <Login onLogin={onLogin} />;

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="flex w-64 flex-col border-r border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-4">
          <h1 className="text-lg font-bold text-slate-800">✅ Task Tracker</h1>
          <p className="text-xs text-slate-500">
            Signed in as <span className="font-medium">{username}</span>
          </p>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {projects.map((p) => (
            <button
              key={p.id}
              onClick={() => setSelectedId(p.id)}
              className={`w-full truncate rounded-lg px-3 py-2 text-left text-sm transition ${
                p.id === selectedId
                  ? "bg-indigo-50 font-semibold text-indigo-700"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {p.name}
            </button>
          ))}
          {projects.length === 0 && (
            <p className="px-3 py-2 text-sm text-slate-400">No projects yet.</p>
          )}
        </nav>
        <form onSubmit={createProject} className="border-t border-slate-200 p-3">
          <input
            value={newProject}
            onChange={(e) => setNewProject(e.target.value)}
            placeholder="New project…"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
          />
          <button className="mt-2 w-full rounded-lg bg-slate-800 py-2 text-sm font-semibold text-white transition hover:bg-slate-900">
            + Add project
          </button>
        </form>
        <button
          onClick={logout}
          className="border-t border-slate-200 px-4 py-3 text-left text-sm text-slate-500 hover:bg-slate-50"
        >
          Sign out
        </button>
      </aside>

      {/* Board */}
      <main className="flex flex-1 flex-col overflow-hidden">
        {error && (
          <div className="bg-red-50 px-6 py-2 text-sm text-red-700">
            {error}{" "}
            <button onClick={() => setError(null)} className="underline">
              dismiss
            </button>
          </div>
        )}
        <Board
          project={selected}
          tasks={tasks}
          onCreateTask={(task) =>
            guard(async () => {
              await api.createTask(token, selectedId, task);
              await loadTasks();
            })
          }
          onChangeStatus={(task, status) =>
            guard(async () => {
              await api.updateTask(token, selectedId, task.id, { status });
              await loadTasks();
            })
          }
          onDelete={(task) =>
            guard(async () => {
              await api.deleteTask(token, selectedId, task.id);
              await loadTasks();
            })
          }
        />
      </main>

      {/* Chat */}
      <ChatPanel token={token} onDataChanged={refreshAll} />
    </div>
  );
}
