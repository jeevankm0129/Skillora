/**
 * SKILLORA PARTICLE ENGINE
 * Theme: Mind Flayer (Stranger Things) - Shadow & Red Storm
 * Logic: Particles follow mouse direction (Drag Effect)
 */

const canvas = document.getElementById('particleCanvas');
const ctx = canvas.getContext('2d');

let width, height;
let particles = [];

// Mouse State
const mouse = {
    x: undefined,
    y: undefined,
    vx: 0,
    vy: 0,
    isActive: false,
    clickX: undefined,
    clickY: undefined,
    clickPower: 0,
    timeout: undefined
};

// Configuration
const CONFIG = {
    particleCount: 2000, // Higher count for "Ash/Dust" feel

    // MIND FLAYER PALETTE (Red, Ash, Shadow)
    colors: [
        'rgba(75, 0, 130, ',   // Indigo
        'rgba(138, 43, 226, ', // Blue Violet
        'rgba(72, 61, 139, ',  // Dark Slate Blue
        'rgba(147, 112, 219, ', // Medium Purple
        'rgba(25, 25, 112, '   // Midnight Blue
    ],

    minSize: 1.5,
    maxSize: 2.5, // Kept small for "Ash" look

    baseSpeed: 0.3,
    hoverRepelRadius: 100,
    clickRippleRadius: 200
};

function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
}
window.addEventListener('resize', resize);
resize();

// Track Mouse Movement & Velocity
window.addEventListener('mousemove', (e) => {
    if (mouse.x !== undefined) {
        mouse.vx = e.x - mouse.x;
        mouse.vy = e.y - mouse.y;
    }

    mouse.x = e.x;
    mouse.y = e.y;
    mouse.isActive = true;

    clearTimeout(mouse.timeout);
    mouse.timeout = setTimeout(() => {
        mouse.vx = 0;
        mouse.vy = 0;
        mouse.isActive = false;
    }, 100);
});

window.addEventListener('mousedown', (e) => {
    mouse.clickX = e.x;
    mouse.clickY = e.y;
    mouse.clickPower = 20;
});

class Particle {
    constructor() {
        this.init();
    }

    init() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.radius = Math.random() * (CONFIG.maxSize - CONFIG.minSize) + CONFIG.minSize;

        this.vx = (Math.random() - 0.5) * CONFIG.baseSpeed;
        this.vy = (Math.random() - 0.5) * CONFIG.baseSpeed;

        this.color = CONFIG.colors[Math.floor(Math.random() * CONFIG.colors.length)];
        // Random opacity: Ash is usually semi-transparent
        this.alpha = Math.random() * 0.5 + 0.3;

        this.dx = 0;
        this.dy = 0;
        this.friction = 0.94;
    }

    update() {
        // 1. Base Drift
        this.x += this.vx;
        this.y += this.vy;

        // 2. Mouse Flow (DRAG)
        if (mouse.isActive && (Math.abs(mouse.vx) > 0.1 || Math.abs(mouse.vy) > 0.1)) {
            const dx = mouse.x - this.x;
            const dy = mouse.y - this.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < CONFIG.hoverRepelRadius) {
                const force = (CONFIG.hoverRepelRadius - distance) / CONFIG.hoverRepelRadius;

                // Drag Strength
                this.dx += mouse.vx * force * 0.08;
                this.dy += mouse.vy * force * 0.08;
            }
        }

        // 3. Click (REPULSION)
        if (mouse.clickPower > 0.1) {
            const cx = mouse.clickX - this.x;
            const cy = mouse.clickY - this.y;
            const cDist = Math.sqrt(cx * cx + cy * cy);

            if (cDist < CONFIG.clickRippleRadius) {
                const power = (1 - cDist / CONFIG.clickRippleRadius) * mouse.clickPower;
                const angle = Math.atan2(cy, cx);

                this.dx -= Math.cos(angle) * power;
                this.dy -= Math.sin(angle) * power;
            }
        }

        this.x += this.dx;
        this.y += this.dy;

        this.dx *= this.friction;
        this.dy *= this.friction;

        // Screen Wrap
        if (this.x < 0) this.x = width;
        if (this.x > width) this.x = 0;
        if (this.y < 0) this.y = height;
        if (this.y > height) this.y = 0;
    }

    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.globalAlpha = this.alpha;
        ctx.fillStyle = this.color;
        ctx.fill();
        ctx.closePath();
        ctx.globalAlpha = 1;
    }
}

function initParticles() {
    particles = [];
    for (let i = 0; i < CONFIG.particleCount; i++) {
        particles.push(new Particle());
    }
}

function animate() {
    ctx.clearRect(0, 0, width, height);

    // 'lighter' makes Red/Grey particles glow when they overlap (Storm effect)
    ctx.globalCompositeOperation = 'lighter';

    if (mouse.clickPower > 0) {
        mouse.clickPower *= 0.92;
    }

    particles.forEach(particle => {
        particle.update();
        particle.draw();
    });

    ctx.globalCompositeOperation = 'source-over';
    requestAnimationFrame(animate);
}

initParticles();
animate();
