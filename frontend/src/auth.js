// Auth glue for two sign-in methods:
//   • local email/password accounts — a JWT this API issued, kept in localStorage
//   • Microsoft (Entra ID) — tokens acquired via MSAL
// getToken() prefers a local session, otherwise falls back to MSAL.
export const LOGIN_SCOPES = ["openid", "profile", "email"];

const LOCAL_TOKEN_KEY = "tt_local_token";
const LOCAL_NAME_KEY = "tt_local_name";

let msalInstance = null;
let microsoftEnabled = false;

export function setMsalInstance(instance) {
  msalInstance = instance;
}

// Whether Microsoft sign-in is configured on the API (AZURE_CLIENT_ID set).
export function setMicrosoftEnabled(value) {
  microsoftEnabled = value;
}
export function isMicrosoftEnabled() {
  return microsoftEnabled;
}

export function getActiveAccount() {
  if (!msalInstance) return null;
  return msalInstance.getActiveAccount() || msalInstance.getAllAccounts()[0] || null;
}

// --- local session ---
export function getLocalSession() {
  const token = localStorage.getItem(LOCAL_TOKEN_KEY);
  if (!token) return null;
  return { token, name: localStorage.getItem(LOCAL_NAME_KEY) || "" };
}

export function setLocalSession(token, name) {
  localStorage.setItem(LOCAL_TOKEN_KEY, token);
  localStorage.setItem(LOCAL_NAME_KEY, name || "");
}

export function clearLocalSession() {
  localStorage.removeItem(LOCAL_TOKEN_KEY);
  localStorage.removeItem(LOCAL_NAME_KEY);
}

// Returns a bearer token for API calls. Throws a 401-prefixed error when no
// session is available so callers (guard) can route back to sign-in.
export async function getToken() {
  const local = getLocalSession();
  if (local) return local.token;

  const account = getActiveAccount();
  if (!msalInstance || !account) throw new Error("401: not signed in");
  try {
    const res = await msalInstance.acquireTokenSilent({ account, scopes: LOGIN_SCOPES });
    return res.idToken;
  } catch (err) {
    throw new Error("401: session expired");
  }
}
