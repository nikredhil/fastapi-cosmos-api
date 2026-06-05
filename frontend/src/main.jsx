import React from "react";
import ReactDOM from "react-dom/client";
import { PublicClientApplication, EventType } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import App from "./App.jsx";
import { BASE } from "./api";
import { setMsalInstance, setMicrosoftEnabled } from "./auth";
import "./index.css";

function Notice({ title, detail }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-xl ring-1 ring-slate-200">
        <h1 className="text-xl font-bold text-slate-800">🏠 RentWise</h1>
        <p className="mt-3 text-sm text-slate-600">{title}</p>
        {detail && <p className="mt-2 text-xs text-slate-400">{detail}</p>}
      </div>
    </div>
  );
}

async function bootstrap() {
  const root = ReactDOM.createRoot(document.getElementById("root"));

  let cfg;
  try {
    cfg = await fetch(`${BASE}/auth/config`).then((r) => r.json());
  } catch {
    root.render(
      <Notice title="Couldn't reach the API." detail={`Is the server running at ${BASE}?`} />
    );
    return;
  }

  // Microsoft sign-in is optional; local accounts work without it. When no
  // client id is configured we still build an MSAL instance (with a placeholder
  // id) so the context exists, but the UI hides the Microsoft button.
  setMicrosoftEnabled(!!cfg.client_id);

  const pca = new PublicClientApplication({
    auth: {
      clientId: cfg.client_id || "00000000-0000-0000-0000-000000000000",
      authority: cfg.authority || "https://login.microsoftonline.com/common",
      redirectUri: window.location.origin,
    },
    cache: { cacheLocation: "localStorage" },
  });
  await pca.initialize();

  const accounts = pca.getAllAccounts();
  if (accounts.length > 0) pca.setActiveAccount(accounts[0]);

  pca.addEventCallback((event) => {
    if (event.eventType === EventType.LOGIN_SUCCESS && event.payload?.account) {
      pca.setActiveAccount(event.payload.account);
    }
  });

  setMsalInstance(pca);

  root.render(
    <React.StrictMode>
      <MsalProvider instance={pca}>
        <App />
      </MsalProvider>
    </React.StrictMode>
  );
}

bootstrap();
