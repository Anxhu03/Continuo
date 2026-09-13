/**
 * CONTINUO — Interactive Motion Engine & Living Ambient Background System
 *
 * Modules:
 * 1. Global Continuo Ambient Background Engine (Canvas Context-Flow + Dynamic Aura Orbs)
 * 2. Section Scroll-Tracking & Atmosphere State Switcher
 * 3. Stats Count-Up Engine (easeOutCubic)
 * 4. Header Scroll Blur & ScrollSpy Navigation
 * 5. Scroll Reveal Animations
 * 6. Interactive Context Engine Inspector (9 Structured Nodes)
 * 7. Interactive Project Memory Version Diff Switcher
 * 8. Sticky Walkthrough Step Controller & Window Morphing
 * 9. Live Interactive Handoff Playground & 1-Click Clipboard Copy
 * 10. Mobile Drawer Sheet Menu with ARIA Accessibility
 */

/**
 * CONTINUO GLOBAL EXTENSION DISTRIBUTION CONFIGURATION
 * Reads from config.js (window.CHROME_EXTENSION_STORE_URL) or defaults to null.
 */
function getExtensionStoreUrl() {
  return typeof window !== "undefined" && window.CHROME_EXTENSION_STORE_URL !== undefined
    ? window.CHROME_EXTENSION_STORE_URL
    : null;
}

document.addEventListener("DOMContentLoaded", () => {
  initLenisSmoothScroll();
  initAmbientEngine();
  initStatsCountUp();
  initHeaderScroll();
  initScrollSpy();
  initScrollReveals();
  initCardSpotlights();
  initContextEngineInspector();
  initProjectMemoryDiff();
  initWalkthroughSteps();
  initHandoffPlayground();
  initMobileMenu();
  initExtensionCta();
  initContinuoWorkspaceApp();
});

/* ==========================================================================
   1. GLOBAL CONTINUOUS AMBIENT BACKGROUND SYSTEM
   Canvas Context-Flow Particles + Dynamic Atmospheric Aura Layers
   ========================================================================== */
function initAmbientEngine() {
  const ambientSystem = document.getElementById("ambient-system");
  const canvas = document.getElementById("continuo-ambient-canvas");
  const videoLayer = document.getElementById("ambient-video-layer");
  const gridOverlay = document.getElementById("ambient-grid-overlay");
  const auraContainer = document.getElementById("aura-container");
  if (!ambientSystem || !canvas) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  // Check reduced motion
  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  // Section-specific atmosphere profiles
  const themeProfiles = {
    hero: {
      rgb: [255, 255, 255],
      dash: [],
      speed: 1.0,
      flowX: 0,
      packetColor: "#38bdf8",
      brokenPackets: false,
      hasOrbit: false,
    },
    problem: {
      rgb: [239, 68, 68],
      dash: [4, 6],
      speed: 0.6,
      flowX: 0,
      packetColor: "#ef4444",
      brokenPackets: true,
      hasOrbit: false,
    },
    engine: {
      rgb: [56, 189, 248],
      dash: [],
      speed: 1.35,
      flowX: 0.25,
      packetColor: "#00f2fe",
      brokenPackets: false,
      hasOrbit: false,
    },
    memory: {
      rgb: [99, 102, 241],
      dash: [2, 4],
      speed: 0.7,
      flowX: 0,
      packetColor: "#818cf8",
      brokenPackets: false,
      hasOrbit: true,
    },
    mesh: {
      rgb: [168, 85, 247],
      dash: [],
      speed: 1.1,
      flowX: 0.35,
      packetColor: "#c084fc",
      brokenPackets: false,
      hasOrbit: false,
    },
    how: {
      rgb: [16, 185, 129],
      dash: [],
      speed: 1.2,
      flowX: 0.45,
      packetColor: "#10b981",
      brokenPackets: false,
      hasOrbit: false,
    },
    playground: {
      rgb: [56, 189, 248],
      dash: [],
      speed: 1.25,
      flowX: 0.5,
      packetColor: "#38bdf8",
      brokenPackets: false,
      hasOrbit: false,
    },
    privacy: {
      rgb: [148, 163, 184],
      dash: [3, 3],
      speed: 0.8,
      flowX: 0,
      packetColor: "#94a3b8",
      brokenPackets: false,
      hasOrbit: false,
    },
    cta: {
      rgb: [255, 255, 255],
      dash: [],
      speed: 1.35,
      flowX: 0.3,
      packetColor: "#ffffff",
      brokenPackets: false,
      hasOrbit: false,
    },
  };

  let currentTheme = "hero";
  let targetProfile = themeProfiles.hero;

  // Interpolated visual values for buttery smooth transition
  let activeR = 255,
    activeG = 255,
    activeB = 255;
  let activeSpeed = 1.0;
  let activeFlowX = 0;

  // Switch atmosphere smoothly
  function switchAtmosphere(theme) {
    if (!theme || !themeProfiles[theme] || theme === currentTheme) return;
    currentTheme = theme;
    targetProfile = themeProfiles[theme];

    // Hardware-accelerated cross-fade of dedicated aura layers
    const auraLayers = document.querySelectorAll(".aura-layer");
    auraLayers.forEach((layer) => {
      if (layer.classList.contains(`aura-${theme}`)) {
        layer.classList.add("active");
      } else {
        layer.classList.remove("active");
      }
    });

    // Cross-fade background video layer smoothly per section theme
    if (videoLayer) {
      if (theme === "hero") {
        videoLayer.style.opacity = "0.85";
      } else if (theme === "cta") {
        videoLayer.style.opacity = "0.32";
      } else {
        videoLayer.style.opacity = "0.08";
      }
    }

    // Update ambient-system container class
    ambientSystem.className = `continuo-ambient-system theme-${theme}`;
  }

  // Observe all sections with data-ambient-theme
  const sections = document.querySelectorAll("section[data-ambient-theme]");
  if (sections.length && "IntersectionObserver" in window) {
    const themeObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const theme = entry.target.getAttribute("data-ambient-theme");
            switchAtmosphere(theme);
          }
        });
      },
      { threshold: 0.25 }
    );

    sections.forEach((sec) => themeObserver.observe(sec));
  }

  // If user prefers reduced motion, draw calm starfield & return
  if (prefersReducedMotion) {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
    for (let i = 0; i < 45; i++) {
      ctx.beginPath();
      ctx.arc(
        Math.random() * canvas.width,
        Math.random() * canvas.height,
        1.2,
        0,
        Math.PI * 2
      );
      ctx.fill();
    }
    return;
  }

  // Canvas DPR and Resizing
  let width = 0;
  let height = 0;
  let dpr = Math.min(window.devicePixelRatio || 1, 2);

  function resizeCanvas() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
  }

  resizeCanvas();
  window.addEventListener("resize", resizeCanvas, { passive: true });

  // Mouse / Pointer Interaction (Gentle, subtle aura)
  const mouse = {
    x: width / 2,
    y: height / 2,
    targetX: width / 2,
    targetY: height / 2,
    active: false,
  };

  const isCoarsePointer = window.matchMedia("(pointer: coarse)").matches;
  if (!isCoarsePointer) {
    window.addEventListener(
      "mousemove",
      (e) => {
        mouse.targetX = e.clientX;
        mouse.targetY = e.clientY;
        mouse.active = true;
      },
      { passive: true }
    );

    document.addEventListener("mouseleave", () => {
      mouse.active = false;
    });
  }

  // Context-Flow Node Structure (Adaptive for mobile, tablet, desktop)
  const isMobile = width <= 768;
  const isTablet = width > 768 && width <= 1024;
  const nodeCount = isMobile ? 12 : isTablet ? 22 : Math.min(36, Math.floor(width / 36));
  const nodes = [];

  class ContextNode {
    constructor() {
      this.reset(true);
    }

    reset(initial = false) {
      this.x = Math.random() * width;
      this.y = initial ? Math.random() * height : -20;
      this.baseRadius = 1.2 + Math.random() * 1.8;
      this.radius = this.baseRadius;

      // Gentle drift speed
      this.vx = (Math.random() - 0.5) * 0.4;
      this.vy = 0.15 + Math.random() * 0.35;

      // Color variation (white, cyan, soft violet)
      const r = Math.random();
      if (r < 0.5) {
        this.color = "rgba(255, 255, 255, 0.4)";
        this.packetColor = "#ffffff";
      } else if (r < 0.8) {
        this.color = "rgba(56, 189, 248, 0.5)";
        this.packetColor = "#38bdf8";
      } else {
        this.color = "rgba(168, 85, 247, 0.45)";
        this.packetColor = "#a855f7";
      }

      this.pulsePhase = Math.random() * Math.PI * 2;
      this.pulseSpeed = 0.02 + Math.random() * 0.03;
    }

    update(speedMult, flowX) {
      this.x += (this.vx + flowX) * speedMult;
      this.y += this.vy * speedMult;

      // Gentle pulse
      this.pulsePhase += this.pulseSpeed;
      this.radius = this.baseRadius + Math.sin(this.pulsePhase) * 0.45;

      // Subtle mouse deflection
      if (mouse.active) {
        const dx = this.x - mouse.x;
        const dy = this.y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const maxDist = 130;

        if (dist < maxDist && dist > 0) {
          const force = (1 - dist / maxDist) * 1.4;
          this.x += (dx / dist) * force;
          this.y += (dy / dist) * force;
        }
      }

      // Wrap boundaries
      if (this.x < -30) this.x = width + 30;
      if (this.x > width + 30) this.x = -30;
      if (this.y > height + 30) {
        this.reset(false);
      }
    }

    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, Math.max(0.6, this.radius), 0, Math.PI * 2);
      ctx.fillStyle = this.color;
      ctx.fill();
    }
  }

  for (let i = 0; i < nodeCount; i++) {
    nodes.push(new ContextNode());
  }

  // Orbiting Satellite Memory Nodes (For Project Memory theme)
  const memoryAnchors = [
    { xRatio: 0.28, yRatio: 0.42, angle: 0, speed: 0.015, radius: 26 },
    { xRatio: 0.72, yRatio: 0.58, angle: Math.PI, speed: 0.012, radius: 32 },
  ];

  // Traveling Data Packets between nodes
  class DataPacket {
    constructor() {
      this.nodeA = null;
      this.nodeB = null;
      this.progress = 0;
      this.speed = 0.015;
      this.color = "#38bdf8";
      this.active = false;
      this.isBroken = false;
      this.breakPoint = 0.5;
    }

    spawn(a, b, color, isBroken = false) {
      this.nodeA = a;
      this.nodeB = b;
      this.progress = 0;
      this.speed = 0.012 + Math.random() * 0.02;
      this.color = color || "#38bdf8";
      this.active = true;
      this.isBroken = isBroken;
      this.breakPoint = 0.35 + Math.random() * 0.35;
    }

    update() {
      if (!this.active) return;
      this.progress += this.speed;

      // If broken packet (e.g. Problem section token wall), vanish at breakPoint
      if (this.isBroken && this.progress >= this.breakPoint) {
        this.active = false;
        return;
      }

      if (this.progress >= 1) {
        this.active = false;
      }
    }

    draw() {
      if (!this.active || !this.nodeA || !this.nodeB) return;
      const curX = this.nodeA.x + (this.nodeB.x - this.nodeA.x) * this.progress;
      const curY = this.nodeA.y + (this.nodeB.y - this.nodeA.y) * this.progress;

      let alpha = 1;
      if (this.isBroken) {
        alpha = Math.max(0, 1 - this.progress / this.breakPoint);
      }

      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.beginPath();
      ctx.arc(curX, curY, 2.2, 0, Math.PI * 2);
      ctx.fillStyle = this.color;
      ctx.shadowColor = this.color;
      ctx.shadowBlur = 8;
      ctx.fill();
      ctx.restore();
    }
  }

  const packetPool = [];
  const maxPackets = isMobile ? 5 : isTablet ? 8 : 14;
  for (let i = 0; i < maxPackets; i++) {
    packetPool.push(new DataPacket());
  }

  function triggerPacket(a, b, color, isBroken) {
    const idlePacket = packetPool.find((p) => !p.active);
    if (idlePacket) {
      idlePacket.spawn(a, b, color, isBroken);
    }
  }

  // Animation Loop (60 FPS optimized)
  let animationId = null;
  let lastPacketTime = 0;

  function render(timestamp) {
    ctx.clearRect(0, 0, width, height);

    // Smoothly interpolate RGB and dynamics toward target profile
    activeR += (targetProfile.rgb[0] - activeR) * 0.05;
    activeG += (targetProfile.rgb[1] - activeG) * 0.05;
    activeB += (targetProfile.rgb[2] - activeB) * 0.05;
    activeSpeed += (targetProfile.speed - activeSpeed) * 0.05;
    activeFlowX += (targetProfile.flowX - activeFlowX) * 0.05;

    // Smooth mouse lerp
    mouse.x += (mouse.targetX - mouse.x) * 0.08;
    mouse.y += (mouse.targetY - mouse.y) * 0.08;

    // Subtle cursor ambient aura (desktop pointer only)
    if (mouse.active && !isCoarsePointer) {
      const gradient = ctx.createRadialGradient(
        mouse.x,
        mouse.y,
        0,
        mouse.x,
        mouse.y,
        170
      );
      gradient.addColorStop(0, "rgba(56, 189, 248, 0.06)");
      gradient.addColorStop(0.6, "rgba(99, 102, 241, 0.02)");
      gradient.addColorStop(1, "transparent");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, width, height);
    }

    // Connect close nodes (optimized with squared-distance threshold)
    const connectionDist = isMobile ? 80 : isTablet ? 100 : 120;
    const maxDistSq = connectionDist * connectionDist;
    const rInt = Math.round(activeR);
    const gInt = Math.round(activeG);
    const bInt = Math.round(activeB);

    for (let i = 0; i < nodes.length; i++) {
      nodes[i].update(activeSpeed, activeFlowX);
      nodes[i].draw();

      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const distSq = dx * dx + dy * dy;

        if (distSq < maxDistSq) {
          const dist = Math.sqrt(distSq);
          const alpha = (1 - dist / connectionDist) * 0.18;

          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);

          if (targetProfile.dash.length) {
            ctx.setLineDash(targetProfile.dash);
          } else {
            ctx.setLineDash([]);
          }

          ctx.strokeStyle = `rgba(${rInt}, ${gInt}, ${bInt}, ${alpha})`;
          ctx.lineWidth = 1;
          ctx.stroke();
          ctx.setLineDash([]);

          // Trigger context packets
          if (
            timestamp - lastPacketTime > (isMobile ? 360 : 200) &&
            Math.random() < 0.07
          ) {
            triggerPacket(
              nodes[i],
              nodes[j],
              targetProfile.packetColor,
              targetProfile.brokenPackets && Math.random() < 0.45
            );
            lastPacketTime = timestamp;
          }
        }
      }
    }

    // Draw orbiting memory structures when in Memory section
    if (targetProfile.hasOrbit) {
      memoryAnchors.forEach((anchor) => {
        const ax = width * anchor.xRatio;
        const ay = height * anchor.yRatio;
        anchor.angle += anchor.speed;

        // Central anchor node
        ctx.beginPath();
        ctx.arc(ax, ay, 3.2, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(99, 102, 241, 0.65)";
        ctx.shadowColor = "#818cf8";
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;

        // Orbit ring
        ctx.beginPath();
        ctx.arc(ax, ay, anchor.radius, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(99, 102, 241, 0.12)";
        ctx.setLineDash([2, 4]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Orbiting satellite particle
        const sx = ax + Math.cos(anchor.angle) * anchor.radius;
        const sy = ay + Math.sin(anchor.angle) * anchor.radius;
        ctx.beginPath();
        ctx.arc(sx, sy, 2, 0, Math.PI * 2);
        ctx.fillStyle = "#38bdf8";
        ctx.fill();
      });
    }

    // Update and draw packets
    for (let i = 0; i < packetPool.length; i++) {
      packetPool[i].update();
      packetPool[i].draw();
    }

    animationId = requestAnimationFrame(render);
  }

  // Start animation loop
  animationId = requestAnimationFrame(render);

  // Pause when document hidden to conserve CPU/battery
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      if (animationId) cancelAnimationFrame(animationId);
    } else {
      animationId = requestAnimationFrame(render);
    }
  });
}

/* ==========================================================================
   2. Stats Count-Up Engine (easeOutCubic, exact formulas)
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
   3. Header Scroll Blur & ScrollSpy Navigation
   ========================================================================== */
function initHeaderScroll() {
  // If Lenis is not active, provide a throttled fallback listener for header state
  if (typeof Lenis === "undefined" || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    let ticking = false;
    window.addEventListener("scroll", () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          if (window.scrollY > 30) {
            document.body.classList.add("scrolled");
          } else {
            document.body.classList.remove("scrolled");
          }
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });
  }
}

function initScrollSpy() {
  const sections = document.querySelectorAll("section[id]");
  const navLinks = document.querySelectorAll(".nav-link, .mobile-link");
  if (!sections.length || !navLinks.length) return;

  if ("IntersectionObserver" in window) {
    const spyObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const id = entry.target.getAttribute("id");
            navLinks.forEach((link) => {
              const href = link.getAttribute("href");
              if (href === `#${id}`) {
                link.classList.add("active");
              } else if (href && href.startsWith("#")) {
                link.classList.remove("active");
              }
            });
          }
        });
      },
      {
        rootMargin: "-20% 0px -60% 0px",
        threshold: 0,
      }
    );

    sections.forEach((sec) => spyObserver.observe(sec));
  }
}

/* ==========================================================================
   4. Scroll Reveal Animations (IntersectionObserver)
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
   4.5 Lenis Premium Smooth Scrolling & Inspira UI Spotlights
   ========================================================================== */
let lenisInstance = null;

function initLenisSmoothScroll() {
  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  if (prefersReducedMotion || typeof Lenis === "undefined") {
    // Accessible instant/native navigation for reduced motion
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      anchor.addEventListener("click", (e) => {
        const href = anchor.getAttribute("href");
        if (!href || href === "#") return;
        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          if (document.body.classList.contains("menu-open")) {
            document.body.classList.remove("menu-open");
            const burger = document.getElementById("burger-btn");
            const sheet = document.getElementById("mobile-sheet");
            if (burger) burger.setAttribute("aria-expanded", "false");
            if (sheet) sheet.hidden = true;
          }
          target.scrollIntoView({ behavior: "auto", block: "start" });
        }
      });
    });
    return;
  }

  // Single authoritative Lenis instance
  lenisInstance = new Lenis({
    duration: 1.15,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    orientation: "vertical",
    gestureOrientation: "vertical",
    smoothWheel: true,
    wheelMultiplier: 1.0,
    touchMultiplier: 1.2,
    infinite: false,
  });

  function raf(time) {
    lenisInstance.raf(time);
    requestAnimationFrame(raf);
  }
  requestAnimationFrame(raf);

  // Consolidated Lenis scroll listener (synchronizes header state and background grid parallax)
  const gridOverlay = document.getElementById("ambient-grid-overlay");
  lenisInstance.on("scroll", (e) => {
    const scrollY = e.scroll;

    // Header scrolled state
    if (scrollY > 30) {
      document.body.classList.add("scrolled");
    } else {
      document.body.classList.remove("scrolled");
    }

    // Grid optical parallax (safe modulo loop, running in lockstep with RAF)
    if (gridOverlay) {
      gridOverlay.style.transform = `translate3d(0, ${-(scrollY * 0.04) % 60}px, 0)`;
    }
  });

  // Wire internal anchor navigation to Lenis scrollTo with calculated header offset
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const href = anchor.getAttribute("href");
      if (!href || href === "#") return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        // Close mobile menu if opened
        if (document.body.classList.contains("menu-open")) {
          document.body.classList.remove("menu-open");
          const burger = document.getElementById("burger-btn");
          const sheet = document.getElementById("mobile-sheet");
          if (burger) burger.setAttribute("aria-expanded", "false");
          if (sheet) sheet.hidden = true;
        }

        // Landing offset accounts for floating header; #hero scrolls to absolute top
        const isHero = target.getAttribute("id") === "hero";
        lenisInstance.scrollTo(target, {
          offset: isHero ? 0 : -76,
          duration: 1.15,
          easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        });
      }
    });
  });

  // Ensure Lenis keeps dimensions accurately calibrated across image loads and viewport changes
  window.addEventListener("load", () => {
    if (lenisInstance) lenisInstance.resize();
  });
  window.addEventListener("resize", () => {
    if (lenisInstance) lenisInstance.resize();
  }, { passive: true });
}

function initCardSpotlights() {
  const spotlightCards = document.querySelectorAll(
    ".compare-card, .engine-column, .step-card, .p-node, .final-cta-card"
  );
  if (!spotlightCards.length) return;

  spotlightCards.forEach((card) => {
    let rect = null;
    card.addEventListener("mouseenter", () => {
      rect = card.getBoundingClientRect();
    }, { passive: true });
    card.addEventListener("mousemove", (e) => {
      if (!rect) rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty("--mouse-x", `${x}px`);
      card.style.setProperty("--mouse-y", `${y}px`);
    }, { passive: true });
    card.addEventListener("mouseleave", () => {
      rect = null;
    }, { passive: true });
  });
}

/* ==========================================================================
   5. Interactive Context Engine Inspector (9 Structured Nodes)
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
   6. Interactive Project Memory Version Diff Switcher
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
   7. Sticky Walkthrough Step Controller & Window Morphing
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
   8. Live Interactive Handoff Playground & 1-Click Clipboard Copy
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

  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      const text = codeBlock ? codeBlock.textContent : "";
      if (!text) return;

      navigator.clipboard
        .writeText(text)
        .then(() => {
          showToast("Handoff payload copied to clipboard!");
        })
        .catch(() => {
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
   9. Mobile Drawer Sheet Menu Controller
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
    if (window.innerWidth > 960 && document.body.classList.contains("menu-open")) {
      closeMenu();
    }
  });
}

/* ==========================================================================
   10. CONTINUO LIVE WORKSPACE APPLICATION & API INTEGRATION
   Connects the frontend UI to FastAPI backend, project persistence,
   context engine, quality scoring, version diff, and handoffs.
   ========================================================================== */
function initContinuoWorkspaceApp() {
  const API_BASE = "http://127.0.0.1:8008/api/v1";

  // App State
  let authToken = localStorage.getItem("continuo_jwt") || null;
  let currentUser = JSON.parse(localStorage.getItem("continuo_user") || "null");
  let currentProjects = [];
  let selectedProjectId = null;
  let activeContextPkg = null;
  let activeVersions = [];
  let lastHandoffUrl = "https://claude.ai/new";

  // DOM Elements - Workspace Modal
  const wsOverlay = document.getElementById("workspace-overlay");
  const wsCloseBtn = document.getElementById("ws-close-btn");
  const headerLaunchBtn = document.getElementById("header-launch-btn");
  const headerSigninBtn = document.getElementById("header-signin-btn");
  const navAuthLabel = document.getElementById("nav-auth-label");
  const wsProjectSelect = document.getElementById("ws-project-select");
  const wsBtnNewProject = document.getElementById("ws-btn-new-project");
  const wsVerChip = document.getElementById("ws-ver-chip");
  const wsHealthChip = document.getElementById("ws-health-chip");
  const wsUserPill = document.getElementById("ws-user-pill");
  const wsUserEmail = document.getElementById("ws-user-email");
  const wsBtnSignout = document.getElementById("ws-btn-signout");
  const wsReadinessBadge = document.getElementById("ws-readiness-badge");
  const wsReadinessText = document.getElementById("ws-readiness-text");
  const wsOverviewTitle = document.getElementById("ws-overview-title");
  const wsOverviewDesc = document.getElementById("ws-overview-desc");
  const wsHumanObjective = document.getElementById("ws-human-objective");
  const wsHumanState = document.getElementById("ws-human-state");
  const wsHumanCompleted = document.getElementById("ws-human-completed");
  const wsHumanPending = document.getElementById("ws-human-pending");
  const wsHumanNext = document.getElementById("ws-human-next");
  const wsOverviewContChatgpt = document.getElementById("ws-overview-cont-chatgpt");
  const wsOverviewContClaude = document.getElementById("ws-overview-cont-claude");
  const wsOverviewContGemini = document.getElementById("ws-overview-cont-gemini");
  const wsBtnJumpMemory = document.getElementById("ws-btn-jump-memory");
  const wsBtnJumpDiagnostics = document.getElementById("ws-btn-jump-diagnostics");

  // Extension Install Modal Elements (Section 29)
  const extInstallModal = document.getElementById("extension-install-modal");
  const btnCloseExtModal = document.getElementById("btn-close-ext-modal");
  const btnExtGotIt = document.getElementById("btn-ext-got-it");

  // DOM Elements - Tabs
  const wsTabs = document.querySelectorAll(".ws-tab");
  const wsPanels = document.querySelectorAll(".ws-panel");

  // DOM Elements - Panel 1: Capture
  const wsSourceProvider = document.getElementById("ws-source-provider");
  const wsSessionTitle = document.getElementById("ws-session-title");
  const wsRawTranscript = document.getElementById("ws-raw-transcript");
  const wsBtnLoadSample = document.getElementById("ws-btn-load-sample");
  const wsBtnRunCapture = document.getElementById("ws-btn-run-capture");
  const wsCaptureStatus = document.getElementById("ws-capture-status");
  const wsCaptureBtnText = document.getElementById("ws-capture-btn-text");
  const wsQualityVal = document.getElementById("ws-quality-val");
  const wsMeterFill = document.getElementById("ws-meter-fill");
  const wsValComp = document.getElementById("ws-val-comp");
  const wsValClarity = document.getElementById("ws-val-clarity");
  const wsValAction = document.getElementById("ws-val-action");
  const wsValCons = document.getElementById("ws-val-cons");
  const wsContradictionAlert = document.getElementById("ws-contradiction-alert");
  const wsContraTopic = document.getElementById("ws-contra-topic");
  const wsContraExp = document.getElementById("ws-contra-exp");
  const wsRecsList = document.getElementById("ws-recs-list");
  const wsSummaryVer = document.getElementById("ws-summary-ver");
  const wsSummaryObjective = document.getElementById("ws-summary-objective");
  const wsCountReqs = document.getElementById("ws-count-reqs");
  const wsCountConst = document.getElementById("ws-count-const");
  const wsCountDec = document.getElementById("ws-count-dec");
  const wsCountFiles = document.getElementById("ws-count-files");

  // DOM Elements - Panel 2: Memory Editor
  const wsEditObjective = document.getElementById("ws-edit-objective");
  const wsEditState = document.getElementById("ws-edit-state");
  const wsEditRequirements = document.getElementById("ws-edit-requirements");
  const wsEditConstraints = document.getElementById("ws-edit-constraints");
  const wsEditDecisions = document.getElementById("ws-edit-decisions");
  const wsEditFiles = document.getElementById("ws-edit-files");
  const wsEditNext = document.getElementById("ws-edit-next");
  const wsBtnSaveMemory = document.getElementById("ws-btn-save-memory");

  // DOM Elements - Panel 3: Diff
  const wsDiffFromSelect = document.getElementById("ws-diff-from-select");
  const wsDiffToSelect = document.getElementById("ws-diff-to-select");
  const wsBtnCalcDiff = document.getElementById("ws-btn-calc-diff");
  const wsDiffTitle = document.getElementById("ws-diff-title");
  const wsDiffSummaryText = document.getElementById("ws-diff-summary-text");
  const wsDiffAddedList = document.getElementById("ws-diff-added-list");
  const wsDiffModList = document.getElementById("ws-diff-mod-list");
  const wsDiffRemList = document.getElementById("ws-diff-rem-list");

  // DOM Elements - Panel 4: Handoff
  const wsHoSource = document.getElementById("ws-ho-source");
  const wsHoDest = document.getElementById("ws-ho-dest");
  const wsHoNotes = document.getElementById("ws-ho-notes");
  const wsBtnGenerateHandoff = document.getElementById("ws-btn-generate-handoff");
  const wsBtnCopyPayload = document.getElementById("ws-btn-copy-payload");
  const wsBtnOpenTarget = document.getElementById("ws-btn-open-target");
  const wsOpenTargetText = document.getElementById("ws-open-target-text");
  const wsHoCodeBlock = document.getElementById("ws-ho-code-block");

  // DOM Elements - Submodals
  const newProjectModal = document.getElementById("new-project-modal");
  const btnCloseNewProject = document.getElementById("btn-close-new-project");
  const btnCancelNewProject = document.getElementById("btn-cancel-new-project");
  const btnSubmitNewProject = document.getElementById("btn-submit-new-project");
  const newProjName = document.getElementById("new-proj-name");
  const newProjDesc = document.getElementById("new-proj-desc");
  const newProjGoal = document.getElementById("new-proj-goal");

  const authModal = document.getElementById("auth-modal");
  const btnCloseAuth = document.getElementById("btn-close-auth");
  const authTabLogin = document.getElementById("auth-tab-login");
  const authTabRegister = document.getElementById("auth-tab-register");
  const authNameGroup = document.getElementById("auth-name-group");
  const authName = document.getElementById("auth-name");
  const authEmail = document.getElementById("auth-email");
  const authPassword = document.getElementById("auth-password");
  const btnSubmitAuth = document.getElementById("btn-submit-auth");
  const btnDemoEngineer = document.getElementById("btn-demo-engineer");
  const authErrorMsg = document.getElementById("auth-error-msg");
  let authMode = "login";

  // Toast Helper
  function showToast(msg) {
    const toast = document.getElementById("toast-notice");
    const toastText = document.getElementById("toast-text");
    if (!toast) return;
    if (toastText) toastText.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 3500);
  }

  // HTTP Helper with Bearer Token
  async function apiRequest(endpoint, method = "GET", body = null) {
    const headers = { "Content-Type": "application/json" };
    if (authToken) {
      headers["Authorization"] = `Bearer ${authToken}`;
    }

    try {
      const resp = await fetch(`${API_BASE}${endpoint}`, {
        method,
        headers,
        body: body ? JSON.stringify(body) : null,
      });

      if (resp.status === 401) {
        // Token expired or invalid
        authToken = null;
        localStorage.removeItem("continuo_jwt");
        updateUserUI();
      }

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || `Server error (${resp.status})`);
      }
      return data;
    } catch (err) {
      console.warn(`[Continuo API Error] ${method} ${endpoint}:`, err);
      throw err;
    }
  }

  // =========================================================================
  // Auth Operations
  // =========================================================================
  function updateUserUI() {
    if (currentUser && authToken) {
      if (wsUserEmail) wsUserEmail.textContent = currentUser.email.split("@")[0];
      if (navAuthLabel) navAuthLabel.textContent = "Workspace";
      if (wsBtnSignout) wsBtnSignout.style.display = "inline-flex";
    } else {
      if (wsUserEmail) wsUserEmail.textContent = "Sign In";
      if (navAuthLabel) navAuthLabel.textContent = "Sign In";
      if (wsBtnSignout) wsBtnSignout.style.display = "none";
    }
  }

  function signOutUser() {
    if (authToken) {
      apiRequest("/auth/logout", "POST").catch(() => {});
    }
    authToken = null;
    currentUser = null;
    localStorage.removeItem("continuo_jwt");
    localStorage.removeItem("continuo_user");
    updateUserUI();
    closeWorkspace();
    showToast("Signed out of Continuo");
  }

  if (wsBtnSignout) wsBtnSignout.addEventListener("click", signOutUser);

  async function ensureAuthenticated() {
    if (authToken && currentUser) return true;

    // Automatic Demo Authentication for frictionless testing
    try {
      const demoRes = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: "demo@continuo.ai",
          password: "DemoContinuo2026!",
        }),
      });

      let tokenData;
      if (demoRes.ok) {
        tokenData = await demoRes.json();
      } else {
        // Register demo user
        const regRes = await fetch(`${API_BASE}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: "demo@continuo.ai",
            password: "DemoContinuo2026!",
            full_name: "Elena Rostova (Demo Engineer)",
          }),
        });
        tokenData = await regRes.json();
      }

      authToken = tokenData.access_token;
      currentUser = { email: tokenData.email, id: tokenData.user_id };
      localStorage.setItem("continuo_jwt", authToken);
      localStorage.setItem("continuo_user", JSON.stringify(currentUser));
      updateUserUI();
      return true;
    } catch (err) {
      console.warn("Backend not available yet, using local guest state.");
      return false;
    }
  }

  // =========================================================================
  // Project Management
  // =========================================================================
  async function loadProjects() {
    try {
      const projs = await apiRequest("/projects");
      currentProjects = projs;

      if (!currentProjects.length) {
        // Create initial default project
        const newProj = await apiRequest("/projects", "POST", {
          name: "Nexora AI Platform",
          description: "Multi-agent context persistence orchestrator",
          initial_objective:
            "Build an AI-agnostic context continuity layer that captures structured project memory across ChatGPT, Claude, and Gemini.",
        });
        currentProjects = [newProj];
      }

      // Populate Select
      wsProjectSelect.innerHTML = "";
      currentProjects.forEach((p) => {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `${p.name} (${p.current_version})`;
        wsProjectSelect.appendChild(opt);
      });

      if (!selectedProjectId && currentProjects.length > 0) {
        selectedProjectId = currentProjects[0].id;
      }
      wsProjectSelect.value = selectedProjectId;

      await loadActiveProjectContext();
      await loadProjectVersions();
    } catch (err) {
      if (wsCaptureStatus) {
        wsCaptureStatus.textContent = "Backend connecting...";
      }
    }
  }

  async function loadActiveProjectContext() {
    if (!selectedProjectId) return;
    const proj = currentProjects.find((p) => p.id === selectedProjectId);
    if (!proj) return;

    wsVerChip.textContent = proj.current_version || "v1.0";
    wsHealthChip.textContent = `${Math.round(proj.health_score || 85)}% Health`;

    try {
      const ctxPkg = await apiRequest(`/context/projects/${selectedProjectId}/context`);
      activeContextPkg = ctxPkg;
      renderContextPackage(ctxPkg);
    } catch (err) {
      console.log("No existing context package found, waiting for capture.");
    }
  }

  async function loadProjectVersions() {
    if (!selectedProjectId) return;
    try {
      const versions = await apiRequest(`/versions/projects/${selectedProjectId}`);
      activeVersions = versions;

      wsDiffFromSelect.innerHTML = "";
      wsDiffToSelect.innerHTML = "";

      versions.forEach((v, idx) => {
        const optA = document.createElement("option");
        optA.value = v.version_number;
        optA.textContent = `${v.version_number} (${v.changelog ? v.changelog.substring(0, 30) + '...' : 'Milestone'})`;
        wsDiffFromSelect.appendChild(optA);

        const optB = document.createElement("option");
        optB.value = v.version_number;
        optB.textContent = `${v.version_number} (${v.changelog ? v.changelog.substring(0, 30) + '...' : 'Milestone'})`;
        wsDiffToSelect.appendChild(optB);
      });

      // Default compare: oldest to newest
      if (versions.length >= 2) {
        wsDiffFromSelect.selectedIndex = versions.length - 1;
        wsDiffToSelect.selectedIndex = 0;
      }
    } catch (err) {
      console.warn("Could not load versions:", err);
    }
  }

  function renderContextPackage(pkg) {
    if (!pkg) return;

    // 1. Intelligence Head & Quality Meter
    const score = Math.round(pkg.quality_score || 85);
    wsQualityVal.textContent = `${score}%`;
    wsHealthChip.textContent = `${score}% Health`;
    wsVerChip.textContent = pkg.version;
    wsMeterFill.style.width = `${Math.min(100, score)}%`;

    // Dynamic color gradient based on score
    if (score >= 80) {
      wsMeterFill.style.background = "linear-gradient(90deg, #38bdf8, #34d399)";
      wsQualityVal.style.color = "#34d399";
    } else if (score >= 60) {
      wsMeterFill.style.background = "linear-gradient(90deg, #38bdf8, #facc15)";
      wsQualityVal.style.color = "#facc15";
    } else {
      wsMeterFill.style.background = "linear-gradient(90deg, #f87171, #ef4444)";
      wsQualityVal.style.color = "#f87171";
    }

    // 2. Summary Card & Readiness Status (Part 14)
    if (wsReadinessBadge) {
      if (score >= 75 && (!pkg.contradiction_count || pkg.contradiction_count === 0)) {
        wsReadinessBadge.className = "memory-readiness-badge";
        wsReadinessBadge.innerHTML = `<i class="fa-solid fa-circle-check"></i> <span id="ws-readiness-text">Memory Ready</span>`;
      } else {
        wsReadinessBadge.className = "memory-readiness-badge review";
        wsReadinessBadge.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <span id="ws-readiness-text">Needs Review</span>`;
      }
    }

    wsSummaryVer.textContent = `Version ${pkg.version}`;
    if (wsSummaryObjective) wsSummaryObjective.textContent = pkg.objective || "No objective defined yet.";
    wsCountReqs.textContent = (pkg.requirements || []).length;
    wsCountConst.textContent = (pkg.constraints || []).length;
    wsCountDec.textContent = (pkg.decisions || []).length;
    wsCountFiles.textContent = (pkg.files_context || []).length;

    // Human-Readable Project Memory Representation (Section 10 & 11)
    const activeProj = currentProjects.find(p => p.id === selectedProjectId);
    if (activeProj) {
      if (wsOverviewTitle) wsOverviewTitle.textContent = activeProj.name;
      if (wsOverviewDesc) wsOverviewDesc.textContent = activeProj.description || "Continuo AI Context Continuity";
    }

    if (wsHumanObjective) {
      wsHumanObjective.textContent = pkg.objective || "No objective defined yet.";
    }
    if (wsHumanState) {
      wsHumanState.textContent = pkg.current_state || "Active development.";
    }
    if (wsHumanCompleted) {
      wsHumanCompleted.innerHTML = "";
      const doneList = pkg.completed_work && pkg.completed_work.length ? pkg.completed_work : ["Initial foundation setup."];
      doneList.forEach(item => {
        const li = document.createElement("li");
        li.textContent = item;
        wsHumanCompleted.appendChild(li);
      });
    }
    if (wsHumanPending) {
      wsHumanPending.innerHTML = "";
      const pendingList = (pkg.requirements && pkg.requirements.length) ? pkg.requirements : ["Core functional features."];
      pendingList.forEach(item => {
        const li = document.createElement("li");
        li.textContent = item;
        wsHumanPending.appendChild(li);
      });
    }
    if (wsHumanNext) {
      const nextList = pkg.next_steps || [];
      wsHumanNext.textContent = nextList.length ? nextList[0] : "Capture or edit context to advance.";
    }

    // 3. Breakdown
    const compScore = Math.min(30, 8 + (pkg.requirements?.length || 0) * 2.5);
    const clarityScore = Math.min(25, 8 + (pkg.files_context?.length || 0) * 3);
    const actionScore = Math.min(25, 10 + (pkg.next_steps?.length || 0) * 4);
    const consScore = pkg.contradiction_count ? 10.0 : 20.0;

    wsValComp.textContent = `${compScore.toFixed(1)} / 30`;
    wsValClarity.textContent = `${clarityScore.toFixed(1)} / 25`;
    wsValAction.textContent = `${actionScore.toFixed(1)} / 25`;
    wsValCons.textContent = `${consScore.toFixed(1)} / 20`;

    // 4. Contradiction Alert
    if (pkg.contradiction_count > 0) {
      wsContradictionAlert.style.display = "flex";
      wsContraTopic.textContent = "Architectural Decision Contradiction";
      wsContraExp.textContent = "A recent choice or requirement conflicts with established constraints. Review decisions in Project Memory.";
    } else {
      wsContradictionAlert.style.display = "none";
    }

    // 5. Recommendations
    wsRecsList.innerHTML = "";
    const recs = [];
    if ((pkg.requirements || []).length < 3) {
      recs.push("Specify at least 3 explicit functional requirements.");
    }
    if ((pkg.constraints || []).length < 2) {
      recs.push("Document non-negotiable architectural constraints to prevent AI drift.");
    }
    if ((pkg.files_context || []).length === 0) {
      recs.push("Tag primary file paths to give direct grounding.");
    }
    if (!recs.length) {
      recs.push("Context package has high operational fidelity and is ready for model transit.");
    }
    recs.forEach((r) => {
      const li = document.createElement("li");
      li.textContent = r;
      wsRecsList.appendChild(li);
    });

    // 6. Populate Memory Editor (Tab 2)
    wsEditObjective.value = pkg.objective || "";
    wsEditState.value = pkg.current_state || "";
    wsEditRequirements.value = (pkg.requirements || []).join("\n");
    wsEditConstraints.value = (pkg.constraints || []).join("\n");
    wsEditDecisions.value = (pkg.decisions || []).join("\n");
    wsEditFiles.value = (pkg.files_context || []).join("\n");
    wsEditNext.value = (pkg.next_steps || []).join("\n");
  }

  // =========================================================================
  // Sample Conversation Generator
  // =========================================================================
  const SAMPLE_SESSION = `User: I've been working on our authentication microservice for Nexora AI.
We decided to use FastAPI with SQLAlchemy and PyJWT for stateless token validation.
Database is Supabase PostgreSQL.

Requirement: Support Google and GitHub OAuth login providers with PKCE flow.
Requirement: Issue short-lived access JWTs (15 min) and rotating refresh tokens stored in httpOnly secure cookies.
Requirement: Never allow unauthenticated requests past the /api/v1 gateway.

Constraint: Never store plaintext passwords or secrets under any circumstances.
Constraint: Do not use third-party auth services like Auth0; maintain full local data sovereignty.
Constraint: Must run on Python 3.12+ and pass all pytest suites before deployment.

Current State: OAuth callback handler and JWT issuing routes are implemented and passing unit tests.
Completed: Setup database migrations for refresh_tokens table and verified password hashing with PBKDF2.
Pending: Implement token revocation blacklist endpoint and setup Redis cache.

Files in scope:
- backend/routers/auth.py
- backend/services/auth.py
- backend/models/user.py
- tests/test_auth.py

Next step: Connect frontend auth modal and verify cross-domain CORS tokens with the Chrome Extension.`;

  if (wsBtnLoadSample) {
    wsBtnLoadSample.addEventListener("click", () => {
      wsRawTranscript.value = SAMPLE_SESSION;
      wsSessionTitle.value = "Auth Architecture & OAuth2 Refactor";
      showToast("Engineering session sample loaded!");
    });
  }

  // =========================================================================
  // Context Capture Flow
  // =========================================================================
  if (wsBtnRunCapture) {
    wsBtnRunCapture.addEventListener("click", async () => {
      const rawText = wsRawTranscript.value.trim();
      if (!rawText || rawText.length < 15) {
        showToast("Please enter a conversation transcript to capture.");
        return;
      }

      if (!selectedProjectId) {
        showToast("Please select or create a project first.");
        return;
      }

      wsBtnRunCapture.disabled = true;

      // Sequential Contextual Loading States
      const steps = [
        "Capturing context from " + wsSourceProvider.value.toUpperCase() + "...",
        "Extracting objective, requirements & decisions...",
        "Checking architectural consistency & contradictions...",
        "Synthesizing Project Memory Package...",
      ];

      let stepIdx = 0;
      wsCaptureBtnText.textContent = steps[0];
      wsCaptureStatus.textContent = steps[0];

      const interval = setInterval(() => {
        stepIdx++;
        if (stepIdx < steps.length) {
          wsCaptureBtnText.textContent = steps[stepIdx];
          wsCaptureStatus.textContent = steps[stepIdx];
        }
      }, 380);

      try {
        const pkg = await apiRequest("/context/capture", "POST", {
          project_id: selectedProjectId,
          provider: wsSourceProvider.value,
          raw_transcript: rawText,
          title: wsSessionTitle.value || `Capture from ${wsSourceProvider.value}`,
        });

        clearInterval(interval);
        renderContextPackage(pkg);
        await loadProjectVersions();

        wsCaptureStatus.textContent = `Context captured successfully as ${pkg.version}!`;
        showToast(`Synthesized Context Package ${pkg.version} with ${Math.round(pkg.quality_score)}% Health!`);

        // Refresh project list to reflect version bump
        await loadProjects();
      } catch (err) {
        clearInterval(interval);
        wsCaptureStatus.textContent = "Extraction completed.";
        showToast(err.message || "Failed to capture context.");
      } finally {
        wsBtnRunCapture.disabled = false;
        wsCaptureBtnText.textContent = "Ingest & Synthesize Context Package";
      }
    });
  }

  // =========================================================================
  // Memory Editor (Human Control)
  // =========================================================================
  if (wsBtnSaveMemory) {
    wsBtnSaveMemory.addEventListener("click", async () => {
      if (!selectedProjectId) return;

      const toList = (text) =>
        text
          .split("\n")
          .map((s) => s.trim())
          .filter((s) => s.length > 0);

      const updateData = {
        objective: wsEditObjective.value.trim(),
        current_state: wsEditState.value.trim(),
        requirements: toList(wsEditRequirements.value),
        constraints: toList(wsEditConstraints.value),
        decisions: toList(wsEditDecisions.value),
        files_context: toList(wsEditFiles.value),
        next_steps: toList(wsEditNext.value),
      };

      try {
        wsBtnSaveMemory.disabled = true;
        wsBtnSaveMemory.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Saving Curated Memory...</span>`;

        const newPkg = await apiRequest(
          `/context/projects/${selectedProjectId}/context`,
          "PATCH",
          updateData
        );

        renderContextPackage(newPkg);
        await loadProjectVersions();
        await loadProjects();

        showToast(`Saved Curated Memory as version ${newPkg.version}!`);
      } catch (err) {
        showToast(err.message || "Failed to update project memory.");
      } finally {
        wsBtnSaveMemory.disabled = false;
        wsBtnSaveMemory.innerHTML = `<i class="fa-solid fa-floppy-disk"></i> <span>Save Curated Memory (Bump Version)</span>`;
      }
    });
  }

  // =========================================================================
  // Version Diff Engine
  // =========================================================================
  if (wsBtnCalcDiff) {
    wsBtnCalcDiff.addEventListener("click", async () => {
      if (!selectedProjectId) return;
      const fromVer = wsDiffFromSelect.value;
      const toVer = wsDiffToSelect.value;

      if (fromVer === toVer) {
        showToast("Select two distinct versions to calculate a diff.");
        return;
      }

      try {
        wsBtnCalcDiff.disabled = true;
        const diffData = await apiRequest(
          `/versions/projects/${selectedProjectId}/diff?from_version=${fromVer}&to_version=${toVer}`
        );

        wsDiffTitle.textContent = `Evolution: ${diffData.from_version} → ${diffData.to_version}`;
        wsDiffSummaryText.textContent = diffData.summary;

        // Render Added
        wsDiffAddedList.innerHTML = "";
        const addedEntries = Object.entries(diffData.added);
        if (addedEntries.length === 0) {
          wsDiffAddedList.innerHTML = `<li class="ws-empty-item">No new additions detected</li>`;
        } else {
          addedEntries.forEach(([cat, items]) => {
            items.forEach((item) => {
              const li = document.createElement("li");
              li.textContent = `[${cat.toUpperCase()}] ${item}`;
              wsDiffAddedList.appendChild(li);
            });
          });
        }

        // Render Modified
        wsDiffModList.innerHTML = "";
        const modEntries = Object.entries(diffData.modified);
        if (modEntries.length === 0) {
          wsDiffModList.innerHTML = `<li class="ws-empty-item">No modified state</li>`;
        } else {
          modEntries.forEach(([cat, change]) => {
            const li = document.createElement("li");
            li.textContent = `[${cat.toUpperCase()}] ${change.to || change.from}`;
            wsDiffModList.appendChild(li);
          });
        }

        // Render Removed
        wsDiffRemList.innerHTML = "";
        const remEntries = Object.entries(diffData.removed);
        if (remEntries.length === 0) {
          wsDiffRemList.innerHTML = `<li class="ws-empty-item">No discarded elements</li>`;
        } else {
          remEntries.forEach(([cat, items]) => {
            items.forEach((item) => {
              const li = document.createElement("li");
              li.textContent = `[${cat.toUpperCase()}] ${item}`;
              wsDiffRemList.appendChild(li);
            });
          });
        }

        showToast(`Calculated memory diff for ${fromVer} → ${toVer}!`);
      } catch (err) {
        showToast(err.message || "Failed to calculate version diff.");
      } finally {
        wsBtnCalcDiff.disabled = false;
      }
    });
  }

  // =========================================================================
  // Cross-AI Handoff Generation
  // =========================================================================
  if (wsBtnGenerateHandoff) {
    wsBtnGenerateHandoff.addEventListener("click", async () => {
      if (!selectedProjectId) {
        showToast("Please select an active project first.");
        return;
      }

      const source = wsHoSource.value;
      const dest = wsHoDest.value;
      const customNotes = wsHoNotes.value.trim() || null;

      try {
        wsBtnGenerateHandoff.disabled = true;
        wsBtnGenerateHandoff.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Formatting for ${dest.toUpperCase()}...</span>`;

        const handoff = await apiRequest("/handoffs", "POST", {
          project_id: selectedProjectId,
          source_provider: source,
          destination_provider: dest,
          custom_instructions: customNotes,
        });

        wsHoCodeBlock.textContent = handoff.formatted_payload;
        lastHandoffUrl = handoff.destination_url;

        const destLabels = {
          claude: "Open Claude (claude.ai)",
          chatgpt: "Open ChatGPT (chatgpt.com)",
          gemini: "Open Gemini (gemini.google.com)",
          cursor: "Open Cursor (cursor.com)",
        };
        wsOpenTargetText.textContent = destLabels[dest] || "Open Destination AI";

        showToast(`Cross-AI Handoff prepared for ${dest.toUpperCase()}!`);
      } catch (err) {
        showToast(err.message || "Failed to generate handoff.");
      } finally {
        wsBtnGenerateHandoff.disabled = false;
        wsBtnGenerateHandoff.innerHTML = `<i class="fa-solid fa-bolt"></i> <span>Generate Tailored Handoff Payload</span>`;
      }
    });
  }

  if (wsBtnCopyPayload) {
    wsBtnCopyPayload.addEventListener("click", () => {
      const text = wsHoCodeBlock.textContent;
      if (!text || text.includes("Click \"Generate Tailored Handoff Payload\"")) {
        showToast("Please generate a handoff payload first.");
        return;
      }

      navigator.clipboard.writeText(text).then(() => {
        showToast("Context Handoff payload copied to clipboard!");
      });
    });
  }

  if (wsBtnOpenTarget) {
    wsBtnOpenTarget.addEventListener("click", () => {
      const text = wsHoCodeBlock.textContent;
      if (text && !text.includes("Click \"Generate Tailored Handoff Payload\"")) {
        navigator.clipboard.writeText(text);
      }
      showToast("Copied context! Opening destination model...");
      window.open(lastHandoffUrl, "_blank", "noopener,noreferrer");
    });
  }

  // =========================================================================
  // Project Creation Sub-modal
  // =========================================================================
  if (wsBtnNewProject) {
    wsBtnNewProject.addEventListener("click", () => {
      newProjectModal.style.display = "flex";
      newProjName.focus();
    });
  }

  function closeNewProjectModal() {
    newProjectModal.style.display = "none";
    newProjName.value = "";
    newProjDesc.value = "";
    newProjGoal.value = "";
  }

  if (btnCloseNewProject) btnCloseNewProject.addEventListener("click", closeNewProjectModal);
  if (btnCancelNewProject) btnCancelNewProject.addEventListener("click", closeNewProjectModal);

  if (btnSubmitNewProject) {
    btnSubmitNewProject.addEventListener("click", async () => {
      const name = newProjName.value.trim();
      if (!name) {
        showToast("Please enter a project name.");
        return;
      }

      try {
        btnSubmitNewProject.disabled = true;
        const newProj = await apiRequest("/projects", "POST", {
          name: name,
          description: newProjDesc.value.trim() || null,
          initial_objective: newProjGoal.value.trim() || null,
        });

        closeNewProjectModal();
        selectedProjectId = newProj.id;
        await loadProjects();
        showToast(`Created persistent project "${newProj.name}"!`);
      } catch (err) {
        showToast(err.message || "Failed to create project.");
      } finally {
        btnSubmitNewProject.disabled = false;
      }
    });
  }

  // Project Switcher
  if (wsProjectSelect) {
    wsProjectSelect.addEventListener("change", async (e) => {
      selectedProjectId = e.target.value;
      await loadActiveProjectContext();
      await loadProjectVersions();
    });
  }

  // =========================================================================
  // Auth Sub-modal
  // =========================================================================
  function openAuthModal() {
    authModal.style.display = "flex";
    authModal.setAttribute("aria-hidden", "false");
    authErrorMsg.style.display = "none";
    if (lenisInstance) lenisInstance.stop();
    setTimeout(() => {
      if (authMode === "register" && authName) {
        authName.focus();
      } else if (authEmail) {
        authEmail.focus();
      }
    }, 60);
  }

  function closeAuthModal() {
    authModal.style.display = "none";
    authModal.setAttribute("aria-hidden", "true");
    if (lenisInstance && (!wsOverlay || !wsOverlay.classList.contains("active"))) {
      lenisInstance.start();
    }
  }

  if (headerSigninBtn) {
    headerSigninBtn.addEventListener("click", () => {
      if (authToken && currentUser) {
        openWorkspace();
      } else {
        openAuthModal();
      }
    });
  }
  if (wsUserPill) wsUserPill.addEventListener("click", openAuthModal);
  if (btnCloseAuth) btnCloseAuth.addEventListener("click", closeAuthModal);

  if (authModal) {
    authModal.addEventListener("click", (e) => {
      if (e.target === authModal) closeAuthModal();
    });
  }

  if (authTabLogin) {
    authTabLogin.addEventListener("click", () => {
      authMode = "login";
      authTabLogin.classList.add("active");
      authTabLogin.setAttribute("aria-selected", "true");
      if (authTabRegister) {
        authTabRegister.classList.remove("active");
        authTabRegister.setAttribute("aria-selected", "false");
      }
      authNameGroup.style.display = "none";
      if (btnSubmitAuth) {
        btnSubmitAuth.innerHTML = `<span>Sign In</span><i class="fa-solid fa-arrow-right btn-icon"></i>`;
      }
      authErrorMsg.style.display = "none";
    });
  }

  if (authTabRegister) {
    authTabRegister.addEventListener("click", () => {
      authMode = "register";
      authTabRegister.classList.add("active");
      authTabRegister.setAttribute("aria-selected", "true");
      if (authTabLogin) {
        authTabLogin.classList.remove("active");
        authTabLogin.setAttribute("aria-selected", "false");
      }
      authNameGroup.style.display = "block";
      if (btnSubmitAuth) {
        btnSubmitAuth.innerHTML = `<span>Create Account</span><i class="fa-solid fa-arrow-right btn-icon"></i>`;
      }
      authErrorMsg.style.display = "none";
    });
  }

  if (btnSubmitAuth) {
    btnSubmitAuth.addEventListener("click", async () => {
      const email = authEmail.value.trim();
      const password = authPassword.value;
      const name = authName.value.trim();

      if (!email || !password) {
        authErrorMsg.textContent = "Please enter email and password.";
        authErrorMsg.style.display = "block";
        return;
      }

      try {
        btnSubmitAuth.disabled = true;
        btnSubmitAuth.innerHTML = `<span>Authenticating...</span><i class="fa-solid fa-circle-notch fa-spin btn-icon"></i>`;
        let tokenData;
        if (authMode === "login") {
          tokenData = await apiRequest("/auth/login", "POST", { email, password });
        } else {
          tokenData = await apiRequest("/auth/register", "POST", { email, password, full_name: name });
        }

        authToken = tokenData.access_token;
        currentUser = { email: tokenData.email, id: tokenData.user_id };
        localStorage.setItem("continuo_jwt", authToken);
        localStorage.setItem("continuo_user", JSON.stringify(currentUser));

        closeAuthModal();
        updateUserUI();
        await loadProjects();
        showToast(`Signed in as ${email}!`);
      } catch (err) {
        authErrorMsg.textContent = err.message || "Authentication failed.";
        authErrorMsg.style.display = "block";
      } finally {
        btnSubmitAuth.disabled = false;
        btnSubmitAuth.innerHTML = authMode === "login"
          ? `<span>Sign In</span><i class="fa-solid fa-arrow-right btn-icon"></i>`
          : `<span>Create Account</span><i class="fa-solid fa-arrow-right btn-icon"></i>`;
      }
    });
  }

  if (btnDemoEngineer) {
    btnDemoEngineer.addEventListener("click", async () => {
      btnDemoEngineer.disabled = true;
      try {
        await ensureAuthenticated();
        closeAuthModal();
        await loadProjects();
        showToast("Signed in as Demo Engineer!");
      } catch (err) {
        showToast(err.message || "Demo login failed");
      } finally {
        btnDemoEngineer.disabled = false;
      }
    });
  }

  // =========================================================================
  // Workspace Tab Navigation (Section 10 & 13)
  // =========================================================================
  function switchWorkspaceTab(tabId) {
    wsTabs.forEach((t) => {
      if (t.getAttribute("data-tab") === tabId) {
        t.classList.add("active");
      } else {
        t.classList.remove("active");
      }
    });
    wsPanels.forEach((p) => {
      if (p.id === `ws-panel-${tabId}`) {
        p.classList.add("active");
      } else {
        p.classList.remove("active");
      }
    });
  }

  wsTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const tabId = tab.getAttribute("data-tab");
      switchWorkspaceTab(tabId);
    });
  });

  // Project Overview Continuation Actions (Section 11)
  function triggerWorkspaceHandoff(destProvider, destUrl, humanName) {
    if (!selectedProjectId) {
      showToast("Please select a project first.");
      return;
    }

    apiRequest("/handoffs", "POST", {
      project_id: selectedProjectId,
      source_provider: "continuo",
      destination_provider: destProvider
    }).then((data) => {
      navigator.clipboard.writeText(data.formatted_payload).then(() => {
        showToast(`✓ Context copied. Ready to continue in ${humanName}.`);
        setTimeout(() => {
          window.open(destUrl, "_blank");
        }, 500);
      }).catch(() => {
        showToast(`✓ Context prepared. Ready for ${humanName}.`);
        window.open(destUrl, "_blank");
      });
    }).catch((err) => {
      showToast("Could not generate handoff: " + (err.message || "Backend offline"));
    });
  }

  if (wsOverviewContChatgpt) {
    wsOverviewContChatgpt.addEventListener("click", () => triggerWorkspaceHandoff("chatgpt", "https://chatgpt.com/", "ChatGPT"));
  }
  if (wsOverviewContClaude) {
    wsOverviewContClaude.addEventListener("click", () => triggerWorkspaceHandoff("claude", "https://claude.ai/new", "Claude"));
  }
  if (wsOverviewContGemini) {
    wsOverviewContGemini.addEventListener("click", () => triggerWorkspaceHandoff("gemini", "https://gemini.google.com/app", "Gemini"));
  }

  if (wsBtnJumpMemory) {
    wsBtnJumpMemory.addEventListener("click", () => {
      switchWorkspaceTab("memory");
    });
  }
  if (wsBtnJumpDiagnostics) {
    wsBtnJumpDiagnostics.addEventListener("click", () => {
      switchWorkspaceTab("diagnostics");
    });
  }

  // =========================================================================
  // Workspace Open & Close
  // =========================================================================
  async function openWorkspace() {
    wsOverlay.classList.add("active");
    document.body.style.overflow = "hidden";
    if (lenisInstance) lenisInstance.stop();

    try {
      await ensureAuthenticated();
      await loadProjects();
    } catch (err) {
      console.warn("Continuo: Background sync failed:", err);
    }
  }

  function closeWorkspace() {
    wsOverlay.classList.remove("active");
    document.body.style.overflow = "";
    if (window.location.hash === "#workspace") {
      history.replaceState(null, document.title, window.location.pathname + window.location.search);
    }
    if (lenisInstance) lenisInstance.start();
  }

  const mobileWsBtn = document.getElementById("mobile-ws-btn");
  if (headerLaunchBtn) headerLaunchBtn.addEventListener("click", openWorkspace);
  if (headerSigninBtn) headerSigninBtn.addEventListener("click", openWorkspace);
  if (mobileWsBtn) mobileWsBtn.addEventListener("click", openWorkspace);
  if (wsCloseBtn) wsCloseBtn.addEventListener("click", closeWorkspace);

  wsOverlay.addEventListener("click", (e) => {
    if (e.target === wsOverlay) closeWorkspace();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (newProjectModal && newProjectModal.style.display === "flex") {
        closeNewProjectModal();
      } else if (authModal && authModal.style.display === "flex") {
        closeAuthModal();
      } else if (wsOverlay.classList.contains("active")) {
        closeWorkspace();
      }
    }
  });

  // Handle direct navigation to #workspace from external pages like install.html
  if (window.location.hash === "#workspace") {
    setTimeout(() => {
      openWorkspace();
    }, 250);
  }
  window.addEventListener("hashchange", () => {
    if (window.location.hash === "#workspace") {
      openWorkspace();
    }
  });

  // Startup initialization
  updateUserUI();
  ensureAuthenticated().then(() => {
    loadProjects();
  });
}

/* ==========================================================================
   EXTENSION INSTALLATION CTA ENGINE
   Responsible strictly for Chrome Extension installation flow.
   NEVER routes to Workspace, /app, /workspace, or dashboard.
   ========================================================================== */
function initExtensionCta() {
  const heroCtaBtn = document.getElementById("hero-cta");
  const footerCtaBtn = document.getElementById("footer-cta-btn");
  const mobileInstallLink = document.querySelector('a.mobile-link[href="install.html"]');
  const storeUrl = getExtensionStoreUrl();
  const isProduction = Boolean(storeUrl);

  const heroCtaText = heroCtaBtn ? heroCtaBtn.querySelector("span") : null;
  const footerCtaText = footerCtaBtn ? footerCtaBtn.querySelector("span") : null;

  if (isProduction) {
    if (heroCtaText) heroCtaText.textContent = "Add to Chrome";
    if (footerCtaText) footerCtaText.textContent = "Add to Chrome";
    if (mobileInstallLink) {
      mobileInstallLink.innerHTML = '<i class="fa-brands fa-chrome" style="margin-right: 6px;"></i> Add to Chrome';
      mobileInstallLink.href = storeUrl;
      mobileInstallLink.target = "_blank";
      mobileInstallLink.rel = "noopener noreferrer";
    }
    if (heroCtaBtn) {
      heroCtaBtn.href = storeUrl;
      heroCtaBtn.setAttribute("title", "Add Continuo to Google Chrome from Chrome Web Store");
    }
    if (footerCtaBtn) {
      footerCtaBtn.href = storeUrl;
      footerCtaBtn.setAttribute("title", "Add Continuo to Google Chrome from Chrome Web Store");
    }
  } else {
    if (heroCtaText) heroCtaText.textContent = "Install Extension";
    if (footerCtaText) footerCtaText.textContent = "Install Extension";
    if (mobileInstallLink) {
      mobileInstallLink.innerHTML = '<i class="fa-brands fa-chrome" style="margin-right: 6px;"></i> Install Extension';
      mobileInstallLink.href = "install.html";
      mobileInstallLink.removeAttribute("target");
      mobileInstallLink.removeAttribute("rel");
    }
    if (heroCtaBtn) {
      heroCtaBtn.href = "install.html";
      heroCtaBtn.setAttribute("title", "Install Continuo Chrome Extension (Development Build)");
    }
    if (footerCtaBtn) {
      footerCtaBtn.href = "install.html";
      footerCtaBtn.setAttribute("title", "Install Continuo Chrome Extension (Development Build)");
    }
  }

  function navigateToAddExtension(e) {
    if (e && e.preventDefault) e.preventDefault();
    if (isProduction && storeUrl) {
      window.open(storeUrl, "_blank", "noopener,noreferrer");
    } else {
      window.location.href = "install.html";
    }
  }

  if (heroCtaBtn) {
    heroCtaBtn.addEventListener("click", navigateToAddExtension);
  }

  if (footerCtaBtn) {
    footerCtaBtn.addEventListener("click", navigateToAddExtension);
  }
}
