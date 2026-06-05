import { useState } from "react";
import { AVATAR_COLORS } from "../api";
import Avatar from "./Avatar";

export default function MembersModal({ members, onAdd, onDelete, onClose }) {
  const [name, setName] = useState("");
  const [role, setRole] = useState("");
  const [color, setColor] = useState(AVATAR_COLORS[members.length % AVATAR_COLORS.length]);

  function submit(e) {
    e.preventDefault();
    if (!name.trim()) return;
    onAdd({ name: name.trim(), role: role.trim() || null, avatar_color: color });
    setName("");
    setRole("");
    setColor(AVATAR_COLORS[(members.length + 1) % AVATAR_COLORS.length]);
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/40 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-800">👥 Team members</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>

        <form onSubmit={submit} className="mb-4 space-y-2">
          <div className="flex gap-2">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Full name"
              className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
            />
            <input
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="Role (optional)"
              className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Color:</span>
            {AVATAR_COLORS.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setColor(c)}
                style={{ backgroundColor: c }}
                className={`h-6 w-6 rounded-full transition ${
                  color === c ? "ring-2 ring-offset-2 ring-slate-700" : ""
                }`}
              />
            ))}
            <button className="ml-auto rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700">
              Add
            </button>
          </div>
        </form>

        <div className="max-h-72 space-y-1 overflow-y-auto">
          {members.length === 0 && (
            <p className="py-4 text-center text-sm text-slate-400">No members yet.</p>
          )}
          {members.map((m) => (
            <div
              key={m.id}
              className="flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-slate-50"
            >
              <Avatar name={m.name} color={m.avatar_color} size="md" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-slate-800">{m.name}</p>
                {m.role && <p className="truncate text-xs text-slate-500">{m.role}</p>}
              </div>
              <button
                onClick={() => onDelete(m)}
                title="Remove member"
                className="text-slate-300 transition hover:text-red-500"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
