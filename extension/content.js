/**
 * CONTINUO — Chrome Extension Content Script
 * Safely extracts structured dialogue turns from supported AI interfaces (ChatGPT, Claude, Gemini).
 */

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "CAPTURE_CONVERSATION") {
    try {
      const result = extractActiveConversation();
      sendResponse(result);
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  }
  return true; // Keep channel open for async response
});

function extractActiveConversation() {
  const host = window.location.hostname;
  let provider = "chatgpt";
  let title = document.title || "AI Session";
  let turns = [];

  if (host.includes("openai.com") || host.includes("chatgpt.com")) {
    provider = "chatgpt";
    // ChatGPT message selector
    const messageNodes = document.querySelectorAll("[data-message-author-role]");
    if (messageNodes.length > 0) {
      messageNodes.forEach((node) => {
        const role = node.getAttribute("data-message-author-role");
        const roleLabel = role === "user" ? "User" : "Assistant";
        const text = node.innerText.trim();
        if (text) {
          turns.push(`${roleLabel}: ${text}`);
        }
      });
    } else {
      // Fallback for newer or older ChatGPT layouts
      const articles = document.querySelectorAll("article");
      articles.forEach((art) => {
        const text = art.innerText.trim();
        if (text) turns.push(text);
      });
    }
  } else if (host.includes("claude.ai")) {
    provider = "claude";
    // Claude message containers
    const humanNodes = document.querySelectorAll(".font-user-message, [data-testid='user-message']");
    const claudeNodes = document.querySelectorAll(".font-claude-message, [data-testid='assistant-message']");
    
    // Generic fallback: all message containers
    const allContainers = document.querySelectorAll(".grid-cols-1");
    if (allContainers.length > 0) {
      allContainers.forEach((c) => {
        const text = c.innerText.trim();
        if (text) turns.push(text);
      });
    }
  } else if (host.includes("gemini.google.com")) {
    provider = "gemini";
    const userPrompts = document.querySelectorAll(".user-query, .query-text");
    const modelResponses = document.querySelectorAll(".model-response, .response-content");
    
    userPrompts.forEach((up, idx) => {
      turns.push(`User: ${up.innerText.trim()}`);
      if (modelResponses[idx]) {
        turns.push(`Assistant: ${modelResponses[idx].innerText.trim()}`);
      }
    });
  }

  // Generic fallback if selector didn't catch specific tags
  if (turns.length === 0) {
    const mainContent = document.querySelector("main") || document.body;
    const text = mainContent.innerText.substring(0, 8000);
    turns.push(text);
  }

  const rawTranscript = turns.join("\n\n");

  return {
    success: true,
    provider,
    title,
    rawTranscript,
    messageCount: turns.length,
    charCount: rawTranscript.length
  };
}
