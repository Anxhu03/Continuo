# Chrome Web Store Listing & Publishing Specification

This document is the single source of truth for the official Chrome Web Store listing of the **Continuo Context Continuity Companion** extension.

---

## 1. Store Listing Metadata

| Field | Specification |
| :--- | :--- |
| **Extension Name** | `Continuo — Context Continuity Companion` |
| **Short Description** (max 132 chars) | `Capture and sync your project context across ChatGPT, Claude, and Gemini with one click. Never re-explain your work.` *(113 chars)* |
| **Category** | `Productivity` / `Developer Tools` |
| **Default Language** | `English` |
| **Manifest Version** | `Manifest V3` |
| **Version** | `1.0.0` |

---

## 2. Detailed Store Description

```markdown
Continuo keeps your project context alive across AI assistants.

Switching between ChatGPT, Claude, and Gemini usually means losing all your hard-earned context, repeating constraints, and re-explaining architectural decisions. Continuo eliminates this friction with a focused, extension-first companion.

HOW IT WORKS:
1. Have a conversation in ChatGPT, Claude, or Google Gemini.
2. Click the Continuo extension icon in your toolbar.
3. Select or create a Project (e.g. "React Dashboard" or "Backend Migration").
4. Click "Save Context" — Continuo extracts technical decisions, active constraints, code context, and next steps into Project Memory.
5. Click "Continue with Claude", "Continue with ChatGPT", or "Continue with Gemini" — Continuo copies a standardized 11-section continuation payload to your clipboard and opens the destination AI.
6. Press Ctrl+V (or Cmd+V) to resume your work instantly without re-explanation.

KEY CAPABILITIES:
• Live Active Tab Detection: Automatically identifies conversations on ChatGPT, Claude, and Gemini.
• Intelligent Noise Filtering: Strips conversational chatter, button labels, and feedback chips.
• User-Scoped Project Memory: Organizes decisions, pending work, constraints, and files by project.
• Versioned Memory Engine: Tracks project evolution across sessions (v1.0 → v1.1 → v1.2) with clear diffs.
• Zero-Noise Continuation Schema: Formats handoffs with 11 structured sections (Objective, Current State, Completed Work, Constraints, Next Steps) that any LLM understands immediately.
• Honest & Transparent: No fragile automated typing or hidden browser scripts. You stay in control with 1-click clipboard continuation.
• Privacy-First Architecture: Zero tracking scripts, zero ads, and zero data brokering. Your context is stored strictly in your user-scoped project memory.

SUPPORTED PLATFORMS:
• OpenAI ChatGPT (chatgpt.com & chat.openai.com)
• Anthropic Claude (claude.ai)
• Google Gemini (gemini.google.com)

Keep your context. Continue anywhere.
```

---

## 3. Permissions Justification

The Chrome Web Store review process requires an exact, plain-English justification for each declared permission. Vague statements like "needed for extension to work" will be rejected.

| Permission | Review Justification |
| :--- | :--- |
| `activeTab` | Required to detect whether the user is actively viewing a supported conversational AI provider (ChatGPT, Claude, or Gemini) when opening the extension popup. |
| `storage` | Required to store the user's authentication token and last-selected project ID locally in Chrome (`chrome.storage.local`) for cross-tab persistence. |
| `scripting` | Required to execute content scripts that extract visible dialogue turns from the active AI chat interface upon user request. |
| `clipboardWrite` | Required to copy the structured 11-section continuation context directly to the user's system clipboard when they click a "Continue with [AI]" action. |
| `tabs` | Required to synchronize session login states across open Continuo tabs and locate destination AI windows. |

### Host Permissions Justification

| Host Pattern | Review Justification |
| :--- | :--- |
| `https://chatgpt.com/*` | Required to extract active dialogue turns and conversation state when saving context from ChatGPT. |
| `https://chat.openai.com/*` | Required to support legacy ChatGPT URLs during dialogue turn capture. |
| `https://claude.ai/*` | Required to extract user messages and assistant responses when saving context from Claude conversations. |
| `https://gemini.google.com/*` | Required to extract queries and model responses when saving context from Google Gemini. |
| `http://127.0.0.1:8008/*` | Required to communicate with the local Continuo Context Engine gateway for context synthesis and storage. |
| `http://localhost:8008/*` | Required for local development and self-hosted gateway connectivity on port 8008. |
| `http://127.0.0.1:8000/*` | Secondary fallback port for local Continuo gateway connectivity. |
| `http://localhost:8000/*` | Secondary fallback port for local development workspace connectivity. |

---

## 4. Privacy & Data Handling Disclosures

| Disclosure Item | Response | Detail |
| :--- | :--- | :--- |
| **Single Purpose** | Yes | Context continuity across conversational AI platforms. |
| **Personally Identifiable Info** | No | Continuo does not collect personal identity or biometric data. |
| **Health / Financial Information** | No | None collected. |
| **Authentication Info** | Yes | User email and password hash for optional account creation and project sync. |
| **User Activity / Browsing History** | No | Continuo only inspects URLs of supported AI domains on active tabs. |
| **Website Content** | Yes | Extracts user-initiated conversational text from supported AI tabs to build project memory. |
| **Data Selling Policy** | No | Continuo never sells, rents, or monetizes user data under any circumstance. |
| **Data Transfer Policy** | No | Data is not transferred to unrelated third parties or advertising networks. |

---

## 5. Asset & Visual Checklist

- [x] **16×16 Icon**: `extension/assets/icon16.png` (PNG, 16×16 px)
- [x] **32×32 Icon**: `extension/assets/icon32.png` (PNG, 32×32 px)
- [x] **48×48 Icon**: `extension/assets/icon48.png` (PNG, 48×48 px)
- [x] **128×128 Icon**: `extension/assets/icon128.png` (PNG, 128×128 px)
- [ ] **Store Screenshot 1**: 1280×800 px — Extension popup detecting ChatGPT with conversation turns ready.
- [ ] **Store Screenshot 2**: 1280×800 px — One-click Save Context and continuation target picker.
- [ ] **Store Screenshot 3**: 1280×800 px — Web Workspace Project Memory with 10 structured fields.
- [ ] **Small Promo Tile**: 440×280 px (PNG)
- [ ] **Marquee Promo Tile**: 1400×560 px (Optional)

---

## 6. Pre-Submission Packaging Command

Run the deterministic packager:
```bash
python scripts/package-extension.py
```
Output archive: `dist/continuo-extension.zip`
