import { useState } from "react";
import { useMsal } from "@azure/msal-react";
import { LOGIN_SCOPES } from "../auth";

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

export default function Login() {
  const { instance } = useMsal();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function signIn() {
    setBusy(true);
    setError(null);
    try {
      await instance.loginPopup({ scopes: LOGIN_SCOPES });
      // On success the MSAL event callback sets the active account and the app
      // re-renders into the authenticated view.
    } catch (err) {
      if (err?.errorCode !== "user_cancelled") {
        setError("Sign-in failed. Please try again.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-xl ring-1 ring-slate-200">
        <h1 className="text-2xl font-bold text-slate-800">✅ Task Tracker</h1>
        <p className="mt-1 text-sm text-slate-500">
          Sign in with your Microsoft account to continue.
        </p>

        <button
          onClick={signIn}
          disabled={busy}
          className="mt-6 flex w-full items-center justify-center gap-3 rounded-lg border border-slate-300 bg-white py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
        >
          <MicrosoftLogo />
          {busy ? "Signing in…" : "Sign in with Microsoft"}
        </button>

        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

        <p className="mt-6 text-xs text-slate-400">
          Work, school, and personal Microsoft accounts are supported.
        </p>
      </div>
    </div>
  );
}
