import { STATUSES, STATUS_LABELS } from "../api";

const PRIORITY_STYLES = {
  low: "bg-slate-100 text-slate-600",
  medium: "bg-sky-100 text-sky-700",
  high: "bg-amber-100 text-amber-700",
  urgent: "bg-red-100 text-red-700",
};

export default function TaskCard({ task, onChangeStatus, onDelete }) {
  return (
    <div className="rounded-xl bg-white p-3 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-slate-800">{task.title}</p>
        <button
          onClick={() => onDelete(task)}
          title="Delete task"
          className="text-slate-300 transition hover:text-red-500"
        >
          ✕
        </button>
      </div>
      <div className="mt-2 flex items-center gap-2">
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
            PRIORITY_STYLES[task.priority] || PRIORITY_STYLES.medium
          }`}
        >
          {task.priority}
        </span>
        {task.assignee && (
          <span className="text-xs text-slate-500">@{task.assignee}</span>
        )}
      </div>
      <select
        value={task.status}
        onChange={(e) => onChangeStatus(task, e.target.value)}
        className="mt-3 w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-600 outline-none focus:border-indigo-400"
      >
        {STATUSES.map((s) => (
          <option key={s} value={s}>
            {STATUS_LABELS[s]}
          </option>
        ))}
      </select>
    </div>
  );
}
