import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  api, rupees, formatPeriod, recentPeriods, currentPeriod,
  BILL_TYPE_META, STATUS_STYLES, BILL_TYPES, BILL_STATUSES,
} from "../api";
import {
  Button, Card, Modal, Select, NumberInput, TextInput, Badge, Spinner, EmptyState, PageHeader,
} from "../components/ui";
import {
  BillTypeIcon, CashIcon, GearIcon, WaterIcon, BoltIcon, WrenchIcon,
} from "../components/icons";

// Sort key from a unit/flat label: leading digits ascending, blanks last.
function flatSortKey(label) {
  if (!label) return Number.POSITIVE_INFINITY;
  const n = parseInt(String(label).replace(/[^0-9]/g, ""), 10);
  return Number.isNaN(n) ? Number.POSITIVE_INFINITY : n;
}

function GenerateModal({ buildingId, period, onClose, onDone }) {
  const [form, setForm] = useState({
    include_water: false, water_amount: 0,
    include_electricity: false, electricity_amount: 0,
    include_maintenance: false, maintenance_amount: 0,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const items = await api.generateBills(buildingId, { period, ...form });
      setResult(items.length);
      onDone();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const toggle = (k) => (e) => setForm({ ...form, [k]: e.target.checked });
  const amount = (k) => (e) => setForm({ ...form, [k]: Number(e.target.value) || 0 });

  return (
    <Modal title="Generate bills" subtitle={`Rent for ${formatPeriod(period)}`} onClose={onClose}>
      {result != null ? (
        <div className="space-y-4 text-center">
          <CashIcon className="mx-auto h-12 w-12 text-emerald-500" />
          <p className="text-sm text-slate-600">
            {result === 0
              ? "No new bills — they may already exist for this month."
              : `Created ${result} bill(s) for ${formatPeriod(period)}.`}
          </p>
          <Button onClick={onClose}>Done</Button>
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <p className="text-sm text-slate-500">
            Creates a rent bill for every active tenant. Optionally add flat utility charges
            applied to each tenant.
          </p>
          {[
            ["water", "include_water", "water_amount", "Water", WaterIcon],
            ["electricity", "include_electricity", "electricity_amount", "Electricity", BoltIcon],
            ["maintenance", "include_maintenance", "maintenance_amount", "Maintenance", WrenchIcon],
          ].map(([key, incl, amt, label, Icon]) => (
            <div key={key} className="flex items-center gap-3">
              <label className="flex flex-1 items-center gap-2 text-sm font-medium text-slate-700">
                <input type="checkbox" checked={form[incl]} onChange={toggle(incl)}
                  className="h-4 w-4 rounded border-slate-300 text-blue-600" />
                <Icon className="h-4 w-4 text-slate-500" />
                {label}
              </label>
              <div className="w-32">
                <NumberInput placeholder="₹ per tenant" value={form[amt] || ""}
                  onChange={amount(amt)} disabled={!form[incl]} />
              </div>
            </div>
          ))}
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={busy}>{busy ? "Generating…" : "Generate"}</Button>
          </div>
        </form>
      )}
    </Modal>
  );
}

function PaymentModal({ buildingId, bill, onClose, onDone }) {
  const outstanding = bill.amount - bill.paid_amount;
  const [form, setForm] = useState({ amount: outstanding, method: "upi", note: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.recordPayment(buildingId, bill.id, {
        amount: Number(form.amount),
        method: form.method,
        note: form.note || null,
      });
      onDone();
      onClose();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <Modal title="Record payment"
      subtitle={`${bill.tenant_name || "—"} · ${BILL_TYPE_META[bill.bill_type]?.label} · ${formatPeriod(bill.period)}`}
      onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <p className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">
          {rupees(bill.paid_amount)} paid of {rupees(bill.amount)} — {rupees(outstanding)} outstanding
        </p>
        <NumberInput label="Amount (₹)" value={form.amount}
          onChange={(e) => setForm({ ...form, amount: e.target.value })} autoFocus />
        <Select label="Method" value={form.method}
          onChange={(e) => setForm({ ...form, method: e.target.value })}>
          {["upi", "cash", "bank", "card", "cheque"].map((m) => (
            <option key={m} value={m}>{m.toUpperCase()}</option>
          ))}
        </Select>
        <TextInput label="Note" value={form.note}
          onChange={(e) => setForm({ ...form, note: e.target.value })} />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={busy}>{busy ? "Saving…" : "Record payment"}</Button>
        </div>
      </form>
    </Modal>
  );
}

// Per-tenant, per-month rent tracker: a grid the landlord ticks as rent comes in.
function RentTracker({ buildingId }) {
  const [tenants, setTenants] = useState([]);
  const [billMap, setBillMap] = useState({}); // `${tenant_id}|${period}` -> bill
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [busyCell, setBusyCell] = useState(null);
  // Oldest → newest left-to-right (recentPeriods is newest-first).
  const months = useMemo(() => recentPeriods(6).slice().reverse(), []);

  async function load() {
    if (!buildingId) return;
    setLoading(true);
    try {
      const [ts, rentBills] = await Promise.all([
        api.listTenants(buildingId),
        api.listBills(buildingId, { bill_type: "rent" }),
      ]);
      setTenants(ts.filter((t) => t.status === "active"));
      const map = {};
      for (const b of rentBills) map[`${b.tenant_id}|${b.period}`] = b;
      setBillMap(map);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [buildingId]);

  async function toggle(tenant, period) {
    const key = `${tenant.id}|${period}`;
    const bill = billMap[key];
    const paid = bill?.status === "paid";
    setBusyCell(key);
    try {
      await api.setRentStatus(buildingId, { tenant_id: tenant.id, period, paid: !paid });
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusyCell(null);
    }
  }

  if (loading) return <Spinner />;
  if (tenants.length === 0) {
    return (
      <EmptyState icon={<CashIcon className="mx-auto h-8 w-8 text-slate-400" />}
        title="No active tenants">
        Add tenants to this building to track their monthly rent here.
      </EmptyState>
    );
  }

  return (
    <Card className="overflow-x-auto">
      {error && <p className="px-4 pt-3 text-sm text-red-600">{error}</p>}
      <table className="w-full min-w-[640px] text-sm">
        <thead>
          <tr className="border-b border-slate-100 bg-slate-50 text-xs text-slate-500">
            <th className="px-4 py-2 text-left font-medium">Tenant</th>
            {months.map((m) => (
              <th key={m.value} className="px-2 py-2 text-center font-medium">{m.label}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {tenants.map((t) => (
            <tr key={t.id}>
              <td className="px-4 py-2">
                <p className="font-medium text-slate-800">{t.name}</p>
              </td>
              {months.map((m) => {
                const key = `${t.id}|${m.value}`;
                const bill = billMap[key];
                const paid = bill?.status === "paid";
                const partial = bill?.status === "partial";
                const overdue = bill?.status === "overdue";
                const cls = paid
                  ? "bg-emerald-500 border-emerald-500 text-white"
                  : partial
                  ? "bg-amber-100 border-amber-300 text-amber-700"
                  : overdue
                  ? "bg-rose-50 border-rose-300 text-rose-500"
                  : "bg-white border-slate-300 text-transparent hover:border-emerald-400";
                return (
                  <td key={m.value} className="px-2 py-2 text-center">
                    <button
                      type="button"
                      disabled={busyCell === key}
                      onClick={() => toggle(t, m.value)}
                      title={paid ? "Rent paid — click to undo" : "Mark rent paid"}
                      className={`mx-auto flex h-7 w-7 items-center justify-center rounded-md border text-sm font-bold transition ${cls} disabled:opacity-50`}
                    >
                      {paid ? "✓" : partial ? "½" : overdue ? "!" : "✓"}
                    </button>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="px-4 py-3 text-xs text-slate-400">
        Tick a cell when a tenant pays that month's rent. A green ✓ records a full rent payment;
        click again to undo. Amber = partial, red = overdue.
      </p>
    </Card>
  );
}

export default function Bills() {
  const [buildings, setBuildings] = useState([]);
  const [buildingId, setBuildingId] = useState("");
  const [period, setPeriod] = useState(currentPeriod());
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modal, setModal] = useState(null); // 'generate' | {type:'pay', bill}
  const [view, setView] = useState("list"); // 'list' | 'tracker'
  const periods = useMemo(() => recentPeriods(12), []);

  useEffect(() => {
    api.listBuildings().then((bs) => {
      setBuildings(bs);
      setBuildingId((cur) => cur || bs[0]?.id || "");
      if (bs.length === 0) setLoading(false);
    }).catch((e) => { setError(e.message); setLoading(false); });
  }, []);

  async function loadBills() {
    if (!buildingId) return;
    setLoading(true);
    try {
      const items = await api.listBills(buildingId, {
        period, status: statusFilter || undefined, bill_type: typeFilter || undefined,
      });
      // Ascending by flat number (blanks last), then tenant name, then type.
      items.sort((a, b) => {
        const d = flatSortKey(a.unit_label) - flatSortKey(b.unit_label);
        if (d !== 0) return d;
        const t = (a.tenant_name || "").localeCompare(b.tenant_name || "");
        if (t !== 0) return t;
        return a.bill_type.localeCompare(b.bill_type);
      });
      setBills(items);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadBills();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [buildingId, period, statusFilter, typeFilter]);

  async function deleteBill(bill) {
    if (!confirm("Delete this bill?")) return;
    await api.deleteBill(buildingId, bill.id);
    loadBills();
  }

  const totals = bills.reduce(
    (acc, b) => ({ billed: acc.billed + b.amount, paid: acc.paid + b.paid_amount }),
    { billed: 0, paid: 0 }
  );

  if (buildings.length === 0 && !loading) {
    return (
      <div>
        <PageHeader title="Rent & Bills" />
        <EmptyState icon={<CashIcon className="mx-auto h-8 w-8 text-slate-400" />} title="No buildings yet"
          action={<Link to="/buildings"><Button>Add a building</Button></Link>}>
          Add a building and tenants, then generate monthly bills here.
        </EmptyState>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Rent & Bills"
        subtitle="Track rent, water, electricity, and maintenance"
        action={
          <Button onClick={() => setModal("generate")} disabled={!buildingId}>
            <GearIcon className="h-4 w-4" /> Generate {formatPeriod(period)}
          </Button>
        }
      />

      <div className="mb-4 inline-flex rounded-lg border border-slate-200 bg-white p-0.5 text-sm">
        {[["list", "Bills"], ["tracker", "Rent tracker"]].map(([v, label]) => (
          <button key={v} onClick={() => setView(v)}
            className={`rounded-md px-3 py-1.5 font-medium transition ${
              view === v ? "bg-blue-600 text-white" : "text-slate-600 hover:bg-slate-50"
            }`}>
            {label}
          </button>
        ))}
      </div>

      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Select label="Building" value={buildingId} onChange={(e) => setBuildingId(e.target.value)}>
          {buildings.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
        </Select>
        {view === "list" && (
          <>
            <Select label="Month" value={period} onChange={(e) => setPeriod(e.target.value)}>
              {periods.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
            </Select>
            <Select label="Type" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
              <option value="">All types</option>
              {BILL_TYPES.map((t) => <option key={t} value={t}>{BILL_TYPE_META[t].label}</option>)}
            </Select>
            <Select label="Status" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">All statuses</option>
              {BILL_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </Select>
          </>
        )}
      </div>

      {view === "tracker" && buildingId && <RentTracker buildingId={buildingId} />}

      {view === "list" && error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      {view === "list" && (loading ? (
        <Spinner />
      ) : bills.length === 0 ? (
        <EmptyState icon={<CashIcon className="mx-auto h-8 w-8 text-slate-400" />} title={`No bills for ${formatPeriod(period)}`}
          action={<Button onClick={() => setModal("generate")}>Generate bills</Button>}>
          Generate this month's rent and utility bills for all active tenants.
        </EmptyState>
      ) : (
        <Card className="overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-4 py-2 text-xs text-slate-500">
            <span>{bills.length} bill(s)</span>
            <span>
              {rupees(totals.paid)} collected of {rupees(totals.billed)}
            </span>
          </div>
          <div className="divide-y divide-slate-100">
            {bills.map((b) => {
              const meta = BILL_TYPE_META[b.bill_type] || {};
              const outstanding = b.amount - b.paid_amount;
              return (
                <div key={b.id} className="flex flex-wrap items-center gap-3 px-4 py-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100"
                    title={meta.label} style={{ color: meta.color }}>
                    <BillTypeIcon type={b.bill_type} className="h-4 w-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-slate-800">
                      {b.tenant_name || "—"}
                      {b.unit_label ? <span className="text-slate-400"> · {b.unit_label}</span> : ""}
                    </p>
                    <p className="text-xs text-slate-400">
                      {meta.label} · {formatPeriod(b.period)}{b.due_date ? ` · due ${b.due_date}` : ""}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-slate-800">{rupees(b.amount)}</p>
                    {b.paid_amount > 0 && outstanding > 0 && (
                      <p className="text-xs text-slate-400">{rupees(outstanding)} left</p>
                    )}
                  </div>
                  <Badge className={STATUS_STYLES[b.status]}>{b.status}</Badge>
                  <div className="flex gap-1">
                    {b.status !== "paid" && (
                      <Button variant="secondary" className="!px-2 !py-1 text-xs"
                        onClick={() => setModal({ type: "pay", bill: b })}>
                        Record
                      </Button>
                    )}
                    <Button variant="ghost" className="!px-2 !py-1 text-xs"
                      onClick={() => deleteBill(b)}>✕</Button>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      ))}

      {modal === "generate" && (
        <GenerateModal buildingId={buildingId} period={period}
          onClose={() => setModal(null)} onDone={loadBills} />
      )}
      {modal?.type === "pay" && (
        <PaymentModal buildingId={buildingId} bill={modal.bill}
          onClose={() => setModal(null)} onDone={loadBills} />
      )}
    </div>
  );
}
