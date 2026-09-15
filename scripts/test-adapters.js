/**
 * Automated Verification Script for Continuo Extension Adapters
 * Tests ChatGPTAdapter, ClaudeAdapter, and GeminiAdapter across DOM structures.
 */

const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

// Load content.js into a sandbox with a mock DOM environment
const contentCode = fs.readFileSync("extension/content.js", "utf-8");

function matchesSingle(el, rawPart) {
  let part = rawPart.replace(/:not\([^)]*\)/g, "").trim();
  if (!part) return false;

  let tagMatch = true;
  const tagPart = part.match(/^[a-zA-Z0-9_-]+/);
  if (tagPart) {
    if (tagPart[0].toUpperCase() !== el.tagName) {
      tagMatch = false;
    }
    part = part.slice(tagPart[0].length);
  }
  if (!tagMatch) return false;

  // Check attributes [k=v] or [k]
  const attrMatches = part.matchAll(/\[([^\]]+)\]/g);
  for (const m of attrMatches) {
    const inner = m[1];
    if (inner.includes("=")) {
      if (inner.includes("^=")) {
        const [k, v] = inner.split("^=").map(x => x.replace(/['"]/g, "").trim());
        if (!el.attributes[k] || !el.attributes[k].startsWith(v)) return false;
      } else if (inner.includes("*=")) {
        const [k, v] = inner.split("*=").map(x => x.replace(/['"]/g, "").trim());
        if (!el.attributes[k] || !el.attributes[k].includes(v)) return false;
      } else {
        const [k, v] = inner.split("=").map(x => x.replace(/['"]/g, "").trim());
        if (el.attributes[k] !== v) return false;
      }
    } else {
      if (el.attributes[inner] === undefined) return false;
    }
  }

  // Check classes .cls
  const classMatches = part.matchAll(/\.([a-zA-Z0-9_-]+)/g);
  for (const m of classMatches) {
    const cls = m[1];
    if (!el.attributes.class || !el.attributes.class.includes(cls)) return false;
  }

  // Check ID #id
  const idMatch = part.match(/#([a-zA-Z0-9_-]+)/);
  if (idMatch) {
    if (el.attributes.id !== idMatch[1]) return false;
  }

  return true;
}

function createMockElement(tag, attrs = {}, text = "", children = []) {
  const el = {
    tagName: tag.toUpperCase(),
    nodeType: 1,
    attributes: attrs,
    innerText: text,
    textContent: text,
    value: text,
    isContentEditable: attrs.contenteditable === "true",
    children: [...children],
    parent: null,
    getAttribute(name) { return this.attributes[name] || null; },
    setAttribute(name, val) { this.attributes[name] = val; },
    removeAttribute(name) { delete this.attributes[name]; },
    matches(selector) {
      const branches = selector.split(",").map(s => s.trim());
      for (const branch of branches) {
        const tokens = branch.split(/\s+/).filter(t => t && t !== ">");
        if (tokens.length === 0) continue;
        const lastToken = tokens[tokens.length - 1];
        if (!matchesSingle(this, lastToken)) continue;

        if (tokens.length === 1) return true;

        let curr = this.parent;
        let matchedHierarchy = true;
        for (let i = tokens.length - 2; i >= 0; i--) {
          let found = false;
          while (curr) {
            if (matchesSingle(curr, tokens[i])) {
              found = true;
              curr = curr.parent;
              break;
            }
            curr = curr.parent;
          }
          if (!found) {
            matchedHierarchy = false;
            break;
          }
        }
        if (matchedHierarchy) return true;
      }
      return false;
    },
    querySelector(selector) {
      const all = this.querySelectorAll(selector);
      return all.length > 0 ? all[0] : null;
    },
    querySelectorAll(selector) {
      const results = [];
      const seen = new Set();
      const walk = (node) => {
        for (const child of (node.children || [])) {
          if (child.matches && child.matches(selector)) {
            if (!seen.has(child)) {
              seen.add(child);
              results.push(child);
            }
          }
          walk(child);
        }
      };
      walk(this);
      return results;
    },
    focus() { this.focused = true; },
    dispatchEvent(event) { this.lastEvent = event; return true; }
  };
  for (const child of el.children) {
    child.parent = el;
  }
  return el;
}

function createDOMContext(url, rootChildren = []) {
  const parsedUrl = new URL(url);
  const documentElement = createMockElement("html", {}, "", [
    createMockElement("head", {}, ""),
    createMockElement("body", {}, "", rootChildren)
  ]);

  const doc = {
    readyState: "complete",
    title: "Test Page",
    body: documentElement.children[1],
    querySelector(sel) { return documentElement.querySelector(sel); },
    querySelectorAll(sel) { return documentElement.querySelectorAll(sel); },
    createElement(tag) { return createMockElement(tag); },
    addEventListener() {},
    execCommand() { return true; }
  };

  const sandbox = {
    window: {
      location: {
        href: url,
        hostname: parsedUrl.hostname,
        pathname: parsedUrl.pathname,
        search: parsedUrl.search
      },
      __CONTINUO_DEBUG__: true,
      __CONTINUO_DEBUG_LOGS__: [],
      addEventListener() {}
    },
    document: doc,
    chrome: {
      runtime: { onMessage: { addListener() {} } },
      storage: { local: { get() {}, set() {}, remove() {} } }
    },
    localStorage: { getItem() { return null; }, setItem() {}, removeItem() {} },
    console
  };
  sandbox.window.document = doc;
  return sandbox;
}

console.log("============================================================");
console.log("TESTING CONTINUO EXTENSION PROVIDER ADAPTERS");
console.log("============================================================\n");

// --- TEST 1: ChatGPT with standard data-message-author-role ---
{
  const chatGptDom = [
    createMockElement("main", {}, "", [
      createMockElement("div", { "data-message-author-role": "user" }, "", [
        createMockElement("div", { class: "whitespace-pre-wrap" }, "Hello ChatGPT, can you write an implementation plan?")
      ]),
      createMockElement("div", { "data-message-author-role": "assistant" }, "", [
        createMockElement("div", { class: "markdown" }, "Yes, here is the structured implementation plan.")
      ])
    ]),
    createMockElement("div", { id: "prompt-textarea", contenteditable: "true" }, "")
  ];

  const ctx = createDOMContext("https://chatgpt.com/c/67d02842-abcd-1234-5678-0123456789ab", chatGptDom);
  vm.runInNewContext(contentCode, ctx);

  const state = ctx.inspectConversationState();
  assert.strictEqual(state.provider, "chatgpt", "ChatGPT detected");
  assert.strictEqual(state.conversationFound, true, "ChatGPT conversation found");
  assert.strictEqual(state.conversationId, "67d02842-abcd-1234-5678-0123456789ab", "ChatGPT conversation ID extracted");
  assert.strictEqual(state.messageCount, 2, "ChatGPT extracted 2 messages");

  const capture = ctx.extractActiveConversation();
  assert.strictEqual(capture.success, true);
  assert.strictEqual(capture.messages.length, 2);
  assert.strictEqual(capture.messages[0].role, "user");
  assert.strictEqual(capture.messages[0].content, "Hello ChatGPT, can you write an implementation plan?");
  assert.strictEqual(capture.messages[1].role, "assistant");
  assert.strictEqual(capture.messages[1].content, "Yes, here is the structured implementation plan.");
  console.log("  [PASS] ChatGPT Strategy 1 (data-message-author-role): 2 messages extracted correctly.");
}

// --- TEST 2: ChatGPT with article conversation-turn containers ---
{
  const chatGptTurnDom = [
    createMockElement("main", {}, "", [
      createMockElement("article", { "data-testid": "conversation-turn-0" }, "", [
        createMockElement("div", { class: "whitespace-pre-wrap" }, "What are quantum dots?")
      ]),
      createMockElement("article", { "data-testid": "conversation-turn-1" }, "", [
        createMockElement("div", { class: "markdown prose" }, "Quantum dots are nanoscale semiconductor particles.")
      ])
    ]),
    createMockElement("textarea", { id: "prompt-textarea" }, "")
  ];

  const ctx = createDOMContext("https://chatgpt.com/c/quantum-dots-123", chatGptTurnDom);
  vm.runInNewContext(contentCode, ctx);

  const state = ctx.inspectConversationState();
  assert.strictEqual(state.provider, "chatgpt");
  assert.strictEqual(state.conversationFound, true);
  assert.strictEqual(state.messageCount, 2);

  const capture = ctx.extractActiveConversation();
  assert.strictEqual(capture.messages[0].role, "user");
  assert.strictEqual(capture.messages[1].role, "assistant");
  console.log("  [PASS] ChatGPT Strategy 2 (article[data-testid='conversation-turn']): 2 messages extracted correctly.");
}

// --- TEST 3: ChatGPT on empty new chat page ---
{
  const emptyChatGptDom = [
    createMockElement("main", {}, "", []),
    createMockElement("div", { id: "prompt-textarea", contenteditable: "true" }, "")
  ];

  const ctx = createDOMContext("https://chatgpt.com/", emptyChatGptDom);
  vm.runInNewContext(contentCode, ctx);

  const state = ctx.inspectConversationState();
  assert.strictEqual(state.provider, "chatgpt");
  assert.strictEqual(state.conversationFound, false, "Must NOT mark conversation as found on empty chat");
  assert.strictEqual(state.messageCount, 0);

  const capture = ctx.extractActiveConversation();
  assert.strictEqual(capture.success, false, "Must return honest error on empty conversation");
  assert.strictEqual(capture.conversationFound, false);
  console.log("  [PASS] ChatGPT Empty New Chat honest state verified (0 messages, conversationFound: false).");
}

// --- TEST 4: Claude with testid message turns ---
{
  const claudeDom = [
    createMockElement("main", {}, "", [
      createMockElement("div", { "data-testid": "user-message" }, "Claude, summarize this paper for me."),
      createMockElement("div", { "data-testid": "assistant-message" }, "Here is the summary of the key findings.")
    ]),
    createMockElement("div", { class: "ProseMirror", contenteditable: "true" }, "")
  ];

  const ctx = createDOMContext("https://claude.ai/chat/a1b2c3d4-e5f6-7890-abcd-ef1234567890", claudeDom);
  vm.runInNewContext(contentCode, ctx);

  const state = ctx.inspectConversationState();
  assert.strictEqual(state.provider, "claude");
  assert.strictEqual(state.conversationFound, true);
  assert.strictEqual(state.conversationId, "a1b2c3d4-e5f6-7890-abcd-ef1234567890");
  assert.strictEqual(state.messageCount, 2);

  const capture = ctx.extractActiveConversation();
  assert.strictEqual(capture.success, true);
  assert.strictEqual(capture.messages[0].role, "user");
  assert.strictEqual(capture.messages[0].content, "Claude, summarize this paper for me.");
  assert.strictEqual(capture.messages[1].role, "assistant");
  assert.strictEqual(capture.messages[1].content, "Here is the summary of the key findings.");
  console.log("  [PASS] Claude Strategy 1 (data-testid='user-message' / 'assistant-message'): 2 messages extracted correctly.");
}

// --- TEST 5: Claude with font classes ---
{
  const claudeFontDom = [
    createMockElement("main", {}, "", [
      createMockElement("div", { class: "font-user-message" }, "How do neural networks work?"),
      createMockElement("div", { class: "font-claude-message" }, "Neural networks are computational models inspired by biological neural networks.")
    ]),
    createMockElement("div", { class: "ProseMirror", contenteditable: "true" }, "")
  ];

  const ctx = createDOMContext("https://claude.ai/chat/font-test-uuid", claudeFontDom);
  vm.runInNewContext(contentCode, ctx);

  const state = ctx.inspectConversationState();
  assert.strictEqual(state.provider, "claude");
  assert.strictEqual(state.conversationFound, true);
  assert.strictEqual(state.messageCount, 2);

  const capture = ctx.extractActiveConversation();
  assert.strictEqual(capture.messages[0].role, "user");
  assert.strictEqual(capture.messages[1].role, "assistant");
  console.log("  [PASS] Claude Strategy 2 (.font-user-message / .font-claude-message): 2 messages extracted correctly.");
}

// --- TEST 6: Claude on empty /new page ---
{
  const emptyClaudeDom = [
    createMockElement("main", {}, "", [
      createMockElement("h1", {}, "What can I help you with today?")
    ]),
    createMockElement("div", { class: "ProseMirror", contenteditable: "true" }, "")
  ];

  const ctx = createDOMContext("https://claude.ai/new", emptyClaudeDom);
  vm.runInNewContext(contentCode, ctx);

  const state = ctx.inspectConversationState();
  assert.strictEqual(state.provider, "claude");
  assert.strictEqual(state.conversationFound, false, "Must NOT mark conversation as found on empty /new page");
  assert.strictEqual(state.messageCount, 0);

  const capture = ctx.extractActiveConversation();
  assert.strictEqual(capture.success, false);
  console.log("  [PASS] Claude Empty /new page honest state verified (0 messages, conversationFound: false).");
}

// --- TEST 7: Gemini reference implementation (Zero regression) ---
{
  const geminiDom = [
    createMockElement("div", { class: "user-query" }, "Explain general relativity simply."),
    createMockElement("div", { class: "model-response" }, "General relativity describes gravity as the warping of spacetime by mass."),
    createMockElement("user-query-content", {}, "What is an event horizon?"),
    createMockElement("message-content", {}, "An event horizon is the boundary beyond which nothing can escape a black hole."),
    createMockElement("rich-textarea", {}, "", [
      createMockElement("div", { class: "ql-editor", contenteditable: "true" }, "")
    ])
  ];

  const ctx = createDOMContext("https://gemini.google.com/app/c8d7e6f5", geminiDom);
  vm.runInNewContext(contentCode, ctx);

  const state = ctx.inspectConversationState();
  assert.strictEqual(state.provider, "gemini");
  assert.strictEqual(state.conversationFound, true);
  assert.strictEqual(state.conversationId, "c8d7e6f5");
  assert.strictEqual(state.messageCount, 4);

  const capture = ctx.extractActiveConversation();
  assert.strictEqual(capture.success, true);
  assert.strictEqual(capture.messages.length, 4);
  assert.strictEqual(capture.messages[0].role, "user");
  assert.strictEqual(capture.messages[1].role, "assistant");
  assert.strictEqual(capture.messages[2].role, "user");
  assert.strictEqual(capture.messages[3].role, "assistant");
  console.log("  [PASS] Gemini Reference Implementation: 4 messages extracted with zero regression.");
}

// --- TEST 8: Destination Input Element Detection ---
{
  const gptCtx = createDOMContext("https://chatgpt.com/", [createMockElement("div", { id: "prompt-textarea", contenteditable: "true" }, "")]);
  vm.runInNewContext(contentCode, gptCtx);
  const gptAdapter = gptCtx.getActiveAdapter();
  assert.ok(gptAdapter.getInputElement(), "ChatGPT input element located");

  const claudeCtx = createDOMContext("https://claude.ai/new", [createMockElement("div", { class: "ProseMirror", contenteditable: "true" }, "")]);
  vm.runInNewContext(contentCode, claudeCtx);
  const claudeAdapter = claudeCtx.getActiveAdapter();
  assert.ok(claudeAdapter.getInputElement(), "Claude input element located");

  const geminiCtx = createDOMContext("https://gemini.google.com/app", [
    createMockElement("rich-textarea", {}, "", [createMockElement("div", { class: "ql-editor", contenteditable: "true" }, "")])
  ]);
  vm.runInNewContext(contentCode, geminiCtx);
  const geminiAdapter = geminiCtx.getActiveAdapter();
  assert.ok(geminiAdapter.getInputElement(), "Gemini input element located");

  console.log("  [PASS] Destination input prompt detection verified for ChatGPT, Claude, and Gemini.");
}

console.log("\n============================================================");
console.log("ALL PROVIDER ADAPTER TESTS PASSED (8/8)");
console.log("============================================================\n");
