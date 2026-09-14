/**
 * CONTINUO — Chrome Extension Content Script
 * Robust, honest DOM extraction for ChatGPT, Claude, and Gemini conversations.
 * Enforces zero-noise filtering and prevents fake captures on empty new-chat pages.
 */

// Listener for popup inspection and capture commands
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
    // If on Continuo Web App tab, forward stored token
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

      // Initial read
      syncToken();

      // Listen for standard storage events from other tabs
      window.addEventListener("storage", () => syncToken());

      // Listen for instantaneous custom DOM event dispatched by main.js in same tab
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

// Clean noisy UI artifacts (Copy buttons, feedback chips, etc.)
function cleanTurnText(str) {
  if (!str) return "";
  return str
    .replace(/\b(Copy code|Copy to clipboard|Copy|Edit|Share|Regenerate response|Regenerate|Read aloud|Was this response better or worse\?|Retry|Thumbs up|Thumbs down)\b/gi, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function detectProvider() {
  const host = window.location.hostname;
  if (host.includes("chatgpt.com") || host.includes("chat.openai.com")) return "chatgpt";
  if (host.includes("claude.ai")) return "claude";
  if (host.includes("gemini.google.com")) return "gemini";
  return null;
}

function inspectConversationState() {
  const provider = detectProvider();
  if (!provider) {
    return {
      success: true,
      provider: null,
      conversationFound: false,
      messageCount: 0,
      snippet: "",
      title: document.title || "Unknown Page"
    };
  }

  const turns = extractTurnsForProvider(provider);
  let snippet = "";
  if (turns.length > 0) {
    const latest = turns[turns.length - 1];
    snippet = latest.length > 130 ? latest.substring(0, 127) + "..." : latest;
  }

  return {
    success: true,
    provider,
    conversationFound: turns.length > 0,
    messageCount: turns.length,
    snippet,
    title: document.title || `${provider.toUpperCase()} Conversation`
  };
}

function extractTurnsForProvider(provider) {
  const turns = [];

  if (provider === "chatgpt") {
    // 1. Modern ChatGPT conversation turns
    const turnNodes = document.querySelectorAll("[data-message-author-role], article[data-testid^='conversation-turn']");
    if (turnNodes.length > 0) {
      turnNodes.forEach((node) => {
        const role = node.getAttribute("data-message-author-role") ||
                     (node.querySelector("[data-message-author-role='user']") ? "user" : "assistant");
        const roleLabel = role === "user" ? "User" : "Assistant";
        const contentEl = node.querySelector(".markdown, .whitespace-pre-wrap") || node;
        const text = cleanTurnText(contentEl.innerText);
        if (text && text.length > 2) {
          turns.push(`${roleLabel}: ${text}`);
        }
      });
    } else {
      // Alternate ChatGPT articles with identifiable author
      const articles = document.querySelectorAll("article");
      articles.forEach((art) => {
        const isUser = art.querySelector("svg.user-icon, [data-user='true']") !== null;
        const roleLabel = isUser ? "User" : "Assistant";
        const text = cleanTurnText(art.innerText);
        if (text && text.length > 5) {
          turns.push(`${roleLabel}: ${text}`);
        }
      });
    }
  } else if (provider === "claude") {
    // 2. Claude message turns
    const messageTurns = document.querySelectorAll(
      "[data-testid='user-message'], [data-testid='assistant-message'], .font-user-message, .font-claude-message"
    );
    if (messageTurns.length > 0) {
      messageTurns.forEach((node) => {
        const isUser = node.matches("[data-testid='user-message'], .font-user-message");
        const roleLabel = isUser ? "User" : "Assistant";
        const text = cleanTurnText(node.innerText);
        if (text && text.length > 2) {
          turns.push(`${roleLabel}: ${text}`);
        }
      });
    } else {
      // Claude container fallbacks
      const chatRows = document.querySelectorAll(".grid-cols-1 > div, [data-is-streaming]");
      chatRows.forEach((row) => {
        const text = cleanTurnText(row.innerText);
        if (text && text.length > 10 && !text.includes("What can I help you with today?")) {
          turns.push(text);
        }
      });
    }
  } else if (provider === "gemini") {
    // 3. Gemini prompt and model response pairs
    const queryNodes = document.querySelectorAll(".user-query, .query-text, user-query-content, .query-content");
    const responseNodes = document.querySelectorAll(".model-response, .response-content, message-content, .model-response-text");

    const maxCount = Math.max(queryNodes.length, responseNodes.length);
    for (let i = 0; i < maxCount; i++) {
      if (queryNodes[i]) {
        const uText = cleanTurnText(queryNodes[i].innerText);
        if (uText) turns.push(`User: ${uText}`);
      }
      if (responseNodes[i]) {
        const aText = cleanTurnText(responseNodes[i].innerText);
        if (aText) turns.push(`Assistant: ${aText}`);
      }
    }
  }

  return turns;
}

function extractActiveConversation() {
  const provider = detectProvider() || "chatgpt";
  const title = document.title || `${provider.toUpperCase()} Session`;
  const turns = extractTurnsForProvider(provider);

  // CRITICAL HONEST STATE: Do NOT manufacture fake text if no turns exist
  if (turns.length === 0) {
    return {
      success: false,
      conversationFound: false,
      provider,
      title,
      rawTranscript: "",
      messageCount: 0,
      charCount: 0,
      error: "No conversation turns detected on this page."
    };
  }

  const rawTranscript = turns.join("\n\n");

  return {
    success: true,
    conversationFound: true,
    provider,
    title,
    rawTranscript,
    messageCount: turns.length,
    charCount: rawTranscript.length
  };
}
