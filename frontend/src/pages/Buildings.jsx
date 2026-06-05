import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import {
  Button, Card, Modal, TextInput, TextArea, Spinner, EmptyState, PageHeader,
} from "../components/ui";
import { BuildingIcon } from "../components/icons";

function AddBuildingModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ name: "", address: "", city: "", notes: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    if (!form.name.trim()) return;
    setBusy(true);
    try {
      await api.createBuilding(form);
      onCreated();
      onClose();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <Modal title="Add building" subtitle="A property you rent out" onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <TextInput label="Name" value={form.name} onChange={set("name")}
          placeholder="Lakeview Apartments" autoFocus />
        <TextInput label="City" value={form.city} onChange={set("city")} placeholder="Bengaluru" />
        <TextInput label="Address" value={form.address} onChange={set("address")}
          placeholder="12 Lakeview Rd, Indiranagar" />
        <TextArea label="Notes" value={form.notes} onChange={set("notes")} />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={busy}>{busy ? "Saving…" : "Add building"}</Button>
        </div>
      </form>
    </Modal>
  );
}

export default function Buildings() {
  const [buildings, setBuildings] = useState([]);
  const [units, setUnits] = useState({}); // buildingId -> units[]
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [error, setError] = useState(null);

  async function load() {
    setLoading(true);
    try {
      const items = await api.listBuildings();
      setBuildings(items);
      const entries = await Promise.all(
        items.map(async (b) => [b.id, await api.listUnits(b.id)])
      );
      setUnits(Object.fromEntries(entries));
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

  return (
    <div>
      <PageHeader
        title="Buildings"
        subtitle="Your rental properties"
        action={<Button onClick={() => setShowAdd(true)}>+ Add building</Button>}
      />

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
      {loading ? (
        <Spinner />
      ) : buildings.length === 0 ? (
        <EmptyState
          icon={<BuildingIcon className="mx-auto h-8 w-8 text-slate-400" />}
          title="No buildings yet"
          action={<Button onClick={() => setShowAdd(true)}>+ Add building</Button>}
        >
          Add a building to start adding units and tenants.
        </EmptyState>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {buildings.map((b) => {
            const us = units[b.id] || [];
            const occ = us.filter((u) => u.status === "occupied").length;
            return (
              <Link key={b.id} to={`/buildings/${b.id}`}>
                <Card className="p-5 transition hover:border-blue-300 hover:shadow-md">
                  <div className="flex items-start justify-between">
                    <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 ring-1 ring-blue-100">
                      <BuildingIcon className="h-6 w-6 text-blue-600" />
                    </span>
                    <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                      {occ}/{us.length} occupied
                    </span>
                  </div>
                  <h3 className="mt-3 font-semibold text-slate-800">{b.name}</h3>
                  <p className="text-sm text-slate-500">
                    {[b.address, b.city].filter(Boolean).join(", ") || "No address set"}
                  </p>
                </Card>
              </Link>
            );
          })}
        </div>
      )}

      {showAdd && <AddBuildingModal onClose={() => setShowAdd(false)} onCreated={load} />}
    </div>
  );
}
