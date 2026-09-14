# CONTINUO — Production Deployment & Live Infrastructure Guide

This guide provides complete instructions for transitioning Continuo from local development to a live, secure, high-availability production environment.

---

## 1. System Architecture

```
[ End User Browser / Client ]
             │
             ├──► https://continuo.ai           (Frontend CDN: Cloudflare Pages / Vercel / S3)
             │
             ├──► https://api.continuo.ai       (FastAPI Gateway: Railway / Render / Fly.io / ECS)
             │            │
             │            ▼
             │    [ PostgreSQL DB ]             (Supabase / Neon / AWS RDS)
             │
[ Chrome Extension MV3 ]
             └──► https://api.continuo.ai/api/v1
```

- **Frontend**: Static Web Application (HTML5, Vanilla CSS, JS, Lenis, FontAwesome, WebFonts) served over global edge CDN with strict SSL/TLS.
- **Backend**: FastAPI ASGI Python Application running in a lightweight Docker container with 2+ Uvicorn workers and pooled database connections.
- **Database**: Managed PostgreSQL 15+ (Supabase / Neon / AWS RDS) with automatic table metadata provisioning and connection pooling.
- **Companion**: Manifest V3 Chrome Extension connecting strictly over secure HTTPS (`api.continuo.ai`), with zero localhost references in the distribution package.

---

## 2. Prerequisites & Domain Requirements

> [!IMPORTANT]
> **Domain Status**: `DOMAIN REQUIRED`
> Continuo requires a domain name (e.g. `continuo.ai`) with DNS control to configure HTTPS and subdomains. If deploying to staging first, use platform-provided domains (e.g. `*.railway.app`, `*.pages.dev`).

### DNS Records Configuration
| Type | Name | Target / Value | Purpose |
|------|------|----------------|---------|
| `A` / `CNAME` | `@` | Frontend CDN Edge IP / URL | Main Landing & Workspace |
| `CNAME` | `www` | `continuo.ai` | Canonical redirect |
| `CNAME` | `api` | Backend Server Target (e.g. `app.railway.app`) | FastAPI Production Gateway |

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
4. On startup, Continuo executes `Base.metadata.create_all()`, automatically provisioning all required tables (`users`, `projects`, `context_packages`, `context_versions`, `handoff_logs`).

---

## 4. Backend Deployment (Docker / FastAPI)

### Build & Run Locally with Docker
```bash
# Build the production container
docker build -t continuo-backend:latest .

# Run container with production environment variables
docker run -d -p 8008:8008 \
  --name continuo-api \
  --env-file .env \
  continuo-backend:latest
```

### Production Environment Variables
Configure the following in your hosting provider's dashboard:

```ini
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8008
FRONTEND_URL=https://continuo.ai
CORS_ORIGINS=https://continuo.ai,https://www.continuo.ai,https://app.continuo.ai
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
SECRET_KEY=generate-a-secure-64-character-hex-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM=HS256
CONTINUO_API_URL=https://api.continuo.ai/api/v1
```

### Health Check Endpoint
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

## 5. Frontend Deployment (Cloudflare Pages / Vercel / Static CDN)

Deploy the static web repository files to your CDN:
- Root directory contains `index.html`, `styles.css`, `main.js`, `config.js`, `install.html`, `install.css`, `robots.txt`, `sitemap.xml`, and the `assets/` directory.

### Production Endpoint Configuration (`config.js`)
In `config.js`, set `CONTINUO_API_URL` to your production backend URL:
```javascript
const CONTINUO_API_URL = "https://api.continuo.ai/api/v1";
```
*(When set, all browser sessions communicate with your secure cloud backend).*

---

## 6. Chrome Web Store Packaging & Release

### Generate Zero-Localhost Release Archive
Run the automated packaging engine in `--production` mode:
```bash
python scripts/package-extension.py --production
```

This performs automated security audits and build steps:
1. Validates Manifest V3 schemas and icons.
2. Replaces all development ports (`8008`, `8000`) and localhost IP addresses (`127.0.0.1`) with `https://api.continuo.ai` and `https://continuo.ai`.
3. Sanitizes host permissions in `manifest.json`.
4. Executes a strict zero-localhost audit asserting 0 occurrences of local development strings.
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
   The landing page and installation guide automatically transition to official "Add to Chrome" mode.

---

## 7. Post-Deployment Verification Checklist

- [ ] `curl -I https://continuo.ai` returns `200 OK` with valid SSL certificate.
- [ ] `curl https://api.continuo.ai/health` returns `200 OK` with `"environment": "production"`.
- [ ] `curl https://continuo.ai/robots.txt` returns public search engine rules.
- [ ] `curl https://continuo.ai/sitemap.xml` returns valid XML index.
- [ ] Account registration (`POST /api/v1/auth/register`) creates a user in PostgreSQL.
- [ ] Project creation (`POST /api/v1/projects`) persists in database.
- [ ] Unhandled backend exceptions return sanitized 500 JSON without stack trace leakage.
- [ ] Chrome Extension connects to `https://api.continuo.ai/api/v1` and displays green "Ready" status.
