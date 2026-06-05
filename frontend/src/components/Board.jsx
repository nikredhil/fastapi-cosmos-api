import { useState } from "react";
import { STATUSES, STATUS_LABELS, PRIORITIES } from "../api";
import TaskCard from "./TaskCard";

const COLUMN_ACCENT = {
  todo: "border-t-slate-400",
  in_progress: "border-t-indigo-400",
  blocked: "border-t-red-400",
  done: "border-t-emerald-400",
};

export default function Board({ project, tasks, onCreateTask, onChangeStatus, onDelete }) {
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState("medium");

  if (!project) {
    return (
      <div className="flex flex-1 items-center justify-center text-slate-400">
        Select or create a project to get started.
      </div>
    );
  }

  function submit(e) {
    e.preventDefault();
    if (!title.trim()) return;
    onCreateTask({ title: title.trim(), priority, status: "todo" });
    setTitle("");
    setPriority("medium");
  }

  const byStatus = (s) => tasks.filter((t) => t.status === s);

  return (
    <div className="flex flex-1 flex-col overflow-hidden p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-slate-800">{project.name}</h2>
        <p className="text-sm text-slate-500">{tasks.length} task(s)</p>
      </div>

      <form onSubmit={submit} className="mb-5 flex flex-wrap gap-2">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="New task title…"
          className="min-w-[220px] flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
        />
        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-600 outline-none focus:border-indigo-500"
        >
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <button className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700">
          Add task
        </button>
      </form>

      <div className="grid flex-1 grid-cols-1 gap-4 overflow-y-auto sm:grid-cols-2 lg:grid-cols-4">
        {STATUSES.map((status) => (
          <div
            key={status}
            className={`flex flex-col rounded-xl border-t-4 bg-slate-50 p-3 ${COLUMN_ACCENT[status]}`}
          >
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-700">{STATUS_LABELS[status]}</h3>
              <span className="rounded-full bg-white px-2 text-xs text-slate-500 ring-1 ring-slate-200">
                {byStatus(status).length}
              </span>
            </div>
            <div className="flex flex-col gap-2">
              {byStatus(status).map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onChangeStatus={onChangeStatus}
                  onDelete={onDelete}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
