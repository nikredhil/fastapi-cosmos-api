import { useState, useRef, useEffect } from "react";
import { api } from "../api";

const SUGGESTIONS = ["what's blocked?", "summary", "list my projects"];

export default function ChatPanel({ onDataChanged }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hi! Ask me about your tasks, or tell me to create one. Try *what's blocked?*",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    if (open) endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy, open]);

  async function send(text) {
    const message = (text ?? input).trim();
    if (!message || busy) return;
    setInput("");
    const history = messages.map(({ role, content }) => ({ role, content }));
    setMessages((m) => [...m, { role: "user", content: message }]);
    setBusy(true);
    try {
      const res = await api.chat(message, history);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.reply, backend: res.backend },
      ]);
      onDataChanged?.();
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `Error: ${err.message}`, backend: "error" },
      ]);
    } finally {
      setBusy(false);
    }
  }

  // Collapsed: a floating launcher button in the bottom-right corner.
  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        title="Open assistant"
        className="fixed bottom-5 right-5 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-indigo-600 text-2xl shadow-lg ring-1 ring-indigo-700/20 transition hover:scale-105 hover:bg-indigo-700"
      >
        💬
      </button>
    );
  }

  // Expanded: a floating chat window anchored to the bottom-right.
  return (
    <div className="fixed bottom-5 right-5 z-40 flex h-[560px] max-h-[calc(100vh-2.5rem)] w-[380px] max-w-[calc(100vw-2.5rem)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
      <div className="flex items-start justify-between border-b border-slate-200 px-4 py-3">
        <div>
          <h3 className="font-semibold text-slate-800">💬 Assistant</h3>
          <p className="text-xs text-slate-500">Natural-language project & task control</p>
        </div>
        <button
          onClick={() => setOpen(false)}
          title="Minimize"
          className="rounded-md px-2 text-lg leading-none text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
        >
          —
        </button>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[90%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-sm ${
                m.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-100 text-slate-800"
              }`}
            >
              {m.content}
            </div>
            {m.backend && m.backend !== "error" && (
              <div className="mt-0.5 text-[10px] text-slate-400">via {m.backend}</div>
            )}
          </div>
        ))}
        {busy && <div className="text-sm text-slate-400">Thinking…</div>}
        <div ref={endRef} />
      </div>

      <div className="border-t border-slate-200 p-3">
        <div className="mb-2 flex flex-wrap gap-1">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              disabled={busy}
              className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600 transition hover:bg-slate-200 disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          className="flex gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Message the assistant…"
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
          />
          <button
            disabled={busy}
            className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
