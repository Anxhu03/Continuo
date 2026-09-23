# Security Policy

Continuo treats data privacy, secret safety, and security as foundational requirements. Because Continuo captures, transfers, and manages AI conversation context, project decisions, and visual assets, maintaining strict tenant isolation and secure credential storage is paramount.

---

## Supported Versions

Only the latest release and the current `main` branch are actively supported with security patches and vulnerability assessments.

| Version | Supported          |
| ------- | ------------------ |
| `0.2.x` (main) | :white_check_mark: |
| `< 0.2.0`      | :x:                |

---

## Reporting a Vulnerability

If you discover a security vulnerability within Continuo, **please do not disclose it publicly** via public GitHub issues, discussions, or social media.

Instead, please report vulnerabilities via one of the following channels:

1. **GitHub Private Security Advisory**: Use the [Security Advisories tab](https://github.com/Anxhu03/Continuo/security/advisories/new) on GitHub to submit a confidential report.
2. **Email Disclosure**: Email the maintainers directly at `security@continuo.dev` or reach out via GitHub profile contact options.

### What to Include in Your Report
Please provide:
- A clear description of the vulnerability and its potential impact.
- Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
- Any affected endpoints, components (backend, browser extension, or database models), or versions.
- Your assessment of the severity (e.g., CVSS estimate).

### Our Response Timeline
- **Initial Acknowledgement**: Within 48 hours of receipt.
- **Triage & Assessment**: Within 5 business days.
- **Fix & Public Advisory**: Coordinated release schedule with credit to the reporter.

---

## Built-in Security Architecture

Continuo implements defense-in-depth across the application lifecycle:

### 1. Encryption at Rest
- Sensitive provider API keys (OpenAI, Anthropic, Google Gemini) stored in the database are encrypted at rest using **Fernet symmetric encryption (AES-128-CBC with PKCS7 padding and HMAC-SHA256 authentication)**.
- Encryption keys are loaded via the `ENCRYPTION_KEY` environment variable and never committed to version control.

### 2. Password Security
- User authentication leverages **Argon2id** password hashing (`argon2-cffi`), providing industry-standard resistance to GPU/ASIC brute-force attacks.
- JWT access tokens use short-lived HMAC-SHA256 signatures with customizable token lifetimes.

### 3. Strict Multi-Tenant Isolation
- All Context OS entities (`ContextGoal`, `ContextDecision`, `ContextTask`, `ContextTechnicalState`, `ContextImage`) are scoped to both `project_id` and the authenticated `user_id`.
- Foreign key references, visual asset associations, and decision superseding links are rigorously validated to prevent cross-tenant data leakage or IDOR (Insecure Direct Object Reference) vulnerabilities. Attempted cross-tenant access returns `403 Forbidden` or `404 Not Found`.

### 4. Secret Sanitization in Handoffs & Extraction
- Both the context handoff generator and the context extraction intelligence pipeline apply automated regex secret redaction.
- Detected secrets—including OpenAI API keys (`sk-...`), Anthropic keys (`sk-ant-...`), AWS access keys (`AKIA...`), GitHub personal access tokens (`ghp_...`), Bearer tokens, and private RSA/EC keys—are stripped and replaced with `[REDACTED_SECRET]` before output or storage.

### 5. Visual Asset Security
- Image uploads are restricted to supported MIME types (`image/png`, `image/jpeg`, `image/webp`, `image/gif`, `image/svg+xml`).
- Maximum upload size is strictly enforced (default: 10 MB).
- Image filenames are sanitized with UUID-prefixed path hashing to prevent directory traversal attacks (`../`).

---

## Contributor Security Guidelines

When contributing to Continuo:
- Never commit `.env`, `.pem`, `.key`, or credentials to Git. Continuo's `.gitignore` explicitly prevents environment files from being tracked.
- Always include automated regression tests for any authentication or authorization modifications.
- Ensure all new API endpoints enforce `get_current_user` dependency checks.
