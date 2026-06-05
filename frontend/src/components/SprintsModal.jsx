import { useState } from "react";

const STATUS_BADGE = {
  planned: "bg-slate-100 text-slate-600",
  active: "bg-emerald-100 text-emerald-700",
  completed: "bg-indigo-100 text-indigo-700",
};

export default function SprintsModal({ sprints, onAdd, onUpdate, onDelete, onClose }) {
  const [name, setName] = useState("");
  const [goal, setGoal] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");

  function submit(e) {
    e.preventDefault();
    if (!name.trim()) return;
    onAdd({
      name: name.trim(),
      goal: goal.trim() || null,
      start_date: start || null,
      end_date: end || null,
    });
    setName("");
    setGoal("");
    setStart("");
    setEnd("");
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/40 p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white p-5 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-800">🏃 Sprints</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>

        <form onSubmit={submit} className="mb-4 space-y-2 rounded-xl bg-slate-50 p-3">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Sprint name (e.g. Sprint 1)"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
          />
          <input
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Sprint goal (optional)"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
          />
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-500">Start</label>
            <input
              type="date"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm outline-none focus:border-indigo-500"
            />
            <label className="text-xs text-slate-500">End</label>
            <input
              type="date"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm outline-none focus:border-indigo-500"
            />
            <button className="ml-auto rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700">
              Create
            </button>
          </div>
        </form>

        <div className="max-h-72 space-y-2 overflow-y-auto">
          {sprints.length === 0 && (
            <p className="py-4 text-center text-sm text-slate-400">No sprints yet.</p>
          )}
          {sprints.map((s) => (
            <div key={s.id} className="rounded-xl border border-slate-200 p-3">
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-semibold text-slate-800">{s.name}</p>
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${STATUS_BADGE[s.status]}`}
                    >
                      {s.status}
                    </span>
                  </div>
                  {(s.start_date || s.end_date) && (
                    <p className="text-xs text-slate-500">
                      {s.start_date || "—"} → {s.end_date || "—"}
                    </p>
                  )}
                  {s.goal && <p className="mt-0.5 truncate text-xs text-slate-500">🎯 {s.goal}</p>}
                </div>
                <button
                  onClick={() => onDelete(s)}
                  title="Delete sprint"
                  className="text-slate-300 transition hover:text-red-500"
                >
                  ✕
                </button>
              </div>
              <div className="mt-2 flex gap-2">
                {s.status !== "active" && (
                  <button
                    onClick={() => onUpdate(s, { status: "active" })}
                    className="rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-100"
                  >
                    Start
                  </button>
                )}
                {s.status !== "completed" && (
                  <button
                    onClick={() => onUpdate(s, { status: "completed" })}
                    className="rounded-md bg-indigo-50 px-2 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-100"
                  >
                    Complete
                  </button>
                )}
                {s.status !== "planned" && (
                  <button
                    onClick={() => onUpdate(s, { status: "planned" })}
                    className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-200"
                  >
                    Reset to planned
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
