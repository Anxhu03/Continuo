/**
 * CONTINUO — Chrome Extension Content Script
 * Robust, honest DOM extraction & cross-AI continuation receiver.
 * Modular adapters for ChatGPT, Claude, and Gemini with normalized data output.
 */

// --- 1. SAFE METADATA DIAGNOSTICS ---
function safeLog(label, val = "") {
  try {
    if (val !== undefined && val !== null && val !== "") {
      console.log(`[Continuo] ${label}: ${val}`);
    } else {
      console.log(`[Continuo] ${label}`);
    }
  } catch (e) {
    // Suppress logging errors
  }
}

// Diagnostic: content loaded
safeLog("content loaded");
safeLog("URL", window.location.href);

// --- 2. TEXT CLEANING UTILITY ---
function cleanTurnText(str) {
  if (!str) return "";
  return str
    .replace(/^(?:You said|ChatGPT said|User said|Claude said):\s*/i, "")
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
  isConversationPage() { return false; }
  getConversationId() { return null; }
  getTitle() { return document.title || `${this.provider.toUpperCase()} Conversation`; }
  getConversationTitle() { return this.getTitle(); }
  isConversationReady() { return this.getMessages().length > 0; }
  getMessages() { return []; }
  extractMessages() { return this.getMessages(); }
  getInputElement() { return null; }

  getNormalizedData() {
    return {
      provider: this.provider,
      conversation_id: this.getConversationId(),
      title: this.getTitle(),
      url: window.location.href,
      messages: this.getMessages()
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

  isConversationPage() {
    if (this.getConversationId()) return true;
    const mainEl = document.querySelector("main");
    if (!mainEl) return false;
    const turns = mainEl.querySelectorAll("article, [data-testid^='conversation-turn'], [data-message-author-role]");
    return turns.length > 0;
  }

  getConversationId() {
    const path = window.location.pathname;
    const match = path.match(/\/(?:c|share|g\/[^/]+\/c)\/([a-zA-Z0-9-]+)/);
    return match ? match[1] : null;
  }

  getTitle() {
    let title = document.title ? document.title.replace(/\s*[-–|]\s*ChatGPT.*$/i, "").trim() : "";
    if (!title || title.toLowerCase() === "chatgpt") {
      const headerTitle = document.querySelector("#conversation-header h1, header h1, nav a[aria-current='page']");
      if (headerTitle && headerTitle.textContent.trim()) {
        title = headerTitle.textContent.trim();
      }
    }
    return title || "ChatGPT Conversation";
  }

  getMessages() {
    const messages = [];
    const mainEl = document.querySelector("main") || document.body;

    // Strategy 1: Article turn containers with accessibility and author indicators
    const turnArticles = mainEl.querySelectorAll("article, [data-testid^='conversation-turn']");
    if (turnArticles.length > 0) {
      turnArticles.forEach((art, index) => {
        if (art.tagName === "MAIN") return;

        // Determine role via multiple heuristics
        let role = null;

        // A. Accessibility screen-reader headings (e.g. <h5>You said:</h5> or <h5>ChatGPT said:</h5>)
        const srNodes = art.querySelectorAll(".sr-only, [class*='sr-only'], h5, h6");
        for (const sr of srNodes) {
          const txt = sr.textContent.toLowerCase();
          if (txt.includes("you said")) {
            role = "user";
            break;
          } else if (txt.includes("chatgpt said") || txt.includes("chatgpt")) {
            role = "assistant";
            break;
          }
        }

        // B. Explicit author role attribute on article or children
        if (!role) {
          const roleEl = art.querySelector("[data-message-author-role]") || ((art.hasAttribute && art.hasAttribute("data-message-author-role")) ? art : (art.getAttribute && art.getAttribute("data-message-author-role") ? art : null));
          if (roleEl) {
            const rawRole = roleEl.getAttribute("data-message-author-role");
            role = rawRole === "user" ? "user" : "assistant";
          }
        }

        // C. Structural indicators (User bubble vs Markdown response)
        if (!role) {
          if (art.querySelector("[data-user='true'], .whitespace-pre-wrap:not(.markdown *)") && !art.querySelector(".markdown, .prose")) {
            role = "user";
          } else if (art.querySelector(".markdown, .prose, [data-message-id]")) {
            role = "assistant";
          } else {
            // Sequence alternation fallback
            role = index % 2 === 0 ? "user" : "assistant";
          }
        }

        // Content extraction
        let contentEl = null;
        if (role === "user") {
          contentEl = art.querySelector("[data-message-author-role='user'] .whitespace-pre-wrap, [data-message-author-role='user'], .whitespace-pre-wrap, div[dir='auto']") || art;
        } else {
          contentEl = art.querySelector("[data-message-author-role='assistant'] .markdown, .markdown, .prose, [data-message-author-role='assistant']") || art;
        }

        // Clone or extract text without screen reader headers or action buttons
        let text = "";
        if (contentEl) {
          if (typeof contentEl.cloneNode === "function") {
            const clone = contentEl.cloneNode(true);
            if (clone.querySelectorAll) {
              const removeSelectors = [
                ".sr-only",
                "[class*='sr-only']",
                "button",
                "nav",
                "[aria-label*='Copy']",
                "[aria-label*='Read aloud']",
                "[aria-label*='Good response']",
                "[aria-label*='Bad response']"
              ];
              clone.querySelectorAll(removeSelectors.join(",")).forEach(el => {
                if (el.remove) el.remove();
              });
            }
            text = cleanTurnText(clone.innerText || clone.textContent);
          } else {
            text = cleanTurnText(contentEl.innerText || contentEl.textContent);
          }
        }

        if (text && text.length > 0) {
          messages.push({ role, content: text });
        }
      });

      if (messages.length > 0) return messages;
    }

    // Strategy 2: Direct query of [data-message-author-role] inside main
    const roleNodes = mainEl.querySelectorAll("[data-message-author-role]");
    if (roleNodes.length > 0) {
      roleNodes.forEach((node) => {
        // Exclude sidebar or navigation elements
        if (node.closest && node.closest("nav, aside, header, footer")) return;
        const rawRole = node.getAttribute("data-message-author-role");
        const role = rawRole === "user" ? "user" : "assistant";
        const contentEl = node.querySelector(".markdown, .whitespace-pre-wrap, div[dir='auto']") || node;
        let text = "";
        if (typeof contentEl.cloneNode === "function") {
          const clone = contentEl.cloneNode(true);
          if (clone.querySelectorAll) {
            clone.querySelectorAll(".sr-only, [class*='sr-only'], button").forEach(el => {
              if (el.remove) el.remove();
            });
          }
          text = cleanTurnText(clone.innerText || clone.textContent);
        } else {
          text = cleanTurnText(contentEl.innerText || contentEl.textContent);
        }
        if (text && text.length > 0) {
          messages.push({ role, content: text });
        }
      });
      if (messages.length > 0) return messages;
    }

    // Strategy 3: Elements with data-message-id
    const msgIdNodes = mainEl.querySelectorAll("[data-message-id]");
    if (msgIdNodes.length > 0) {
      msgIdNodes.forEach((node) => {
        if (node.closest && node.closest("nav, aside, header, footer")) return;
        const role = node.getAttribute("data-message-author-role") ||
                     (node.querySelector(".markdown, .prose") ? "assistant" : "user");
        let text = "";
        if (typeof node.cloneNode === "function") {
          const clone = node.cloneNode(true);
          if (clone.querySelectorAll) {
            clone.querySelectorAll(".sr-only, [class*='sr-only'], button").forEach(el => {
              if (el.remove) el.remove();
            });
          }
          text = cleanTurnText(clone.innerText || clone.textContent);
        } else {
          text = cleanTurnText(node.innerText || node.textContent);
        }
        if (text && text.length > 0) {
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

  isConversationPage() {
    if (this.getConversationId()) return true;
    const mainEl = document.querySelector("main");
    if (!mainEl) return false;
    const turns = mainEl.querySelectorAll("[data-testid='user-message'], .font-claude-response, .standard-markdown, div[class*='font-claude']");
    return turns.length > 0;
  }

  getConversationId() {
    const path = window.location.pathname;
    const match = path.match(/\/chat\/([a-zA-Z0-9_-]+)/);
    return match ? match[1] : null;
  }

  getTitle() {
    let title = document.title ? document.title.replace(/\s*[-–|]\s*Claude.*$/i, "").trim() : "";
    if (!title || title.toLowerCase() === "claude") {
      const headerTitle = document.querySelector("button[data-testid='chat-title-button'], header h1, nav [aria-current='page']");
      if (headerTitle && headerTitle.textContent.trim()) {
        title = headerTitle.textContent.trim();
      }
    }
    return title || "Claude Conversation";
  }

  getMessages() {
    const messages = [];
    const mainEl = document.querySelector("main") || document.body;

    // Strategy 1: Data test IDs and message font/response classes (Document order sorting)
    const turnCandidates = mainEl.querySelectorAll(
      "[data-testid='user-message'], [data-testid='assistant-message'], .font-user-message, .font-claude-message, .font-claude-response, div[class*='font-user'], div[class*='font-claude'], div[class*='UserMessage'], div[class*='AssistantMessage'], div[data-is-streaming], div.standard-markdown"
    );

    if (turnCandidates.length > 0) {
      // Filter out nested candidate elements
      const topLevelTurns = [];
      turnCandidates.forEach((node) => {
        if (node.closest && node.closest("nav, aside, header, fieldset, .ProseMirror")) return;
        let isNested = false;
        for (const parent of turnCandidates) {
          if (parent !== node && parent.contains && parent.contains(node)) {
            isNested = true;
            break;
          }
        }
        if (!isNested) {
          topLevelTurns.push(node);
        }
      });

      // Sort by DOM tree order
      if (typeof Node !== "undefined" && Node.DOCUMENT_POSITION_FOLLOWING) {
        topLevelTurns.sort((a, b) => {
          const position = a.compareDocumentPosition ? a.compareDocumentPosition(b) : 0;
          if (position & Node.DOCUMENT_POSITION_FOLLOWING) return -1;
          if (position & Node.DOCUMENT_POSITION_PRECEDING) return 1;
          return 0;
        });
      }

      topLevelTurns.forEach((node) => {
        const isUser = node.matches(
          "[data-testid='user-message'], .font-user-message, div[class*='font-user'], div[class*='UserMessage'], [data-author='human']"
        );
        const role = isUser ? "user" : "assistant";

        let text = "";
        if (typeof node.cloneNode === "function") {
          const clone = node.cloneNode(true);
          if (clone.querySelectorAll) {
            clone.querySelectorAll("button, nav, [aria-label*='Copy'], [aria-label*='Retry'], [data-testid*='action']").forEach(el => {
              if (el.remove) el.remove();
            });
          }
          text = cleanTurnText(clone.innerText || clone.textContent);
        } else {
          text = cleanTurnText(node.innerText || node.textContent);
        }

        if (text && text.length > 0 && !text.includes("What can I help you with today?")) {
          messages.push({ role, content: text });
        }
      });

      if (messages.length > 0) return messages;
    }

    // Strategy 2: Conversation row flow in main scroll container
    const rows = mainEl.querySelectorAll(".grid-cols-1 > div, div[data-test-render-count] > div, div[class*='conversation'] > div");
    if (rows.length > 0) {
      rows.forEach((row) => {
        if (row.closest && row.closest("nav, aside, header, fieldset, .ProseMirror")) return;
        const text = cleanTurnText(row.innerText || row.textContent);
        if (text && text.length > 5 && !text.includes("What can I help you with today?")) {
          const isUser = row.querySelector(".font-user-message, [data-testid='user-message']") ||
                         row.matches("div[class*='user']") ||
                         (!row.querySelector(".standard-markdown, .prose, .font-claude-response") && text.length < 500);
          messages.push({ role: isUser ? "user" : "assistant", content: text });
        }
      });
      if (messages.length > 0) return messages;
    }

    // Strategy 3: Markdown response nodes paired with preceding query containers
    const proseNodes = mainEl.querySelectorAll(".standard-markdown, .font-claude-response, .prose");
    if (proseNodes.length > 0) {
      proseNodes.forEach((p) => {
        if (p.closest && p.closest("nav, aside, header, fieldset, .ProseMirror")) return;
        const text = cleanTurnText(p.innerText || p.textContent);
        if (text && text.length > 5 && !text.includes("What can I help you with today?")) {
          messages.push({ role: "assistant", content: text });
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

// --- 6. GEMINI ADAPTER (PRESERVED REFERENCE IMPLEMENTATION) ---
class GeminiAdapter extends BaseAdapter {
  constructor() {
    super("gemini");
  }

  detect() {
    return window.location.hostname.includes("gemini.google.com");
  }

  isConversationPage() {
    if (this.getConversationId()) return true;
    const queryNodes = document.querySelectorAll(".user-query, .query-text, user-query-content, .query-content");
    const responseNodes = document.querySelectorAll(".model-response, .response-content, message-content, .model-response-text");
    return queryNodes.length > 0 || responseNodes.length > 0;
  }

  getConversationId() {
    const path = window.location.pathname;
    const match = path.match(/\/app\/([a-zA-Z0-9_-]+)/);
    return match ? match[1] : null;
  }

  getTitle() {
    const title = document.title ? document.title.replace(/\s*[-–|]\s*Google Gemini.*$/i, "").replace(/\s*[-–|]\s*Gemini.*$/i, "").trim() : "";
    return title || "Google Gemini Conversation";
  }

  getMessages() {
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

const activeAdapter = getActiveAdapter();
if (activeAdapter) {
  safeLog("provider", activeAdapter.provider);
  safeLog("adapter", activeAdapter.constructor.name);
}

// --- 8. EXTRACTION HANDLER ---
function handleExtractionRequest() {
  safeLog("extraction requested");
  const adapter = getActiveAdapter();

  if (!adapter) {
    safeLog("result sent", "failed: no adapter");
    return {
      success: false,
      error: "ADAPTER_NOT_FOUND",
      conversation: {
        provider: null,
        conversation_id: null,
        title: document.title || "Unknown Page",
        url: window.location.href,
        messages: []
      }
    };
  }

  safeLog("provider", adapter.provider);
  safeLog("adapter", adapter.constructor.name);

  const isConvPage = adapter.isConversationPage();
  const convId = adapter.getConversationId();
  if (convId) {
    safeLog("conversation id detected", convId);
  }

  const rawMessages = adapter.getMessages();
  const candidateCount = (function() {
    try {
      const mainEl = document.querySelector("main") || document.body;
      return mainEl.querySelectorAll("article, [data-testid*='message'], [data-message-author-role], .user-query, .model-response, .standard-markdown").length;
    } catch (e) {
      return rawMessages.length;
    }
  })();

  safeLog("candidate count", candidateCount);
  safeLog("extracted message count", rawMessages.length);

  const normalized = {
    provider: adapter.provider,
    conversation_id: convId,
    title: adapter.getTitle(),
    url: window.location.href,
    messages: rawMessages
  };

  if (rawMessages.length === 0) {
    const errCode = isConvPage ? "NO_MESSAGES" : "CONVERSATION_NOT_FOUND";
    safeLog("result sent", `failed: ${errCode}`);
    return {
      success: false,
      error: errCode,
      conversation: normalized
    };
  }

  safeLog("result sent", "success");
  return {
    success: true,
    conversation: normalized
  };
}

function inspectConversationState() {
  const res = handleExtractionRequest();
  const conv = res.conversation;
  const messages = conv ? conv.messages : [];
  let snippet = "";
  if (messages.length > 0) {
    const latest = messages[messages.length - 1];
    const prefix = latest.role === "user" ? "User: " : "Assistant: ";
    const fullText = prefix + latest.content;
    snippet = fullText.length > 130 ? fullText.substring(0, 127) + "..." : fullText;
  }
  return {
    success: res.success,
    provider: conv ? conv.provider : null,
    conversationFound: res.success && messages.length > 0,
    conversationId: conv ? conv.conversation_id : null,
    messageCount: messages.length,
    snippet,
    title: conv ? conv.title : (document.title || "Unknown Page"),
    error: res.error || null
  };
}

function extractActiveConversation() {
  const res = handleExtractionRequest();
  const conv = res.conversation;
  const messages = conv ? conv.messages : [];
  const turns = messages.map(m => `${m.role === "user" ? "User" : "Assistant"}: ${m.content}`);
  const rawTranscript = turns.join("\n\n");
  return {
    success: res.success,
    conversationFound: res.success && messages.length > 0,
    provider: conv ? conv.provider : null,
    conversationId: conv ? conv.conversation_id : null,
    title: conv ? conv.title : document.title,
    rawTranscript,
    messages,
    messageCount: messages.length,
    charCount: rawTranscript.length,
    error: res.error || null
  };
}

// Expose on window/global for test harness
if (typeof window !== "undefined") {
  window.handleExtractionRequest = handleExtractionRequest;
  window.inspectConversationState = inspectConversationState;
  window.extractActiveConversation = extractActiveConversation;
  window.getActiveAdapter = getActiveAdapter;
}
if (typeof globalThis !== "undefined") {
  globalThis.handleExtractionRequest = handleExtractionRequest;
  globalThis.inspectConversationState = inspectConversationState;
  globalThis.extractActiveConversation = extractActiveConversation;
  globalThis.getActiveAdapter = getActiveAdapter;
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
        showHandoffFallbackBanner(pending, adapter, null);
      }
    }, 300);
  });
}

function attemptPromptInsertion(inputEl, pending, adapter) {
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
      showHandoffSuccessToast(pending.sourceProvider);
      chrome.storage.local.remove(["continuo_pending_handoff"]);
    } else {
      showHandoffFallbackBanner(pending, adapter, inputEl);
    }
  } catch (err) {
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
  // Primary protocol requested by specification
  if (request.type === "CONTINUO_EXTRACT_CONVERSATION") {
    try {
      const result = handleExtractionRequest();
      sendResponse(result);
    } catch (err) {
      sendResponse({
        success: false,
        error: "EXTRACTION_FAILED",
        details: err.message
      });
    }
    return true;
  }

  // Backward-compatible handlers for CHECK_CONVERSATION_STATE & CAPTURE_CONVERSATION
  if (request.action === "CHECK_CONVERSATION_STATE") {
    try {
      const res = handleExtractionRequest();
      const conv = res.conversation;
      const messages = conv ? conv.messages : [];
      let snippet = "";
      if (messages.length > 0) {
        const latest = messages[messages.length - 1];
        const prefix = latest.role === "user" ? "User: " : "Assistant: ";
        const fullText = prefix + latest.content;
        snippet = fullText.length > 130 ? fullText.substring(0, 127) + "..." : fullText;
      }
      sendResponse({
        success: res.success,
        provider: conv ? conv.provider : null,
        conversationFound: res.success && messages.length > 0,
        conversationId: conv ? conv.conversation_id : null,
        messageCount: messages.length,
        snippet,
        title: conv ? conv.title : (document.title || "Unknown Page"),
        error: res.error || null
      });
    } catch (err) {
      sendResponse({ success: false, conversationFound: false, error: err.message });
    }
    return true;
  }

  if (request.action === "CAPTURE_CONVERSATION") {
    try {
      const res = handleExtractionRequest();
      const conv = res.conversation;
      const messages = conv ? conv.messages : [];
      const turns = messages.map(m => `${m.role === "user" ? "User" : "Assistant"}: ${m.content}`);
      const rawTranscript = turns.join("\n\n");
      sendResponse({
        success: res.success,
        conversationFound: res.success && messages.length > 0,
        provider: conv ? conv.provider : null,
        conversationId: conv ? conv.conversation_id : null,
        title: conv ? conv.title : document.title,
        rawTranscript,
        messages,
        messageCount: messages.length,
        charCount: rawTranscript.length,
        error: res.error || null
      });
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
