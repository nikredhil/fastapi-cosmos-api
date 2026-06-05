import { STATUSES, STATUS_LABELS } from "../api";
import Avatar from "./Avatar";

const COLUMN_DOT = {
  todo: "bg-slate-400",
  in_progress: "bg-indigo-400",
  blocked: "bg-red-400",
  done: "bg-emerald-400",
};

export default function SprintBar({
  project,
  sprints,
  members,
  tasks,
  selectedSprintId,
  onSelectSprint,
  assigneeFilter,
  onAssigneeFilter,
  onManageTeam,
  onManageSprints,
}) {
  const activeSprint = sprints.find((s) => s.id === selectedSprintId) || null;
  const totalPoints = tasks.reduce((sum, t) => sum + (t.points || 0), 0);
  const pointsByStatus = (s) =>
    tasks.filter((t) => t.status === s).reduce((sum, t) => sum + (t.points || 0), 0);

  return (
    <div className="border-b border-slate-200 bg-white px-6 py-3">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <h2 className="text-xl font-bold text-slate-800">{project.name}</h2>

        {/* Sprint selector */}
        <select
          value={selectedSprintId}
          onChange={(e) => onSelectSprint(e.target.value)}
          className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-1.5 text-sm font-medium text-slate-700 outline-none focus:border-indigo-500"
        >
          <option value="all">All items</option>
          <option value="backlog">📋 Backlog</option>
          {sprints.map((s) => (
            <option key={s.id} value={s.id}>
              🏃 {s.name}
              {s.status === "active" ? " (active)" : ""}
            </option>
          ))}
        </select>

        {activeSprint && (activeSprint.start_date || activeSprint.end_date) && (
          <span className="flex items-center gap-1 text-sm text-slate-500">
            📅 {activeSprint.start_date || "—"} → {activeSprint.end_date || "—"}
          </span>
        )}

        <span className="flex items-center gap-1 text-sm font-semibold text-slate-600">
          🪙 {totalPoints} pts
        </span>

        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={onManageTeam}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
          >
            👥 Manage Team
          </button>
          <button
            onClick={onManageSprints}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
          >
            🏃 Manage Sprints
          </button>
        </div>
      </div>

      {/* Per-status point summary + assignee filter */}
      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2">
        <div className="flex items-center gap-3">
          {STATUSES.map((s) => (
            <span key={s} className="flex items-center gap-1.5 text-xs text-slate-500">
              <span className={`h-2 w-2 rounded-full ${COLUMN_DOT[s]}`} />
              {STATUS_LABELS[s]}{" "}
              <span className="font-semibold text-slate-700">{pointsByStatus(s)} pts</span>
            </span>
          ))}
        </div>

        {members.length > 0 && (
          <div className="ml-auto flex items-center gap-1.5">
            <span className="text-xs text-slate-400">Filter:</span>
            <button
              onClick={() => onAssigneeFilter(null)}
              className={`rounded-full px-2 py-0.5 text-xs transition ${
                !assigneeFilter ? "bg-indigo-100 font-semibold text-indigo-700" : "text-slate-500 hover:bg-slate-100"
              }`}
            >
              All
            </button>
            {members.map((m) => (
              <button
                key={m.id}
                onClick={() => onAssigneeFilter(assigneeFilter === m.id ? null : m.id)}
                title={m.name}
                className={`rounded-full transition ${
                  assigneeFilter === m.id ? "ring-2 ring-indigo-500 ring-offset-1" : "opacity-80 hover:opacity-100"
                }`}
              >
                <Avatar name={m.name} color={m.avatar_color} size="sm" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
