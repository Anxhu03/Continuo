/**
 * CONTINUO — Chrome Extension Content Script
 * Robust, honest DOM extraction & cross-AI continuation receiver.
 * Modular adapters for ChatGPT, Claude, and Gemini with normalized data output.
 */

// --- 1. DEBUG INSTRUMENTATION ---
function debugLog(event, metadata = {}) {
  try {
    const isDebug = Boolean(
      (typeof window !== "undefined" && window.__CONTINUO_DEBUG__) ||
      (typeof localStorage !== "undefined" && localStorage.getItem("CONTINUO_DEBUG") === "true")
    );
    if (isDebug) {
      const entry = {
        event,
        timestamp: new Date().toISOString(),
        metadata: { ...metadata }
      };
      if (typeof window !== "undefined") {
        window.__CONTINUO_DEBUG_LOGS__ = window.__CONTINUO_DEBUG_LOGS__ || [];
        window.__CONTINUO_DEBUG_LOGS__.push(entry);
        if (window.__CONTINUO_DEBUG_LOGS__.length > 100) {
          window.__CONTINUO_DEBUG_LOGS__.shift();
        }
      }
      console.log(`[Continuo Debug] ${event}:`, metadata);
    }
  } catch (e) {
    // Suppress logging errors
  }
}

// --- 2. TEXT CLEANING UTILITY ---
function cleanTurnText(str) {
  if (!str) return "";
  return str
    .replace(/\b(Copy code|Copy to clipboard|Copy|Edit|Share|Regenerate response|Regenerate|Read aloud|Was this response better or worse\?|Retry|Thumbs up|Thumbs down|Show thinking|Hide thinking)\b/gi, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

// --- 3. BASE PROVIDER ADAPTER ---
class BaseAdapter {
  constructor(provider) {
    this.provider = provider;
  }
  detect() { return false; }
  getConversationId() { return null; }
  getConversationTitle() { return document.title || `${this.provider.toUpperCase()} Conversation`; }
  isConversationReady() { return this.extractMessages().length > 0; }
  extractMessages() { return []; }
  getInputElement() { return null; }

  getNormalizedData() {
    return {
      provider: this.provider,
      conversation_id: this.getConversationId(),
      title: this.getConversationTitle(),
      url: window.location.href,
      messages: this.extractMessages()
    };
  }
}

// --- 4. CHATGPT ADAPTER ---
class ChatGPTAdapter extends BaseAdapter {
  constructor() {
    super("chatgpt");
  }

  detect() {
    const host = window.location.hostname;
    return host.includes("chatgpt.com") || host.includes("chat.openai.com");
  }

  getConversationId() {
    const path = window.location.pathname;
    const match = path.match(/\/(?:c|share|g\/[^/]+\/c)\/([a-zA-Z0-9-]+)/);
    return match ? match[1] : null;
  }

  getConversationTitle() {
    let title = document.title ? document.title.replace(/\s*[-–|]\s*ChatGPT.*$/i, "").trim() : "";
    if (!title || title.toLowerCase() === "chatgpt") {
      const headerTitle = document.querySelector("#conversation-header h1, header h1, nav a[aria-current='page']");
      if (headerTitle && headerTitle.textContent.trim()) {
        title = headerTitle.textContent.trim();
      }
    }
    return title || "ChatGPT Conversation";
  }

  extractMessages() {
    const messages = [];

    // Strategy 1: Data attributes (Standard across all modern ChatGPT versions)
    const roleNodes = document.querySelectorAll("[data-message-author-role]");
    if (roleNodes.length > 0) {
      roleNodes.forEach((node) => {
        const rawRole = node.getAttribute("data-message-author-role");
        const role = rawRole === "user" ? "user" : "assistant";
        const contentEl = node.querySelector(".markdown, .whitespace-pre-wrap, div[dir='auto']") || node;
        const text = cleanTurnText(contentEl.innerText);
        if (text && text.length > 1) {
          messages.push({ role, content: text });
        }
      });
      if (messages.length > 0) return messages;
    }

    // Strategy 2: Article turn containers
    const turnArticles = document.querySelectorAll("article, [data-testid^='conversation-turn']");
    if (turnArticles.length > 0) {
      turnArticles.forEach((art) => {
        if (art.tagName === "MAIN") return;
        let role = "assistant";
        if (
          art.querySelector("[data-message-author-role='user']") ||
          art.querySelector("[data-user='true']") ||
          (art.querySelector(".whitespace-pre-wrap") && !art.querySelector(".markdown, .prose"))
        ) {
          role = "user";
        }
        const contentEl = art.querySelector(".markdown, .prose, .whitespace-pre-wrap, div[dir='auto']") || art;
        const text = cleanTurnText(contentEl.innerText);
        if (text && text.length > 1) {
          messages.push({ role, content: text });
        }
      });
      if (messages.length > 0) return messages;
    }

    // Strategy 3: Elements with data-message-id
    const msgIdNodes = document.querySelectorAll("[data-message-id]");
    if (msgIdNodes.length > 0) {
      msgIdNodes.forEach((node) => {
        const role = node.getAttribute("data-message-author-role") ||
                     (node.querySelector(".markdown") ? "assistant" : "user");
        const text = cleanTurnText(node.innerText);
        if (text && text.length > 1) {
          messages.push({ role, content: text });
        }
      });
      if (messages.length > 0) return messages;
    }

    return messages;
  }

  getInputElement() {
    return (
      document.querySelector("#prompt-textarea") ||
      document.querySelector("div[contenteditable='true']#prompt-textarea") ||
      document.querySelector("textarea[data-id='root']") ||
      document.querySelector("main div[contenteditable='true']") ||
      document.querySelector("main textarea")
    );
  }
}

// --- 5. CLAUDE ADAPTER ---
class ClaudeAdapter extends BaseAdapter {
  constructor() {
    super("claude");
  }

  detect() {
    return window.location.hostname.includes("claude.ai");
  }

  getConversationId() {
    const path = window.location.pathname;
    const match = path.match(/\/chat\/([0-9a-fA-F-]+)/);
    return match ? match[1] : null;
  }

  getConversationTitle() {
    let title = document.title ? document.title.replace(/\s*[-–|]\s*Claude.*$/i, "").trim() : "";
    if (!title || title.toLowerCase() === "claude") {
      const headerTitle = document.querySelector("button[data-testid='chat-title-button'], header h1, nav [aria-current='page']");
      if (headerTitle && headerTitle.textContent.trim()) {
        title = headerTitle.textContent.trim();
      }
    }
    return title || "Claude Conversation";
  }

  extractMessages() {
    const messages = [];

    // Strategy 1: Data test IDs and message font classes
    const turnNodes = document.querySelectorAll(
      "[data-testid='user-message'], [data-testid='assistant-message'], .font-user-message, .font-claude-message, div[class*='font-user'], div[class*='font-claude'], div[class*='UserMessage'], div[class*='AssistantMessage']"
    );
    if (turnNodes.length > 0) {
      turnNodes.forEach((node) => {
        const isUser = node.matches(
          "[data-testid='user-message'], .font-user-message, div[class*='font-user'], div[class*='UserMessage'], [data-author='human']"
        );
        const role = isUser ? "user" : "assistant";
        const text = cleanTurnText(node.innerText);
        if (text && text.length > 1) {
          messages.push({ role, content: text });
        }
      });
      if (messages.length > 0) return messages;
    }

    // Strategy 2: Claude streaming & markdown containers
    const rows = document.querySelectorAll("main div[data-is-streaming], main .grid-cols-1 > div, main div[class*='message']");
    if (rows.length > 0) {
      rows.forEach((row) => {
        const text = cleanTurnText(row.innerText);
        if (text && text.length > 5 && !text.includes("What can I help you with today?")) {
          const isUser = row.querySelector(".font-user-message") ||
                         row.matches("div[class*='user']") ||
                         (!row.querySelector(".standard-markdown, .prose") && text.length < 500);
          messages.push({ role: isUser ? "user" : "assistant", content: text });
        }
      });
      if (messages.length > 0) return messages;
    }

    // Strategy 3: Chat scroll container paragraphs
    const proseNodes = document.querySelectorAll("main .prose, main .standard-markdown, main div.whitespace-pre-wrap");
    if (proseNodes.length > 0) {
      proseNodes.forEach((p) => {
        const text = cleanTurnText(p.innerText);
        if (text && text.length > 5 && !text.includes("What can I help you with today?")) {
          const isAssistant = p.matches(".prose, .standard-markdown") || p.closest(".prose");
          messages.push({ role: isAssistant ? "assistant" : "user", content: text });
        }
      });
    }

    return messages;
  }

  getInputElement() {
    return (
      document.querySelector("div.ProseMirror[contenteditable='true']") ||
      document.querySelector("div[contenteditable='true'][data-placeholder]") ||
      document.querySelector("fieldset div[contenteditable='true']") ||
      document.querySelector("main div[contenteditable='true']") ||
      document.querySelector("textarea[placeholder*='Reply']") ||
      document.querySelector("textarea")
    );
  }
}

// --- 6. GEMINI ADAPTER (REFERENCE IMPLEMENTATION) ---
class GeminiAdapter extends BaseAdapter {
  constructor() {
    super("gemini");
  }

  detect() {
    return window.location.hostname.includes("gemini.google.com");
  }

  getConversationId() {
    const path = window.location.pathname;
    const match = path.match(/\/app\/([a-zA-Z0-9_-]+)/);
    return match ? match[1] : null;
  }

  getConversationTitle() {
    const title = document.title ? document.title.replace(/\s*[-–|]\s*Google Gemini.*$/i, "").replace(/\s*[-–|]\s*Gemini.*$/i, "").trim() : "";
    return title || "Google Gemini Conversation";
  }

  extractMessages() {
    const messages = [];
    const queryNodes = document.querySelectorAll(".user-query, .query-text, user-query-content, .query-content");
    const responseNodes = document.querySelectorAll(".model-response, .response-content, message-content, .model-response-text");

    const maxCount = Math.max(queryNodes.length, responseNodes.length);
    for (let i = 0; i < maxCount; i++) {
      if (queryNodes[i]) {
        const uText = cleanTurnText(queryNodes[i].innerText);
        if (uText) {
          messages.push({ role: "user", content: uText });
        }
      }
      if (responseNodes[i]) {
        const aText = cleanTurnText(responseNodes[i].innerText);
        if (aText) {
          messages.push({ role: "assistant", content: aText });
        }
      }
    }
    return messages;
  }

  getInputElement() {
    return (
      document.querySelector("rich-textarea .ql-editor[contenteditable='true']") ||
      document.querySelector("div[contenteditable='true'][aria-label*='Enter a prompt']") ||
      document.querySelector("div[contenteditable='true'][aria-label*='prompt']") ||
      document.querySelector("textarea[aria-label*='prompt']")
    );
  }
}

// --- 7. ADAPTER REGISTRY ---
const adapters = [
  new ChatGPTAdapter(),
  new ClaudeAdapter(),
  new GeminiAdapter()
];

function getActiveAdapter() {
  for (const adapter of adapters) {
    if (adapter.detect()) return adapter;
  }
  return null;
}

// --- 8. STATE INSPECTION & EXTRACTION HANDLERS ---
function inspectConversationState() {
  const adapter = getActiveAdapter();
  if (!adapter) {
    return {
      success: true,
      provider: null,
      conversationFound: false,
      conversationId: null,
      messageCount: 0,
      snippet: "",
      title: document.title || "Unknown Page"
    };
  }

  const normalized = adapter.getNormalizedData();
  const messages = normalized.messages;
  let snippet = "";
  if (messages.length > 0) {
    const latest = messages[messages.length - 1];
    const prefix = latest.role === "user" ? "User: " : "Assistant: ";
    const fullText = prefix + latest.content;
    snippet = fullText.length > 130 ? fullText.substring(0, 127) + "..." : fullText;
  }

  const isReady = adapter.isConversationReady();

  debugLog("conversationDetected", {
    provider: normalized.provider,
    conversationDetected: isReady,
    messageCount: messages.length
  });

  return {
    success: true,
    provider: normalized.provider,
    conversationFound: isReady,
    conversationId: normalized.conversation_id,
    messageCount: messages.length,
    snippet,
    title: normalized.title
  };
}

function extractActiveConversation() {
  const adapter = getActiveAdapter();
  if (!adapter) {
    return {
      success: false,
      conversationFound: false,
      provider: null,
      title: document.title,
      rawTranscript: "",
      messages: [],
      messageCount: 0,
      charCount: 0,
      error: "No supported AI provider detected on this page."
    };
  }

  const normalized = adapter.getNormalizedData();
  const messages = normalized.messages;

  if (messages.length === 0) {
    return {
      success: false,
      conversationFound: false,
      provider: normalized.provider,
      conversationId: normalized.conversation_id,
      title: normalized.title,
      rawTranscript: "",
      messages: [],
      messageCount: 0,
      charCount: 0,
      error: "No conversation turns detected on this page."
    };
  }

  const turns = messages.map(m => `${m.role === "user" ? "User" : "Assistant"}: ${m.content}`);
  const rawTranscript = turns.join("\n\n");

  debugLog("extractionReady", {
    provider: normalized.provider,
    conversationDetected: true,
    messageCount: messages.length,
    charCount: rawTranscript.length
  });

  return {
    success: true,
    conversationFound: true,
    provider: normalized.provider,
    conversationId: normalized.conversation_id,
    title: normalized.title,
    rawTranscript,
    messages,
    messageCount: messages.length,
    charCount: rawTranscript.length
  };
}

// --- 9. CROSS-AI DESTINATION HANDOFF RECEIVER ---
function initHandoffReceiver() {
  const adapter = getActiveAdapter();
  if (!adapter || typeof chrome === "undefined" || !chrome.storage || !chrome.storage.local) {
    return;
  }

  chrome.storage.local.get(["continuo_pending_handoff"], (res) => {
    const pending = res?.continuo_pending_handoff;
    if (!pending || !pending.payload) return;

    // Verify handoff targets current provider and is fresh (< 2 minutes old)
    const isTarget = pending.provider === adapter.provider;
    const isFresh = Date.now() - (pending.timestamp || 0) < 120000;
    if (!isTarget || !isFresh) {
      return;
    }

    debugLog("destinationOpened", {
      provider: adapter.provider,
      sourceProvider: pending.sourceProvider
    });

    // Poll for the destination input element to become available
    let attempts = 0;
    const maxAttempts = 30; // 30 x 300ms = 9 seconds
    const pollTimer = setInterval(() => {
      attempts++;
      const inputEl = adapter.getInputElement();

      if (inputEl) {
        clearInterval(pollTimer);
        attemptPromptInsertion(inputEl, pending, adapter);
      } else if (attempts >= maxAttempts) {
        clearInterval(pollTimer);
        debugLog("pasteFailed", {
          provider: adapter.provider,
          reason: "input_element_not_found"
        });
        showHandoffFallbackBanner(pending, adapter, null);
      }
    }, 300);
  });
}

function attemptPromptInsertion(inputEl, pending, adapter) {
  debugLog("pasteAttempted", { provider: adapter.provider });
  const payload = pending.payload;
  let inserted = false;

  try {
    inputEl.focus();

    if (inputEl.isContentEditable) {
      // Method A: Standard execCommand insertText (best for ProseMirror / Lexical)
      try {
        inserted = document.execCommand("insertText", false, payload);
      } catch (e) {
        inserted = false;
      }

      // Method B: Synthetic InputEvent fallback
      if (!inserted || !inputEl.innerText || inputEl.innerText.length < 20) {
        try {
          const inputEvent = new InputEvent("beforeinput", {
            bubbles: true,
            cancelable: true,
            inputType: "insertText",
            data: payload
          });
          inputEl.dispatchEvent(inputEvent);

          if (!inputEl.innerText || inputEl.innerText.length < 20) {
            inputEl.textContent = payload;
            inputEl.dispatchEvent(new Event("input", { bubbles: true }));
            inputEl.dispatchEvent(new Event("change", { bubbles: true }));
          }
        } catch (e) {
          // Continue to verification
        }
      }
    } else if (inputEl.tagName === "TEXTAREA" || inputEl.tagName === "INPUT") {
      inputEl.value = payload;
      inputEl.dispatchEvent(new Event("input", { bubbles: true }));
      inputEl.dispatchEvent(new Event("change", { bubbles: true }));
    }

    // Verify whether destination actually contains the payload
    const currentVal = inputEl.isContentEditable ? (inputEl.innerText || "") : (inputEl.value || "");
    const verified = currentVal.includes("PROJECT:") || currentVal.length >= Math.min(payload.length * 0.5, 60);

    if (verified) {
      debugLog("pasteSucceeded", {
        provider: adapter.provider,
        sourceProvider: pending.sourceProvider
      });
      showHandoffSuccessToast(pending.sourceProvider);
      chrome.storage.local.remove(["continuo_pending_handoff"]);
    } else {
      debugLog("pasteFailed", {
        provider: adapter.provider,
        reason: "framework_blocked_direct_mutation"
      });
      showHandoffFallbackBanner(pending, adapter, inputEl);
    }
  } catch (err) {
    debugLog("pasteFailed", {
      provider: adapter.provider,
      error: err.message
    });
    showHandoffFallbackBanner(pending, adapter, inputEl);
  }
}

function showHandoffSuccessToast(sourceProvider) {
  const existing = document.getElementById("continuo-handoff-toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.id = "continuo-handoff-toast";
  toast.style.cssText = `
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: #0f172a;
    color: #f8fafc;
    border: 1px solid #10b981;
    border-radius: 12px;
    padding: 12px 18px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 13px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 10px;
    z-index: 9999999;
    animation: continuoFadeIn 0.25s ease-out;
  `;
  const srcName = sourceProvider ? sourceProvider.toUpperCase() : "previous AI";
  toast.innerHTML = `<span style="color: #10b981; font-weight: bold; font-size: 15px;">✓</span> Context transferred from ${srcName}. Ready to send.`;
  document.body.appendChild(toast);

  setTimeout(() => {
    if (toast.parentNode) toast.remove();
  }, 4000);
}

function showHandoffFallbackBanner(pending, adapter, inputEl) {
  const existing = document.getElementById("continuo-handoff-pill");
  if (existing) existing.remove();

  const srcName = pending.sourceProvider ? pending.sourceProvider.toUpperCase() : "previous AI";
  const pill = document.createElement("div");
  pill.id = "continuo-handoff-pill";
  pill.style.cssText = `
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: #1e293b;
    color: #f8fafc;
    border: 1px solid #38bdf8;
    border-radius: 12px;
    padding: 12px 16px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.5);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 12px;
    z-index: 9999999;
  `;

  pill.innerHTML = `
    <span><strong>Continuo:</strong> Context ready from ${srcName}. Press <strong>Ctrl+V</strong> (or <strong>Cmd+V</strong>) to paste.</span>
    <button id="continuo-pill-copy-btn" style="background: #0284c7; color: white; border: none; border-radius: 6px; padding: 6px 12px; font-size: 12px; font-weight: 600; cursor: pointer;">Copy Again</button>
    <button id="continuo-pill-close-btn" style="background: transparent; color: #94a3b8; border: none; font-size: 16px; cursor: pointer; padding: 0 4px;">✕</button>
  `;

  document.body.appendChild(pill);

  if (inputEl) {
    try { inputEl.focus(); } catch (e) {}
  }

  const copyBtn = pill.querySelector("#continuo-pill-copy-btn");
  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(pending.payload);
        copyBtn.textContent = "Copied ✓";
        if (inputEl) inputEl.focus();
        setTimeout(() => { copyBtn.textContent = "Copy Again"; }, 2000);
      } catch (e) {
        copyBtn.textContent = "Ctrl+V to paste";
      }
    });
  }

  const closeBtn = pill.querySelector("#continuo-pill-close-btn");
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      pill.remove();
      chrome.storage.local.remove(["continuo_pending_handoff"]);
    });
  }

  setTimeout(() => {
    if (pill.parentNode) {
      pill.remove();
      chrome.storage.local.remove(["continuo_pending_handoff"]);
    }
  }, 15000);
}

// --- 10. MESSAGE LISTENER & RUNTIME ENTRY ---
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "CHECK_CONVERSATION_STATE") {
    try {
      const state = inspectConversationState();
      sendResponse(state);
    } catch (err) {
      sendResponse({ success: false, conversationFound: false, error: err.message });
    }
    return true;
  }

  if (request.action === "CAPTURE_CONVERSATION") {
    try {
      const result = extractActiveConversation();
      sendResponse(result);
    } catch (err) {
      sendResponse({ success: false, conversationFound: false, error: err.message });
    }
    return true;
  }

  if (request.action === "GET_LOCAL_AUTH") {
    try {
      const token = localStorage.getItem("continuo_jwt");
      const user = localStorage.getItem("continuo_user");
      sendResponse({ success: true, token, user });
    } catch (e) {
      sendResponse({ success: false, error: e.message });
    }
    return true;
  }

  return true;
});

// Auto-sync token from Continuo Web App to extension storage
(function initAuthSync() {
  const host = window.location.hostname;
  const isContinuoHost = host === "localhost" || host === "127.0.0.1" || host.includes("continuo");
  if (isContinuoHost) {
    try {
      const syncToken = (explicitToken, explicitUser) => {
        let token = explicitToken;
        let user = explicitUser;
        if (token === undefined) {
          token = localStorage.getItem("continuo_jwt");
        }
        if (user === undefined) {
          const rawUser = localStorage.getItem("continuo_user");
          user = rawUser ? JSON.parse(rawUser) : null;
        }
        if (chrome.storage && chrome.storage.local) {
          if (token) {
            chrome.storage.local.set({
              continuo_jwt: token,
              continuo_user: user
            });
          } else {
            chrome.storage.local.remove(["continuo_jwt", "continuo_user"]);
          }
        }
      };

      syncToken();
      window.addEventListener("storage", () => syncToken());
      window.addEventListener("continuo_auth_sync", (e) => {
        if (e && e.detail) {
          syncToken(e.detail.token, e.detail.user);
        } else {
          syncToken();
        }
      });
    } catch (e) {
      // Passive sync attempt
    }
  }
})();

// Initialize Destination Handoff Receiver
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initHandoffReceiver);
} else {
  initHandoffReceiver();
}
