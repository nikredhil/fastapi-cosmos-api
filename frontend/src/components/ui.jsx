// Small, dependency-free UI primitives shared across pages.
import { useEffect } from "react";

const INPUT_CLS =
  "mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200";

export function Button({ variant = "primary", className = "", ...props }) {
  const base =
    "inline-flex items-center justify-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-blue-600 text-white hover:bg-blue-700",
    secondary: "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50",
    danger: "border border-red-200 bg-white text-red-600 hover:bg-red-50",
    ghost: "text-slate-500 hover:bg-slate-100",
  };
  return <button className={`${base} ${variants[variant]} ${className}`} {...props} />;
}

export function Card({ className = "", children }) {
  return (
    <div className={`rounded-2xl border border-slate-200 bg-white shadow-sm ${className}`}>
      {children}
    </div>
  );
}

export function Badge({ className = "", children }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${className}`}>
      {children}
    </span>
  );
}

export function Field({ label, children, hint }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      {children}
      {hint && <span className="mt-1 block text-xs font-normal text-slate-400">{hint}</span>}
    </label>
  );
}

export function TextInput({ label, hint, ...props }) {
  const input = <input className={INPUT_CLS} {...props} />;
  return label ? <Field label={label} hint={hint}>{input}</Field> : input;
}

export function NumberInput({ label, hint, ...props }) {
  const input = <input type="number" className={INPUT_CLS} {...props} />;
  return label ? <Field label={label} hint={hint}>{input}</Field> : input;
}

export function TextArea({ label, hint, ...props }) {
  const el = <textarea className={INPUT_CLS} rows={3} {...props} />;
  return label ? <Field label={label} hint={hint}>{el}</Field> : el;
}

export function Select({ label, hint, children, ...props }) {
  const el = (
    <select className={`${INPUT_CLS} bg-white`} {...props}>
      {children}
    </select>
  );
  return label ? <Field label={label} hint={hint}>{el}</Field> : el;
}

export function Modal({ title, subtitle, onClose, children, wide = false }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      onMouseDown={(e) => e.target === e.currentTarget && onClose?.()}
    >
      <div
        className={`max-h-[90vh] w-full overflow-y-auto rounded-2xl bg-white shadow-2xl ${
          wide ? "max-w-2xl" : "max-w-md"
        }`}
      >
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
            {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
          </div>
          <button
            onClick={onClose}
            className="rounded-md px-2 text-xl leading-none text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            ×
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  );
}

export function Spinner({ label = "Loading…" }) {
  return (
    <div className="flex items-center justify-center gap-2 py-10 text-sm text-slate-400">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
      {label}
    </div>
  );
}

export function EmptyState({ icon = "📭", title, children, action }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
      <div className="text-3xl">{icon}</div>
      <h3 className="mt-3 font-semibold text-slate-700">{title}</h3>
      {children && <p className="mt-1 max-w-sm text-sm text-slate-500">{children}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function PageHeader({ title, subtitle, action }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
