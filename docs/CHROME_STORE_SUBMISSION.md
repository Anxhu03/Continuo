# Chrome Web Store Submission & Distribution Package

This document contains all official store metadata, permission justifications, privacy declarations, and review guidelines prepared for publishing the **Continuo Context Continuity Companion** extension to the Google Chrome Web Store.

---

## 1. Store Listing Metadata

- **Extension Name**: `Continuo — Context Continuity Companion`
- **Category**: `Productivity / Developer Tools`
- **Short Description** (132 characters max):
  ```
  Save your AI context across ChatGPT, Claude, and Gemini with one click. Never re-explain your project again.
  ```
- **Version**: `1.0.0`
- **Manifest Version**: `3` (Manifest V3 Verified)
- **Primary Language**: English

### Detailed Store Description
```markdown
Continuo preserves the working context behind your AI conversations and lets you continue seamlessly across ChatGPT, Claude, and Gemini without explaining your project from scratch.

### The Problem
When working with AI models, switching between tools (e.g. from ChatGPT to Claude or Gemini) requires re-explaining requirements, decisions, constraints, and past progress. This wastes time, increases prompt fatigue, and burns valuable context window tokens.

### The Solution: Working State, Not Raw Chat
Continuo doesn't just copy raw chat transcripts. Its Context Engine automatically distills active AI dialogue into structured Project Memory:
• What you are building (core objective)
• Architectural decisions already made
• Constraints and requirements
• Completed tasks vs. pending work
• Known problems, bugs, and discarded approaches
• Immediate next steps

### How It Works in 3 Steps:
1. Work in ChatGPT, Claude, or Google Gemini as usual.
2. Click the Continuo extension icon in your Chrome toolbar.
3. Click "Save Context" — Continuo extracts your working state and updates your Project Memory.
4. Click "Continue with Claude", "Continue with ChatGPT", or "Continue with Gemini" to copy an optimized, token-efficient continuation prompt and jump directly into your next model.

### Key Features:
• 1-Click Context Capture: Automatic provider detection on chatgpt.com, claude.ai, and gemini.google.com.
• Universal Cross-Model Handoff: Generates clean, model-tailored continuation prompts.
• Project Memory: Persistent, structured tracking of your engineering milestones.
• Private & Secure: Your context is stored in your own authenticated project space. Zero plaintext secrets. We never sell your data or use it for AI model training.
• Zero Distraction: The popup is designed to be fast, minimal, and clean. All heavy extraction happens server-side.
```

---

## 2. Single Purpose Statement

> **Single Purpose**:
> Continuo has one explicit, singular purpose: to extract active working context from AI chat interfaces upon user request, and generate formatted continuation payloads so users can continue their work across different AI platforms without re-explaining prior steps.

---

## 3. Permissions Justification

| Permission | Purpose & Strict Necessity |
| :--- | :--- |
| `activeTab` | Required strictly to read the active conversation DOM when the user explicitly clicks the Continuo action icon or the "Save Context" button. Continuo does **not** read browsing data continuously or on tabs other than the actively focused tab. |
| `storage` | Required to store the user's selected active project ID and extension UI preferences locally on the device for a seamless experience. |
| `scripting` | Required to execute the content extraction script in the active tab to retrieve conversation turns only when triggered by the user. |

---

## 4. Host Permissions Justification

| Host Pattern | Necessity & Scope |
| :--- | :--- |
| `https://chatgpt.com/*` | Official domain of OpenAI ChatGPT. Allows the extension to extract conversation turns when the user clicks "Save Context". |
| `https://chat.openai.com/*` | Legacy domain of OpenAI ChatGPT. Retained to ensure compatibility for users on older session bookmarks. |
| `https://claude.ai/*` | Official domain of Anthropic Claude. Allows the extension to extract conversation turns when the user clicks "Save Context". |
| `https://gemini.google.com/*` | Official domain of Google Gemini. Allows the extension to extract conversation turns when the user clicks "Save Context". |
| `http://127.0.0.1:8008/*` / `http://localhost:8008/*` | Local development API gateway endpoints used strictly during developer testing and local sandboxes. |

*Note: No broad wildcards (`<all_urls>` or `*://*/*`) are requested. Only specific AI interface URLs and the backend API are permitted.*

---

## 5. Privacy & Data Handling Declarations

- **Data Collection**: Continuo collects text content from conversations on supported AI websites **only when explicitly triggered by the user** clicking "Save Context".
- **Zero Background Surveillance**: The extension is completely dormant until the user interacts with the extension popup.
- **No Third-Party Brokers**: Data is transmitted securely over TLS to the user's authenticated Continuo backend instance. It is never sold, shared with advertising brokers, or used for training AI foundation models.
- **User Ownership & Right to Deletion**: Users have complete ownership over their projects and can delete projects and associated context packages at any time via the API or workspace interface.

---

## 6. Pre-Submission Checklist

- [x] Manifest V3 compliant (`manifest_version: 3`).
- [x] No `eval()` or remote code execution.
- [x] Extension icons provided in required sizes (128x128 verified).
- [x] Zero API keys, passwords, or backend secrets bundled in the client package.
- [x] Deterministic build script verified (`python scripts/package-extension.py`).
- [x] Clean archive generated at `dist/continuo-extension.zip`.
- [x] Comprehensive automated unit & end-to-end test suite passing.
