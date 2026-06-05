import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid,
} from "recharts";
import { api, rupees, formatPeriod, recentPeriods, currentPeriod, BILL_TYPE_META } from "../api";
import { Card, Spinner, Select, EmptyState, Button } from "../components/ui";
import { DashboardIcon, BuildingIcon, ClockIcon, CheckIcon } from "../components/icons";

// Soft pastel gradients with dark text for an airy, light dashboard.
const GRADIENTS = {
  orange: { bg: "from-orange-100 to-rose-100", icon: "bg-orange-200/70", value: "text-orange-700", label: "text-orange-900/70", sub: "text-orange-900/55" },
  blue: { bg: "from-sky-100 to-blue-100", icon: "bg-sky-200/70", value: "text-sky-700", label: "text-sky-900/70", sub: "text-sky-900/55" },
  teal: { bg: "from-emerald-100 to-teal-100", icon: "bg-emerald-200/70", value: "text-emerald-700", label: "text-emerald-900/70", sub: "text-emerald-900/55" },
  purple: { bg: "from-violet-100 to-purple-100", icon: "bg-violet-200/70", value: "text-violet-700", label: "text-violet-900/70", sub: "text-violet-900/55" },
};

function GradientStat({ gradient, label, value, sub }) {
  const c = GRADIENTS[gradient];
  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border border-white bg-gradient-to-br ${c.bg} p-5 shadow-sm ring-1 ring-slate-100 transition duration-200 hover:-translate-y-1 hover:shadow-md`}
    >
      {/* soft decorative circles, like the reference template */}
      <div className="pointer-events-none absolute -right-8 -top-10 h-36 w-36 rounded-full bg-white/40 transition-transform duration-300 group-hover:scale-110" />
      <div className="pointer-events-none absolute -bottom-14 right-6 h-28 w-28 rounded-full bg-white/30" />
      <div className="relative">
        <span className={`text-sm font-medium ${c.label}`}>{label}</span>
        <p className={`mt-3 text-3xl font-bold tracking-tight ${c.value}`}>{value}</p>
        <p className={`mt-3 text-xs font-medium ${c.sub}`}>{sub}</p>
      </div>
    </div>
  );
}

function SectionCard({ title, action, children, className = "" }) {
  return (
    <Card className={`p-5 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-base font-bold text-slate-800">{title}</h3>
        {action}
      </div>
      <div className="mt-4">{children}</div>
    </Card>
  );
}

export default function Dashboard() {
  const [period, setPeriod] = useState(currentPeriod());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const periods = useMemo(() => recentPeriods(12), []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    api
      .dashboard(period)
      .then((d) => active && (setData(d), setError(null)))
      .catch((e) => active && setError(e.message))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [period]);

  if (loading && !data) return <Spinner label="Loading dashboard…" />;
  if (error) return <p className="text-sm text-red-600">{error}</p>;

  const collectionRate =
    data.expected > 0 ? Math.round((data.collected / data.expected) * 100) : 0;

  const byType = (data.by_type || []).map((t) => ({
    name: BILL_TYPE_META[t.type]?.label || t.type,
    value: t.amount,
    color: BILL_TYPE_META[t.type]?.color || "#64748b",
  }));
  const byTypeTotal = byType.reduce((s, t) => s + t.value, 0);

  const perBuilding = (data.per_building || []).map((b) => ({
    name: b.name,
    Collected: b.collected,
    Outstanding: b.outstanding,
  }));

  const noData = data.buildings === 0;

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-violet-100 to-purple-100 ring-1 ring-violet-200">
            <DashboardIcon className="h-6 w-6 text-slate-700" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
            <p className="text-sm text-slate-500">Overview for {formatPeriod(data.period)}</p>
          </div>
        </div>
        <Select value={period} onChange={(e) => setPeriod(e.target.value)}>
          {periods.map((p) => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </Select>
      </div>

      {noData ? (
        <EmptyState
          icon={<BuildingIcon className="mx-auto h-8 w-8 text-slate-400" />}
          title="No buildings yet"
          action={
            <Link to="/buildings">
              <Button>Add your first building</Button>
            </Link>
          }
        >
          Add a building, then its units and tenants, to start tracking rent and bills.
        </EmptyState>
      ) : (
        <>
          {/* Gradient headline stats */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <GradientStat
              gradient="purple"
              label="Buildings"
              value={data.buildings}
              sub={`${data.units} units total`}
            />
            <GradientStat
              gradient="teal"
              label="Occupancy"
              value={`${data.occupancy_pct}%`}
              sub={`${data.occupied_units}/${data.units} units occupied`}
            />
            <GradientStat
              gradient="blue"
              label="Collected"
              value={rupees(data.collected)}
              sub={`${collectionRate}% of expected`}
            />
            <GradientStat
              gradient="orange"
              label="Outstanding"
              value={rupees(data.outstanding)}
              sub={`${data.overdue.length} overdue ${data.overdue.length === 1 ? "bill" : "bills"}`}
            />
          </div>

          {/* Charts */}
          <div className="mt-6 grid gap-4 lg:grid-cols-3">
            <SectionCard
              title="Collected vs outstanding"
              className="lg:col-span-2"
              action={
                <div className="flex items-center gap-4 text-xs text-slate-500">
                  <span className="inline-flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> Collected
                  </span>
                  <span className="inline-flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full bg-rose-500" /> Outstanding
                  </span>
                </div>
              }
            >
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={perBuilding} margin={{ left: -12, right: 8, top: 8 }} barGap={6}>
                    <defs>
                      <linearGradient id="gCollected" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#34d399" />
                        <stop offset="100%" stopColor="#059669" />
                      </linearGradient>
                      <linearGradient id="gOutstanding" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#fb7185" />
                        <stop offset="100%" stopColor="#e11d48" />
                      </linearGradient>
                    </defs>
                    <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#eef2f7" />
                    <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#94a3b8" }}
                      axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={false} tickLine={false}
                      tickFormatter={(v) => `₹${v / 1000}k`} />
                    <Tooltip
                      cursor={{ fill: "rgba(148,163,184,0.08)" }}
                      formatter={(v) => rupees(v)}
                      contentStyle={{
                        borderRadius: 12, border: "1px solid #e2e8f0",
                        boxShadow: "0 10px 30px rgba(2,6,23,0.08)", fontSize: 12,
                      }}
                    />
                    <Bar dataKey="Collected" fill="url(#gCollected)" radius={[6, 6, 0, 0]} maxBarSize={36} />
                    <Bar dataKey="Outstanding" fill="url(#gOutstanding)" radius={[6, 6, 0, 0]} maxBarSize={36} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </SectionCard>

            <SectionCard title="Billed by type">
              {byType.length === 0 ? (
                <p className="py-16 text-center text-sm text-slate-400">No bills this month.</p>
              ) : (
                <>
                  <div className="relative h-52">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={byType} dataKey="value" nameKey="name" innerRadius={58}
                          outerRadius={84} paddingAngle={3} stroke="none">
                          {byType.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                        </Pie>
                        <Tooltip
                          formatter={(v) => rupees(v)}
                          contentStyle={{
                            borderRadius: 12, border: "1px solid #e2e8f0",
                            boxShadow: "0 10px 30px rgba(2,6,23,0.08)", fontSize: 12,
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    {/* center total */}
                    <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-xs text-slate-400">Total</span>
                      <span className="text-lg font-bold text-slate-800">{rupees(byTypeTotal)}</span>
                    </div>
                  </div>
                  <div className="mt-3 space-y-2">
                    {byType.map((t) => (
                      <div key={t.name} className="flex items-center justify-between text-sm">
                        <span className="inline-flex items-center gap-2 text-slate-600">
                          <span className="h-2.5 w-2.5 rounded-full" style={{ background: t.color }} />
                          {t.name}
                        </span>
                        <span className="font-medium text-slate-500">
                          {byTypeTotal ? Math.round((t.value / byTypeTotal) * 100) : 0}%
                        </span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </SectionCard>
          </div>

          {/* Lists */}
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <SectionCard title="Overdue">
              {data.overdue.length === 0 ? (
                <div className="flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-600">
                  🎉 Nothing overdue — all caught up.
                </div>
              ) : (
                <ul className="space-y-1">
                  {data.overdue.map((o) => (
                    <li key={o.id}
                      className="flex items-center justify-between rounded-xl px-2 py-2 text-sm transition hover:bg-slate-50">
                      <div className="flex items-center gap-3">
                        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-rose-100 text-rose-500">
                          <ClockIcon className="h-4 w-4" />
                        </span>
                        <div>
                          <p className="font-medium text-slate-700">{o.tenant_name || "—"}</p>
                          <p className="text-xs text-slate-400">
                            {o.building_name}{o.unit_label ? ` · ${o.unit_label}` : ""} ·{" "}
                            {BILL_TYPE_META[o.bill_type]?.label} · due {o.due_date || "—"}
                          </p>
                        </div>
                      </div>
                      <span className="font-semibold text-rose-600">
                        {rupees(o.amount - o.paid_amount)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>

            <SectionCard title="Recent payments">
              {data.recent_payments.length === 0 ? (
                <p className="py-6 text-center text-sm text-slate-400">No payments recorded yet.</p>
              ) : (
                <ul className="space-y-1">
                  {data.recent_payments.map((p, i) => (
                    <li key={i}
                      className="flex items-center justify-between rounded-xl px-2 py-2 text-sm transition hover:bg-slate-50">
                      <div className="flex items-center gap-3">
                        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                          <CheckIcon className="h-4 w-4" />
                        </span>
                        <div>
                          <p className="font-medium text-slate-700">{p.tenant_name || "—"}</p>
                          <p className="text-xs text-slate-400">
                            {p.building_name} · {BILL_TYPE_META[p.bill_type]?.label} · {p.paid_on || ""}
                          </p>
                        </div>
                      </div>
                      <span className="font-semibold text-emerald-600">{rupees(p.amount)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>
          </div>
        </>
      )}
    </div>
  );
}
