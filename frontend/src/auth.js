// MSAL glue: holds the PublicClientApplication instance and exposes helpers for
// the API client and components to read the active account / acquire a token.
export const LOGIN_SCOPES = ["openid", "profile", "email"];

let msalInstance = null;

export function setMsalInstance(instance) {
  msalInstance = instance;
}

export function getActiveAccount() {
  if (!msalInstance) return null;
  return msalInstance.getActiveAccount() || msalInstance.getAllAccounts()[0] || null;
}

// Returns a fresh Microsoft ID token for the active account, refreshing silently.
// Throws a 401-prefixed error when no session is available so callers (guard)
// can route the user back to sign-in.
export async function getToken() {
  const account = getActiveAccount();
  if (!msalInstance || !account) throw new Error("401: not signed in");
  try {
    const res = await msalInstance.acquireTokenSilent({ account, scopes: LOGIN_SCOPES });
    return res.idToken;
  } catch (err) {
    throw new Error("401: session expired");
  }
}
