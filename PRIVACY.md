# Continuo Privacy Policy

**Effective Date:** September 14, 2026  
**Last Updated:** September 14, 2026

Continuo ("we", "our", or "the application") is committed to building honest, transparent software that protects your intellectual property and conversational privacy. This Privacy Policy details what information Continuo accesses, processes, stores, and retains, and how you retain total ownership over your data.

---

## 1. What Information Continuo Collects & Processes

Continuo only accesses conversational data upon an **explicit user gesture** (clicking the "Save Context" button in the extension companion). It does not monitor background browsing or record unprompted page activity.

### A. Conversation Dialogue
- **When Accessed:** Only when you click "Save Context" while on an active tab of a supported provider (`chatgpt.com`, `claude.ai`, or `gemini.google.com`).
- **What is Captured:** Visible conversation turns (User prompts and Assistant responses) in the active chat thread.
- **Why it is Processed:** To synthesize project memory: extracting technical decisions, active architecture constraints, pending requirements, files in scope, and next steps.
- **Noise Stripping:** Extraneous UI text (copy buttons, thumbs-up ratings, model disclaimers) is filtered out before processing.

### B. Account & Authentication Information
- **Account Creation (Optional):** If you register an account, we store your email address, hashed password (salted bcrypt), and full name.
- **Session Tokens:** Authentication JSON Web Tokens (`continuo_jwt`) and user profiles are stored locally in your browser (`localStorage` and `chrome.storage.local`).
- **No Third-Party Trackers:** Continuo does not include third-party advertising SDKs, Google Analytics, telemetry beacons, or fingerprinting scripts.

---

## 2. Where Context is Stored

- **Local Extension Storage:** Your active project ID and authenticated session token are kept in Chrome's isolated `chrome.storage.local`.
- **Database Persistence:** Project context packages, version diffs, decisions, and constraints are stored in your user-scoped SQLite/PostgreSQL database via the Continuo Context Engine backend.
- **Multi-Tenant Isolation:** Database records are strictly foreign-keyed to your unique user ID (`user_id`). Users cannot read, modify, or generate handoffs for any other user's projects.

---

## 3. Data Sharing & Third-Party Disclosure

- **Zero Data Selling:** We do not sell, rent, trade, or monetize your context, personal data, or conversation transcripts.
- **Zero Cross-Site Tracking:** We do not track your browsing history across other websites.
- **Destination AI Handoffs:** When you initiate a continuation (e.g. "Continue with Claude"), Continuo copies a formatted Markdown payload to your local system clipboard and opens the destination AI URL in a new tab. Continuo does not transmit data directly to third-party AI APIs on your behalf without your involvement.

---

## 4. Retention & Deletion Rights

- **Data Retention:** Context packages and project history remain saved until you delete them.
- **Project Deletion:** You can delete any project and its entire associated memory history directly within the Continuo Workspace.
- **Local Cache Clearance:** Signing out of the Continuo Web App or Extension immediately purges cached JWT tokens and user metadata from `localStorage` and `chrome.storage.local`.

---

## 5. Security Practices

- **Minimal Extension Permissions:** Continuo operates under Google Manifest V3, requesting only strictly necessary capabilities (`activeTab`, `storage`, `scripting`, `clipboardWrite`, `tabs`).
- **Stateless Verification:** APIs authenticate requests via standard Bearer token validation with strict role-based access control (RBAC).
- **HTTPS & Encryption:** All external communication is enforced over HTTPS.

---

## 6. Contact & Support

For privacy inquiries, questions regarding data handling, or security disclosures:
- GitHub Repository: [https://github.com/Anxhu03/Continuo](https://github.com/Anxhu03/Continuo)
- Documentation: [CHROMEWEBSTORE.md](CHROMEWEBSTORE.md)
