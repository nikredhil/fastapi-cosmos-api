import { useState } from "react";
import { STATUSES, STATUS_LABELS, PRIORITIES, ITEM_TYPES, ITEM_TYPE_META } from "../api";
import TaskCard from "./TaskCard";

const COLUMN_ACCENT = {
  todo: "border-t-slate-400",
  in_progress: "border-t-indigo-400",
  blocked: "border-t-red-400",
  done: "border-t-emerald-400",
};

export default function Board({
  project,
  tasks,
  members,
  defaultSprintId,
  onCreateTask,
  onChangeStatus,
  onDelete,
  onOpen,
}) {
  const [title, setTitle] = useState("");
  const [itemType, setItemType] = useState("task");
  const [priority, setPriority] = useState("medium");
  const [points, setPoints] = useState("");
  const [assigneeId, setAssigneeId] = useState("");

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
    onCreateTask({
      title: title.trim(),
      item_type: itemType,
      priority,
      status: "todo",
      points: points === "" ? null : Number(points),
      assignee_id: assigneeId || null,
      // When viewing a specific sprint, drop new items straight into it.
      sprint_id:
        defaultSprintId && defaultSprintId !== "all" && defaultSprintId !== "backlog"
          ? defaultSprintId
          : null,
    });
    setTitle("");
    setPoints("");
    setAssigneeId("");
  }

  const byStatus = (s) => tasks.filter((t) => t.status === s);
  const pointsFor = (s) => byStatus(s).reduce((sum, t) => sum + (t.points || 0), 0);

  const inputCls =
    "rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-600 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200";

  return (
    <div className="flex flex-1 flex-col overflow-hidden p-6">
      <form onSubmit={submit} className="mb-5 flex flex-wrap items-center gap-2">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="New work item…"
          className={`min-w-[200px] flex-1 ${inputCls}`}
        />
        <select value={itemType} onChange={(e) => setItemType(e.target.value)} className={inputCls}>
          {ITEM_TYPES.map((t) => (
            <option key={t} value={t}>
              {ITEM_TYPE_META[t].icon} {ITEM_TYPE_META[t].label}
            </option>
          ))}
        </select>
        <select value={priority} onChange={(e) => setPriority(e.target.value)} className={inputCls}>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <input
          type="number"
          min="0"
          max="100"
          value={points}
          onChange={(e) => setPoints(e.target.value)}
          placeholder="pts"
          className={`w-20 ${inputCls}`}
        />
        <select
          value={assigneeId}
          onChange={(e) => setAssigneeId(e.target.value)}
          className={inputCls}
        >
          <option value="">Unassigned</option>
          {members.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name}
            </option>
          ))}
        </select>
        <button className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700">
          Add item
        </button>
      </form>

      <div className="grid flex-1 grid-cols-1 gap-4 overflow-y-auto sm:grid-cols-2 lg:grid-cols-4">
        {STATUSES.map((status) => (
          <div
            key={status}
            className={`flex flex-col rounded-xl border-t-4 bg-slate-50 p-3 ${COLUMN_ACCENT[status]}`}
          >
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-700">
                {STATUS_LABELS[status]}{" "}
                <span className="text-slate-400">({byStatus(status).length})</span>
              </h3>
              <span className="rounded-full bg-white px-2 text-xs font-medium text-slate-500 ring-1 ring-slate-200">
                {pointsFor(status)} pts
              </span>
            </div>
            <div className="flex flex-col gap-2">
              {byStatus(status).map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onChangeStatus={onChangeStatus}
                  onDelete={onDelete}
                  onOpen={onOpen}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
