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

  // Helper to sanitize extracted text
  const cleanText = (str) => {
    if (!str) return "";
    return str
      .replace(/\b(Copy code|Copy|Edit|Share|Regenerate|Read aloud|Was this response better or worse\?)\b/gi, "")
      .trim();
  };

  if (host.includes("openai.com") || host.includes("chatgpt.com")) {
    provider = "chatgpt";
    // ChatGPT modern conversation turn selectors
    const messageNodes = document.querySelectorAll("[data-message-author-role], article[data-testid^='conversation-turn']");
    if (messageNodes.length > 0) {
      messageNodes.forEach((node) => {
        const role = node.getAttribute("data-message-author-role") ||
                     (node.querySelector("[data-message-author-role='user']") ? "user" : "assistant");
        const roleLabel = role === "user" ? "User" : "Assistant";
        const text = cleanText(node.innerText);
        if (text && text.length > 2) {
          turns.push(`${roleLabel}: ${text}`);
        }
      });
    } else {
      // Fallback for alternate ChatGPT layouts
      const articles = document.querySelectorAll("article, .text-message");
      articles.forEach((art) => {
        const text = cleanText(art.innerText);
        if (text && text.length > 2) turns.push(text);
      });
    }
  } else if (host.includes("claude.ai")) {
    provider = "claude";
    // Claude message containers
    const messageTurns = document.querySelectorAll("[data-testid='user-message'], [data-testid='assistant-message'], .font-user-message, .font-claude-message");
    if (messageTurns.length > 0) {
      messageTurns.forEach((node) => {
        const isUser = node.matches("[data-testid='user-message'], .font-user-message");
        const roleLabel = isUser ? "User" : "Assistant";
        const text = cleanText(node.innerText);
        if (text && text.length > 2) {
          turns.push(`${roleLabel}: ${text}`);
        }
      });
    } else {
      // Generic fallback for Claude
      const allContainers = document.querySelectorAll(".grid-cols-1, [data-is-streaming]");
      if (allContainers.length > 0) {
        allContainers.forEach((c) => {
          const text = cleanText(c.innerText);
          if (text && text.length > 2) turns.push(text);
        });
      }
    }
  } else if (host.includes("gemini.google.com")) {
    provider = "gemini";
    // Gemini prompt and response selectors
    const queryNodes = document.querySelectorAll(".user-query, .query-text, user-query-content");
    const responseNodes = document.querySelectorAll(".model-response, .response-content, message-content");
    
    if (queryNodes.length > 0 || responseNodes.length > 0) {
      const maxLen = Math.max(queryNodes.length, responseNodes.length);
      for (let i = 0; i < maxLen; i++) {
        if (queryNodes[i]) {
          const uText = cleanText(queryNodes[i].innerText);
          if (uText) turns.push(`User: ${uText}`);
        }
        if (responseNodes[i]) {
          const aText = cleanText(responseNodes[i].innerText);
          if (aText) turns.push(`Assistant: ${aText}`);
        }
      }
    }
  }

  // Generic fallback if selectors didn't catch specific tags
  if (turns.length === 0) {
    const mainContent = document.querySelector("main") || document.body;
    const text = cleanText(mainContent.innerText).substring(0, 12000);
    if (text) turns.push(text);
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
