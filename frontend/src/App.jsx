import { useState, useEffect, useCallback } from "react";
import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import { api } from "./api";
import { getActiveAccount } from "./auth";
import Login from "./components/Login";
import Board from "./components/Board";
import ChatPanel from "./components/ChatPanel";
import SprintBar from "./components/SprintBar";
import TaskDetail from "./components/TaskDetail";
import MembersModal from "./components/MembersModal";
import SprintsModal from "./components/SprintsModal";

export default function App() {
  const { instance } = useMsal();
  const isAuthenticated = useIsAuthenticated();
  const account = getActiveAccount();
  const username = account?.name || account?.username || "";

  const [projects, setProjects] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [members, setMembers] = useState([]);
  const [sprints, setSprints] = useState([]);
  const [selectedSprintId, setSelectedSprintId] = useState("all");
  const [assigneeFilter, setAssigneeFilter] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showMembers, setShowMembers] = useState(false);
  const [showSprints, setShowSprints] = useState(false);
  const [newProject, setNewProject] = useState("");
  const [error, setError] = useState(null);

  const logout = useCallback(() => {
    instance.logoutPopup().catch(() => {});
  }, [instance]);

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
    if (!isAuthenticated) return;
    await guard(async () => {
      const items = await api.listProjects();
      setProjects(items);
      setSelectedId((cur) => cur ?? items[0]?.id ?? null);
    });
  }, [isAuthenticated, guard]);

  const loadTasks = useCallback(async () => {
    if (!isAuthenticated || !selectedId) {
      setTasks([]);
      return;
    }
    await guard(async () =>
      setTasks(
        await api.listTasks(selectedId, {
          sprintId: selectedSprintId === "all" ? undefined : selectedSprintId,
          assigneeId: assigneeFilter || undefined,
        })
      )
    );
  }, [isAuthenticated, selectedId, selectedSprintId, assigneeFilter, guard]);

  const loadMeta = useCallback(async () => {
    if (!isAuthenticated || !selectedId) {
      setMembers([]);
      setSprints([]);
      return;
    }
    await guard(async () => {
      const [m, s] = await Promise.all([
        api.listMembers(selectedId),
        api.listSprints(selectedId),
      ]);
      setMembers(m);
      setSprints(s);
    });
  }, [isAuthenticated, selectedId, guard]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);
  useEffect(() => {
    loadTasks();
  }, [loadTasks]);
  useEffect(() => {
    loadMeta();
  }, [loadMeta]);

  // Reset board filters and close overlays when switching projects.
  useEffect(() => {
    setSelectedSprintId("all");
    setAssigneeFilter(null);
    setSelectedTask(null);
    setShowMembers(false);
    setShowSprints(false);
  }, [selectedId]);

  async function createProject(e) {
    e.preventDefault();
    if (!newProject.trim()) return;
    await guard(async () => {
      const p = await api.createProject(newProject.trim());
      setNewProject("");
      await loadProjects();
      setSelectedId(p.id);
    });
  }

  async function refreshAll() {
    await loadProjects();
    await loadTasks();
    await loadMeta();
  }

  // --- task handlers ---
  const createTask = (task) =>
    guard(async () => {
      await api.createTask(selectedId, task);
      await loadTasks();
    });

  const changeStatus = (task, status) =>
    guard(async () => {
      const updated = await api.updateTask(selectedId, task.id, { status });
      await loadTasks();
      if (selectedTask?.id === task.id) setSelectedTask(updated);
    });

  const updateTask = (patch) =>
    guard(async () => {
      const updated = await api.updateTask(selectedId, selectedTask.id, patch);
      setSelectedTask(updated);
      await loadTasks();
    });

  const addComment = (body) =>
    guard(async () => {
      const updated = await api.addComment(selectedId, selectedTask.id, body);
      setSelectedTask(updated);
      await loadTasks();
    });

  const deleteTask = (task) =>
    guard(async () => {
      await api.deleteTask(selectedId, task.id);
      if (selectedTask?.id === task.id) setSelectedTask(null);
      await loadTasks();
    });

  // --- member handlers ---
  const addMember = (member) =>
    guard(async () => {
      await api.createMember(selectedId, member);
      await loadMeta();
    });
  const deleteMember = (member) =>
    guard(async () => {
      await api.deleteMember(selectedId, member.id);
      await loadMeta();
      await loadTasks();
    });

  // --- sprint handlers ---
  const addSprint = (sprint) =>
    guard(async () => {
      await api.createSprint(selectedId, sprint);
      await loadMeta();
    });
  const updateSprint = (sprint, patch) =>
    guard(async () => {
      await api.updateSprint(selectedId, sprint.id, patch);
      await loadMeta();
    });
  const deleteSprint = (sprint) =>
    guard(async () => {
      await api.deleteSprint(selectedId, sprint.id);
      if (selectedSprintId === sprint.id) setSelectedSprintId("all");
      await loadMeta();
      await loadTasks();
    });

  const selected = projects.find((p) => p.id === selectedId) || null;

  if (!isAuthenticated) return <Login />;

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
        {selected && (
          <SprintBar
            project={selected}
            sprints={sprints}
            members={members}
            tasks={tasks}
            selectedSprintId={selectedSprintId}
            onSelectSprint={setSelectedSprintId}
            assigneeFilter={assigneeFilter}
            onAssigneeFilter={setAssigneeFilter}
            onManageTeam={() => setShowMembers(true)}
            onManageSprints={() => setShowSprints(true)}
          />
        )}
        <Board
          project={selected}
          tasks={tasks}
          members={members}
          defaultSprintId={selectedSprintId}
          onCreateTask={createTask}
          onChangeStatus={changeStatus}
          onDelete={deleteTask}
          onOpen={setSelectedTask}
        />
      </main>

      {/* Chat */}
      <ChatPanel onDataChanged={refreshAll} />

      {/* Overlays */}
      {selectedTask && (
        <TaskDetail
          task={selectedTask}
          members={members}
          sprints={sprints}
          onUpdate={updateTask}
          onAddComment={addComment}
          onDelete={deleteTask}
          onClose={() => setSelectedTask(null)}
        />
      )}
      {showMembers && (
        <MembersModal
          members={members}
          onAdd={addMember}
          onDelete={deleteMember}
          onClose={() => setShowMembers(false)}
        />
      )}
      {showSprints && (
        <SprintsModal
          sprints={sprints}
          onAdd={addSprint}
          onUpdate={updateSprint}
          onDelete={deleteSprint}
          onClose={() => setShowSprints(false)}
        />
      )}
    </div>
  );
}
