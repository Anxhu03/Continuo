/**
 * CONTINUO — Chrome Extension Background Service Worker (Manifest V3)
 * Manages token persistence, API proxying, and cross-tab handoff messaging.
 */

const DEFAULT_API_BASE = "http://127.0.0.1:8008/api/v1";
const FALLBACK_API_BASE = "http://127.0.0.1:8000/api/v1";

chrome.runtime.onInstalled.addListener(() => {
  console.log("Continuo Context Companion extension installed.");
});

// Listener for background messages from popup or content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "API_REQUEST") {
    handleApiRequest(message.endpoint, message.method, message.body, message.token)
      .then(data => sendResponse({ success: true, data }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true; // async reply
  }
});

async function handleApiRequest(endpoint, method = "GET", body = null, token = null) {
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let base = DEFAULT_API_BASE;
  try {
    const response = await fetch(`${base}${endpoint}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
    return data;
  } catch (err) {
    // Attempt fallback port
    const fallbackResp = await fetch(`${FALLBACK_API_BASE}${endpoint}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null
    });
    const data = await fallbackResp.json();
    if (!fallbackResp.ok) throw new Error(data.detail || `HTTP ${fallbackResp.status}`);
    return data;
  }
}
