/* ===========================================================
   Snip — URL Shortener  |  Frontend Application Logic
   =========================================================== */

(() => {
    "use strict";

    const API = "/api";

    // ---- DOM refs ----
    const $ = (s, p = document) => p.querySelector(s);
    const $$ = (s, p = document) => [...p.querySelectorAll(s)];

    const navBtns = $$(".nav-btn");
    const views = $$(".view");
    const shortenForm = $("#shorten-form");
    const urlInput = $("#url-input");
    const shortenBtn = $("#shorten-btn");
    const inputError = $("#input-error");
    const resultCard = $("#result-card");
    const resultShort = $("#result-short-url");
    const resultOriginal = $("#result-original-url");
    const copyBtn = $("#copy-btn");
    const urlList = $("#url-list");
    const urlsEmpty = $("#urls-empty");
    const totalUrlsEl = $("#total-urls-count");
    const totalClicksEl = $("#total-clicks-count");

    // Analytics
    const analyticsCodeInput = $("#analytics-code-input");
    const analyticsFetchBtn = $("#analytics-fetch-btn");
    const analyticsContent = $("#analytics-content");
    const analyticsEmpty = $("#analytics-empty");
    const aTotalClicks = $("#a-total-clicks");
    const aCreatedAt = $("#a-created-at");
    const aOriginalUrl = $("#a-original-url");
    const clickTableBody = $("#click-table-body");

    let chartInstance = null;

    // Local memory of created URLs (session)
    let createdUrls = [];

    // =============  NAVIGATION  =============

    navBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const target = btn.dataset.view;
            navBtns.forEach(b => b.classList.remove("nav-btn--active"));
            btn.classList.add("nav-btn--active");
            views.forEach(v => {
                v.classList.remove("view--active");
                if (v.id === `view-${target}`) v.classList.add("view--active");
            });
            if (target === "urls") renderUrlList();
        });
    });

    // =============  SHORTEN  =============

    shortenForm.addEventListener("submit", async e => {
        e.preventDefault();
        inputError.textContent = "";
        const url = urlInput.value.trim();
        if (!url) { inputError.textContent = "Please enter a URL."; return; }

        shortenBtn.classList.add("btn--loading");
        shortenBtn.disabled = true;

        try {
            const res = await fetch(`${API}/shorten`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url }),
            });
            const body = await res.json();

            if (!res.ok) {
                inputError.textContent = body.error || "Something went wrong.";
                return;
            }

            const data = body.data;
            createdUrls.unshift(data);
            resultShort.value = data.short_url;
            resultOriginal.textContent = data.original_url;
            resultCard.style.display = "block";
            urlInput.value = "";
            updateStats();
            toast("Short URL created!", "success");
        } catch (err) {
            console.error(err);
            inputError.textContent = "Network error — is the server running?";
        } finally {
            shortenBtn.classList.remove("btn--loading");
            shortenBtn.disabled = false;
        }
    });

    // Copy
    copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(resultShort.value).then(
            () => toast("Copied to clipboard!", "success"),
            () => toast("Copy failed", "error"),
        );
    });

    // =============  URL LIST  =============

    function renderUrlList() {
        if (createdUrls.length === 0) {
            urlsEmpty.style.display = "block";
            // clear previous items
            $$(".url-item", urlList).forEach(el => el.remove());
            return;
        }
        urlsEmpty.style.display = "none";
        // Remove old items
        $$(".url-item", urlList).forEach(el => el.remove());

        createdUrls.forEach((u, i) => {
            const div = document.createElement("div");
            div.className = "url-item glass-card";
            div.style.animationDelay = `${i * 0.04}s`;
            div.innerHTML = `
                <div class="url-item__info">
                    <a class="url-item__short" href="/${u.short_code}" target="_blank">${u.short_url}</a>
                    <p class="url-item__original">${u.original_url}</p>
                </div>
                <div class="url-item__meta">
                    <span class="url-item__clicks">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6"/><path d="M10 14L21 3"/><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/></svg>
                        ${u.click_count ?? 0} clicks
                    </span>
                    <span>${formatDate(u.created_at)}</span>
                </div>
                <div class="url-item__actions">
                    <button class="btn btn--icon btn--ghost" title="View analytics" data-analytics="${u.short_code}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>
                    </button>
                    <button class="btn btn--icon btn--danger" title="Delete" data-delete="${u.short_code}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
                    </button>
                </div>
            `;
            urlList.appendChild(div);
        });

        // Bind analytics buttons
        $$("[data-analytics]", urlList).forEach(btn => {
            btn.addEventListener("click", () => {
                const code = btn.dataset.analytics;
                analyticsCodeInput.value = code;
                // Switch to analytics view
                navBtns.forEach(b => b.classList.remove("nav-btn--active"));
                $("#nav-analytics").classList.add("nav-btn--active");
                views.forEach(v => v.classList.remove("view--active"));
                $("#view-analytics").classList.add("view--active");
                fetchAnalytics(code);
            });
        });

        // Bind delete buttons
        $$("[data-delete]", urlList).forEach(btn => {
            btn.addEventListener("click", async () => {
                const code = btn.dataset.delete;
                try {
                    const res = await fetch(`${API}/url/${code}`, { method: "DELETE" });
                    if (res.ok || res.status === 204) {
                        createdUrls = createdUrls.filter(u => u.short_code !== code);
                        renderUrlList();
                        updateStats();
                        toast("URL deleted", "info");
                    } else {
                        toast("Delete failed", "error");
                    }
                } catch { toast("Network error", "error"); }
            });
        });
    }

    // =============  ANALYTICS  =============

    analyticsFetchBtn.addEventListener("click", () => {
        const code = analyticsCodeInput.value.trim();
        if (code) fetchAnalytics(code);
    });
    analyticsCodeInput.addEventListener("keydown", e => {
        if (e.key === "Enter") analyticsFetchBtn.click();
    });

    async function fetchAnalytics(code) {
        try {
            const res = await fetch(`${API}/analytics/${code}`);
            if (!res.ok) {
                analyticsContent.style.display = "none";
                analyticsEmpty.innerHTML = "<p>Short code not found.</p>";
                analyticsEmpty.style.display = "block";
                return;
            }
            const body = await res.json();
            const d = body.data;

            analyticsEmpty.style.display = "none";
            analyticsContent.style.display = "block";

            aTotalClicks.textContent = d.total_clicks ?? 0;
            aCreatedAt.textContent = formatDate(d.url.created_at);
            aOriginalUrl.textContent = d.url.original_url;

            // Chart
            renderChart(d.daily_clicks);

            // Recent clicks table
            clickTableBody.innerHTML = "";
            (d.recent_clicks || []).forEach((c, i) => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${i + 1}</td>
                    <td>${c.ip_address}</td>
                    <td title="${esc(c.user_agent)}">${truncate(c.user_agent, 40)}</td>
                    <td>${c.referer || "—"}</td>
                    <td>${formatDate(c.clicked_at)}</td>
                `;
                clickTableBody.appendChild(tr);
            });
        } catch (err) {
            console.error(err);
            toast("Failed to load analytics", "error");
        }
    }

    function renderChart(dailyClicks) {
        const ctx = $("#clicks-chart");
        if (chartInstance) chartInstance.destroy();

        const labels = (dailyClicks || []).map(d => d.date).reverse();
        const data = (dailyClicks || []).map(d => d.count).reverse();

        chartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Clicks",
                    data,
                    backgroundColor: "rgba(129,140,248,0.45)",
                    borderColor: "rgba(129,140,248,0.9)",
                    borderWidth: 1.5,
                    borderRadius: 6,
                    hoverBackgroundColor: "rgba(192,132,252,0.6)",
                }],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "rgba(15,15,25,0.92)",
                        borderColor: "rgba(129,140,248,0.3)",
                        borderWidth: 1,
                        titleFont: { family: "'Inter', sans-serif", size: 12 },
                        bodyFont: { family: "'JetBrains Mono', monospace", size: 12 },
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: "#64748b", font: { size: 11 }, stepSize: 1 },
                        grid: { color: "rgba(255,255,255,0.04)" },
                    },
                    x: {
                        ticks: { color: "#64748b", font: { size: 11 } },
                        grid: { display: false },
                    },
                },
            },
        });
    }

    // =============  STATS  =============
    function updateStats() {
        totalUrlsEl.textContent = createdUrls.length;
        totalClicksEl.textContent = createdUrls.reduce((s, u) => s + (u.click_count ?? 0), 0);
    }

    // =============  TOASTS  =============
    function toast(msg, type = "info") {
        const container = $("#toast-container");
        const el = document.createElement("div");
        el.className = `toast toast--${type}`;
        el.textContent = msg;
        container.appendChild(el);
        setTimeout(() => { el.classList.add("toast--out"); setTimeout(() => el.remove(), 300); }, 3000);
    }

    // =============  HELPERS  =============
    function formatDate(iso) {
        if (!iso) return "—";
        const d = new Date(iso);
        return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
    }
    function truncate(s, n) { return s && s.length > n ? s.slice(0, n) + "…" : (s || "—"); }
    function esc(s) { const d = document.createElement("div"); d.textContent = s || ""; return d.innerHTML; }
})();
