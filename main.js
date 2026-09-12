/**
 * CONTINUO — Interactive Motion Engine & Storytelling Controller
 * Features:
 * 1. IntersectionObserver Stats Count-Up
 * 2. Header Scroll Blur & ScrollSpy Navigation
 * 3. Scroll Reveal Animations
 * 4. Interactive Context Engine Inspector (9 Structured Nodes)
 * 5. Interactive Project Memory Version Diff Switcher
 * 6. Sticky Walkthrough Step Controller & Window Morphing
 * 7. Live Interactive Handoff Playground & 1-Click Clipboard Copy
 * 8. Mobile Drawer Sheet Menu with ARIA Accessibility
 */

document.addEventListener("DOMContentLoaded", () => {
  initStatsCountUp();
  initHeaderScroll();
  initScrollSpy();
  initScrollReveals();
  initContextEngineInspector();
  initProjectMemoryDiff();
  initWalkthroughSteps();
  initHandoffPlayground();
  initMobileMenu();
});

/* ==========================================================================
   1. Stats Count-Up Engine (easeOutCubic, exact formulas)
   ========================================================================== */
function initStatsCountUp() {
  const statElements = document.querySelectorAll(".stat-val");
  if (!statElements.length) return;

  const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);
  let hasAnimated = false;

  const animateItem = (el, index) => {
    const target = parseFloat(el.getAttribute("data-target")) || 0;
    const suffix = el.getAttribute("data-suffix") || "";
    const decimals = parseInt(el.getAttribute("data-decimals"), 10) || 0;

    const duration = 1500 + index * 80;
    const startOffset = 480 + index * 90;

    setTimeout(() => {
      let startTime = null;

      const step = (timestamp) => {
        if (!startTime) startTime = timestamp;
        const elapsed = timestamp - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easedProgress = easeOutCubic(progress);
        const currentValue = (easedProgress * target).toFixed(decimals);

        el.textContent = `${currentValue}${suffix}`;

        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          el.textContent = `${target.toFixed(decimals)}${suffix}`;
        }
      };

      requestAnimationFrame(step);
    }, startOffset);
  };

  const startAll = () => {
    if (hasAnimated) return;
    hasAnimated = true;
    statElements.forEach((el, idx) => animateItem(el, idx));
  };

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            startAll();
            observer.disconnect();
          }
        });
      },
      { threshold: 0.25 }
    );

    const statsSec = document.getElementById("stats-section");
    if (statsSec) observer.observe(statsSec);
    else startAll();
  } else {
    startAll();
  }
}

/* ==========================================================================
   2. Header Scroll Blur & ScrollSpy Navigation
   ========================================================================== */
function initHeaderScroll() {
  let ticking = false;

  window.addEventListener("scroll", () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        if (window.scrollY > 40) {
          document.body.classList.add("scrolled");
        } else {
          document.body.classList.remove("scrolled");
        }
        ticking = false;
      });
      ticking = true;
    }
  });
}

function initScrollSpy() {
  const sections = document.querySelectorAll("section[id]");
  const navLinks = document.querySelectorAll(".nav-link");

  const onScroll = () => {
    const scrollPos = window.scrollY + 180;

    sections.forEach((sec) => {
      const top = sec.offsetTop;
      const height = sec.offsetHeight;
      const id = sec.getAttribute("id");

      if (scrollPos >= top && scrollPos < top + height) {
        navLinks.forEach((link) => {
          link.classList.remove("active");
          if (link.getAttribute("href") === `#${id}`) {
            link.classList.add("active");
          }
        });
      }
    });
  };

  window.addEventListener("scroll", onScroll, { passive: true });
}

/* ==========================================================================
   3. Scroll Reveal Animations (IntersectionObserver)
   ========================================================================== */
function initScrollReveals() {
  const revealElements = document.querySelectorAll(".reveal-on-scroll");
  if (!revealElements.length) return;

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("revealed");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -50px 0px" }
    );

    revealElements.forEach((el) => observer.observe(el));
  } else {
    revealElements.forEach((el) => el.classList.add("revealed"));
  }
}

/* ==========================================================================
   4. Interactive Context Engine Inspector (9 Structured Nodes)
   ========================================================================== */
function initContextEngineInspector() {
  const contextDetails = {
    goal: {
      title: "GOAL & OBJECTIVE",
      tag: "Extracted from 14 conversation turns",
      content:
        '"Build an AI-agnostic context continuity layer that captures structured project memory across ChatGPT, Claude, and Gemini, enabling seamless model handoffs with zero re-explanation."',
    },
    requirements: {
      title: "EXTRACTED REQUIREMENTS",
      tag: "Deterministic specs",
      content:
        '1. Chrome Extension (Manifest V3) for zero-friction DOM capture.\n2. Deterministic Context Package schema adhering to JSON Schema standard.\n3. One-click destination handoff prompt generation for Claude & Cursor.\n4. Zero training data storage guarantee.',
    },
    decisions: {
      title: "LOCKED ARCHITECTURAL DECISIONS",
      tag: "3 Decisions Recorded",
      content:
        '• Migrated backend prototype from Flask to FastAPI for async schema validation.\n• Database: Supabase PostgreSQL with Row Level Security (RLS) policies.\n• Auth: Supabase Auth with JWT refresh token rotation in httpOnly cookies.',
    },
    constraints: {
      title: "HARD CONSTRAINTS & LIMITS",
      tag: "Non-negotiable parameters",
      content:
        '• Must run within Chrome MV3 service worker lifecycle without background persistence.\n• No external third-party tracking or conversation content telemetry.\n• Total payload size compressed under 4,000 tokens for universal LLM context entry.',
    },
    files: {
      title: "FILES & CODE ARTIFACTS",
      tag: "Active repository context",
      content:
        '• api/routers/context.py (Context extraction pipeline)\n• packages/schema/context.json (Shared TypeScript/Pydantic schema)\n• apps/extension/src/content.ts (Supported AI DOM reader)\n• supabase/migrations/001_init.sql (RLS table schema)',
    },
    state: {
      title: "CURRENT WORKING STATE",
      tag: "Milestone: v1.2",
      content:
        'FastAPI API server running at /api/v1. Context generation pipeline tested with 94% completeness score. Active branch: feat/claude-handoff. Ready to implement RLS policies.',
    },
    failed: {
      title: "FAILED ATTEMPTS & DEAD ENDS",
      tag: "Prevents repeated mistakes",
      content:
        '• Attempted in-memory dictionary caching: Caused state desync across horizontal workers.\n• Attempted raw asyncpg connection pool: Event loop conflict in sub-task threads.',
    },
    problems: {
      title: "OPEN PROBLEMS & BLOCKERS",
      tag: "1 Blocker Tagged",
      content:
        '1. CORS pre-flight origin mismatch on Chrome Extension localhost development endpoint. (Fix queued: Add chrome-extension:// to FastAPI allow_origins).',
    },
    next: {
      title: "PRIORITIZED NEXT STEPS",
      tag: "Actionable tasks",
      content:
        '1. Authorize Supabase RLS policies for multi-tenant workspace tables.\n2. Finalize Manifest V3 popup review editor component.\n3. Execute integration handoff from ChatGPT to Claude 3.7.',
    },
  };

  const cards = document.querySelectorAll(".context-card");
  const titleEl = document.getElementById("inspector-title");
  const contentEl = document.getElementById("inspector-content");
  const tagEl = document.querySelector(".inspector-tag");

  cards.forEach((card) => {
    card.addEventListener("click", () => {
      cards.forEach((c) => c.classList.remove("active-card"));
      card.classList.add("active-card");

      const key = card.getAttribute("data-key");
      const data = contextDetails[key];

      if (data && titleEl && contentEl) {
        contentEl.style.opacity = "0";
        setTimeout(() => {
          titleEl.textContent = data.title;
          if (tagEl) tagEl.textContent = data.tag;
          contentEl.textContent = data.content;
          contentEl.style.opacity = "1";
        }, 150);
      }
    });
  });
}

/* ==========================================================================
   5. Interactive Project Memory Version Diff Switcher
   ========================================================================== */
function initProjectMemoryDiff() {
  const diffData = {
    v1: {
      title: "Inception v1.0 — Architecture Proposal",
      badge: "ChatGPT Exploration",
      added: [
        "Initial monorepo directory layout (apps/web, apps/extension)",
        "Draft specification of Context Package schema",
        "Basic Flask API route prototype",
      ],
      modified: [
        "Project description updated from 'AI bookmark' to 'Universal Context Bridge'",
      ],
      removed: ["Scrapped direct DOM auto-typing concept due to browser security constraints"],
    },
    v2: {
      title: "Refactor v1.1 — Backend & Auth Migration",
      badge: "ChatGPT → Claude Session",
      added: [
        "FastAPI framework with Pydantic v2 validation models",
        "Supabase Auth integration with JWT token parsing",
        "Unit tests for context extraction parser",
      ],
      modified: [
        "Replaced Flask with FastAPI for asynchronous performance",
        "Upgraded extension manifest from V2 to Manifest V3",
      ],
      removed: ["Removed raw local session storage in favor of encrypted cookie headers"],
    },
    v3: {
      title: "What Changed in v1.2 — Current Production State",
      badge: "ChatGPT → Claude Handoff",
      added: [
        "Supabase RLS access policies for user workspace isolation",
        "JWT refresh token rotation flow with secure cookie headers",
        "Context schema validation test suite",
      ],
      modified: [
        "Backend framework: Migrated from Flask prototype to production FastAPI",
        "Database schema: Added foreign key constraint on project_id",
      ],
      removed: [
        "In-memory session cache (caused multi-node state desync)",
        "Discarded legacy Flask CORS middleware",
      ],
    },
  };

  const tabs = document.querySelectorAll(".ver-tab");
  const titleEl = document.getElementById("diff-title");
  const badgeEl = document.getElementById("diff-badge");
  const addedEl = document.getElementById("diff-added");
  const modifiedEl = document.getElementById("diff-modified");
  const removedEl = document.getElementById("diff-removed");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");

      const ver = tab.getAttribute("data-ver");
      const data = diffData[ver];
      if (!data) return;

      if (titleEl) titleEl.textContent = data.title;
      if (badgeEl) badgeEl.textContent = data.badge;

      if (addedEl) {
        addedEl.innerHTML = data.added.map((item) => `<li>${item}</li>`).join("");
      }
      if (modifiedEl) {
        modifiedEl.innerHTML = data.modified.map((item) => `<li>${item}</li>`).join("");
      }
      if (removedEl) {
        removedEl.innerHTML = data.removed.map((item) => `<li>${item}</li>`).join("");
      }
    });
  });
}

/* ==========================================================================
   6. Sticky Walkthrough Step Controller & Window Morphing
   ========================================================================== */
function initWalkthroughSteps() {
  const stepCards = document.querySelectorAll(".step-card");
  const windowTitle = document.getElementById("window-title-text");
  const windowBody = document.getElementById("window-body-content");

  const stepPreviews = {
    1: {
      title: "ChatGPT — Active Conversation",
      html: `
        <div class="ext-mockup">
          <div class="ext-head">
            <div class="ext-brand">
              <i class="fa-solid fa-robot" style="color: #10b981;"></i>
              <span>ChatGPT Session</span>
            </div>
            <span class="ext-chip">42 messages • 18k tokens</span>
          </div>
          <div class="chat-msg user-msg" style="margin: 6px 0;">
            <div class="chat-role">You</div>
            <div class="chat-text">"Let's migrate the auth system to FastAPI and prepare for Claude handoff."</div>
          </div>
          <div class="chat-msg ai-msg">
            <div class="chat-role">ChatGPT</div>
            <div class="chat-text">"I have updated the token validation models and routes..."</div>
          </div>
        </div>
      `,
    },
    2: {
      title: "Continuo Extension — Manifest V3",
      html: `
        <div class="ext-mockup">
          <div class="ext-head">
            <div class="ext-brand">
              <img src="assets/logo.webp" alt="" class="ext-logo" />
              <span>CONTINUO</span>
            </div>
            <span class="ext-chip">ChatGPT Detected</span>
          </div>
          <div class="ext-card">
            <div class="ext-card-row">
              <span class="ext-muted">Active Project</span>
              <strong class="ext-bold">Nexora AI Platform</strong>
            </div>
            <div class="ext-card-row">
              <span class="ext-muted">Context Completeness</span>
              <span class="ext-green-pill">94% Health</span>
            </div>
            <div class="ext-progress-bar">
              <div class="ext-fill" style="width: 94%"></div>
            </div>
          </div>
          <div class="ext-items-summary">
            <span class="ext-badge"><i class="fa-solid fa-check"></i> 14 Decisions</span>
            <span class="ext-badge"><i class="fa-solid fa-check"></i> 6 Constraints</span>
            <span class="ext-badge"><i class="fa-solid fa-check"></i> State: v1.2</span>
          </div>
          <div class="ext-btn-row">
            <button class="ext-btn primary"><i class="fa-solid fa-cube"></i> Capture Context</button>
            <button class="ext-btn secondary"><i class="fa-solid fa-arrow-up-right-from-square"></i> Continue Elsewhere</button>
          </div>
        </div>
      `,
    },
    3: {
      title: "Continuo Web App — Context Review Editor",
      html: `
        <div class="ext-mockup">
          <div class="ext-head">
            <div class="ext-brand">
              <i class="fa-regular fa-pen-to-square" style="color: #38bdf8;"></i>
              <span>Review Context Package</span>
            </div>
            <span class="ext-chip" style="background: rgba(16, 185, 129, 0.15); color: #34d399;">Validated</span>
          </div>
          <div style="font-size: 12px; color: #d4d4d8; line-height: 1.5; background: #141416; padding: 12px; border-radius: 10px;">
            <div style="color: #38bdf8; font-weight: 600; margin-bottom: 4px;">PROJECT OBJECTIVE [EDITABLE]</div>
            <div>"Build an autonomous AI-agnostic context continuity layer across ChatGPT and Claude."</div>
            <div style="color: #38bdf8; font-weight: 600; margin-top: 10px; margin-bottom: 4px;">CONSTRAINTS (3)</div>
            <div style="color: #a1a1aa;">✓ Python 3.12+ • ✓ Supabase RLS • ✓ Manifest V3</div>
          </div>
          <button class="ext-btn primary" style="width: 100%;"><i class="fa-solid fa-check"></i> Approve & Save to Project Memory</button>
        </div>
      `,
    },
    4: {
      title: "Continuo — Select AI Destination",
      html: `
        <div class="ext-mockup">
          <div class="ext-head">
            <div class="ext-brand">
              <i class="fa-solid fa-compass" style="color: #eab308;"></i>
              <span>Choose Destination Model</span>
            </div>
          </div>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.08); padding: 10px 14px; border-radius: 10px; border: 1px solid #ffffff;">
              <span style="font-size: 13px; font-weight: 600; color: #ffffff;"><i class="fa-solid fa-bolt" style="color: #38bdf8; margin-right: 8px;"></i> Claude 3.7 Sonnet</span>
              <span style="font-size: 11px; color: #34d399; font-weight: 600;">Optimal for Code Refactoring</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; background: #141416; padding: 10px 14px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.08);">
              <span style="font-size: 13px; color: #a1a1aa;"><i class="fa-solid fa-terminal" style="margin-right: 8px;"></i> Cursor IDE</span>
              <span style="font-size: 11px; color: #71717a;">Local Workspace Agent</span>
            </div>
          </div>
          <button class="ext-btn primary" style="width: 100%;"><i class="fa-solid fa-paper-plane"></i> Prepare Optimized Handoff</button>
        </div>
      `,
    },
    5: {
      title: "Claude 3.7 — Instant Working Continuation",
      html: `
        <div class="ext-mockup">
          <div class="ext-head">
            <div class="ext-brand">
              <i class="fa-solid fa-bolt" style="color: #38bdf8;"></i>
              <span>Claude 3.7 Active</span>
            </div>
            <span class="ext-chip" style="color: #34d399;">Zero Explanation</span>
          </div>
          <div class="chat-msg ai-msg">
            <div class="chat-role">Claude 3.7</div>
            <div class="chat-text">"I have received the Nexora v1.2 Context Package. I see the FastAPI auth endpoints are in place. Now implementing the Supabase RLS policies as requested in your NEXT STEPS."</div>
          </div>
          <div style="display: flex; align-items: center; gap: 8px; font-size: 12px; color: #34d399; margin-top: 6px;">
            <i class="fa-solid fa-circle-check"></i> Continuation succeeded in 1.4 seconds
          </div>
        </div>
      `,
    },
  };

  stepCards.forEach((card) => {
    card.addEventListener("click", () => {
      stepCards.forEach((c) => c.classList.remove("active-step"));
      card.classList.add("active-step");

      const step = card.getAttribute("data-step");
      const preview = stepPreviews[step];

      if (preview && windowTitle && windowBody) {
        windowBody.style.opacity = "0";
        setTimeout(() => {
          windowTitle.textContent = preview.title;
          windowBody.innerHTML = preview.html;
          windowBody.style.opacity = "1";
        }, 150);
      }
    });
  });
}

/* ==========================================================================
   7. Live Interactive Handoff Playground & 1-Click Clipboard Copy
   ========================================================================== */
function initHandoffPlayground() {
  const sourceSelect = document.getElementById("source-ai-select");
  const destSelect = document.getElementById("dest-ai-select");
  const codeBlock = document.getElementById("payload-code-block");
  const copyBtn = document.getElementById("copy-payload-btn");
  const toast = document.getElementById("toast-notice");
  const toastText = document.getElementById("toast-text");

  const generatePayload = () => {
    const src = sourceSelect ? sourceSelect.value : "chatgpt";
    const dest = destSelect ? destSelect.value : "claude";

    const srcName =
      src === "chatgpt" ? "ChatGPT (o3-mini)" : src === "claude" ? "Claude 3.7" : "Gemini 2.0";
    const destName =
      dest === "claude"
        ? "Claude 3.7 Sonnet"
        : dest === "chatgpt"
        ? "ChatGPT"
        : dest === "cursor"
        ? "Cursor Agent"
        : "Gemini 2.0 Flash";

    return `You are continuing an existing software project.

PROJECT
Nexora AI Platform (v1.2) [Transferred from ${srcName} → ${destName}]

OBJECTIVE
Build an autonomous AI-agnostic context continuity layer for cross-model handoffs.

CURRENT WORKING STATE
Backend API routes /auth/login and /context/capture implemented and tested.
Database migration to Supabase PostgreSQL applied.

LOCKED ARCHITECTURAL DECISIONS
1. Framework: Python 3.12+ with FastAPI (migrated away from Flask prototype).
2. Database: Supabase PostgreSQL with RLS enabled.
3. Extension: Chrome Manifest V3 with minimal tab permissions.

REJECTED APPROACHES / FAILED ATTEMPTS
- In-memory session dictionaries failed on horizontal scaling; use JWT with refresh token rotation.
- Avoid asyncpg raw connection pool conflicts with sub-task loops.

OPEN PROBLEMS / PENDING TASKS
1. Implement Supabase RLS security policies for workspace isolation.
2. Complete Chrome Extension popup review editor.

INSTRUCTION
Continue directly from the CURRENT WORKING STATE for ${destName}. Do NOT restart from scratch or re-suggest rejected approaches.`;
  };

  const updateCode = () => {
    if (codeBlock) {
      codeBlock.textContent = generatePayload();
    }
  };

  if (sourceSelect) sourceSelect.addEventListener("change", updateCode);
  if (destSelect) destSelect.addEventListener("change", updateCode);

  // Copy button
  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      const text = codeBlock ? codeBlock.textContent : "";
      if (!text) return;

      navigator.clipboard.writeText(text).then(() => {
        showToast("Handoff payload copied to clipboard!");
      }).catch(() => {
        // Fallback
        const textarea = document.createElement("textarea");
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
        showToast("Handoff payload copied to clipboard!");
      });
    });
  }

  function showToast(msg) {
    if (!toast) return;
    if (toastText) toastText.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 3200);
  }
}

/* ==========================================================================
   8. Mobile Drawer Sheet Menu Controller
   ========================================================================== */
function initMobileMenu() {
  const burgerBtn = document.getElementById("burger-btn");
  const mobileSheet = document.getElementById("mobile-sheet");
  const mobileOverlay = document.getElementById("mobile-overlay");
  const mobileLinks = document.querySelectorAll(".mobile-link, .mobile-signin-btn");

  if (!burgerBtn || !mobileSheet || !mobileOverlay) return;

  function openMenu() {
    mobileSheet.hidden = false;
    void mobileSheet.offsetWidth;
    mobileSheet.classList.add("active");
    mobileOverlay.classList.add("active");
    document.body.classList.add("menu-open");
    burgerBtn.setAttribute("aria-expanded", "true");
  }

  function closeMenu() {
    mobileSheet.classList.remove("active");
    mobileOverlay.classList.remove("active");
    document.body.classList.remove("menu-open");
    burgerBtn.setAttribute("aria-expanded", "false");

    setTimeout(() => {
      if (!document.body.classList.contains("menu-open")) {
        mobileSheet.hidden = true;
      }
    }, 380);
  }

  function toggleMenu() {
    const isOpen = document.body.classList.contains("menu-open");
    if (isOpen) {
      closeMenu();
    } else {
      openMenu();
    }
  }

  burgerBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleMenu();
  });

  mobileOverlay.addEventListener("click", () => {
    closeMenu();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && document.body.classList.contains("menu-open")) {
      closeMenu();
      burgerBtn.focus();
    }
  });

  mobileLinks.forEach((link) => {
    link.addEventListener("click", () => {
      closeMenu();
    });
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 768 && document.body.classList.contains("menu-open")) {
      closeMenu();
    }
  });
}
