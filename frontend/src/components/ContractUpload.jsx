import { useState, useRef, useEffect } from "react";
import { api } from "../api";
import { Button, Modal, TextInput, NumberInput, TextArea, Select } from "./ui";
import { DocumentIcon, CameraIcon } from "./icons";

const EMPTY = {
  tenant_name: "", tenant_age: "", tenant_phone: "", tenant_email: "",
  permanent_address: "", unit_label: "",
  monthly_rent: "", deposit: "", start_date: "", end_date: "", rent_due_day: 5,
  lease_months: "", rent_increase_pct: "", terms_summary: "",
};

// Two-step modal: (1) upload a contract photo to auto-parse, then
// (2) review/edit the fields and create the tenant + lease.
export default function ContractUpload({ building, units, onClose, onComplete }) {
  const [step, setStep] = useState("upload"); // upload | review
  const [files, setFiles] = useState([]); // all pages (File[])
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [imageIds, setImageIds] = useState([]); // pages already uploaded (during parse)
  const [form, setForm] = useState(EMPTY);
  const [cameraOn, setCameraOn] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  function addFiles(list) {
    const arr = Array.from(list || []).filter(Boolean);
    if (!arr.length) return;
    setFiles((prev) => [...prev, ...arr]);
    setError(null);
  }

  function removeFile(i) {
    setFiles((prev) => prev.filter((_, idx) => idx !== i));
  }

  function stopCamera() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setCameraOn(false);
  }

  // Open the device webcam (works on desktop too, via getUserMedia).
  async function startCamera() {
    setError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("This browser can't access the camera. Choose a file instead.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      streamRef.current = stream;
      setCameraOn(true);
    } catch {
      setError("Couldn't access the camera. Check the browser permission, or choose a file.");
    }
  }

  // Attach the live stream once the <video> is mounted.
  useEffect(() => {
    if (cameraOn && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [cameraOn]);

  // Stop any active stream when the modal unmounts.
  useEffect(() => stopCamera, []);

  function capturePhoto() {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        // Keep the camera on so all pages can be captured in one go.
        addFiles([new File([blob], `contract-${Date.now()}.jpg`, { type: "image/jpeg" })]);
      },
      "image/jpeg",
      0.92
    );
  }

  async function parse() {
    if (!files.length) return;
    setBusy(true);
    setError(null);
    try {
      // Parse the first page (it carries the key fields); all pages are stored on save.
      const res = await api.parseContract(building.id, files[0]);
      setImageIds([res.contract_image_id]);
      setForm({
        tenant_name: res.tenant_name || "",
        tenant_age: res.tenant_age ?? "",
        tenant_phone: res.tenant_phone || "",
        tenant_email: res.tenant_email || "",
        permanent_address: res.permanent_address || "",
        unit_label: res.unit_label || "",
        monthly_rent: res.monthly_rent ?? "",
        deposit: res.deposit ?? "",
        start_date: res.start_date || "",
        end_date: res.end_date || "",
        rent_due_day: res.rent_due_day ?? 5,
        lease_months: res.lease_months ?? "",
        rent_increase_pct: res.rent_increase_pct ?? "",
        terms_summary: res.terms_summary || "",
      });
      setNotice(
        res.parsed
          ? "Parsed with Claude — review the fields below before saving."
          : "Auto-parsing is off (no Claude API key). Enter the details manually."
      );
      setStep("review");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function skipToManual() {
    setNotice("Enter the contract details manually.");
    setStep("review");
  }

  async function save(e) {
    e.preventDefault();
    if (!form.tenant_name.trim()) {
      setError("Tenant name is required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const rent = Number(form.monthly_rent) || 0;
      const deposit = Number(form.deposit) || 0;
      const leaseMonths = Number(form.lease_months) || null;
      const increasePct =
        form.rent_increase_pct === "" ? null : Number(form.rent_increase_pct);

      // Pages 0..imageIds.length were uploaded during parse; upload the rest now.
      const pending = files.slice(imageIds.length);
      const uploaded = [];
      for (const f of pending) {
        const { image_id } = await api.uploadImage(building.id, f);
        uploaded.push(image_id);
      }
      const pageIds = [...imageIds, ...uploaded];

      // Match an existing unit by label, else create one.
      let unit = units.find(
        (u) => u.label.toLowerCase() === form.unit_label.trim().toLowerCase()
      );
      if (!unit && form.unit_label.trim()) {
        unit = await api.createUnit(building.id, {
          label: form.unit_label.trim(),
          default_rent: rent,
        });
      }

      const tenant = await api.createTenant(building.id, {
        name: form.tenant_name.trim(),
        age: form.tenant_age === "" ? null : Number(form.tenant_age),
        phone: form.tenant_phone || null,
        email: form.tenant_email || null,
        permanent_address: form.permanent_address || null,
        unit_id: unit?.id || null,
        deposit,
        monthly_rent: rent,
        move_in_date: form.start_date || null,
        lease_months: leaseMonths,
        rent_increase_pct: increasePct,
      });

      await api.createLease(building.id, {
        unit_id: unit?.id || null,
        tenant_id: tenant.id,
        monthly_rent: rent,
        deposit,
        rent_due_day: Number(form.rent_due_day) || 5,
        start_date: form.start_date || null,
        end_date: form.end_date || null,
        lease_months: leaseMonths,
        rent_increase_pct: increasePct,
        terms: form.terms_summary || null,
        contract_image_id: pageIds[0] || null,
        contract_image_ids: pageIds,
        parsed: imageIds.length > 0,
      });

      onComplete();
      onClose();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <Modal
      title="Add from contract"
      subtitle={building.name}
      onClose={onClose}
      wide={step === "review"}
    >
      {step === "upload" ? (
        <div className="space-y-4">
          <p className="text-sm text-slate-500">
            Add every page of the rental agreement (e.g. all 6). Claude reads the first page to
            pre-fill the tenant, rent, deposit, and dates — all pages are saved with the lease.
          </p>
          {cameraOn ? (
            <div className="space-y-3">
              <video ref={videoRef} autoPlay playsInline
                className="w-full rounded-xl bg-black" />
              <div className="flex justify-between gap-2">
                <Button onClick={capturePhoto}>
                  <CameraIcon className="h-4 w-4" /> Capture page {files.length + 1}
                </Button>
                <Button variant="secondary" onClick={stopCamera}>Done</Button>
              </div>
            </div>
          ) : (
            <>
              {files.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {files.map((f, i) => (
                    <div key={i} className="relative">
                      <img src={URL.createObjectURL(f)} alt={`page ${i + 1}`}
                        className="h-20 w-16 rounded-lg border border-slate-200 object-cover" />
                      <span className="absolute left-1 top-1 rounded bg-slate-900/70 px-1 text-[10px] font-semibold text-white">
                        {i + 1}
                      </span>
                      <button type="button" onClick={() => removeFile(i)}
                        className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-rose-500 text-xs text-white shadow">
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
              <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-8 text-center hover:border-blue-400">
                <DocumentIcon className="h-9 w-9 text-slate-400" />
                <span className="mt-2 text-sm font-medium text-slate-600">
                  {files.length ? "Add more pages" : "Click to choose image(s)"}
                </span>
                <span className="text-xs text-slate-400">JPG, PNG, or WEBP up to 10 MB each</span>
                <input type="file" accept="image/*" multiple className="hidden"
                  onChange={(e) => addFiles(e.target.files)} />
              </label>
              <button type="button" onClick={startCamera}
                className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                <span className="text-lg">📷</span>
                {files.length ? "Add a page with camera" : "Take a photo"}
              </button>
            </>
          )}
          {error && <p className="text-sm text-red-600">{error}</p>}
          {!cameraOn && (
            <div className="flex items-center justify-between gap-2">
              <Button variant="ghost" onClick={skipToManual}>Skip — enter manually</Button>
              <div className="flex items-center gap-2">
                {files.length > 0 && (
                  <span className="text-xs text-slate-400">{files.length} page(s)</span>
                )}
                <Button onClick={parse} disabled={!files.length || busy}>
                  {busy ? "Reading contract…" : "Parse contract"}
                </Button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <form onSubmit={save} className="space-y-3">
          {notice && (
            <p className="rounded-lg bg-blue-50 px-3 py-2 text-xs text-blue-700">{notice}</p>
          )}
          {files.length > 0 && (
            <p className="text-xs text-slate-400">{files.length} contract page(s) will be saved.</p>
          )}
          <div className="grid gap-3 sm:grid-cols-2">
            <TextInput label="Tenant name" value={form.tenant_name}
              onChange={set("tenant_name")} autoFocus />
            <NumberInput label="Age" min={0} max={120} value={form.tenant_age}
              onChange={set("tenant_age")} />
            <TextInput label="Phone" value={form.tenant_phone} onChange={set("tenant_phone")} />
            <TextInput label="Email" value={form.tenant_email} onChange={set("tenant_email")} />
            <div className="sm:col-span-2">
              <TextInput label="Permanent address" value={form.permanent_address}
                onChange={set("permanent_address")}
                hint="Tenant's home address from the agreement" />
            </div>
            <TextInput label="Unit / flat" value={form.unit_label} onChange={set("unit_label")}
              hint="Matched to an existing unit, or created" />
            <NumberInput label="Monthly rent (₹)" value={form.monthly_rent}
              onChange={set("monthly_rent")} />
            <NumberInput label="Deposit / advance (₹)" value={form.deposit}
              onChange={set("deposit")} />
            <TextInput label="Move-in / start date" type="date" value={form.start_date}
              onChange={set("start_date")} />
            <TextInput label="End date" type="date" value={form.end_date}
              onChange={set("end_date")} />
            <NumberInput label="Contract length (months)" min={1} max={600}
              value={form.lease_months} onChange={set("lease_months")}
              hint="Reminds you to raise rent on renewal" />
            <NumberInput label="Rent increase on renewal (%)" min={0} max={100}
              value={form.rent_increase_pct} onChange={set("rent_increase_pct")} />
            <NumberInput label="Rent due day" min={1} max={31} value={form.rent_due_day}
              onChange={set("rent_due_day")} />
          </div>
          <TextArea label="Terms summary" value={form.terms_summary}
            onChange={set("terms_summary")} />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={busy}>
              {busy ? "Saving…" : "Create tenant & lease"}
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}
