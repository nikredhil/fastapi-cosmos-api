# Deploying RentWise to wiserent.in

RentWise is two apps: a **FastAPI backend** and a **Vite/React frontend**. They
deploy separately and the domain points at both.

- Frontend → **Vercel** at `https://wiserent.in`
- Backend → **Render** at `https://api.wiserent.in`

Repo: `nikredhil/fastapi-cosmos-api`, branch `rentwise-rebuild`.

---

## 1. Backend on Render

1. Render → **New → Blueprint** → select this repo. It reads [`render.yaml`](./render.yaml)
   and creates the `rentwise-api` web service.
2. Set the secret env vars in the dashboard:
   - `ANTHROPIC_API_KEY` — for contract photo parsing (optional; without it the
     app falls back to manual entry).
   - If using Cosmos: set `DB_BACKEND=cosmos`, `COSMOS_ENDPOINT`, `COSMOS_KEY`,
     `COSMOS_DATABASE=rentwise`.
3. Deploy. Note the service URL (e.g. `https://rentwise-api.onrender.com`) and
   confirm `…/health` returns `{"status":"ok"}`.
4. Add the custom domain `api.wiserent.in` (Settings → Custom Domains). Render
   shows the CNAME target to use in step 3 of DNS below.

> **Persistence:** the Render *free* plan filesystem is ephemeral — data resets
> on restart. For real use, either upgrade the instance and uncomment the `disk:`
> block in `render.yaml`, or switch to Cosmos (`DB_BACKEND=cosmos`).

## 2. Frontend on Vercel

1. Vercel → **Add New → Project** → import this repo.
2. Set **Root Directory = `frontend`** (framework auto-detects as Vite; build
   settings come from [`frontend/vercel.json`](./frontend/vercel.json), which
   also rewrites all routes to `index.html` so deep links work).
3. Add an environment variable:
   - `VITE_API_BASE = https://api.wiserent.in`
4. Deploy. Then **Settings → Domains → Add** `wiserent.in` **and** `www.wiserent.in`.
   Vercel shows the exact A/CNAME values to use below.

## 3. GoDaddy DNS

GoDaddy → your domain → **DNS**. Add (use the exact targets Vercel/Render show —
they can differ from these defaults):

| Type  | Name  | Value                          | Points to        |
|-------|-------|--------------------------------|------------------|
| A     | `@`   | `76.76.21.21`                  | Vercel (apex)    |
| CNAME | `www` | `cname.vercel-dns.com`         | Vercel (www)     |
| CNAME | `api` | `rentwise-api.onrender.com`    | Render (backend) |

DNS can take 5–30 min to propagate. HTTPS certificates are issued automatically
by both Vercel and Render once the records resolve.

## 4. Verify

- `https://api.wiserent.in/health` → `{"status":"ok"}`
- `https://wiserent.in` loads, you can register/sign in, and the dashboard reads
  from the API (check the browser Network tab hits `api.wiserent.in`).
- If API calls are blocked by CORS, confirm `CORS_ORIGINS` on Render includes
  exactly `https://wiserent.in` (and `https://www.wiserent.in`).

---

## Environment variables (backend)

| Var | Purpose | Example |
|-----|---------|---------|
| `ENVIRONMENT` | run mode | `prod` |
| `CORS_ORIGINS` | allowed frontend origins (comma-separated) | `https://wiserent.in,https://www.wiserent.in` |
| `DB_BACKEND` | `file` \| `cosmos` \| `memory` | `file` |
| `DATA_DIR` / `UPLOADS_DIR` | file-backend + image storage paths | `/var/data` |
| `JWT_SECRET` | signs local-account tokens | (generated) |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` | contract parsing | `claude-opus-4-8` |
| `COSMOS_ENDPOINT` / `COSMOS_KEY` / `COSMOS_DATABASE` | only if `DB_BACKEND=cosmos` | |

## Frontend

| Var | Purpose | Example |
|-----|---------|---------|
| `VITE_API_BASE` | backend base URL (baked in at build) | `https://api.wiserent.in` |
