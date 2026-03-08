document.addEventListener("DOMContentLoaded", () => {
    /* =========================================
        1. THEME SWITCHER
        ========================================= */
    const themeToggle = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);

    if (themeToggle) {
        themeToggle.innerHTML = currentTheme === 'dark' ? '☀️' : '🌙';
        themeToggle.addEventListener('click', () => {
            let theme = document.documentElement.getAttribute('data-theme');
            let newTheme = theme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            themeToggle.innerHTML = newTheme === 'dark' ? '☀️' : '🌙';
            updateParticleColor(newTheme);
        });
    }

    /* =========================================
        2. BUTTERY SMOOTH 3D HOVERBOARD (Lerping)
        ========================================= */
    const glassContainer = document.querySelector('.glass-container');
    const maxTilt = 1.2;

    let targetRotateX = 0;
    let targetRotateY = 0;
    let currentRotateX = 0;
    let currentRotateY = 0;

    if (glassContainer && window.matchMedia("(hover: hover)").matches) {
        document.addEventListener('mousemove', (e) => {
            const x = (e.clientX / window.innerWidth) * 2 - 1;
            const y = (e.clientY / window.innerHeight) * 2 - 1;
            targetRotateX = y * maxTilt;
            targetRotateY = -x * maxTilt;
        });

        document.addEventListener('mouseleave', () => {
            targetRotateX = 0;
            targetRotateY = 0;
        });

        function animateGlass() {
            currentRotateX += (targetRotateX - currentRotateX) * 0.08;
            currentRotateY += (targetRotateY - currentRotateY) * 0.08;
            glassContainer.style.transform = `rotateX(${currentRotateX}deg) rotateY(${currentRotateY}deg) translateZ(0)`;
            requestAnimationFrame(animateGlass);
        }
        animateGlass();
    }

    /* =========================================
        3. OPTIMIZED FLUID SWARM & RIPPLE ENGINE
        ========================================= */
    const canvas = document.getElementById('morphic-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: false });

    let particles = [];
    let ripples = [];
    let mouse = { x: null, y: null };
    const PI2 = Math.PI * 2;

    function setCanvasSize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    setCanvasSize();
    window.addEventListener('resize', () => { setCanvasSize(); initParticles(); });

    window.addEventListener('mousemove', (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });
    window.addEventListener('mouseout', () => {
        mouse.x = null;
        mouse.y = null;
    });

    window.addEventListener('mousedown', (e) => {
        ripples.push({
            x: e.clientX, y: e.clientY,
            radius: 0, maxRadius: 100, speed: 10, force: 25
        });
    });

    let particleColor = currentTheme === 'light' ? 'rgba(91, 60, 228, 0.9)' : 'rgba(167, 139, 250, 0.9)';

    function updateParticleColor(theme) {
        particleColor = theme === 'light' ? 'rgba(91, 60, 228, 0.9)' : 'rgba(167, 139, 250, 0.9)';
        initParticles();
    }

    class Particle {
        constructor(x, y, size) {
            this.x = x; this.y = y;
            this.vx = (Math.random() - 0.5) * 2;
            this.vy = (Math.random() - 0.5) * 2;
            this.size = size;
        }

        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, PI2);
            ctx.fillStyle = particleColor;
            ctx.fill();
        }

        update() {
            if (mouse.x !== null && mouse.y !== null) {
                let dx = mouse.x - this.x;
                let dy = mouse.y - this.y;
                let distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 400) {
                    let pullForce = (400 - distance) / 400;
                    this.vx += (dx / distance) * pullForce * 0.15;
                    this.vy += (dy / distance) * pullForce * 0.15;
                }
            }

            for (let i = 0; i < ripples.length; i++) {
                let ripple = ripples[i];
                let dx = this.x - ripple.x;
                let dy = this.y - ripple.y;
                let distance = Math.sqrt(dx * dx + dy * dy);

                if (distance > ripple.radius - 30 && distance < ripple.radius + 30) {
                    let pushStrength = ripple.force * (1 - ripple.radius / ripple.maxRadius);
                    this.vx += (dx / distance) * pushStrength;
                    this.vy += (dy / distance) * pushStrength;
                }
            }

            this.vx += (Math.random() - 0.5) * 0.2;
            this.vy += (Math.random() - 0.5) * 0.2;
            this.vx *= 0.94; this.vy *= 0.94;
            this.x += this.vx; this.y += this.vy;

            if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
            if (this.y < 0 || this.y > canvas.height) this.vy *= -1;

            this.draw();
        }
    }

    function initParticles() {
        particles = [];
        let numberOfParticles = 1000;
        for (let i = 0; i < numberOfParticles; i++) {
            let size = (Math.random() * 2) + 1.5;
            let x = Math.random() * canvas.width;
            let y = Math.random() * canvas.height;
            particles.push(new Particle(x, y, size));
        }
    }

    function clearCanvas() {
        ctx.fillStyle = document.documentElement.getAttribute('data-theme') === 'light' ? '#e6dcfc' : '#0b0320';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    function animate() {
        requestAnimationFrame(animate);
        clearCanvas();

        for (let i = 0; i < ripples.length; i++) {
            ripples[i].radius += ripples[i].speed;
        }
        ripples = ripples.filter(r => r.radius < r.maxRadius);

        for (let i = 0; i < particles.length; i++) {
            particles[i].update();
        }
    }

    initParticles();
    animate();

    /* =========================================
        4. FRONTEND UI CHOREOGRAPHY (Job Card)
        ========================================= */
    const jobCard = document.getElementById('job-card');
    const heroText = document.getElementById('hero-text');
    const btnResume = document.getElementById('btn-resume');

    window.expandJobCard = function () {
        if (!jobCard.classList.contains('expanded')) {
            jobCard.classList.add('expanded');
            heroText.classList.add('shift-up');
            btnResume.classList.add('shift-down');
        }
    };

    window.closeJobCard = function (event) {
        event.stopPropagation();
        jobCard.classList.remove('expanded');
        heroText.classList.remove('shift-up');
        btnResume.classList.remove('shift-down');
    };

    /* =========================================
        5. SEAMLESS REDIRECTION: BUILD RESUME
        ========================================= */
    window.redirectToTelegramResume = function () {
        // Replace 'YourBotUsername' with your actual Telegram bot username
        const botUsername = "mySkilloraBot";
        const startParam = "build_resume";

        // Telegram Deep Link URL
        const telegramUrl = `https://t.me/${botUsername}?start=${startParam}`;

        // Open Telegram app/web in a new tab
        window.open(telegramUrl, '_blank');
    };

    /* =========================================
        6. BACKEND API INTEGRATION & LIVE AI UI
        ========================================= */
    window.handleFileUpload = async function (event) {
        const file = event.target.files[0];
        if (!file) return;

        const dropZoneText = document.getElementById('drop-zone-text');
        const scanLine = document.getElementById('scan-line');
        const uploadUI = document.querySelector('.job-upload-ui');
        const jobCardContainer = document.getElementById('job-card');

        // UI Update: Show Loading Scanner
        dropZoneText.innerHTML = `Extracting Intelligence from <strong>${file.name}</strong>...<br><span style="font-size: 0.8rem; color: var(--accent-1);">Pinging global job markets...</span>`;
        scanLine.style.display = 'block';

        let scanPos = 0;
        let scanDirection = 1;
        const scanInterval = setInterval(() => {
            scanPos += 5 * scanDirection;
            if (scanPos > 95 || scanPos < 0) scanDirection *= -1;
            scanLine.style.top = `${scanPos}%`;
        }, 50);

        const formData = new FormData();
        formData.append('resume', file);

        try {
            const response = await fetch('/api/recommend-jobs', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            clearInterval(scanInterval);

            if (data.status === "success" || data.status === "needs_email") {
                uploadUI.style.display = 'none';

                const resultsDiv = document.createElement('div');
                resultsDiv.id = 'job-results-ui';
                resultsDiv.style.width = '100%';
                resultsDiv.style.height = '100%';
                resultsDiv.style.padding = '20px';
                resultsDiv.style.display = 'flex';
                resultsDiv.style.flexDirection = 'column';
                resultsDiv.style.overflowY = 'auto';

                let htmlContent = '';

                // --- STATE A: JOBS FOUND ---
                if (data.status === "success") {
                    htmlContent += `<h3 class="gradient-text" style="font-size: 1.5rem; margin-bottom: 15px; text-align: center;">${data.jobs.length} Top Matches</h3>`;
                    htmlContent += `<div style="display: flex; flex-direction: column; gap: 12px; padding-right: 5px;">`;

                    data.jobs.forEach(job => {
                        htmlContent += `
                            <div style="background: rgba(255,255,255,0.05); border: 1px solid var(--glass-border); padding: 18px; border-radius: 12px; display: flex; flex-direction: column; gap: 10px; transition: all 0.3s;" onmouseover="this.style.borderColor='var(--accent-1)'" onmouseout="this.style.borderColor='var(--glass-border)'">

                                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                    <div style="text-align: left;">
                                        <h4 style="margin-bottom: 3px; font-size: 1.1rem; color: var(--text-main);">${job.title}</h4>
                                        <p style="color: var(--text-muted); font-size: 0.85rem; font-weight: 600;">${job.company} • ${job.location}</p>
                                    </div>
                                    <div style="background: rgba(124, 92, 255, 0.2); color: var(--accent-1); padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.8rem; border: 1px solid rgba(124, 92, 255, 0.4); flex-shrink: 0;">
                                        ${job.match}
                                    </div>
                                </div>

                                <p style="color: #d1d5db; font-size: 0.85rem; text-align: left; border-left: 2px solid var(--accent-1); padding-left: 10px; margin-top: 5px; font-style: italic;">
                                    "${job.reasoning}"
                                </p>

                                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 5px;">
                                    <span style="color: var(--text-muted); font-size: 0.85rem;">${job.salary}</span>
                                    <a href="${job.link}" target="_blank" class="btn btn-primary" style="padding: 6px 16px; font-size: 0.85rem; min-width: auto; text-decoration: none;">Apply Now</a>
                                </div>
                            </div>
                        `;
                    });
                    htmlContent += `</div>`;
                }
                // --- STATE B: NO JOBS FOUND (Needs Email) ---
                else if (data.status === "needs_email") {
                    htmlContent += `
                  <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center;">
                      <h3 class="gradient-text" style="font-size: 1.5rem; margin-bottom: 10px;">Market Analysis Complete</h3>
                      <p style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 25px; max-width: 80%;">${data.message}</p>

                      <div style="display: flex; gap: 10px; width: 100%; max-width: 400px;">
                          <input type="email" id="alert-email" placeholder="Enter your email address" style="flex: 1; padding: 12px 15px; border-radius: 8px; border: 1px solid var(--glass-border); background: rgba(0,0,0,0.2); color: white; outline: none; font-size: 0.95rem;">
                          <button class="btn btn-primary" onclick="submitEmailAlert()" style="padding: 10px 20px;">Track</button>
                      </div>
                      <p id="alert-status" style="margin-top: 15px; font-size: 0.85rem; min-height: 1.2rem;"></p>
                  </div>
              `;
                }

                htmlContent += `<button class="btn btn-outline" style="margin-top: 20px; align-self: center; flex-shrink: 0;" onclick="resetJobCard(event)">Close Dashboard</button>`;

                resultsDiv.innerHTML = htmlContent;
                jobCardContainer.appendChild(resultsDiv);

            } else {
                dropZoneText.innerHTML = `<span style="color: #f87171;">Error: ${data.message}</span>`;
                scanLine.style.display = 'none';
            }

        } catch (error) {
            clearInterval(scanInterval);
            scanLine.style.display = 'none';
            dropZoneText.innerHTML = `<span style="color: #f87171;">Server offline. Transmission failed.</span>`;
            console.error(error);
        }
    };

    /* =========================================
        7. UTILITY FUNCTIONS
        ========================================= */
    window.resetJobCard = function (event) {
        event.stopPropagation();

        const resultsDiv = document.getElementById('job-results-ui');
        if (resultsDiv) resultsDiv.remove();

        const uploadUI = document.querySelector('.job-upload-ui');
        if (uploadUI) uploadUI.style.display = 'flex';

        const dropZoneText = document.getElementById('drop-zone-text');
        if (dropZoneText) dropZoneText.innerHTML = 'Click to Upload PDF Document';

        const resumeUpload = document.getElementById('resume-upload');
        if (resumeUpload) resumeUpload.value = '';

        if (typeof closeJobCard === "function") {
            closeJobCard(event);
        }
    };

    window.submitEmailAlert = async function () {
        const emailInput = document.getElementById('alert-email');
        const statusText = document.getElementById('alert-status');
        const email = emailInput.value;

        if (!email || !email.includes('@')) {
            statusText.style.color = '#f87171';
            statusText.innerText = "Please enter a valid email.";
            return;
        }

        const formData = new FormData();
        formData.append('email', email);

        try {
            const response = await fetch('/api/save-email-alert', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            statusText.style.color = '#4ade80';
            statusText.innerText = result.message;
            emailInput.value = ''; // Clear input
        } catch (e) {
            statusText.style.color = '#f87171';
            statusText.innerText = "Error connecting to server.";
        }
    };
});
