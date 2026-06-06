import { useState } from "react";
import { useMsal } from "@azure/msal-react";
import { api } from "../api";
import { LOGIN_SCOPES, setLocalSession, isMicrosoftEnabled } from "../auth";

function MicrosoftLogo() {
  return (
    <span className="grid h-5 w-5 grid-cols-2 gap-0.5">
      <span className="bg-[#f25022]" />
      <span className="bg-[#7fba00]" />
      <span className="bg-[#00a4ef]" />
      <span className="bg-[#ffb900]" />
    </span>
  );
}

function friendlyError(err, mode) {
  const msg = String(err.message || "");
  if (msg.startsWith("409")) return "An account with that email already exists. Try signing in.";
  if (msg.startsWith("401")) return "Incorrect email or password.";
  if (msg.startsWith("422")) return "Enter a valid email and a password of at least 8 characters.";
  return mode === "register" ? "Couldn't create the account." : "Couldn't sign in.";
}

export default function Login({ onLocalAuthed }) {
  const { instance } = useMsal();
  const [mode, setMode] = useState("signin"); // "signin" | "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const isRegister = mode === "register";
  const msEnabled = isMicrosoftEnabled();

  async function submitLocal(e) {
    e.preventDefault();
    if (!email.trim() || !password) return;
    setBusy(true);
    setError(null);
    try {
      const res = isRegister
        ? await api.register(email.trim(), password, displayName.trim())
        : await api.loginLocal(email.trim(), password);
      setLocalSession(res.access_token, res.display_name);
      onLocalAuthed(res.display_name);
    } catch (err) {
      setError(friendlyError(err, mode));
    } finally {
      setBusy(false);
    }
  }

  async function signInMicrosoft() {
    setBusy(true);
    setError(null);
    try {
      // Full-page redirect — more reliable than a popup behind Vercel's
      // cross-origin headers. The returning #code is handled on next load.
      await instance.loginRedirect({ scopes: LOGIN_SCOPES });
    } catch (err) {
      setError("Microsoft sign-in failed. Please try again.");
      setBusy(false);
    }
  }

  const inputCls =
    "mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200";

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-xl ring-1 ring-slate-200">
        <h1 className="text-2xl font-bold text-slate-800">🏠 RentWise</h1>
        <p className="mt-1 text-sm text-slate-500">
          {isRegister
            ? "Create your landlord account to get started."
            : "Sign in to manage your rentals."}
        </p>

        <form onSubmit={submitLocal} className="mt-6 space-y-3">
          {isRegister && (
            <label className="block text-sm font-medium text-slate-700">
              Name
              <input
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Your name (optional)"
                className={inputCls}
              />
            </label>
          )}
          <label className="block text-sm font-medium text-slate-700">
            Email
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className={inputCls}
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Password
            <input
              type="password"
              autoComplete={isRegister ? "new-password" : "current-password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={isRegister ? "At least 8 characters" : "Your password"}
              className={inputCls}
            />
          </label>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-blue-600 py-2 font-semibold text-white transition hover:bg-blue-700 disabled:opacity-50"
          >
            {busy ? "Please wait…" : isRegister ? "Create account" : "Sign in"}
          </button>
        </form>

        <p className="mt-3 text-center text-sm text-slate-500">
          {isRegister ? "Already have an account?" : "No account?"}{" "}
          <button
            onClick={() => {
              setMode(isRegister ? "signin" : "register");
              setError(null);
            }}
            className="font-semibold text-blue-600 hover:underline"
          >
            {isRegister ? "Sign in" : "Create one"}
          </button>
        </p>

        {msEnabled && (
          <>
            <div className="my-5 flex items-center gap-3 text-xs text-slate-400">
              <span className="h-px flex-1 bg-slate-200" />
              OR
              <span className="h-px flex-1 bg-slate-200" />
            </div>

            <button
              onClick={signInMicrosoft}
              disabled={busy}
              className="flex w-full items-center justify-center gap-3 rounded-lg border border-slate-300 bg-white py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
            >
              <MicrosoftLogo />
              Sign in with Microsoft
            </button>
          </>
        )}
      </div>
    </div>
  );
}
