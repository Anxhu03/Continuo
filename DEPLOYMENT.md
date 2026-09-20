# CONTINUO — Production Deployment & Live Infrastructure Guide

This guide provides complete instructions for transitioning Continuo to the live production domain: **`continuo.run.place`**.

---

## 1. System Architecture

```
[ End User Browser / Client ]
             │
             ├──► https://continuo.run.place       (Frontend CDN: Vercel / Cloudflare Pages)
             │
             ├──► https://api.continuo.run.place   (FastAPI Gateway: Render / Railway / Fly.io)
             │            │
             │            ▼
             │    [ PostgreSQL DB ]                (Supabase / Neon / AWS RDS)
             │
[ Chrome Extension MV3 ]
             └──► https://api.continuo.run.place/api/v1
```

- **Frontend**: Static Web Application (HTML5, Vanilla CSS, JS, Lenis, FontAwesome, WebFonts) served over global edge CDN with strict SSL/TLS.
- **Backend**: FastAPI ASGI Python Application running in a lightweight Docker container with 2+ Uvicorn workers and pooled database connections.
- **Database**: Managed PostgreSQL 15+ (Supabase / Neon / AWS RDS) with automatic table metadata provisioning and connection pooling.
- **Companion**: Manifest V3 Chrome Extension connecting strictly over secure HTTPS (`api.continuo.run.place`), with zero localhost references in the distribution package.

---

## 2. DNS Configuration (`continuo.run.place`)

Configure the following DNS records in your domain control panel:

| Record Type | Host / Name | Target / Destination | Purpose |
|-------------|-------------|----------------------|---------|
| `A` / `CNAME` | `@` (or `continuo.run.place`) | Provided by Frontend CDN (e.g., `76.76.21.21` or `cname.vercel-dns.com`) | Main Landing & Workspace |
| `CNAME` | `api` | Provided by Backend Provider (e.g., `continuo-api-xxxx.onrender.com`) | FastAPI Production Gateway |

---

## 3. Database Setup (Supabase / Neon / PostgreSQL)

1. Provision a PostgreSQL 15+ database on [Supabase](https://supabase.com) or [Neon](https://neon.tech).
2. Copy the database connection URI:
   ```
   postgresql://postgres:[PASSWORD]@[HOST]:5432/[DATABASE]
   ```
   *(Note: Continuo automatically normalizes legacy `postgres://` strings to `postgresql://`).*
3. Set connection pooling parameters:
   - `DB_POOL_SIZE=10`
   - `DB_MAX_OVERFLOW=20`
4. On startup, Continuo executes `Base.metadata.create_all()`, automatically provisioning all required tables (`users`, `projects`, `context_packages`, `context_versions`, `handoff_logs`). Alternatively, run Alembic migrations to apply or verify schema revisions:
   ```bash
   alembic upgrade head
   ```

---

## 4. Backend Deployment (Render / Railway / Docker)

### Deploy with Render (Recommended)
1. In [Render Dashboard](https://dashboard.render.com), click **New +** ➔ **Blueprint** (or **Web Service**).
2. Select repository `Anxhu03/Continuo`.
3. If using Web Service:
   - **Runtime**: `Docker`
   - **Health Check Path**: `/health`
   - **Port**: `8008`
4. Configure Environment Variables:
   ```ini
   ENVIRONMENT=production
   HOST=0.0.0.0
   PORT=8008
   FRONTEND_URL=https://continuo.run.place
   CORS_ORIGINS=https://continuo.run.place,https://api.continuo.run.place
   DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
   DB_POOL_SIZE=10
   DB_MAX_OVERFLOW=20
   SECRET_KEY=[generate-a-secure-64-character-hex-key]
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ALGORITHM=HS256
   CONTINUO_API_URL=https://api.continuo.run.place/api/v1
   ```
5. In Render **Settings** ➔ **Custom Domains**, add `api.continuo.run.place`.
6. Copy the provided CNAME target and add it to your DNS registrar for `api`.

### Health Check Endpoints
- Path: `GET /health` (or `GET /api/v1/health`)
- Expected HTTP response: `200 OK`
- JSON Payload:
  ```json
  {
    "status": "operational",
    "platform": "Continuo Context Layer",
    "version": "1.0.0",
    "environment": "production",
    "engine": "active"
  }
  ```

---

## 5. Frontend Deployment (Vercel / Cloudflare Pages)

### Deploy with Vercel (Recommended)
1. In [Vercel Dashboard](https://vercel.com), click **Add New...** ➔ **Project**.
2. Select repository `Anxhu03/Continuo`.
3. The included `vercel.json` automatically configures routes, security headers, and asset caching.
4. Click **Deploy**.
5. In **Project Settings** ➔ **Domains**, add `continuo.run.place`.
6. Configure your apex `@` DNS record to point to Vercel (A record `76.76.21.21` or CNAME `cname.vercel-dns.com`).

---

## 6. Chrome Web Store Packaging & Release

### Generate Zero-Localhost Release Archive
Run the automated packaging engine in `--production` mode:
```bash
python scripts/package-extension.py --production
```

This performs automated security audits and build steps:
1. Validates Manifest V3 schemas and icons.
2. Replaces development endpoints with `https://api.continuo.run.place/api/v1` and `https://continuo.run.place/`.
3. Sanitizes host permissions in `manifest.json`.
4. Executes a strict zero-localhost and zero-placeholder audit asserting 0 occurrences of local development and old domain strings.
5. Emits the release archive at:
   ```
   dist/continuo-extension.zip
   ```

### Chrome Web Store Submission
1. Navigate to the [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole).
2. Click **Upload new item** and select `dist/continuo-extension.zip`.
3. Follow the metadata guidelines in `CHROMEWEBSTORE.md` for description, privacy policy declaration (`PRIVACY.md`), and single-purpose justification.
4. Once Google approves the listing, update `config.js`:
   ```javascript
   const CHROME_EXTENSION_STORE_URL = "https://chromewebstore.google.com/detail/continuo/[STORE_ID]";
   ```

---

## 7. Post-Deployment Verification Checklist

- [ ] `curl -I https://continuo.run.place` returns `200 OK` with valid SSL certificate.
- [ ] `curl https://api.continuo.run.place/health` returns `200 OK` with `"environment": "production"`.
- [ ] `curl https://continuo.run.place/robots.txt` returns public search engine rules.
- [ ] `curl https://continuo.run.place/sitemap.xml` returns valid XML index.
- [ ] Account registration (`POST /api/v1/auth/register`) creates a user in PostgreSQL.
- [ ] Project creation (`POST /api/v1/projects`) persists in database.
- [ ] Unhandled backend exceptions return sanitized 500 JSON without stack trace leakage.
- [ ] Chrome Extension connects to `https://api.continuo.run.place/api/v1` and displays green "Ready" status.
