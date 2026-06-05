import { STATUSES, STATUS_LABELS, PRIORITY_STYLES, ITEM_TYPE_META } from "../api";
import Avatar from "./Avatar";

export default function TaskCard({ task, onChangeStatus, onDelete, onOpen }) {
  const meta = ITEM_TYPE_META[task.item_type] || ITEM_TYPE_META.task;
  const tags = task.tags || [];
  const commentCount = (task.comments || []).length;

  return (
    <div
      onClick={() => onOpen(task)}
      className="cursor-pointer rounded-xl bg-white p-3 shadow-sm ring-1 ring-slate-200 transition hover:ring-indigo-300"
    >
      <div className="flex items-center justify-between gap-2 text-xs text-slate-400">
        <span className="flex items-center gap-1">
          <span title={meta.label}>{meta.icon}</span>
          <span className="font-mono font-semibold">{task.key || task.id.slice(0, 6)}</span>
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(task);
          }}
          title="Delete task"
          className="text-slate-300 transition hover:text-red-500"
        >
          ✕
        </button>
      </div>

      <p className="mt-1 text-sm font-medium text-slate-800">{task.title}</p>

      {tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {tags.map((t) => (
            <span
              key={t}
              className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600"
            >
              {t}
            </span>
          ))}
        </div>
      )}

      <div className="mt-2 flex items-center gap-2">
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
            PRIORITY_STYLES[task.priority] || PRIORITY_STYLES.medium
          }`}
        >
          {task.priority}
        </span>
        {task.points != null && (
          <span className="rounded-full bg-violet-100 px-2 py-0.5 text-xs font-semibold text-violet-700">
            {task.points} pts
          </span>
        )}
        {commentCount > 0 && (
          <span className="text-xs text-slate-400">💬 {commentCount}</span>
        )}
        <span className="ml-auto">
          <Avatar
            name={task.assignee_name}
            color="#6366f1"
            size="sm"
            title={task.assignee_name || "Unassigned"}
          />
        </span>
      </div>

      <select
        value={task.status}
        onClick={(e) => e.stopPropagation()}
        onChange={(e) => {
          e.stopPropagation();
          onChangeStatus(task, e.target.value);
        }}
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
