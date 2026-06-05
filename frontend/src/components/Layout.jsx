import { NavLink, Outlet } from "react-router-dom";
import { DashboardIcon, BuildingIcon, TenantsIcon, CashIcon, HomeIcon } from "./icons";

const NAV = [
  { to: "/", label: "Dashboard", Icon: DashboardIcon, end: true },
  { to: "/buildings", label: "Buildings", Icon: BuildingIcon },
  { to: "/tenants", label: "Tenants", Icon: TenantsIcon },
  { to: "/bills", label: "Rent & Bills", Icon: CashIcon },
];

export default function Layout({ username, onLogout }) {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <aside className="flex w-60 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="flex items-center gap-2.5 border-b border-slate-200 px-5 py-4">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 ring-1 ring-blue-100">
            <HomeIcon className="h-5 w-5 text-blue-600" />
          </span>
          <div>
            <h1 className="text-lg font-bold leading-none text-slate-800">RentWise</h1>
            <p className="text-[11px] text-slate-400">Rental manager</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {NAV.map(({ to, label, Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
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
            Signed in as <span className="font-medium text-slate-700">Narayan Reddy</span>
          </p>
          <button
            onClick={onLogout}
            className="mt-2 w-full rounded-lg px-2 py-2 text-left text-sm text-slate-500 hover:bg-slate-50"
          >
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl px-6 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
