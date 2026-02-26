// script.js
// Interactive procedural nebula + starfield:
// - Mouse move: subtle turbulence disturbance
// - Click: gentle ripple pulse (slight "drip" feel)
// No images, no libraries.

(() => {
    const canvas = document.getElementById("bgfx");
    const ctx = canvas.getContext("2d", { alpha: false });

    const DPR = Math.min(2, window.devicePixelRatio || 1);

    let W = 0, H = 0;

    // ----- Stars (static field, slight shimmer) -----
    const stars = [];
    function initStars(count) {
        stars.length = 0;
        for (let i = 0; i < count; i++) {
            const x = Math.random();
            const y = Math.random();
            const r = Math.random() * 1.4 + 0.2;
            const warm = Math.random() < 0.18; // few golden stars
            const a = Math.random() * 0.6 + 0.25;
            const tw = Math.random() * 0.8 + 0.2;
            stars.push({ x, y, r, warm, a, tw, p: Math.random() * Math.PI * 2 });
        }
    }

    // ----- Ripple field (heightmap) -----
    // Small-res sim for performance. Used to distort nebula sampling.
    let simW = 0, simH = 0;
    let h0, h1; // height buffers
    function initRippleSim() {
        // keep it proportional + light
        simW = Math.max(160, Math.floor(W / 10));
        simH = Math.max(120, Math.floor(H / 10));
        h0 = new Float32Array(simW * simH);
        h1 = new Float32Array(simW * simH);
    }

    function splash(nx, ny, strength = 0.9, radius = 6) {
        const cx = Math.floor(nx * simW);
        const cy = Math.floor(ny * simH);
        const r2 = radius * radius;

        for (let y = -radius; y <= radius; y++) {
            for (let x = -radius; x <= radius; x++) {
                const dx = x, dy = y;
                if (dx * dx + dy * dy > r2) continue;
                const ix = cx + x;
                const iy = cy + y;
                if (ix < 1 || iy < 1 || ix >= simW - 1 || iy >= simH - 1) continue;
                const falloff = 1 - (dx * dx + dy * dy) / r2;
                h0[iy * simW + ix] += strength * falloff;
            }
        }
    }

    function stepRipples() {
        // classic ripple: h1 = (neighbors avg - h1) * damping
        const damping = 0.985; // higher = subtler/longer
        for (let y = 1; y < simH - 1; y++) {
            const row = y * simW;
            for (let x = 1; x < simW - 1; x++) {
                const i = row + x;
                const n =
                    h0[i - 1] + h0[i + 1] +
                    h0[i - simW] + h0[i + simW];
                const v = (n * 0.5 - h1[i]);
                h1[i] = v * damping;
            }
        }
        // swap
        const tmp = h0; h0 = h1; h1 = tmp;
    }

    // ----- Mouse interaction -----
    const pointer = {
        x: 0.5, y: 0.5,
        vx: 0, vy: 0,
        down: false
    };

    let t = 0;

    function resize() {
        W = Math.floor(window.innerWidth);
        H = Math.floor(window.innerHeight);
        canvas.width = Math.floor(W * DPR);
        canvas.height = Math.floor(H * DPR);
        canvas.style.width = W + "px";
        canvas.style.height = H + "px";
        ctx.setTransform(DPR, 0, 0, DPR, 0, 0);

        initStars(Math.floor((W * H) / 18000)); // density
        initRippleSim();
    }

    window.addEventListener("resize", resize, { passive: true });

    // Mouse move = gentle disturbance
    window.addEventListener("mousemove", (e) => {
        const nx = e.clientX / W;
        const ny = e.clientY / H;

        pointer.vx = (nx - pointer.x);
        pointer.vy = (ny - pointer.y);
        pointer.x = nx;
        pointer.y = ny;

        // subtle continuous disturbance (small)
        const vel = Math.hypot(pointer.vx, pointer.vy);
        const s = Math.min(0.5, vel * 4.0) * 0.35; // keep subtle
        splash(nx, ny, s, 5);
    }, { passive: true });

    // Click ripple (slight drip pulse)
    window.addEventListener("pointerdown", (e) => {
        pointer.down = true;
        const nx = e.clientX / W;
        const ny = e.clientY / H;

        // Small, premium ripple: not too strong
        splash(nx, ny, 1.2, 8);
        // a tiny second pulse to mimic "drip"
        setTimeout(() => splash(nx, ny, 0.55, 6), 70);
    }, { passive: true });

    window.addEventListener("pointerup", () => { pointer.down = false; }, { passive: true });

    // ----- Procedural Nebula -----
    // Cheap “flow” using layered sin fields + ripple distortion.
    function nebulaColor(u, v, time, dx, dy) {
        // Distort UV (mouse ripples)
        u += dx;
        v += dy;

        // Flowing streaks: layered waves
        const a =
            Math.sin((u * 7.2 + time * 0.55) + Math.cos(v * 3.2 - time * 0.35)) +
            Math.sin((v * 6.0 - time * 0.42) + Math.cos(u * 2.8 + time * 0.25));

        const b =
            Math.sin((u * 14.0 - time * 0.75) + v * 3.0) * 0.55 +
            Math.cos((v * 12.0 + time * 0.62) - u * 2.0) * 0.45;

        const streak = (a * 0.6 + b * 0.4);
        const density = Math.max(0, streak);

        // Soft vignetting & depth
        const cx = u - 0.5, cy = v - 0.5;
        const vign = 1 - Math.min(1, (cx * cx + cy * cy) * 1.35);

        // Palette (deep space -> modern purple -> lilac glow)
        const deep = { r: 10, g: 6, b: 24 };
        const mid = { r: 90, g: 32, b: 160 };
        const hi = { r: 175, g: 110, b: 255 };

        const k = Math.min(1, density * 0.72 + 0.08) * vign;

        // Extra bloom banding
        const glow = Math.pow(Math.max(0, density), 1.6) * 0.55;

        const r = deep.r + (mid.r - deep.r) * k + (hi.r - mid.r) * glow;
        const g = deep.g + (mid.g - deep.g) * k + (hi.g - mid.g) * glow;
        const bcol = deep.b + (mid.b - deep.b) * k + (hi.b - mid.b) * glow;

        return { r, g, b: bcol, k };
    }

    // Render strategy:
    // - Draw base gradient
    // - Draw nebula in low-res offscreen, scale up w/ blur-ish alpha layers (premium softness)
    // - Draw stars on top
    const off = document.createElement("canvas");
    const offCtx = off.getContext("2d");

    function render() {
        t += 0.016;

        stepRipples();

        // Base gradient (premium deep space)
        const grd = ctx.createLinearGradient(0, 0, W, H);
        grd.addColorStop(0, "#05040b");
        grd.addColorStop(0.35, "#0b0616");
        grd.addColorStop(0.7, "#120622");
        grd.addColorStop(1, "#07030d");
        ctx.fillStyle = grd;
        ctx.fillRect(0, 0, W, H);

        // Offscreen nebula (low res for speed)
        const scale = 0.55; // lower = faster, smoother
        const nW = Math.floor(W * scale);
        const nH = Math.floor(H * scale);
        off.width = nW;
        off.height = nH;

        const img = offCtx.createImageData(nW, nH);
        const data = img.data;

        // Ripple->distortion mapping
        const amp = 0.012; // distortion amount (keep subtle/premium)
        const time = t;

        for (let y = 0; y < nH; y++) {
            const v = y / nH;
            const sy = Math.floor(v * (simH - 1));

            for (let x = 0; x < nW; x++) {
                const u = x / nW;
                const sx = Math.floor(u * (simW - 1));
                const h = h0[sy * simW + sx] || 0;

                // Use ripple height to distort sampling
                const dx = h * amp;
                const dy = h * amp * 0.8;

                const c = nebulaColor(u, v, time, dx, dy);

                const i = (y * nW + x) * 4;

                // Add soft “dust” speckles inside nebula
                const dust = Math.max(0, Math.sin((u * 48 + v * 32) + time * 0.9)) * 0.03 * c.k;

                data[i + 0] = Math.max(0, Math.min(255, c.r + 255 * dust));
                data[i + 1] = Math.max(0, Math.min(255, c.g + 255 * dust));
                data[i + 2] = Math.max(0, Math.min(255, c.b + 255 * dust));
                data[i + 3] = 255;
            }
        }

        offCtx.putImageData(img, 0, 0);

        // Composite nebula: multiple passes = soft “blurred streaks” look
        ctx.globalCompositeOperation = "screen";
        ctx.globalAlpha = 0.34;
        ctx.drawImage(off, -W * 0.02, -H * 0.02, W * 1.04, H * 1.04);

        ctx.globalAlpha = 0.22;
        ctx.drawImage(off, 0, 0, W, H);

        // extra glow pass
        ctx.globalAlpha = 0.14;
        ctx.drawImage(off, W * 0.01, H * 0.01, W * 0.98, H * 0.98);

        ctx.globalCompositeOperation = "source-over";
        ctx.globalAlpha = 1;

        // Stars (on top) + subtle twinkle
        for (const s of stars) {
            s.p += 0.01 * s.tw;
            const tw = 0.75 + Math.sin(s.p) * 0.25;
            const x = s.x * W;
            const y = s.y * H;
            const r = s.r * tw;
            const a = s.a * tw;

            ctx.beginPath();
            ctx.arc(x, y, r, 0, Math.PI * 2);

            if (s.warm) {
                ctx.fillStyle = `rgba(255, 210, 120, ${a})`;
            } else {
                ctx.fillStyle = `rgba(255, 255, 255, ${a})`;
            }
            ctx.fill();
        }

        // Soft vignette to keep it premium
        const vg = ctx.createRadialGradient(W * 0.5, H * 0.45, Math.min(W, H) * 0.2, W * 0.5, H * 0.5, Math.max(W, H) * 0.75);
        vg.addColorStop(0, "rgba(0,0,0,0)");
        vg.addColorStop(1, "rgba(0,0,0,0.55)");
        ctx.fillStyle = vg;
        ctx.fillRect(0, 0, W, H);

        requestAnimationFrame(render);
    }

    // Tiny tilt for the card (kept premium)
    const card = document.getElementById("glassCard");
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (!reduceMotion) {
        window.addEventListener("mousemove", (e) => {
            const x = (e.clientX / W) - 0.5;
            const y = (e.clientY / H) - 0.5;
            const tx = (y * 4).toFixed(2);
            const ty = (-x * 6).toFixed(2);
            card.style.transform = `perspective(900px) rotateX(${tx}deg) rotateY(${ty}deg) translateZ(0)`;
        }, { passive: true });

        window.addEventListener("mouseleave", () => {
            card.style.transform = `perspective(900px) rotateX(0deg) rotateY(0deg) translateZ(0)`;
        });
    }

    // CTA micro animation
    document.getElementById("ctaBtn").addEventListener("click", () => {
        card.animate(
            [
                { transform: card.style.transform || "perspective(900px) translateZ(0)" },
                { transform: "perspective(900px) translateZ(0) scale(1.012)" },
                { transform: card.style.transform || "perspective(900px) translateZ(0)" }
            ],
            { duration: 360, easing: "cubic-bezier(.2,.9,.2,1)" }
        );
    });

    // Boot
    resize();
    render();
})();
