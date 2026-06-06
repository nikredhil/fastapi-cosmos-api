import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { DashboardIcon, BuildingIcon, TenantsIcon, CashIcon, HomeIcon } from "./icons";

const NAV = [
  { to: "/", label: "Dashboard", Icon: DashboardIcon, end: true },
  { to: "/buildings", label: "Buildings", Icon: BuildingIcon },
  { to: "/tenants", label: "Tenants", Icon: TenantsIcon },
  { to: "/bills", label: "Rent & Bills", Icon: CashIcon },
];

function Brand() {
  return (
    <div className="flex items-center gap-2.5 border-b border-slate-200 px-5 py-4">
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 ring-1 ring-blue-100">
        <HomeIcon className="h-5 w-5 text-blue-600" />
      </span>
      <div>
        <h1 className="text-lg font-bold leading-none text-slate-800">WiseRent</h1>
        <p className="text-[11px] text-slate-400">Rental manager</p>
      </div>
    </div>
  );
}

function SidebarBody({ username, onLogout, onNavigate }) {
  return (
    <>
      <Brand />
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {NAV.map(({ to, label, Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                isActive
                  ? "bg-blue-50 font-semibold text-blue-700"
                  : "text-slate-600 hover:bg-slate-50"
              }`
            }
          >
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-slate-200 p-3">
        <p className="px-2 text-xs text-slate-500">
          Signed in as <span className="font-medium text-slate-700">{username}</span>
        </p>
        <button
          onClick={onLogout}
          className="mt-2 w-full rounded-lg px-2 py-2 text-left text-sm text-slate-500 hover:bg-slate-50"
        >
          Sign out
        </button>
      </div>
    </>
  );
}

export default function Layout({ username, onLogout }) {
  const [drawer, setDrawer] = useState(false);
  const location = useLocation();

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setDrawer(false);
  }, [location.pathname]);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Desktop sidebar */}
      <aside className="hidden w-60 shrink-0 flex-col border-r border-slate-200 bg-white md:flex">
        <SidebarBody username={username} onLogout={onLogout} />
      </aside>

      {/* Mobile drawer */}
      {drawer && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-slate-900/40" onClick={() => setDrawer(false)} />
          <aside className="absolute left-0 top-0 flex h-full w-64 flex-col bg-white shadow-xl">
            <SidebarBody
              username={username}
              onLogout={onLogout}
              onNavigate={() => setDrawer(false)}
            />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {/* Mobile top bar */}
        <header className="flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3 md:hidden">
          <button
            onClick={() => setDrawer(true)}
            aria-label="Open menu"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100"
          >
            <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor"
              strokeWidth="2" strokeLinecap="round">
              <path d="M4 7h16M4 12h16M4 17h16" />
            </svg>
          </button>
          <span className="flex items-center gap-2 font-bold text-slate-800">
            <HomeIcon className="h-5 w-5 text-blue-600" /> WiseRent
          </span>
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
