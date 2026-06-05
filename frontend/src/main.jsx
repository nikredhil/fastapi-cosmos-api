import React from "react";
import ReactDOM from "react-dom/client";
import { PublicClientApplication, EventType } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import App from "./App.jsx";
import { BASE } from "./api";
import { setMsalInstance } from "./auth";
import "./index.css";

function Notice({ title, detail }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-xl ring-1 ring-slate-200">
        <h1 className="text-xl font-bold text-slate-800">✅ Task Tracker</h1>
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

  if (!cfg.client_id) {
    root.render(
      <Notice
        title="Microsoft sign-in isn't configured."
        detail="Set AZURE_CLIENT_ID on the API (see README) and reload."
      />
    );
    return;
  }

  const pca = new PublicClientApplication({
    auth: {
      clientId: cfg.client_id,
      authority: cfg.authority,
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
