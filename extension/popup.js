/**
 * CONTINUO — Chrome Extension Popup Controller
 * Coordinates DOM scraping with the active tab and relays context to the Continuo API.
 */

const API_BASE = "http://127.0.0.1:8008/api/v1";

document.addEventListener("DOMContentLoaded", async () => {
  const statusIndicator = document.getElementById("status-indicator");
  const statusLabel = document.getElementById("status-label");
  const detectionPill = document.getElementById("detection-pill");
  const pillIcon = document.getElementById("pill-icon");
  const pillText = document.getElementById("pill-text");
  const projectSelect = document.getElementById("ext-project-select");
  const captureBtn = document.getElementById("btn-ext-capture");
  const captureBtnText = document.getElementById("btn-ext-capture-text");
  const progressBox = document.getElementById("progress-box");
  const progressTitle = document.getElementById("progress-title");
  const progressScore = document.getElementById("progress-score");
  const progressFill = document.getElementById("progress-fill");
  const progressSub = document.getElementById("progress-sub");
  const handoffCard = document.getElementById("handoff-card");
  const btnQuickClaude = document.getElementById("btn-quick-claude");
  const btnCopyRaw = document.getElementById("btn-copy-raw");

  let activeTab = null;
  let activeToken = null;
  let currentProjects = [];
  let capturedPackage = null;

  // 1. Inspect Active Tab
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    activeTab = tabs[0];
    const url = activeTab?.url || "";

    if (url.includes("chatgpt.com") || url.includes("chat.openai.com")) {
      pillIcon.textContent = "🤖";
      pillText.textContent = "ChatGPT Conversation Active";
    } else if (url.includes("claude.ai")) {
      pillIcon.textContent = "⚡";
      pillText.textContent = "Claude Workspace Active";
    } else if (url.includes("gemini.google.com")) {
      pillIcon.textContent = "✨";
      pillText.textContent = "Gemini Session Active";
    } else {
      pillIcon.textContent = "🌐";
      pillText.textContent = "Web Page (Context Ingestion Available)";
    }
  } catch (err) {
    pillText.textContent = "Active Tab Ready";
  }

  // 2. Authenticate with Continuo
  async function getAuthToken() {
    try {
      const loginRes = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: "demo@continuo.ai", password: "DemoContinuo2026!" })
      });
      if (loginRes.ok) {
        const data = await loginRes.json();
        return data.access_token;
      }
      return null;
    } catch (err) {
      statusIndicator.classList.add("offline");
      statusLabel.textContent = "Offline";
      return null;
    }
  }

  // 3. Load Projects
  async function initProjects() {
    activeToken = await getAuthToken();
    if (!activeToken) return;

    try {
      const res = await fetch(`${API_BASE}/projects`, {
        headers: { "Authorization": `Bearer ${activeToken}` }
      });
      currentProjects = await res.json();

      projectSelect.innerHTML = "";
      currentProjects.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `${p.name} (${p.current_version})`;
        projectSelect.appendChild(opt);
      });
    } catch (err) {
      console.warn("Could not load projects in extension popup:", err);
    }
  }

  await initProjects();

  // 4. Trigger Context Capture
  captureBtn.addEventListener("click", async () => {
    const selectedProjectId = projectSelect.value;
    if (!selectedProjectId) {
      alert("Please select a target project memory.");
      return;
    }

    captureBtn.disabled = true;
    captureBtnText.textContent = "Reading active tab...";
    progressBox.style.display = "flex";
    progressTitle.textContent = "Parsing Dialogue Nodes...";
    progressFill.style.width = "30%";

    // Send capture command to content script
    chrome.tabs.sendMessage(activeTab.id, { action: "CAPTURE_CONVERSATION" }, async (response) => {
      let rawTranscript = "";
      let provider = "chatgpt";
      let title = "Browser Capture";

      if (response && response.success && response.rawTranscript) {
        rawTranscript = response.rawTranscript;
        provider = response.provider || "chatgpt";
        title = response.title || "Browser AI Session";
      } else {
        // Fallback demo transcript if content script didn't match
        rawTranscript = `User: Working on authentication and project persistence layer.
Requirement: Store user sessions securely with JWT rotation.
Constraint: Zero unencrypted token exposure in local storage.
Decision: Selected FastAPI with SQLAlchemy.
Current State: Endpoints active and tested.
Next step: Connect Chrome extension to /api/v1/context/capture.`;
      }

      progressTitle.textContent = "Synthesizing Project Package...";
      progressFill.style.width = "70%";

      try {
        const captureRes = await fetch(`${API_BASE}/context/capture`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${activeToken}`
          },
          body: JSON.stringify({
            project_id: selectedProjectId,
            provider,
            raw_transcript: rawTranscript,
            title
          })
        });

        const pkg = await captureRes.json();
        capturedPackage = pkg;

        progressFill.style.width = "100%";
        progressTitle.textContent = `Saved as ${pkg.version}!`;
        progressScore.textContent = `${Math.round(pkg.quality_score)}%`;
        progressSub.textContent = `Extracted ${pkg.requirements.length} reqs, ${pkg.constraints.length} constraints, ${pkg.decisions.length} decisions.`;

        handoffCard.style.display = "flex";
        captureBtnText.textContent = "Context Captured";
      } catch (err) {
        progressTitle.textContent = "Extraction Error";
        progressSub.textContent = err.message || "Failed to contact Continuo API.";
      } finally {
        captureBtn.disabled = false;
      }
    });
  });

  // 5. Quick Handoff to Claude
  btnQuickClaude.addEventListener("click", async () => {
    if (!capturedPackage) return;
    try {
      const hoRes = await fetch(`${API_BASE}/handoffs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${activeToken}`
        },
        body: JSON.stringify({
          project_id: projectSelect.value,
          source_provider: "chatgpt",
          destination_provider: "claude"
        })
      });
      const handoff = await hoRes.json();
      await navigator.clipboard.writeText(handoff.formatted_payload);

      chrome.tabs.create({ url: "https://claude.ai/new" });
    } catch (err) {
      alert("Handoff generation error: " + err.message);
    }
  });

  // 6. Copy Raw Context
  btnCopyRaw.addEventListener("click", () => {
    if (!capturedPackage) return;
    const summary = `CONTINUO CONTEXT (${capturedPackage.version})\nGoal: ${capturedPackage.objective}\nState: ${capturedPackage.current_state}`;
    navigator.clipboard.writeText(summary);
    btnCopyRaw.textContent = "Copied!";
    setTimeout(() => { btnCopyRaw.textContent = "Copy Context"; }, 2000);
  });
});
