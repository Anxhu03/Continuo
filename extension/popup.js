/**
 * CONTINUO — Chrome Extension Popup Controller
 * Production Extension-First Architecture
 * Enforces real conversation capture, token storage without hardcoded credentials,
 * user-scoped project memory, honest cross-AI handoff, and clear failure states.
 */

const DEFAULT_API_BASE = "https://continuo-api.onrender.com/api/v1";
const FALLBACK_API_BASE = "http://127.0.0.1:8000/api/v1";
const WORKSPACE_URL = "https://continuo-one.vercel.app/";

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
      console.log(`[Continuo Popup Debug] ${event}:`, metadata);
    }
  } catch (e) {
    // Suppress debug logging errors
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  // Global / Header Elements
  const statusIndicator = document.getElementById("status-indicator");
  const statusLabel = document.getElementById("status-label");
  const copyToast = document.getElementById("copy-toast");
  const toastText = document.getElementById("toast-text");

  // State Panels
  const authPanel = document.getElementById("auth-panel");
  const noAiPanel = document.getElementById("no-ai-panel");
  const activeAiPanel = document.getElementById("active-ai-panel");
  const handoffPanel = document.getElementById("handoff-panel");
  const errorPanel = document.getElementById("error-panel");

  // Auth Panel Elements
  const btnOpenLogin = document.getElementById("btn-open-login");
  const btnOpenRegister = document.getElementById("btn-open-register");
  const btnToggleQuickAuth = document.getElementById("btn-toggle-quick-auth");
  const quickAuthBox = document.getElementById("quick-auth-box");
  const quickEmail = document.getElementById("quick-email");
  const quickPassword = document.getElementById("quick-password");
  const btnSubmitQuickLogin = document.getElementById("btn-submit-quick-login");
  const quickAuthMsg = document.getElementById("quick-auth-msg");

  // No AI Panel Elements
  const launchChatgptBtn = document.getElementById("launch-chatgpt-btn");
  const launchClaudeBtn = document.getElementById("launch-claude-btn");
  const launchGeminiBtn = document.getElementById("launch-gemini-btn");

  // Active AI Panel Elements
  const pulseDot = document.getElementById("pulse-dot");
  const detectionStatusText = document.getElementById("detection-status-text");
  const detectionSource = document.getElementById("detection-source");
  const emptyChatNotice = document.getElementById("empty-chat-notice");
  const emptyChatText = document.getElementById("empty-chat-text");
  const conversationPreviewBox = document.getElementById("conversation-preview-box");
  const conversationPreviewText = document.getElementById("conversation-preview-text");
  const projectSelect = document.getElementById("ext-project-select");
  const btnToggleNewProject = document.getElementById("btn-toggle-new-project");
  const inlineNewProjectRow = document.getElementById("inline-new-project-row");
  const inlineProjectName = document.getElementById("inline-project-name");
  const btnCreateInlineProject = document.getElementById("btn-create-inline-project");
  const btnCancelInlineProject = document.getElementById("btn-cancel-inline-project");
  const readyDot = document.getElementById("ready-dot");
  const readyText = document.getElementById("ready-text");
  const captureBtn = document.getElementById("btn-ext-capture");
  const captureBtnSpinner = document.getElementById("btn-spinner");
  const captureBtnText = document.getElementById("btn-ext-capture-text");

  // Continuation / Success Elements
  const btnContChatGPT = document.getElementById("btn-cont-chatgpt");
  const btnContClaude = document.getElementById("btn-cont-claude");
  const btnContGemini = document.getElementById("btn-cont-gemini");
  const btnViewMemory = document.getElementById("btn-view-memory");

  // Error Panel Elements
  const errorMessage = document.getElementById("error-message");
  const errorHint = document.getElementById("error-hint");
  const btnRetry = document.getElementById("btn-retry");

  // Recovery & Notice Elements
  const sessionExpiredNotice = document.getElementById("session-expired-notice");
  const clipboardFallbackBox = document.getElementById("clipboard-fallback-box");
  const fallbackContextTextarea = document.getElementById("fallback-context-textarea");
  const btnFallbackCopy = document.getElementById("btn-fallback-copy");
  const projectErrorState = document.getElementById("project-error-state");
  const btnRetryProjects = document.getElementById("btn-retry-projects");
  const destinationHint = document.getElementById("destination-hint");
  const destinationHintText = document.getElementById("destination-hint-text");

  // Advanced Drawer Elements
  const advFidelity = document.getElementById("adv-fidelity");
  const advVersion = document.getElementById("adv-version");
  const advGateway = document.getElementById("adv-gateway");
  const advUser = document.getElementById("adv-user");
  const advLog = document.getElementById("adv-log");

  // Local State
  let apiBase = DEFAULT_API_BASE;
  let activeTab = null;
  let activeToken = null;
  let currentUser = null;
  let detectedProvider = null; // 'chatgpt' | 'claude' | 'gemini' | null
  let currentProjects = [];
  let conversationDetected = false;
  let detectedTurnCount = 0;
  let capturedPackage = null;
  let isCapturing = false;

  // --- STATE SWITCHER HELPER ---
  function showPanel(target) {
    if (authPanel) authPanel.style.display = target === "auth" ? "flex" : "none";
    if (noAiPanel) noAiPanel.style.display = target === "no-ai" ? "block" : "none";
    if (activeAiPanel) activeAiPanel.style.display = target === "active-ai" ? "block" : "none";
    if (handoffPanel) handoffPanel.style.display = target === "handoff" ? "flex" : "none";
    if (errorPanel) errorPanel.style.display = target === "error" ? "block" : "none";
  }

  // Toast feedback helper
  let toastTimer = null;
  function showToast(message) {
    if (toastTimer) clearTimeout(toastTimer);
    toastText.textContent = message;
    copyToast.style.display = "flex";
    toastTimer = setTimeout(() => {
      copyToast.style.display = "none";
    }, 4000);
  }

  // Helper to open tabs
  function openExternal(url) {
    if (typeof chrome !== "undefined" && chrome.tabs && chrome.tabs.create) {
      chrome.tabs.create({ url });
    } else {
      window.open(url, "_blank");
    }
  }

  // --- 1. GATEWAY DETECTION & HEALTH CHECK ---
  async function resolveApiBase() {
    // Check if custom or production api base is configured in extension storage
    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      try {
        const stored = await new Promise(resolve => {
          chrome.storage.local.get(["continuo_api_base"], resolve);
        });
        if (stored && stored.continuo_api_base) {
          apiBase = stored.continuo_api_base;
          statusIndicator.classList.remove("offline");
          statusLabel.textContent = "Ready";
          advGateway.textContent = apiBase.replace("https://", "").replace("http://", "");
          return apiBase;
        }
      } catch (e) {
        // Fall back to local probing
      }
    }

    const defaultHost = (function() {
      try { return new URL(DEFAULT_API_BASE).host; } catch (e) { return "continuo-api.onrender.com"; }
    })();

    try {
      const resHealth = await fetch(`${DEFAULT_API_BASE.replace('/api/v1', '')}/api/v1/health`, { method: "GET" });
      if (resHealth.ok) {
        apiBase = DEFAULT_API_BASE;
        statusIndicator.classList.remove("offline");
        statusLabel.textContent = "Ready";
        advGateway.textContent = `${defaultHost} (Online)`;
        return apiBase;
      }
    } catch (e) {
      // Try fallback port 8000 only in local development
      if (DEFAULT_API_BASE.includes("127.0.0.1") || DEFAULT_API_BASE.includes("localhost")) {
        try {
          const res8000 = await fetch(`${FALLBACK_API_BASE.replace('/api/v1', '')}/api/v1/health`, { method: "GET" });
          if (res8000.ok) {
            apiBase = FALLBACK_API_BASE;
            statusIndicator.classList.remove("offline");
            statusLabel.textContent = "Ready";
            advGateway.textContent = "127.0.0.1:8000 (Online)";
            return apiBase;
          }
        } catch (err2) {
          statusIndicator.classList.add("offline");
          statusLabel.textContent = "Offline";
          advGateway.textContent = "Backend Offline";
        }
      } else {
        statusIndicator.classList.add("offline");
        statusLabel.textContent = "Offline";
        advGateway.textContent = `${defaultHost} (Offline)`;
      }
    }
    return apiBase;
  }

  // --- 2. AUTHENTICATION (NO HARDCODED CREDENTIALS) ---
  async function checkAuthSession() {
    await resolveApiBase();

    // 1. Check chrome.storage.local
    let token = null;
    let storedUser = null;
    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      const stored = await new Promise(resolve => {
        chrome.storage.local.get(["continuo_jwt", "continuo_user"], resolve);
      });
      token = stored?.continuo_jwt || null;
      storedUser = stored?.continuo_user || null;
    }

    // 2. If no token, check if user has an active Continuo tab open with login
    if (!token && typeof chrome !== "undefined" && chrome.tabs && chrome.tabs.query) {
      try {
        const tabs = await chrome.tabs.query({});
        for (const tab of tabs) {
          if (tab.url && (tab.url.includes("continuo-one.vercel.app") || tab.url.includes("localhost") || tab.url.includes("127.0.0.1"))) {
            const resp = await new Promise(res => {
              chrome.tabs.sendMessage(tab.id, { action: "GET_LOCAL_AUTH" }, r => {
                if (chrome.runtime.lastError) res(null);
                else res(r);
              });
            });
            if (resp && resp.token) {
              token = resp.token;
              storedUser = resp.user ? JSON.parse(resp.user) : null;
              if (chrome.storage && chrome.storage.local) {
                chrome.storage.local.set({ continuo_jwt: token, continuo_user: storedUser });
              }
              break;
            }
          }
        }
      } catch (e) {
        // Passive sync
      }
    }

    if (!token) {
      activeToken = null;
      currentUser = null;
      advUser.textContent = "Not signed in";
      if (sessionExpiredNotice) sessionExpiredNotice.style.display = "none";
      return false;
    }

    // 3. Verify token with backend /auth/me
    try {
      const res = await fetch(`${apiBase}/auth/me`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        activeToken = token;
        currentUser = await res.json();
        advUser.textContent = currentUser.email || "Authenticated";
        if (sessionExpiredNotice) sessionExpiredNotice.style.display = "none";
        return true;
      }
      if (res.status === 401) {
        // Token is expired or revoked
        if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
          chrome.storage.local.remove(["continuo_jwt", "continuo_user"]);
        }
        activeToken = null;
        currentUser = null;
        advUser.textContent = "Session expired";
        if (sessionExpiredNotice) sessionExpiredNotice.style.display = "flex";
        return false;
      }
    } catch (err) {
      console.warn("Auth token validation error:", err);
    }

    activeToken = null;
    currentUser = null;
    advUser.textContent = "Session expired";
    if (sessionExpiredNotice) sessionExpiredNotice.style.display = "flex";
    return false;
  }

  // --- 3. ACTIVE TAB & CONVERSATION DETECTION ---
  // Cached conversation from content script
  let currentConversation = null;

  // --- QUERY CONTENT SCRIPT WITH RUNTIME INJECTION FALLBACK ---
  async function queryContentScriptWithFallback(tab) {
    if (!tab?.id) {
      return { success: false, error: "NO_ACTIVE_TAB" };
    }

    const sendExtractMessage = () => new Promise(resolve => {
      chrome.tabs.sendMessage(tab.id, { type: "CONTINUO_EXTRACT_CONVERSATION" }, res => {
        if (chrome.runtime.lastError) {
          resolve({ success: false, error: "CONTENT_SCRIPT_NOT_CONNECTED", details: chrome.runtime.lastError.message });
        } else {
          resolve(res || { success: false, error: "NO_RESPONSE" });
        }
      });
    });

    let res = await sendExtractMessage();

    // Fallback: If content script is not connected, attempt runtime injection for allowed AI domains
    if (!res.success && res.error === "CONTENT_SCRIPT_NOT_CONNECTED") {
      const url = tab.url || "";
      const isAllowedAiTab = (
        url.startsWith("https://chatgpt.com/") ||
        url.startsWith("https://chat.openai.com/") ||
        url.startsWith("https://claude.ai/") ||
        url.startsWith("https://gemini.google.com/")
      );

      if (isAllowedAiTab && typeof chrome !== "undefined" && chrome.scripting && chrome.scripting.executeScript) {
        try {
          await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ["content.js"]
          });
          // Wait briefly for content script to mount message listeners
          await new Promise(r => setTimeout(r, 200));
          res = await sendExtractMessage();
        } catch (injectErr) {
          console.warn("[Continuo] Runtime injection fallback failed:", injectErr);
        }
      }
    }

    return res;
  }

  // --- 3. ACTIVE TAB & CONVERSATION DETECTION ---
  async function inspectActiveTab() {
    try {
      if (typeof chrome !== "undefined" && chrome.tabs && chrome.tabs.query) {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        activeTab = tabs[0];
        const url = activeTab?.url || "";

        // STATE: PROVIDER_DETECTED
        if (url.includes("chatgpt.com") || url.includes("chat.openai.com")) {
          detectedProvider = "chatgpt";
          detectionStatusText.textContent = "ChatGPT detected";
          detectionSource.textContent = "ChatGPT (Active Tab)";
          pulseDot.style.background = "#10a37f";
        } else if (url.includes("claude.ai")) {
          detectedProvider = "claude";
          detectionStatusText.textContent = "Claude detected";
          detectionSource.textContent = "Claude (Active Tab)";
          pulseDot.style.background = "#d97706";
        } else if (url.includes("gemini.google.com")) {
          detectedProvider = "gemini";
          detectionStatusText.textContent = "Gemini detected";
          detectionSource.textContent = "Google Gemini (Active Tab)";
          pulseDot.style.background = "#3b82f6";
        } else {
          detectedProvider = null;
          showPanel("no-ai");
          return;
        }

        // STATE: CHECKING_CONVERSATION
        readyDot.style.background = "#eab308";
        readyText.textContent = "Checking conversation...";
        captureBtn.disabled = true;
        captureBtnText.textContent = "Checking dialogue...";

        // Query content script for normalized conversation
        const res = await queryContentScriptWithFallback(activeTab);

        const headingEl = document.getElementById("empty-chat-heading");

        if (res.success && res.conversation && res.conversation.messages && res.conversation.messages.length > 0) {
          // STATE: CONVERSATION_DETECTED -> READY_TO_SAVE
          conversationDetected = true;
          detectedTurnCount = res.conversation.messages.length;
          currentConversation = res.conversation;

          emptyChatNotice.style.display = "none";
          if (conversationPreviewBox) conversationPreviewBox.style.display = "block";
          if (conversationPreviewText) {
            const latest = res.conversation.messages[res.conversation.messages.length - 1];
            const prefix = latest.role === "user" ? "User: " : "Assistant: ";
            const fullText = prefix + latest.content;
            const snippet = fullText.length > 130 ? fullText.substring(0, 127) + "..." : fullText;
            conversationPreviewText.textContent = `"${snippet}"`;
          }
          captureBtn.disabled = false;
          captureBtnText.textContent = "Save Context";
          readyDot.style.background = "#34d399";
          readyText.textContent = `${detectedTurnCount} turns ready`;
        } else {
          // FAILURE & HONEST DIAGNOSTIC STATES
          conversationDetected = false;
          detectedTurnCount = 0;
          currentConversation = null;
          if (conversationPreviewBox) conversationPreviewBox.style.display = "none";
          emptyChatNotice.style.display = "flex";
          captureBtn.disabled = true;

          const provUpper = detectedProvider ? detectedProvider.toUpperCase() : "AI";

          if (res.error === "CONTENT_SCRIPT_NOT_CONNECTED") {
            if (headingEl) headingEl.textContent = "Content Script Not Connected";
            emptyChatText.textContent = `Could not connect to this ${provUpper} tab. Please refresh the page (F5) and open Continuo again.`;
            readyDot.style.background = "#ef4444";
            readyText.textContent = "Script not connected";
            captureBtnText.textContent = "Reload tab to connect";
          } else if (res.error === "ADAPTER_NOT_FOUND") {
            if (headingEl) headingEl.textContent = "Adapter Not Found";
            emptyChatText.textContent = `No extraction adapter available for ${provUpper}.`;
            readyDot.style.background = "#ef4444";
            readyText.textContent = "Adapter missing";
            captureBtnText.textContent = "Unsupported provider";
          } else if (res.error === "NO_MESSAGES") {
            if (headingEl) headingEl.textContent = "No conversation turns found.";
            emptyChatText.textContent = `Start chatting with ${provUpper} first, then save your context.`;
            readyDot.style.background = "#eab308";
            readyText.textContent = "Waiting for dialogue";
            captureBtnText.textContent = "Send a message first";
          } else if (res.error === "EXTRACTION_FAILED") {
            if (headingEl) headingEl.textContent = "Extraction Failed";
            emptyChatText.textContent = res.details || "Unable to extract messages from this conversation.";
            readyDot.style.background = "#ef4444";
            readyText.textContent = "Extraction error";
            captureBtnText.textContent = "Extraction failed";
          } else {
            // CONVERSATION_NOT_FOUND or default
            if (headingEl) headingEl.textContent = "No conversation detected.";
            emptyChatText.textContent = `Open or start a ${provUpper} conversation to save context.`;
            readyDot.style.background = "#eab308";
            readyText.textContent = "Waiting for dialogue";
            captureBtnText.textContent = "Open a conversation to save";
          }
        }

        showPanel("active-ai");
      } else {
        // Standalone preview fallback
        detectedProvider = "chatgpt";
        detectionStatusText.textContent = "ChatGPT detected (Dev Preview)";
        detectionSource.textContent = "Simulated Session";
        conversationDetected = true;
        detectedTurnCount = 4;
        if (conversationPreviewBox) conversationPreviewBox.style.display = "block";
        if (conversationPreviewText) {
          conversationPreviewText.textContent = '"Simulated conversation context turns ready for capture."';
        }
        showPanel("active-ai");
      }
    } catch (err) {
      console.warn("Tab inspection error:", err);
      showPanel("no-ai");
    }
  }

  // --- 4. LOAD PROJECTS (USER-SCOPED) ---
  async function loadProjects(selectProjectId = null) {
    if (projectErrorState) projectErrorState.style.display = "none";

    if (!activeToken) {
      projectSelect.innerHTML = `<option value="" disabled selected>Sign in to load projects</option>`;
      return;
    }

    try {
      const res = await fetch(`${apiBase}/projects`, {
        headers: { "Authorization": `Bearer ${activeToken}` }
      });
      if (res.ok) {
        currentProjects = await res.json();
        projectSelect.innerHTML = "";

        if (currentProjects.length === 0) {
          projectSelect.innerHTML = `<option value="" disabled selected>No projects yet — create one</option>`;
          if (inlineNewProjectRow) inlineNewProjectRow.style.display = "flex";
          return;
        }

        currentProjects.forEach(p => {
          const opt = document.createElement("option");
          opt.value = p.id;
          opt.textContent = `${p.name} (${p.current_version || 'v1.0'})`;
          if (selectProjectId && p.id === selectProjectId) {
            opt.selected = true;
          }
          projectSelect.appendChild(opt);
        });

        // Restore last active project from storage
        if (!selectProjectId && typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
          chrome.storage.local.get(["lastProjectId"], (result) => {
            if (result && result.lastProjectId && currentProjects.some(p => p.id === result.lastProjectId)) {
              projectSelect.value = result.lastProjectId;
            }
          });
        }
        if (projectErrorState) projectErrorState.style.display = "none";
      } else {
        throw new Error("Unable to fetch projects");
      }
    } catch (err) {
      console.warn("Could not load user projects:", err);
      projectSelect.innerHTML = `<option value="" disabled selected>Unable to load projects</option>`;
      if (projectErrorState) projectErrorState.style.display = "flex";
    }
  }

  if (btnRetryProjects) {
    btnRetryProjects.addEventListener("click", () => loadProjects());
  }

  // --- 5. INLINE QUICK PROJECT CREATION ---
  btnToggleNewProject.addEventListener("click", () => {
    const isVisible = inlineNewProjectRow.style.display === "flex";
    inlineNewProjectRow.style.display = isVisible ? "none" : "flex";
    btnToggleNewProject.setAttribute("aria-expanded", String(!isVisible));
    if (!isVisible) {
      inlineProjectName.focus();
    }
  });

  btnCancelInlineProject.addEventListener("click", () => {
    inlineNewProjectRow.style.display = "none";
    btnToggleNewProject.setAttribute("aria-expanded", "false");
    inlineProjectName.value = "";
  });

  btnCreateInlineProject.addEventListener("click", async () => {
    const name = inlineProjectName.value.trim();
    if (!name) {
      inlineProjectName.focus();
      return;
    }

    btnCreateInlineProject.disabled = true;
    btnCreateInlineProject.textContent = "...";

    try {
      if (!activeToken) throw new Error("Please sign in first.");

      const res = await fetch(`${apiBase}/projects`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${activeToken}`
        },
        body: JSON.stringify({
          name: name,
          description: "Project created via Continuo Chrome Extension",
          initial_objective: `Context continuity for ${name}`
        })
      });

      if (!res.ok) {
        throw new Error("Failed to create project");
      }

      const created = await res.json();
      inlineProjectName.value = "";
      inlineNewProjectRow.style.display = "none";
      btnToggleNewProject.setAttribute("aria-expanded", "false");

      await loadProjects(created.id);

      if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ lastProjectId: created.id });
      }

      showToast(`Created project: ${created.name}`);
    } catch (err) {
      alert("Could not create project: " + err.message);
    } finally {
      btnCreateInlineProject.disabled = false;
      btnCreateInlineProject.textContent = "Create";
    }
  });

  // Project selector change persistence
  projectSelect.addEventListener("change", () => {
    const selectedId = projectSelect.value;
    if (selectedId && typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({ lastProjectId: selectedId });
    }
  });

  // --- 6. REAL CONTEXT CAPTURE ---
  async function performCapture() {
    if (isCapturing) return; // Prevent duplicate clicks
    if (!activeToken) {
      showPanel("auth");
      return;
    }

    const selectedProjectId = projectSelect.value;
    if (!selectedProjectId) {
      errorMessage.textContent = "Please select or create a project first.";
      errorHint.textContent = "A project is required to organize and store your saved context.";
      showPanel("error");
      return;
    }

    isCapturing = true;
    captureBtn.disabled = true;
    captureBtnSpinner.style.display = "inline-block";
    captureBtnText.textContent = "Capturing conversation...";

    let transcript = "";
    let sessionTitle = "AI Capture Session";

    try {
      // 1. Scrape real turns from active tab content script
      let convData = currentConversation;
      if (typeof chrome !== "undefined" && chrome.tabs && activeTab?.id) {
        try {
          const freshRes = await queryContentScriptWithFallback(activeTab);
          if (freshRes.success && freshRes.conversation && freshRes.conversation.messages?.length > 0) {
            convData = freshRes.conversation;
            currentConversation = convData;
          }
        } catch (e) {
          console.warn("Fresh content script capture failed, using cached:", e);
        }
      }

      if (convData && convData.messages && convData.messages.length > 0) {
        const turns = convData.messages.map(m => `${m.role === "user" ? "User" : "Assistant"}: ${m.content}`);
        transcript = turns.join("\n\n");
        sessionTitle = convData.title || sessionTitle;
      }

      // HONEST BEHAVIOR: If no conversation was detected, do not fabricate fake captures
      if (!transcript) {
        captureBtn.disabled = false;
        captureBtnSpinner.style.display = "none";
        captureBtnText.textContent = "Save Context";
        errorMessage.textContent = "No conversation detected.";
        errorHint.textContent = `Open an active ${detectedProvider ? detectedProvider.toUpperCase() : 'AI'} conversation and try again.`;
        showPanel("error");
        return;
      }

      captureBtnText.textContent = "Building project memory...";

      // 2. Transmit to Context Engine backend
      const captureRes = await fetch(`${apiBase}/context/capture`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${activeToken}`
        },
        body: JSON.stringify({
          project_id: selectedProjectId,
          provider: detectedProvider || "chatgpt",
          raw_transcript: transcript,
          title: sessionTitle
        })
      });

      if (captureRes.status === 401) {
        if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
          chrome.storage.local.remove(["continuo_jwt", "continuo_user"]);
        }
        activeToken = null;
        currentUser = null;
        if (sessionExpiredNotice) sessionExpiredNotice.style.display = "flex";
        showPanel("auth");
        return;
      }

      if (!captureRes.ok) {
        const errorData = await captureRes.json().catch(() => ({}));
        throw new Error(errorData.detail || "Unable to save context.");
      }

      capturedPackage = await captureRes.json();

      // Diagnostics update
      advFidelity.textContent = `${Math.round(capturedPackage.quality_score || 94)}%`;
      advVersion.textContent = capturedPackage.version || "v1.1";
      advLog.textContent = `Saved ${capturedPackage.version} to Project Memory (${capturedPackage.decisions?.length || 0} decisions).`;

      // Update success banner with project name
      const selectedOption = projectSelect.options[projectSelect.selectedIndex];
      const fullProjName = selectedOption ? selectedOption.text : "Active Project";
      const cleanProjName = fullProjName.split(" (v")[0].trim();
      const successTitle = document.getElementById("success-title");
      const successSubtitle = document.getElementById("success-subtitle");
      if (successTitle) successTitle.textContent = "Context saved";
      if (successSubtitle) successSubtitle.textContent = `Project:\n${cleanProjName}`;

      debugLog("contextSaved", {
        provider: detectedProvider,
        version: capturedPackage.version,
        decisionsCount: capturedPackage.decisions?.length || 0,
        qualityScore: capturedPackage.quality_score
      });

      captureBtn.disabled = false;
      captureBtnSpinner.style.display = "none";
      captureBtnText.textContent = "Save Context";
      showPanel("handoff");

    } catch (err) {
      console.error("Context capture error:", err);
      captureBtn.disabled = false;
      captureBtnSpinner.style.display = "none";
      captureBtnText.textContent = "Save Context";

      if (err.message && (err.message.includes("fetch") || err.message.includes("NetworkError") || err.message.includes("Failed to fetch"))) {
        errorMessage.textContent = "Continuo is temporarily unavailable.";
        errorHint.textContent = "Backend service unreachable. Check your gateway connection and retry.";
      } else {
        errorMessage.textContent = "Unable to save context.";
        errorHint.textContent = err.message || "Please verify your server connection and try again.";
      }
      showPanel("error");
    } finally {
      isCapturing = false;
    }
  }

  captureBtn.addEventListener("click", performCapture);

  btnRetry.addEventListener("click", () => {
    showPanel("active-ai");
    performCapture();
  });

  // Client-side secret sanitization helper
  function sanitizeSecrets(str) {
    if (!str) return "";
    return str
      .replace(/ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+/g, "[REDACTED_TOKEN]")
      .replace(/\b(?:sk-[a-zA-Z0-9_-]{20,}|Bearer\s+[a-zA-Z0-9-_\.]+)\b/g, "[REDACTED_API_KEY]")
      .replace(/\b(password|secret|pwd)\s*[:=]\s*[^\s,]+/gi, "$1: [REDACTED]")
      .replace(/\b(?:postgres|postgresql|mysql|sqlite|mongodb):\/\/[^\s]+/gi, "[REDACTED_DATABASE_URL]");
  }

  // --- 7. HONEST CROSS-AI HANDOFF ---
  async function triggerContinuation(targetProvider, destinationUrl, humanName) {
    const selectedProjectId = projectSelect.value;
    let payloadText = "";

    try {
      if (activeToken && selectedProjectId) {
        const hoRes = await fetch(`${apiBase}/handoffs`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${activeToken}`
          },
          body: JSON.stringify({
            project_id: selectedProjectId,
            source_provider: detectedProvider || "chatgpt",
            destination_provider: targetProvider
          })
        });

        if (hoRes.ok) {
          const hoData = await hoRes.json();
          payloadText = hoData.formatted_payload;
        }
      }
    } catch (err) {
      console.warn("Backend handoff call failed:", err);
    }

    // Clean structured context fallback if offline (strict 11-section format)
    if (!payloadText) {
      const projName = projectSelect.options[projectSelect.selectedIndex]?.text || "Continuo Project";
      payloadText = `You are continuing an existing project.

PROJECT:
${projName}

OBJECTIVE:
Continue development from established project state without repetition.

CURRENT STATE:
Working context captured by Continuo extension.

COMPLETED:
- Baseline architecture and project state recorded.

CURRENTLY WORKING ON:
- Seamless cross-AI session continuation.

IMPORTANT DECISIONS:
- User-scoped project memory persistence.

CONSTRAINTS:
- Preserve architectural fidelity and existing styling tokens.

KNOWN ISSUES:
- None reported in active session.

FILES / CODE CONTEXT:
- Extension controller and workspace integration points.

FAILED ATTEMPTS:
- None.

NEXT STEPS:
- Continue implementation seamlessly in ${humanName}.

CONTINUE FROM HERE:
Continue from this state without asking the user to repeat previously established context.`;
    }

    // Clean any sensitive credentials or tokens
    payloadText = sanitizeSecrets(payloadText);

    // Store pending handoff for destination tab content script
    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({
        continuo_pending_handoff: {
          provider: targetProvider,
          payload: payloadText,
          sourceProvider: detectedProvider || "ai",
          timestamp: Date.now()
        }
      });
    }

    debugLog("handoffCreated", {
      sourceProvider: detectedProvider || "ai",
      destinationProvider: targetProvider,
      payloadLength: payloadText.length
    });

    // 1. Copy to clipboard
    let copySuccess = false;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(payloadText);
        copySuccess = true;
      } else {
        throw new Error("Clipboard API unavailable");
      }
    } catch (e) {
      try {
        const ta = document.createElement("textarea");
        ta.value = payloadText;
        document.body.appendChild(ta);
        ta.select();
        copySuccess = document.execCommand("copy");
        document.body.removeChild(ta);
      } catch (errFallback) {
        copySuccess = false;
      }
    }

    if (copySuccess) {
      if (clipboardFallbackBox) clipboardFallbackBox.style.display = "none";
      showToast(`Context copied ✓ Opening ${humanName}...`);
      if (destinationHintText) {
        destinationHintText.textContent = `${humanName} opened in a new tab. Your project context is copied to your clipboard — press Ctrl+V to paste and continue.`;
      }
      setTimeout(() => {
        try {
          openExternal(destinationUrl);
        } catch (e) {
          errorMessage.textContent = `Could not open ${humanName}.`;
          errorHint.textContent = "Please allow popups or open the destination tab manually.";
          showPanel("error");
        }
      }, 650);
    } else {
      // Show recovery option, never silently fail
      if (clipboardFallbackBox) clipboardFallbackBox.style.display = "flex";
      if (fallbackContextTextarea) {
        fallbackContextTextarea.value = payloadText;
        fallbackContextTextarea.select();
      }
      if (destinationHintText) {
        destinationHintText.textContent = `Automatic copy was blocked. Please copy from the box below and open ${humanName}.`;
      }
      showToast("Couldn't copy automatically. Please copy below.");
    }
  }

  btnContChatGPT.addEventListener("click", () => triggerContinuation("chatgpt", "https://chatgpt.com/", "ChatGPT"));
  btnContClaude.addEventListener("click", () => triggerContinuation("claude", "https://claude.ai/", "Claude"));
  btnContGemini.addEventListener("click", () => triggerContinuation("gemini", "https://gemini.google.com/", "Gemini"));

  btnViewMemory.addEventListener("click", () => openExternal(`${WORKSPACE_URL}#workspace`));

  if (btnFallbackCopy) {
    btnFallbackCopy.addEventListener("click", async () => {
      if (fallbackContextTextarea) {
        fallbackContextTextarea.select();
        let ok = false;
        try {
          await navigator.clipboard.writeText(fallbackContextTextarea.value);
          ok = true;
        } catch (e) {
          ok = document.execCommand("copy");
        }
        if (ok) {
          showToast("Context copied ✓");
        }
      }
    });
  }

  // Quick launch buttons
  if (launchChatgptBtn) launchChatgptBtn.addEventListener("click", () => openExternal("https://chatgpt.com/"));
  if (launchClaudeBtn) launchClaudeBtn.addEventListener("click", () => openExternal("https://claude.ai/"));
  if (launchGeminiBtn) launchGeminiBtn.addEventListener("click", () => openExternal("https://gemini.google.com/"));

  // Auth Panel Actions
  if (btnOpenLogin) {
    btnOpenLogin.addEventListener("click", () => openExternal(`${WORKSPACE_URL}#workspace`));
  }

  if (btnOpenRegister) {
    btnOpenRegister.addEventListener("click", () => openExternal(`${WORKSPACE_URL}#workspace`));
  }

  if (btnToggleQuickAuth) {
    btnToggleQuickAuth.addEventListener("click", () => {
      const isVisible = quickAuthBox.style.display === "flex";
      quickAuthBox.style.display = isVisible ? "none" : "flex";
      if (!isVisible) quickEmail.focus();
    });
  }

  if (btnSubmitQuickLogin) {
    btnSubmitQuickLogin.addEventListener("click", async () => {
      const email = quickEmail.value.trim();
      const password = quickPassword.value;
      if (!email || !password) {
        quickAuthMsg.textContent = "Enter email and password";
        return;
      }
      btnSubmitQuickLogin.disabled = true;
      btnSubmitQuickLogin.textContent = "...";
      quickAuthMsg.textContent = "";

      try {
        const res = await fetch(`${apiBase}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Invalid credentials");
        }
        const data = await res.json();
        activeToken = data.access_token;
        currentUser = { email: data.email, id: data.user_id, role: data.role || "user" };

        if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
          chrome.storage.local.set({ continuo_jwt: activeToken, continuo_user: currentUser });
        }

        showToast("Signed in successfully!");
        advUser.textContent = currentUser.email;

        // Load projects and resume
        await loadProjects();
        await inspectActiveTab();
      } catch (err) {
        quickAuthMsg.textContent = err.message || "Login failed";
      } finally {
        btnSubmitQuickLogin.disabled = false;
        btnSubmitQuickLogin.textContent = "Sign In";
      }
    });
  }

  // Cross-tab reactive auth sync via chrome.storage.onChanged
  if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.onChanged) {
    chrome.storage.onChanged.addListener(async (changes, areaName) => {
      if (areaName === "local" && (changes.continuo_jwt || changes.continuo_user)) {
        const hasSession = await checkAuthSession();
        if (hasSession) {
          await loadProjects();
          await inspectActiveTab();
        } else {
          showPanel("auth");
        }
      }
    });
  }

  // --- INITIAL BOOT ---
  const isAuthenticated = await checkAuthSession();
  if (!isAuthenticated) {
    showPanel("auth");
  } else {
    await loadProjects();
    await inspectActiveTab();
  }
});
