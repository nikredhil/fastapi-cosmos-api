import { Fragment, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, rupees } from "../api";
import {
  Button, Card, Modal, TextInput, NumberInput, Select, Spinner, EmptyState, PageHeader,
} from "../components/ui";
import Avatar from "../components/Avatar";
import { TenantsIcon, UserIcon } from "../components/icons";

// Sort key from a unit/flat label: leading digits ascending, blanks last.
function unitSortKey(label) {
  if (!label) return Number.POSITIVE_INFINITY;
  const n = parseInt(String(label).replace(/[^0-9]/g, ""), 10);
  return Number.isNaN(n) ? Number.POSITIVE_INFINITY : n;
}

function AddTenantModal({ buildings, onClose, onDone }) {
  const [form, setForm] = useState({
    building_id: buildings[0]?.id || "", name: "", phone: "", email: "", unit_id: "", deposit: "",
  });
  const [units, setUnits] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  useEffect(() => {
    if (!form.building_id) return;
    api.listUnits(form.building_id).then(setUnits).catch(() => setUnits([]));
  }, [form.building_id]);

  async function submit(e) {
    e.preventDefault();
    if (!form.building_id || !form.name.trim()) return;
    setBusy(true);
    try {
      await api.createTenant(form.building_id, {
        name: form.name.trim(),
        phone: form.phone || null,
        email: form.email || null,
        unit_id: form.unit_id || null,
        deposit: Number(form.deposit) || 0,
      });
      onDone();
      onClose();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <Modal title="Add tenant" onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <Select label="Building" value={form.building_id}
          onChange={(e) => setForm({ ...form, building_id: e.target.value, unit_id: "" })}>
          {buildings.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
        </Select>
        <TextInput label="Name" value={form.name} onChange={set("name")} autoFocus />
        <div className="grid grid-cols-2 gap-3">
          <TextInput label="Phone" value={form.phone} onChange={set("phone")} />
          <TextInput label="Email" value={form.email} onChange={set("email")} />
        </div>
        <Select label="Unit" value={form.unit_id} onChange={set("unit_id")}>
          <option value="">— Unassigned —</option>
          {units.map((u) => <option key={u.id} value={u.id}>{u.label}</option>)}
        </Select>
        <NumberInput label="Deposit (₹)" value={form.deposit} onChange={set("deposit")} />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={busy}>{busy ? "Saving…" : "Add tenant"}</Button>
        </div>
      </form>
    </Modal>
  );
}

function EditTenantModal({ row, onClose, onDone }) {
  const { tenant, buildingName } = row;
  const [form, setForm] = useState({
    name: tenant.name || "",
    phone: tenant.phone || "",
    emergency_phone: tenant.emergency_phone || "",
    email: tenant.email || "",
    unit_id: tenant.unit_id || "",
    move_in_date: tenant.move_in_date || "",
    deposit: tenant.deposit ?? "",
    monthly_rent: tenant.monthly_rent ?? "",
    status: tenant.status || "active",
  });
  const [units, setUnits] = useState([]);
  const [busy, setBusy] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState(null);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  useEffect(() => {
    api.listUnits(tenant.building_id).then(setUnits).catch(() => setUnits([]));
  }, [tenant.building_id]);

  async function submit(e) {
    e.preventDefault();
    if (!form.name.trim()) return;
    setBusy(true);
    try {
      const rent = Number(form.monthly_rent) || 0;
      await api.updateTenant(tenant.building_id, tenant.id, {
        name: form.name.trim(),
        phone: form.phone || null,
        emergency_phone: form.emergency_phone || null,
        email: form.email || null,
        unit_id: form.unit_id || null,
        move_in_date: form.move_in_date || null,
        deposit: Number(form.deposit) || 0,
        monthly_rent: rent,
        status: form.status,
      });
      // Re-price the tenant's open rent bills so Rent & Bills reflects the change.
      if (rent > 0) {
        await api.syncRent(tenant.building_id, { tenant_id: tenant.id, monthly_rent: rent });
      }
      onDone();
      onClose();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  async function remove() {
    if (!window.confirm(`Delete tenant "${tenant.name}"? This can't be undone.`)) return;
    setDeleting(true);
    try {
      await api.deleteTenant(tenant.building_id, tenant.id);
      onDone();
      onClose();
    } catch (err) {
      setError(err.message);
      setDeleting(false);
    }
  }

  return (
    <Modal title="Edit tenant" subtitle={buildingName} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <TextInput label="Name" value={form.name} onChange={set("name")} autoFocus />
        <div className="grid grid-cols-2 gap-3">
          <TextInput label="Phone" value={form.phone} onChange={set("phone")} />
          <TextInput label="Emergency phone" value={form.emergency_phone}
            onChange={set("emergency_phone")} />
        </div>
        <TextInput label="Email" value={form.email} onChange={set("email")} />
        <Select label="Unit" value={form.unit_id} onChange={set("unit_id")}>
          <option value="">— Unassigned —</option>
          {units.map((u) => <option key={u.id} value={u.id}>{u.label}</option>)}
        </Select>
        <TextInput label="Move-in date" type="date" value={form.move_in_date}
          onChange={set("move_in_date")}
          hint="Anchors the 11-month / 5% renewal reminder on the dashboard" />
        <div className="grid grid-cols-2 gap-3">
          <NumberInput label="Deposit (₹)" value={form.deposit} onChange={set("deposit")} />
          <NumberInput label="Monthly rent (₹)" value={form.monthly_rent}
            onChange={set("monthly_rent")} />
        </div>
        <Select label="Status" value={form.status} onChange={set("status")}>
          <option value="active">Active</option>
          <option value="past">Past</option>
        </Select>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="flex items-center justify-between pt-2">
          <Button type="button" variant="danger" onClick={remove} disabled={deleting}>
            {deleting ? "Deleting…" : "Delete"}
          </Button>
          <div className="flex gap-2">
            <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={busy}>{busy ? "Saving…" : "Save"}</Button>
          </div>
        </div>
      </form>
    </Modal>
  );
}

export default function Tenants() {
  const [buildings, setBuildings] = useState([]);
  const [rows, setRows] = useState([]); // {tenant, buildingName, buildingId, unitLabel}
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState(null);

  async function load() {
    setLoading(true);
    try {
      const bs = await api.listBuildings();
      setBuildings(bs);
      const all = [];
      for (const b of bs) {
        const [units, tenants] = await Promise.all([api.listUnits(b.id), api.listTenants(b.id)]);
        const unitLabel = (id) => units.find((u) => u.id === id)?.label;
        tenants.forEach((t) =>
          all.push({ tenant: t, buildingName: b.name, buildingId: b.id, unitLabel: unitLabel(t.unit_id) })
        );
      }
      setRows(all);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const filtered = rows
    .filter((r) =>
      r.tenant.name.toLowerCase().includes(query.toLowerCase()) ||
      (r.buildingName || "").toLowerCase().includes(query.toLowerCase())
    )
    .sort((a, b) => {
      // Group by building, then ascending by flat number within each building.
      const bd = (a.buildingName || "").localeCompare(b.buildingName || "", undefined, {
        numeric: true,
      });
      if (bd !== 0) return bd;
      const ud = unitSortKey(a.unitLabel) - unitSortKey(b.unitLabel);
      if (ud !== 0) return ud;
      return a.tenant.name.localeCompare(b.tenant.name);
    });

  return (
    <div>
      <PageHeader
        title="Tenants"
        subtitle="Everyone renting across your buildings"
        action={
          <Button onClick={() => setShowAdd(true)} disabled={buildings.length === 0}>
            + Add tenant
          </Button>
        }
      />

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
      {loading ? (
        <Spinner />
      ) : buildings.length === 0 ? (
        <EmptyState icon={<TenantsIcon className="mx-auto h-8 w-8 text-slate-400" />} title="No buildings yet"
          action={<Link to="/buildings"><Button>Add a building</Button></Link>}>
          Add a building first, then its tenants.
        </EmptyState>
      ) : rows.length === 0 ? (
        <EmptyState icon={<UserIcon className="mx-auto h-8 w-8 text-slate-400" />} title="No tenants yet"
          action={<Button onClick={() => setShowAdd(true)}>+ Add tenant</Button>}>
          Add tenants here or upload a contract from a building.
        </EmptyState>
      ) : (
        <>
          <TextInput placeholder="Search tenants or buildings…" value={query}
            onChange={(e) => setQuery(e.target.value)} />
          <Card className="mt-4 divide-y divide-slate-100">
            {filtered.map((row, idx) => {
              const { tenant, buildingName, buildingId, unitLabel } = row;
              const showHeader = idx === 0 || filtered[idx - 1].buildingId !== buildingId;
              return (
                <Fragment key={tenant.id}>
                {showHeader && (
                  <div className="bg-slate-50 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    {buildingName}
                  </div>
                )}
                <div className="flex items-center gap-3 px-4 py-3">
                  <Avatar name={tenant.name} color={tenant.avatar_color} />
                  <div className="min-w-0 flex-1">
                    <Link to={`/buildings/${buildingId}/tenants/${tenant.id}`}
                      className="block truncate font-medium text-slate-800 hover:text-blue-600 hover:underline">
                      {tenant.name}
                    </Link>
                    <p className="truncate text-xs text-slate-500">
                      {tenant.phone ? `${tenant.phone} · ` : ""}
                      <Link to={`/buildings/${buildingId}`} className="text-blue-600 hover:underline">
                        {buildingName}
                      </Link>
                      {unitLabel ? ` · ${unitLabel}` : ""}
                    </p>
                  </div>
                  {tenant.deposit > 0 && (
                    <span className="text-xs text-slate-400">Deposit {rupees(tenant.deposit)}</span>
                  )}
                  <Button variant="ghost" className="px-2" onClick={() => setEditing(row)}>
                    Edit
                  </Button>
                </div>
                </Fragment>
              );
            })}
            {filtered.length === 0 && (
              <p className="px-4 py-6 text-center text-sm text-slate-400">No matches.</p>
            )}
          </Card>
        </>
      )}

      {showAdd && (
        <AddTenantModal buildings={buildings} onClose={() => setShowAdd(false)} onDone={load} />
      )}
      {editing && (
        <EditTenantModal row={editing} onClose={() => setEditing(null)} onDone={load} />
      )}
    </div>
  );
}
