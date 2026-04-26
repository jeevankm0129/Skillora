document.addEventListener("DOMContentLoaded", () => {

  /* =========================================
     1. THEME SWITCHER
     ========================================= */
  const themeToggle = document.getElementById("theme-toggle");
  const root = document.documentElement;
  const savedTheme = localStorage.getItem("theme") || "dark";
  root.setAttribute("data-theme", savedTheme);

  if (themeToggle) {
    themeToggle.innerHTML = savedTheme === "dark" ? "☀️" : "🌙";
    themeToggle.addEventListener("click", () => {
      const cur = root.getAttribute("data-theme");
      const next = cur === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      localStorage.setItem("theme", next);
      themeToggle.innerHTML = next === "dark" ? "☀️" : "🌙";
      updateParticleColor(next);
    });
  }

  /* =========================================
     2. SUBTLE 3D TILT
     ========================================= */
  const glassContainer = document.querySelector(".glass-container");
  const maxTilt = 0.7;
  let tRX = 0, tRY = 0, cRX = 0, cRY = 0;

  if (glassContainer && window.matchMedia("(hover: hover)").matches) {
    document.addEventListener("mousemove", (e) => {
      tRX = ((e.clientY / window.innerHeight) * 2 - 1) * maxTilt;
      tRY = -((e.clientX / window.innerWidth) * 2 - 1) * maxTilt;
    });
    document.addEventListener("mouseleave", () => { tRX = 0; tRY = 0; });

    (function tiltLoop() {
      cRX += (tRX - cRX) * 0.07;
      cRY += (tRY - cRY) * 0.07;
      glassContainer.style.transform = `rotateX(${cRX}deg) rotateY(${cRY}deg) translateZ(0)`;
      requestAnimationFrame(tiltLoop);
    })();
  }

  /* =========================================
     3. ANTI-GRAVITY PARTICLE ENGINE
        Canvas is z-index:20 (above glass).
        Particles are invisible → fade in
        smoothly when mouse approaches.
     ========================================= */
  const canvas = document.getElementById("morphic-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  /* ─── SOFT-ORB PARTICLE ENGINE ─────────────────────────────────── */
  const ORB_COUNT    = 1000;   // balanced quality/performance
  const PROXIMITY    = 100;   // px — mouse glow trigger radius
  const GLOW_FRAMES  = 20;   // ~3 s fade-out @ 60 fps
  const PI2          = Math.PI * 2;

  let particles = [];
  let mouse = { x: null, y: null };

  // Color palettes per theme (RGB triplets)
  const PALETTES = {
      dark: [[167, 139, 250], [139, 92, 246], [196, 181, 253], [109, 77, 255]],
    light: [[107, 70,232], [139,92,246], [167,139,250], [80, 50,200]]
  };

  function getPalette() {
    return PALETTES[root.getAttribute("data-theme")] || PALETTES.dark;
  }

  // Called by theme switcher — palette read live, so no-op needed
  function updateParticleColor() {}

  function setCanvasSize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  setCanvasSize();
  window.addEventListener("resize", () => { setCanvasSize(); initParticles(); });

  window.addEventListener("mousemove", (e) => { mouse.x = e.clientX; mouse.y = e.clientY; });
  window.addEventListener("mouseout",  () => { mouse.x = null; mouse.y = null; });

  class SoftOrb {
    constructor(randomPos = true) {
      if (randomPos) {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
      }
      // Pick a random color from palette
      const pal = getPalette();
      this.color = pal[Math.floor(Math.random() * pal.length)];

      // Slow directional drift with smooth easing
      const angle  = Math.random() * PI2;
      const speed  = 0.06 + Math.random() * 0.2;
      this.vx      = Math.cos(angle) * speed;
      this.vy      = Math.sin(angle) * speed;
      this.tvx     = this.vx;  // target velocity
      this.tvy     = this.vy;
      this.dirTimer = Math.floor(Math.random() * 450) + 200;

      // Orb radius for radial gradient (NOT a hard circle)
      this.baseR = 0.1 + Math.random() * 10;   // 22–62 px
      this.r     = this.baseR;

      // Breathing animation
      this.breathPhase = Math.random() * PI2;
      this.breathSpeed  = 0.005 + Math.random() * 0.007;
      this.breathAmp    = 0.03 + Math.random() * 0.08;  // very subtle when dim

      // Base opacity — very dim when undisturbed (~10%)
      this.baseAlpha = 0.06 + Math.random() * 0.05;  // 6–11%
      this.alpha     = this.baseAlpha;

      // Glow state
      this.glowTimer = 0;
    }

    update() {
      // ── Mouse proximity → trigger glow ──
      if (mouse.x !== null) {
        const dx   = mouse.x - this.x;
        const dy   = mouse.y - this.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < PROXIMITY) {
          this.glowTimer = GLOW_FRAMES;  // refresh while mouse is close
          // Whisper-gentle gravitational pull
          const pull = (1 - dist / PROXIMITY) * 0.03;
          this.tvx  += (dx / dist) * pull;
          this.tvy  += (dy / dist) * pull;
        }
      }

      // ── Breathing opacity ──
      this.breathPhase += this.breathSpeed;
      const breath = Math.sin(this.breathPhase);  // −1 … +1

      // ── Glow boost fades linearly over GLOW_FRAMES ──
      let glowBoost = 0;
      if (this.glowTimer > 0) {
        // Peak boost → baseAlpha (~0.09) + 0.77 ≈ 0.86 (80%+)
        glowBoost = (this.glowTimer / GLOW_FRAMES) * 0.85;
        this.glowTimer--;
      }

      const targetAlpha = this.baseAlpha * (1 + breath * this.breathAmp) + glowBoost;
      // Very slow lerp → smooth, never jarring
      this.alpha += (Math.max(0.02, Math.min(1, targetAlpha)) - this.alpha) * 0.032;

      // Subtle size pulse in sync with breathing
      this.r = this.baseR * (1 + breath * 0.07);

      // ── Smooth velocity easing (direction changes naturally) ──
      this.dirTimer--;
      if (this.dirTimer <= 0) {
        const angle  = Math.random() * PI2;
        const speed  = 0.06 + Math.random() * 0.16;
        this.tvx     = Math.cos(angle) * speed;
        this.tvy     = Math.sin(angle) * speed;
        this.dirTimer = Math.floor(Math.random() * 450) + 200;
      }
      // Clamp target velocity to prevent runaway pulls
      const maxV = 0.8;
      this.tvx = Math.max(-maxV, Math.min(maxV, this.tvx));
      this.tvy = Math.max(-maxV, Math.min(maxV, this.tvy));

      this.vx += (this.tvx - this.vx) * 0.010;
      this.vy += (this.tvy - this.vy) * 0.010;
      this.x  += this.vx;
      this.y  += this.vy;

      // ── Soft boundary wrap (pad so orb fully exits before re-entering) ──
      const pad = this.baseR * 4;
      if (this.x < -pad)                this.x = canvas.width  + pad;
      if (this.x > canvas.width  + pad) this.x = -pad;
      if (this.y < -pad)                this.y = canvas.height + pad;
      if (this.y > canvas.height + pad) this.y = -pad;

      this.draw();
    }

    draw() {
      const [r, g, b] = this.color;
      const cx = this.x, cy = this.y;
      const R  = this.r;
      const a  = this.alpha;

      // ── Glow layers — only when mouse has activated this orb ──
      // Threshold: anything above bare base means it's glowing
      if (a > 0.16) {
        // Layer 1: Outer bloom — subtle, not blinding
        const bloom = ctx.createRadialGradient(cx, cy, 0, cx, cy, R * 2.8);
        bloom.addColorStop(0,    `rgba(${r},${g},${b},${(a * 0.11).toFixed(3)})`);
        bloom.addColorStop(0.5,  `rgba(${r},${g},${b},${(a * 0.033).toFixed(3)})`);
        bloom.addColorStop(1,    `rgba(${r},${g},${b},0)`);
        ctx.fillStyle = bloom;
        ctx.fillRect(cx - R * 2.8, cy - R * 2.8, R * 5.6, R * 5.6);

        // Layer 2: Mid glow ring — soft halo
        const mid = ctx.createRadialGradient(cx, cy, 0, cx, cy, R * 1.5);
        mid.addColorStop(0,   `rgba(${r},${g},${b},${(a * 0.24).toFixed(3)})`);
        mid.addColorStop(0.6, `rgba(${r},${g},${b},${(a * 0.077).toFixed(3)})`);
        mid.addColorStop(1,   `rgba(${r},${g},${b},0)`);
        ctx.fillStyle = mid;
        ctx.fillRect(cx - R * 1.5, cy - R * 1.5, R * 3, R * 3);
      }

      // ── Core — always drawn (dim dot when at rest, bright orb when glowing) ──
      const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
      if (a > 0.16) {
        // Glowing: hot-white centre
        core.addColorStop(0,    `rgba(255,255,255,${(a * 0.90).toFixed(3)})`);
        core.addColorStop(0.15, `rgba(235,220,255,${(a * 0.75).toFixed(3)})`);
        core.addColorStop(0.45, `rgba(${r},${g},${b},${(a * 0.45).toFixed(3)})`);
        core.addColorStop(1,    `rgba(${r},${g},${b},0)`);
      } else {
        // Dim resting state: soft purple dot, no white core
        core.addColorStop(0,   `rgba(${r},${g},${b},${(a * 0.85).toFixed(3)})`);
        core.addColorStop(0.5, `rgba(${r},${g},${b},${(a * 0.30).toFixed(3)})`);
        core.addColorStop(1,   `rgba(${r},${g},${b},0)`);
      }
      ctx.fillStyle = core;
      ctx.fillRect(cx - R, cy - R, R * 2, R * 2);
    }
  }

  function initParticles() {
    particles = [];
    for (let i = 0; i < ORB_COUNT; i++) particles.push(new SoftOrb(true));
  }

  function particleLoop() {
    requestAnimationFrame(particleLoop);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Additive blending: overlapping orbs create naturally brighter merged light
    ctx.globalCompositeOperation = "lighter";
    particles.forEach(p => p.update());
    ctx.globalCompositeOperation = "source-over";  // always reset
  }

  initParticles();
  particleLoop();



  /* =========================================
     4. JOB CARD EXPAND / COLLAPSE
     ========================================= */
  const jobCard  = document.getElementById("job-card");
  const heroText = document.getElementById("hero-text");
  const btnResume = document.getElementById("btn-resume");

  window.expandJobCard = function () {
    if (jobCard && !jobCard.classList.contains("expanded")) {
      jobCard.classList.add("expanded");
      if (heroText)  heroText.classList.add("shift-up");
      if (btnResume) btnResume.classList.add("shift-down");
    }
  };

  window.closeJobCard = function (event) {
    if (event) event.stopPropagation();
    if (jobCard)   jobCard.classList.remove("expanded");
    if (heroText)  heroText.classList.remove("shift-up");
    if (btnResume) btnResume.classList.remove("shift-down");
  };

  /* =========================================
     5. TELEGRAM RESUME REDIRECT
     ========================================= */
  window.redirectToTelegramResume = function () {
    window.open(`https://t.me/mySkilloraBot?start=build_resume`, "_blank");
  };

  /* =========================================
     6. FILE UPLOAD → FETCH JOBS → CARD STACK
     ========================================= */
  window.handleFileUpload = async function (event) {
    const file = event.target.files[0];
    if (!file) return;

    const dropZoneText    = document.getElementById("drop-zone-text");
    const scanLine        = document.getElementById("scan-line");
    const uploadUI        = document.querySelector(".job-upload-ui");
    const jobCardContainer = document.getElementById("job-card");

    // ── Loading animation ──
    dropZoneText.innerHTML = `Extracting from <strong>${file.name}</strong>…<br>
      <span style="font-size:0.78rem;color:var(--accent-1)">Pinging global job markets…</span>`;
    scanLine.style.display = "block";

    let scanPos = 0, scanDir = 1;
    const scanInterval = setInterval(() => {
      scanPos += 5 * scanDir;
      if (scanPos > 95 || scanPos < 0) scanDir *= -1;
      scanLine.style.top = `${scanPos}%`;
    }, 50);

    const formData = new FormData();
    formData.append("resume", file);

    try {
      const response = await fetch("/api/recommend-jobs", { method: "POST", body: formData });
      const data     = await response.json();
      clearInterval(scanInterval);

      if (data.status === "success" || data.status === "needs_email") {

        // ── Hide the job card box completely ──
        jobCardContainer.style.transition = "opacity 0.4s ease, transform 0.4s ease";
        jobCardContainer.style.opacity    = "0";
        jobCardContainer.style.transform  = "scale(0.92)";

        setTimeout(() => {
          jobCardContainer.style.display = "none";
          if (heroText)  heroText.classList.remove("shift-up");
          if (btnResume) {
            btnResume.classList.remove("shift-down");
            btnResume.style.display = "none";  // also hide resume button while cards show
          }

          // ── Build results wrapper ──
          const heroCtas   = document.querySelector(".hero-ctas");
          const wrapper    = document.createElement("div");
          wrapper.id       = "job-results-wrapper";

          // ── STATE A: Jobs found → Anti-Gravity Carousel ──
          if (data.status === "success") {
            const jobs = data.jobs;

            // Build DOM skeleton
            wrapper.innerHTML = `
              <p class="job-results-title">${jobs.length} Semantic Matches</p>
              <div class="carousel-scene" id="carousel-scene">
                <div class="carousel-track" id="carousel-track"></div>
              </div>
              <div class="ag-controls">
                <button class="ag-nav-btn" id="ag-prev" aria-label="Previous">&#8592;</button>
                <div class="ag-dots" id="ag-dots"></div>
                <button class="ag-nav-btn" id="ag-next" aria-label="Next">&#8594;</button>
              </div>
              <div class="job-results-actions">
                <button class="btn btn-outline" onclick="resetJobCard(event)">Close Dashboard</button>
              </div>`;

            heroCtas.appendChild(wrapper);

            /* ── ANTI-GRAVITY CAROUSEL ENGINE ────────────────────── */
            const scene   = document.getElementById("carousel-scene");
            const track   = document.getElementById("carousel-track");
            const dotsBox = document.getElementById("ag-dots");

            // ── Config ──────────────────────────────────────────────
            const CARD_W      = 280;   // px
            const SPREAD      = 340;   // horizontal gap between card centres
            const MAX_VISIBLE = 5;     // cards rendered each side + centre
            const ROT_Y_STEP  = 28;    // degrees rotateY per slot
            const ARC_DEPTH   = 24;    // px translateZ arc falloff
            const ARC_Y       = 14;    // px vertical arc drop at extremes
            const SCALE_STEP  = 0.12;  // scale reduction per slot
            const OPACITY_STEP= 0.22;  // opacity reduction per slot
            const BLUR_STEP   = 1.8;   // px blur per slot (depth of field)

            // Spring physics
            const SPRING_STIFFNESS = 0.09;
            const SPRING_DAMPING   = 0.72;

            // State
            let currentIndex = 0;             // snapped integer index
            let targetOffset  = 0;            // target fractional position
            let currentOffset = 0;            // animated fractional position
            let velocity      = 0;            // spring velocity
            let isDragging    = false;
            let dragStartX    = 0;
            let dragStartOffset = 0;
            let lastDragX     = 0;
            let dragVelocity  = 0;
            let rafId         = null;

            // Float breathing state per slot
            const floatPhase = Array.from({length: jobs.length}, () => Math.random() * Math.PI * 2);

            // ── Build dots ──────────────────────────────────────────
            jobs.forEach((_, i) => {
              const dot = document.createElement("div");
              dot.className = "ag-dot" + (i === 0 ? " ag-dot-active" : "");
              dot.id = `ag-dot-${i}`;
              dot.addEventListener("click", () => agNavigateTo(i));
              dotsBox.appendChild(dot);
            });

            // ── Build card elements ─────────────────────────────────
            const cardEls = jobs.map((job, i) => {
              const el = document.createElement("div");
              el.className = "ag-card";
              el.id = `ag-card-${i}`;
              el.innerHTML = `
                <div class="ag-card-header">
                  <div class="ag-card-info">
                    <div class="ag-card-title">${job.title}</div>
                    <div class="ag-card-company">${job.company} &bull; ${job.location}</div>
                  </div>
                  <div class="ag-match-badge">${job.match}</div>
                </div>
                <p class="ag-card-reason">"${job.reasoning}"</p>
                <div class="ag-card-footer">
                  <span class="ag-card-salary">${job.salary}</span>
                  <a href="${job.link}" target="_blank"
                     class="btn btn-primary ag-card-apply"
                     onclick="event.stopPropagation()">Apply →</a>
                </div>`;
              el.addEventListener("click", () => {
                if (i !== currentIndex) agNavigateTo(i);
              });
              track.appendChild(el);
              return el;
            });

            // ── Layout calculation ──────────────────────────────────
            function computeCardState(slotOffset) {
              // slotOffset: fractional distance from center (0 = active, ±1 = adjacent …)
              const absOff  = Math.abs(slotOffset);
              const sign    = slotOffset < 0 ? -1 : 1;

              const tx      = slotOffset * SPREAD;
              const ry      = -slotOffset * ROT_Y_STEP;
              const tz      = -absOff * absOff * ARC_DEPTH;    // convex arc: Z drops quadratically
              const ty      = absOff * absOff * ARC_Y;         // slight downward arc at extremes
              // Active card gets 1.22× uplift; it fades to 1.0 at |offset| = 1 and below that by SCALE_STEP
              const activeUplift = Math.max(0, 1 - absOff) * 0.22;
              const scale   = Math.max(0.45, 1 + activeUplift - absOff * SCALE_STEP);
              const opacity = Math.max(0.08, 1 - absOff * OPACITY_STEP);
              const blur    = Math.min(absOff * BLUR_STEP, 8);
              const zIndex  = Math.round(100 - absOff * 10);

              return { tx, ty, tz, ry, scale, opacity, blur, zIndex };
            }

            // ── Apply transforms ────────────────────────────────────
            let frameCount = 0;
            function applyLayout() {
              frameCount++;
              const floatT = frameCount * 0.012;

              jobs.forEach((_, i) => {
                const el         = cardEls[i];
                const slotOffset = i - currentOffset;           // fractional distance from visual center

                // Only render cards within visible window
                if (Math.abs(slotOffset) > MAX_VISIBLE) {
                  el.style.visibility = "hidden";
                  return;
                }
                el.style.visibility = "visible";

                const s = computeCardState(slotOffset);

                // Idle breathing float — each card has unique phase; only center breathes fully
                const breathAmp  = Math.max(0, 1 - Math.abs(slotOffset)) * 4;
                floatPhase[i]   += 0.008;
                const floatY     = Math.sin(floatPhase[i]) * breathAmp;

                // Parallax micro-tilt from drag velocity
                const parallelTilt = velocity * 0.6;

                const transform = [
                  `translate(-50%, -50%)`,
                  `translateX(${s.tx}px)`,
                  `translateY(${s.ty + floatY}px)`,
                  `translateZ(${s.tz}px)`,
                  `rotateY(${s.ry + parallelTilt}deg)`,
                  `scale(${s.scale})`
                ].join(" ");

                el.style.transform  = transform;
                el.style.opacity    = s.opacity;
                el.style.zIndex     = s.zIndex;
                el.style.filter     = s.blur > 0 ? `blur(${s.blur.toFixed(1)}px)` : "";
                el.style.willChange = "transform, opacity, filter";

                // Active class management
                const isActive = Math.round(currentOffset) === i;
                el.classList.toggle("ag-active", isActive);
              });
            }

            // ── Physics spring loop ─────────────────────────────────
            function springLoop() {
              if (!isDragging) {
                const diff = targetOffset - currentOffset;
                velocity   = velocity * SPRING_DAMPING + diff * SPRING_STIFFNESS;
                currentOffset += velocity;

                // Snap when very close and slow
                if (Math.abs(diff) < 0.001 && Math.abs(velocity) < 0.0005) {
                  currentOffset = targetOffset;
                  velocity      = 0;
                }
              }

              applyLayout();
              updateDots();
              rafId = requestAnimationFrame(springLoop);
            }

            // ── Dot update ──────────────────────────────────────────
            function updateDots() {
              const snap = Math.round(currentOffset);
              jobs.forEach((_, i) => {
                const dot = document.getElementById(`ag-dot-${i}`);
                if (dot) dot.classList.toggle("ag-dot-active", i === snap);
              });
              currentIndex = snap;
            }

            // ── Navigate ────────────────────────────────────────────
            function agNavigateTo(index) {
              index        = Math.max(0, Math.min(jobs.length - 1, index));
              targetOffset = index;
            }

            // Expose to nav buttons
            document.getElementById("ag-prev").addEventListener("click", () => {
              agNavigateTo(Math.round(targetOffset) - 1);
            });
            document.getElementById("ag-next").addEventListener("click", () => {
              agNavigateTo(Math.round(targetOffset) + 1);
            });

            // ── Drag / Swipe ─────────────────────────────────────────
            function onDragStart(clientX) {
              isDragging      = true;
              dragStartX      = clientX;
              dragStartOffset = currentOffset;
              lastDragX       = clientX;
              dragVelocity    = 0;
              velocity        = 0;
              scene.style.cursor = "grabbing";
            }

            function onDragMove(clientX) {
              if (!isDragging) return;
              const dx        = clientX - dragStartX;
              dragVelocity    = clientX - lastDragX;
              lastDragX       = clientX;
              currentOffset   = dragStartOffset - dx / SPREAD;
              // Soft rubber-band at edges
              const maxIdx    = jobs.length - 1;
              if (currentOffset < 0)      currentOffset = currentOffset * 0.25;
              if (currentOffset > maxIdx) currentOffset = maxIdx + (currentOffset - maxIdx) * 0.25;
            }

            function onDragEnd() {
              if (!isDragging) return;
              isDragging = false;
              scene.style.cursor = "grab";
              // Momentum flick: let drag velocity determine final target
              const momentumBoost = -dragVelocity / SPREAD * 3.5;
              let snapTarget = Math.round(currentOffset + momentumBoost);
              snapTarget = Math.max(0, Math.min(jobs.length - 1, snapTarget));
              agNavigateTo(snapTarget);
              velocity = -dragVelocity / SPREAD * 1.5;  // seed spring with drag momentum
            }

            // Mouse events
            scene.addEventListener("mousedown",  e => { e.preventDefault(); onDragStart(e.clientX); });
            window.addEventListener("mousemove", e => { if (isDragging) onDragMove(e.clientX); });
            window.addEventListener("mouseup",   ()  => onDragEnd());

            // Touch events
            scene.addEventListener("touchstart",  e => onDragStart(e.touches[0].clientX), { passive: true });
            scene.addEventListener("touchmove",   e => { e.preventDefault(); onDragMove(e.touches[0].clientX); }, { passive: false });
            scene.addEventListener("touchend",    ()  => onDragEnd());

            // Keyboard navigation
            scene.setAttribute("tabindex", "0");
            scene.addEventListener("keydown", e => {
              if (e.key === "ArrowLeft")  agNavigateTo(Math.round(targetOffset) - 1);
              if (e.key === "ArrowRight") agNavigateTo(Math.round(targetOffset) + 1);
            });

            // Cursor parallax micro-tilt
            scene.addEventListener("mousemove", e => {
              if (isDragging) return;
              const rect = scene.getBoundingClientRect();
              const cx   = rect.left + rect.width / 2;
              const nx   = (e.clientX - cx) / (rect.width / 2);   // −1 … +1
              // Gentle parallax on center card only — via velocity approximation
              velocity += nx * 0.0008;
            });

            // Start loop
            rafId = requestAnimationFrame(springLoop);

            // Cleanup on card reset
            window._agCleanup = () => {
              if (rafId) cancelAnimationFrame(rafId);
            };
          }

          // ── STATE B: No jobs → Email alert ──
          else if (data.status === "needs_email") {
            wrapper.innerHTML = `
              <div style="display:flex;flex-direction:column;align-items:center;text-align:center;padding:10px 0;gap:14px;max-width:420px">
                <h3 class="gradient-text" style="font-size:1.4rem">Market Analysis Complete</h3>
                <p style="color:var(--text-muted);font-size:0.9rem;line-height:1.5">${data.message}</p>
                <div style="display:flex;gap:10px;width:100%">
                  <input type="email" id="alert-email" placeholder="Your email address"
                    style="flex:1;padding:11px 14px;border-radius:8px;border:1px solid var(--glass-border);
                           background:var(--card-bg);color:var(--text-main);outline:none;
                           font-size:0.9rem;font-family:inherit">
                  <button class="btn btn-primary" onclick="submitEmailAlert()">Track</button>
                </div>
                <p id="alert-status" style="font-size:0.82rem;min-height:1.1rem"></p>
              </div>
              <div class="job-results-actions">
                <button class="btn btn-outline" onclick="resetJobCard(event)">Close Dashboard</button>
              </div>`;
            heroCtas.appendChild(wrapper);
          }
        }, 420);  // wait for fade-out

      } else {
        // API error
        dropZoneText.innerHTML = `<span style="color:#f87171">Error: ${data.message}</span>`;
        scanLine.style.display = "none";
      }

    } catch (err) {
      clearInterval(scanInterval);
      scanLine.style.display = "none";
      dropZoneText.innerHTML = `<span style="color:#f87171">Server offline. Transmission failed.</span>`;
      console.error(err);
    }
  };

  /* =========================================
     7. RESET — restore original button state
     ========================================= */
  window.resetJobCard = function (event) {
    if (event) event.stopPropagation();

    // Cancel carousel rAF loop if running
    if (typeof window._agCleanup === "function") {
      window._agCleanup();
      window._agCleanup = null;
    }

    // Remove results wrapper
    const wrapper = document.getElementById("job-results-wrapper");
    if (wrapper) wrapper.remove();

    // Reset and show job card button
    const jobCardContainer = document.getElementById("job-card");
    if (jobCardContainer) {
      jobCardContainer.style.display    = "";
      jobCardContainer.style.opacity    = "";
      jobCardContainer.style.transform  = "";
      jobCardContainer.style.transition = "";
      jobCardContainer.classList.remove("expanded", "hidden");
    }

    // Show resume button
    if (btnResume) {
      btnResume.style.display = "";
      btnResume.classList.remove("shift-down");
    }
    if (heroText) heroText.classList.remove("shift-up");

    // Reset file input + drop zone text
    const dropZoneText = document.getElementById("drop-zone-text");
    if (dropZoneText) dropZoneText.innerHTML = "Click to Upload PDF Document";
    const resumeUpload = document.getElementById("resume-upload");
    if (resumeUpload) resumeUpload.value = "";

    // Hide scan line
    const scanLine = document.getElementById("scan-line");
    if (scanLine) scanLine.style.display = "none";
  };

  /* =========================================
     8. EMAIL ALERT SUBMIT
     ========================================= */
  window.submitEmailAlert = async function () {
    const emailInput = document.getElementById("alert-email");
    const statusText = document.getElementById("alert-status");
    const email = emailInput.value;

    if (!email || !email.includes("@")) {
      statusText.style.color = "#f87171";
      statusText.innerText = "Please enter a valid email.";
      return;
    }

    const formData = new FormData();
    formData.append("email", email);
    try {
      const response = await fetch("/api/save-email-alert", { method: "POST", body: formData });
      const result   = await response.json();
      statusText.style.color = "#4ade80";
      statusText.innerText   = result.message;
      emailInput.value = "";
    } catch (e) {
      statusText.style.color = "#f87171";
      statusText.innerText   = "Error connecting to server.";
    }
  };
});

/* =========================================
   SCROLL-REVEAL — secondary pages
   Observes .sr elements and adds .sr-visible
   when they enter the viewport.
   No dependency on the DOMContentLoaded block.
   ========================================= */
(function () {
  if (typeof IntersectionObserver === "undefined") {
    // Fallback: just show everything immediately
    document.querySelectorAll(".sr").forEach(el => el.classList.add("sr-visible"));
    return;
  }

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("sr-visible");
          io.unobserve(entry.target);   // fire once only
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -32px 0px" }
  );

  // Observe all .sr elements present now and any added later
  function observeAll() {
    document.querySelectorAll(".sr:not(.sr-visible)").forEach(el => io.observe(el));
  }

  // Run immediately for static elements
  observeAll();

  // Also watch for dynamically injected .sr nodes (e.g. job results wrapper)
  const mo = new MutationObserver(observeAll);
  mo.observe(document.body, { childList: true, subtree: true });
})();
