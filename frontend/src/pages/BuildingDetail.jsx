import { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { api, rupees } from "../api";
import {
  Button, Card, Modal, TextInput, NumberInput, Select, Spinner, EmptyState, Badge,
} from "../components/ui";
import Avatar from "../components/Avatar";
import ContractUpload from "../components/ContractUpload";
import { DocumentIcon, KeyIcon, UserIcon } from "../components/icons";

function UnitModal({ buildingId, unit, onClose, onDone }) {
  const editing = !!unit;
  const [form, setForm] = useState({
    label: unit?.label ?? "",
    floor: unit?.floor ?? "",
    bedrooms: unit?.bedrooms ?? "",
    default_rent: unit?.default_rent ?? "",
    status: unit?.status ?? "vacant",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    if (!form.label.trim()) return;
    setBusy(true);
    try {
      const body = {
        label: form.label.trim(),
        floor: form.floor === "" ? null : Number(form.floor),
        bedrooms: form.bedrooms === "" ? null : Number(form.bedrooms),
        default_rent: Number(form.default_rent) || 0,
      };
      if (editing) {
        await api.updateUnit(buildingId, unit.id, { ...body, status: form.status });
      } else {
        await api.createUnit(buildingId, body);
      }
      onDone();
      onClose();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  async function remove() {
    if (!confirm(`Delete unit ${unit.label}?`)) return;
    setBusy(true);
    try {
      await api.deleteUnit(buildingId, unit.id);
      onDone();
      onClose();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <Modal title={editing ? "Edit unit" : "Add unit"} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <TextInput label="Label" value={form.label} onChange={set("label")}
          placeholder="A-101" autoFocus />
        <div className="grid grid-cols-2 gap-3">
          <NumberInput label="Floor" value={form.floor} onChange={set("floor")} />
          <NumberInput label="Bedrooms" value={form.bedrooms} onChange={set("bedrooms")} />
        </div>
        <NumberInput label="Default rent (₹)" value={form.default_rent}
          onChange={set("default_rent")} />
        {editing && (
          <Select label="Status" value={form.status} onChange={set("status")}>
            <option value="vacant">Vacant</option>
            <option value="occupied">Occupied</option>
          </Select>
        )}
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="flex items-center justify-between pt-2">
          {editing ? (
            <Button type="button" variant="danger" onClick={remove} disabled={busy}>Delete</Button>
          ) : <span />}
          <div className="flex gap-2">
            <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={busy}>
              {busy ? "Saving…" : editing ? "Save changes" : "Add unit"}
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
}

function AddTenantModal({ buildingId, units, onClose, onDone }) {
  const [form, setForm] = useState({ name: "", phone: "", email: "", unit_id: "", deposit: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    if (!form.name.trim()) return;
    setBusy(true);
    try {
      await api.createTenant(buildingId, {
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
        <TextInput label="Name" value={form.name} onChange={set("name")} autoFocus />
        <div className="grid grid-cols-2 gap-3">
          <TextInput label="Phone" value={form.phone} onChange={set("phone")} />
          <TextInput label="Email" value={form.email} onChange={set("email")} />
        </div>
        <Select label="Unit" value={form.unit_id} onChange={set("unit_id")}>
          <option value="">— Unassigned —</option>
          {units.map((u) => (
            <option key={u.id} value={u.id}>{u.label}</option>
          ))}
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

export default function BuildingDetail() {
  const { buildingId } = useParams();
  const navigate = useNavigate();
  const [building, setBuilding] = useState(null);
  const [units, setUnits] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modal, setModal] = useState(null); // 'unit' | 'tenant' | 'contract'

  async function load() {
    setLoading(true);
    try {
      const [b, u, t] = await Promise.all([
        api.getBuilding(buildingId),
        api.listUnits(buildingId),
        api.listTenants(buildingId),
      ]);
      setBuilding(b);
      setUnits(u);
      setTenants(t);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [buildingId]);

  async function removeBuilding() {
    if (!confirm("Delete this building? Units, tenants, and bills under it remain in storage.")) return;
    await api.deleteBuilding(buildingId);
    navigate("/buildings");
  }

  if (loading) return <Spinner />;
  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!building) return null;

  const unitLabel = (id) => units.find((u) => u.id === id)?.label;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <Link to="/buildings" className="text-sm text-blue-600 hover:underline">
            ← Buildings
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-slate-800">{building.name}</h1>
          <p className="text-sm text-slate-500">
            {[building.address, building.city].filter(Boolean).join(", ") || "No address set"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="primary" onClick={() => setModal({ type: "contract" })}>
            <DocumentIcon className="h-4 w-4" /> Add from contract
          </Button>
          <Button variant="secondary" onClick={() => setModal({ type: "tenant" })}>+ Tenant</Button>
          <Button variant="secondary" onClick={() => setModal({ type: "unit" })}>+ Unit</Button>
          <Button variant="danger" onClick={removeBuilding}>Delete</Button>
        </div>
      </div>

      <section className="mb-8">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Units ({units.length})
        </h2>
        {units.length === 0 ? (
          <EmptyState icon={<KeyIcon className="mx-auto h-8 w-8 text-slate-400" />} title="No units yet"
            action={<Button onClick={() => setModal({ type: "unit" })}>+ Add unit</Button>}>
            Add the flats in this building.
          </EmptyState>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {units.map((u) => (
              <button
                key={u.id}
                onClick={() => setModal({ type: "unit", unit: u })}
                className="group text-left"
              >
                <Card className="p-4 transition group-hover:border-blue-300 group-hover:shadow-md">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-800">{u.label}</span>
                    <Badge className={u.status === "occupied"
                      ? "bg-teal-100 text-teal-700" : "bg-slate-100 text-slate-500"}>
                      {u.status}
                    </Badge>
                  </div>
                  <p className="mt-1 text-sm text-slate-500">
                    {rupees(u.default_rent)}/mo
                    {u.bedrooms != null ? ` · ${u.bedrooms} BHK` : ""}
                    {u.floor != null ? ` · Floor ${u.floor}` : ""}
                  </p>
                  <p className="mt-2 text-xs text-blue-600 opacity-0 transition group-hover:opacity-100">
                    Edit unit →
                  </p>
                </Card>
              </button>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Tenants ({tenants.length})
        </h2>
        {tenants.length === 0 ? (
          <EmptyState icon={<UserIcon className="mx-auto h-8 w-8 text-slate-400" />} title="No tenants yet"
            action={<Button onClick={() => setModal({ type: "contract" })}>
              <DocumentIcon className="h-4 w-4" /> Add from contract
            </Button>}>
            Upload a contract photo to auto-fill a tenant, or add one manually.
          </EmptyState>
        ) : (
          <Card className="divide-y divide-slate-100">
            {tenants.map((t) => (
              <Link key={t.id} to={`/buildings/${buildingId}/tenants/${t.id}`}
                className="flex items-center gap-3 px-4 py-3 transition hover:bg-slate-50">
                <Avatar name={t.name} color={t.avatar_color} />
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-slate-800">{t.name}</p>
                  <p className="truncate text-xs text-slate-500">
                    {[t.phone, unitLabel(t.unit_id)].filter(Boolean).join(" · ") || "No unit / phone"}
                  </p>
                </div>
                {t.deposit > 0 && (
                  <span className="text-xs text-slate-400">Deposit {rupees(t.deposit)}</span>
                )}
              </Link>
            ))}
          </Card>
        )}
      </section>

      {modal?.type === "unit" && (
        <UnitModal buildingId={buildingId} unit={modal.unit}
          onClose={() => setModal(null)} onDone={load} />
      )}
      {modal?.type === "tenant" && (
        <AddTenantModal buildingId={buildingId} units={units}
          onClose={() => setModal(null)} onDone={load} />
      )}
      {modal?.type === "contract" && (
        <ContractUpload building={building} units={units}
          onClose={() => setModal(null)} onComplete={load} />
      )}
    </div>
  );
}
