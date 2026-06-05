import { useCallback, useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import { getActiveAccount, getLocalSession, clearLocalSession } from "./auth";
import Login from "./components/Login";
import Layout from "./components/Layout";
import ChatPanel from "./components/ChatPanel";
import Dashboard from "./pages/Dashboard";
import Buildings from "./pages/Buildings";
import BuildingDetail from "./pages/BuildingDetail";
import Tenants from "./pages/Tenants";
import TenantDetail from "./pages/TenantDetail";
import Bills from "./pages/Bills";

export default function App() {
  const { instance } = useMsal();
  const msAuthenticated = useIsAuthenticated();
  const [localSession, setLocalSession] = useState(() => getLocalSession());
  const account = getActiveAccount();

  const isAuthenticated = msAuthenticated || !!localSession;
  const username = localSession?.name || account?.name || account?.username || "Landlord";

  const logout = useCallback(() => {
    if (getLocalSession()) {
      clearLocalSession();
      setLocalSession(null);
    } else {
      instance.logoutPopup().catch(() => {});
    }
  }, [instance]);

  if (!isAuthenticated) {
    return <Login onLocalAuthed={() => setLocalSession(getLocalSession())} />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout username={username} onLogout={logout} />}>
          <Route index element={<Dashboard />} />
          <Route path="buildings" element={<Buildings />} />
          <Route path="buildings/:buildingId" element={<BuildingDetail />} />
          <Route path="tenants" element={<Tenants />} />
          <Route path="buildings/:buildingId/tenants/:tenantId" element={<TenantDetail />} />
          <Route path="bills" element={<Bills />} />
          <Route path="*" element={<Dashboard />} />
        </Route>
      </Routes>
      <ChatPanel onAuthError={logout} />
    </BrowserRouter>
  );
}
