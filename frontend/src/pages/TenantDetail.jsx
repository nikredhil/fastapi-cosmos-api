import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  api, rupees, formatPeriod, BILL_TYPE_META, STATUS_STYLES,
} from "../api";
import { Card, Spinner, Badge, Button, EmptyState } from "../components/ui";
import Avatar from "../components/Avatar";
import AuthImage from "../components/AuthImage";
import CameraCapture from "../components/CameraCapture";
import Lightbox from "../components/Lightbox";
import { BillTypeIcon, DocumentIcon, CameraIcon } from "../components/icons";

function Detail({ label, value }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="mt-0.5 text-sm font-medium text-slate-800">{value || "—"}</dd>
    </div>
  );
}

export default function TenantDetail() {
  const { buildingId, tenantId } = useParams();
  const [tenant, setTenant] = useState(null);
  const [units, setUnits] = useState([]);
  const [leases, setLeases] = useState([]);
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [lightbox, setLightbox] = useState(null); // { url, alt }
  const [contractCameraLease, setContractCameraLease] = useState(null);
  const fileRef = useRef(null);
  const contractFileRef = useRef(null);
  const pendingLease = useRef(null);

  async function load() {
    setLoading(true);
    try {
      const [t, u, ls, bs] = await Promise.all([
        api.getTenant(buildingId, tenantId),
        api.listUnits(buildingId),
        api.listLeases(buildingId),
        api.listBills(buildingId, { tenant_id: tenantId }),
      ]);
      setTenant(t);
      setUnits(u);
      setLeases(ls.filter((l) => l.tenant_id === tenantId));
      setBills(bs);
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
  }, [buildingId, tenantId]);

  async function uploadAadhaar(file) {
    if (!file) return;
    setUploading(true);
    try {
      const { image_id } = await api.uploadImage(buildingId, file);
      await api.updateTenant(buildingId, tenantId, { aadhaar_image_id: image_id });
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  }

  // Pages already on a lease, tolerating the legacy single-image field.
  function leasePages(l) {
    if (l.contract_image_ids?.length) return l.contract_image_ids;
    return l.contract_image_id ? [l.contract_image_id] : [];
  }

  async function uploadContract(leaseId, fileInput) {
    const list = fileInput instanceof File ? [fileInput] : Array.from(fileInput || []);
    if (!list.length || !leaseId) return;
    setUploading(true);
    try {
      const lease = leases.find((l) => l.id === leaseId);
      const existing = lease ? leasePages(lease) : [];
      const added = [];
      for (const f of list) {
        const { image_id } = await api.uploadImage(buildingId, f);
        added.push(image_id);
      }
      const all = [...existing, ...added];
      await api.updateLease(buildingId, leaseId, {
        contract_image_ids: all,
        contract_image_id: all[0],
      });
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  }

  if (loading) return <Spinner />;
  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!tenant) return null;

  const unitLabel = (id) => units.find((u) => u.id === id)?.label;
  const billed = bills.reduce((s, b) => s + b.amount, 0);
  const collected = bills.reduce((s, b) => s + b.paid_amount, 0);

  return (
    <div>
      <Link to="/tenants" className="text-sm text-blue-600 hover:underline">← Tenants</Link>

      {/* Profile */}
      <Card className="mt-2 p-6">
        <div className="flex flex-wrap items-center gap-4">
          <Avatar name={tenant.name} color={tenant.avatar_color} size="lg" />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-slate-800">{tenant.name}</h1>
              <Badge className={tenant.status === "active"
                ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"}>
                {tenant.status}
              </Badge>
            </div>
            <p className="text-sm text-slate-500">
              {[tenant.phone, tenant.email].filter(Boolean).join(" · ") || "No contact info"}
            </p>
          </div>
        </div>
        <dl className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Detail label="Unit" value={unitLabel(tenant.unit_id)} />
          <Detail label="Move-in date" value={tenant.move_in_date} />
          <Detail label="Deposit paid" value={tenant.deposit ? rupees(tenant.deposit) : "—"} />
          <Detail label="Outstanding" value={rupees(billed - collected)} />
        </dl>
      </Card>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        {/* Rent & bill history */}
        <div className="lg:col-span-2">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Rent & bill history
          </h2>
          {bills.length === 0 ? (
            <EmptyState icon={<BillTypeIcon type="rent" className="mx-auto h-8 w-8 text-slate-400" />}
              title="No bills yet">
              Generate bills from the Rent & Bills page.
            </EmptyState>
          ) : (
            <Card className="divide-y divide-slate-100">
              <div className="flex justify-between bg-slate-50 px-4 py-2 text-xs text-slate-500">
                <span>{bills.length} bill(s)</span>
                <span>{rupees(collected)} collected of {rupees(billed)}</span>
              </div>
              {bills.map((b) => {
                const meta = BILL_TYPE_META[b.bill_type] || {};
                return (
                  <div key={b.id} className="flex items-center gap-3 px-4 py-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100"
                      style={{ color: meta.color }}>
                      <BillTypeIcon type={b.bill_type} className="h-4 w-4" />
                    </span>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-800">
                        {meta.label} · {formatPeriod(b.period)}
                      </p>
                      <p className="text-xs text-slate-400">
                        {b.due_date ? `due ${b.due_date}` : ""}
                        {b.payments?.length ? ` · ${b.payments.length} payment(s)` : ""}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-slate-800">{rupees(b.amount)}</p>
                      {b.paid_amount > 0 && b.paid_amount < b.amount && (
                        <p className="text-xs text-slate-400">{rupees(b.amount - b.paid_amount)} left</p>
                      )}
                    </div>
                    <Badge className={STATUS_STYLES[b.status]}>{b.status}</Badge>
                  </div>
                );
              })}
            </Card>
          )}
        </div>

        {/* Documents */}
        <div className="space-y-6">
          {/* Contracts */}
          <div>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Contracts
            </h2>
            {leases.length === 0 ? (
              <Card className="p-4 text-sm text-slate-400">No lease on file.</Card>
            ) : (
              <div className="space-y-3">
                {leases.map((l) => (
                  <Card key={l.id} className="p-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-semibold text-slate-800">{rupees(l.monthly_rent)}/mo</span>
                      <Badge className="bg-slate-100 text-slate-500">{l.status}</Badge>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      {[l.start_date, l.end_date].filter(Boolean).join(" → ") || "No dates"}
                      {` · due day ${l.rent_due_day}`}
                    </p>
                    {l.terms && <p className="mt-2 text-xs text-slate-600">{l.terms}</p>}
                    {leasePages(l).length > 0 ? (
                      <>
                        <p className="mt-3 text-xs font-medium text-slate-400">
                          {leasePages(l).length} page(s)
                        </p>
                        <div className="mt-1 grid grid-cols-3 gap-2">
                          {leasePages(l).map((imgId, i) => (
                            <button key={imgId}
                              onClick={() => setLightbox({
                                url: api.contractImageUrl(buildingId, imgId),
                                alt: `Lease page ${i + 1}`,
                              })}
                              title={`Page ${i + 1} — click to expand`}
                              className="group relative block overflow-hidden rounded-lg border border-slate-200"
                            >
                              <AuthImage
                                url={api.contractImageUrl(buildingId, imgId)}
                                alt={`page ${i + 1}`}
                                className="h-24 w-full object-cover transition group-hover:scale-105"
                              />
                              <span className="absolute left-1 top-1 rounded bg-slate-900/70 px-1 text-[10px] font-semibold text-white">
                                {i + 1}
                              </span>
                            </button>
                          ))}
                        </div>
                      </>
                    ) : (
                      <div className="mt-3 flex flex-col items-center gap-1 rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center">
                        <DocumentIcon className="h-6 w-6 text-slate-400" />
                        <span className="text-xs text-slate-500">No contract pages</span>
                      </div>
                    )}
                    <div className="mt-2 grid grid-cols-2 gap-2">
                      <Button variant="secondary" disabled={uploading}
                        onClick={() => { pendingLease.current = l.id; contractFileRef.current?.click(); }}>
                        <DocumentIcon className="h-4 w-4" />
                        {leasePages(l).length ? "Add pages" : "Upload"}
                      </Button>
                      <Button variant="secondary" disabled={uploading}
                        onClick={() => setContractCameraLease(l.id)}>
                        <CameraIcon className="h-4 w-4" /> Camera
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Aadhaar */}
          <div>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Aadhaar card
            </h2>
            <Card className="p-4">
              {tenant.aadhaar_image_id ? (
                <button
                  onClick={() => setLightbox({
                    url: api.contractImageUrl(buildingId, tenant.aadhaar_image_id),
                    alt: "Aadhaar card",
                  })}
                  title="Click to expand"
                  className="group block w-full overflow-hidden rounded-lg border border-slate-200"
                >
                  <AuthImage
                    url={api.contractImageUrl(buildingId, tenant.aadhaar_image_id)}
                    alt="Aadhaar card"
                    className="h-40 w-full object-cover transition group-hover:scale-105"
                  />
                </button>
              ) : (
                <div className="flex flex-col items-center gap-1 rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center">
                  <DocumentIcon className="h-7 w-7 text-slate-400" />
                  <span className="text-sm font-medium text-slate-600">
                    {uploading ? "Uploading…" : "No Aadhaar on file"}
                  </span>
                  <span className="text-xs text-slate-400">Upload or capture an image</span>
                </div>
              )}
              <div className="mt-3 grid grid-cols-2 gap-2">
                <Button variant="secondary" onClick={() => fileRef.current?.click()}
                  disabled={uploading}>
                  <DocumentIcon className="h-4 w-4" />
                  {tenant.aadhaar_image_id ? "Replace" : "Upload"}
                </Button>
                <Button variant="secondary" onClick={() => setShowCamera(true)} disabled={uploading}>
                  <CameraIcon className="h-4 w-4" /> Camera
                </Button>
              </div>
              <input ref={fileRef} type="file" accept="image/*" className="hidden"
                onChange={(e) => uploadAadhaar(e.target.files?.[0])} />
            </Card>
          </div>
        </div>
      </div>

      {showCamera && (
        <CameraCapture
          title="Capture Aadhaar card"
          onClose={() => setShowCamera(false)}
          onCapture={(file) => {
            setShowCamera(false);
            uploadAadhaar(file);
          }}
        />
      )}

      <input ref={contractFileRef} type="file" accept="image/*" multiple className="hidden"
        onChange={(e) => uploadContract(pendingLease.current, e.target.files)} />
      {contractCameraLease && (
        <CameraCapture
          title="Capture lease contract"
          onClose={() => setContractCameraLease(null)}
          onCapture={(file) => {
            const id = contractCameraLease;
            setContractCameraLease(null);
            uploadContract(id, file);
          }}
        />
      )}

      {lightbox && (
        <Lightbox url={lightbox.url} alt={lightbox.alt} onClose={() => setLightbox(null)} />
      )}
    </div>
  );
}
