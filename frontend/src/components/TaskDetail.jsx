import { useEffect, useState } from "react";
import {
  STATUSES,
  STATUS_LABELS,
  PRIORITIES,
  ITEM_TYPES,
  ITEM_TYPE_META,
} from "../api";
import Avatar from "./Avatar";

export default function TaskDetail({
  task,
  members,
  sprints,
  onUpdate,
  onAddComment,
  onDelete,
  onClose,
}) {
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description || "");
  const [tagInput, setTagInput] = useState("");
  const [comment, setComment] = useState("");

  // Re-sync local editable fields when a different task is opened.
  useEffect(() => {
    setTitle(task.title);
    setDescription(task.description || "");
  }, [task.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const meta = ITEM_TYPE_META[task.item_type] || ITEM_TYPE_META.task;
  const tags = task.tags || [];

  function commitTitle() {
    const next = title.trim();
    if (next && next !== task.title) onUpdate({ title: next });
  }
  function commitDescription() {
    if (description !== (task.description || "")) onUpdate({ description });
  }
  function addTag(e) {
    e.preventDefault();
    const t = tagInput.trim();
    if (!t || tags.includes(t)) return;
    onUpdate({ tags: [...tags, t] });
    setTagInput("");
  }
  function removeTag(t) {
    onUpdate({ tags: tags.filter((x) => x !== t) });
  }
  function submitComment(e) {
    e.preventDefault();
    if (!comment.trim()) return;
    onAddComment(comment.trim());
    setComment("");
  }

  return (
    <div className="fixed inset-0 z-30 flex justify-end bg-slate-900/40">
      <div className="flex h-full w-full max-w-md flex-col bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
          <div className="flex items-center gap-2 text-sm">
            <span title={meta.label}>{meta.icon}</span>
            <span className="font-mono font-semibold text-slate-500">
              {task.key || task.id.slice(0, 6)}
            </span>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-5 py-4">
          {/* Title */}
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onBlur={commitTitle}
            className="w-full rounded-lg border border-transparent px-2 py-1 text-lg font-bold text-slate-800 outline-none hover:border-slate-200 focus:border-indigo-400"
          />

          {/* Field grid */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <Field label="Type">
              <select
                value={task.item_type}
                onChange={(e) => onUpdate({ item_type: e.target.value })}
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 outline-none focus:border-indigo-400"
              >
                {ITEM_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {ITEM_TYPE_META[t].icon} {ITEM_TYPE_META[t].label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Status">
              <select
                value={task.status}
                onChange={(e) => onUpdate({ status: e.target.value })}
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 outline-none focus:border-indigo-400"
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {STATUS_LABELS[s]}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Priority">
              <select
                value={task.priority}
                onChange={(e) => onUpdate({ priority: e.target.value })}
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 outline-none focus:border-indigo-400"
              >
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Story points">
              <input
                type="number"
                min="0"
                max="100"
                value={task.points ?? ""}
                onChange={(e) =>
                  onUpdate({ points: e.target.value === "" ? null : Number(e.target.value) })
                }
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 outline-none focus:border-indigo-400"
              />
            </Field>
            <Field label="Assignee">
              <select
                value={task.assignee_id || ""}
                onChange={(e) => onUpdate({ assignee_id: e.target.value || null })}
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 outline-none focus:border-indigo-400"
              >
                <option value="">Unassigned</option>
                {members.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Sprint">
              <select
                value={task.sprint_id || ""}
                onChange={(e) => onUpdate({ sprint_id: e.target.value || null })}
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 outline-none focus:border-indigo-400"
              >
                <option value="">Backlog</option>
                {sprints.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Due date">
              <input
                type="date"
                value={task.due_date || ""}
                onChange={(e) => onUpdate({ due_date: e.target.value || null })}
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 outline-none focus:border-indigo-400"
              />
            </Field>
          </div>

          {/* Description */}
          <div>
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Description
            </p>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onBlur={commitDescription}
              rows={4}
              placeholder="Add a description…"
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-indigo-400"
            />
          </div>

          {/* Tags */}
          <div>
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Tags
            </p>
            <div className="flex flex-wrap items-center gap-1.5">
              {tags.map((t) => (
                <span
                  key={t}
                  className="flex items-center gap-1 rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700"
                >
                  {t}
                  <button onClick={() => removeTag(t)} className="text-indigo-400 hover:text-indigo-700">
                    ✕
                  </button>
                </span>
              ))}
              <form onSubmit={addTag}>
                <input
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  placeholder="+ tag"
                  className="w-20 rounded-full border border-slate-200 px-2 py-0.5 text-xs outline-none focus:border-indigo-400"
                />
              </form>
            </div>
          </div>

          {/* Comments */}
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Comments ({(task.comments || []).length})
            </p>
            <div className="space-y-2">
              {(task.comments || []).map((c) => (
                <div key={c.id} className="rounded-lg bg-slate-50 p-2.5 text-sm">
                  <div className="mb-0.5 flex items-center justify-between">
                    <span className="font-medium text-slate-700">@{c.author}</span>
                    <span className="text-[10px] text-slate-400">
                      {new Date(c.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="whitespace-pre-wrap text-slate-600">{c.body}</p>
                </div>
              ))}
            </div>
            <form onSubmit={submitComment} className="mt-2 flex gap-2">
              <input
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Write a comment…"
                className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
              />
              <button className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
                Send
              </button>
            </form>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-slate-200 px-5 py-3">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Avatar name={task.assignee_name} color="#6366f1" size="sm" />
            {task.assignee_name || "Unassigned"}
          </div>
          <button
            onClick={() => onDelete(task)}
            className="rounded-lg px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-400">
        {label}
      </span>
      {children}
    </label>
  );
}
