/* ═══════════════════════════════════════════════════════════
   ContentShield AI — Dashboard Logic
   ═══════════════════════════════════════════════════════════

   API Endpoints (unchanged):
     Layer 1-2 (8001):  POST /process, GET /health
     Layer 3-7 (8000):  GET  /api/v1/dashboard/summary
                        GET  /api/v1/dashboard/detections
                        GET  /api/v1/layer56/scan/:id
                        POST /api/v1/layer56/scan
                        GET  /api/v1/layers/3-4/content/:id
*/

// ⚠️ DEPLOYMENT: Replace these with your actual Render backend URLs
const API_L12 = "http://127.0.0.1:8001";
const API_L37 = "http://127.0.0.1:8000";

const $ = sel => document.querySelector(sel);
const $$ = sel => Array.from(document.querySelectorAll(sel));

// ─── ELEMENTS ───
const toastContainer = $("#toast-container");
const detectionsGrid = $("#detections-grid");
const emptyState = $("#empty-state");
const activityList = $("#activity-list");

let selectedFile = null;
let currentFilter = "all";
let allDetections = [];

// ═══════════════════════════════════════════════════════════
//  UTILITIES
// ═══════════════════════════════════════════════════════════

function showToast(msg) {
  if (!toastContainer) return;
  const t = document.createElement("div");
  t.className = "toast";
  t.textContent = msg;
  toastContainer.appendChild(t);
  setTimeout(() => { t.style.opacity = "0"; t.style.transform = "translateY(8px)"; }, 2500);
  setTimeout(() => t.remove(), 2800);
}

function formatSize(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

function truncateUrl(url, max = 40) {
  if (!url) return "";
  try {
    const u = new URL(url);
    const display = u.hostname + u.pathname;
    return display.length > max ? display.substring(0, max) + "…" : display;
  } catch { return url.length > max ? url.substring(0, max) + "…" : url; }
}

// ═══════════════════════════════════════════════════════════
//  SERVICE HEALTH CHECKS
// ═══════════════════════════════════════════════════════════

async function checkHealth() {
  // Layer 1-2
  try {
    const r = await fetch(`${API_L12}/health`, { cache: "no-store" });
    if (r.ok) {
      $("#status-dot-12")?.classList.add("online");
      $("#status-dot-12")?.classList.remove("offline");
    } else throw 0;
  } catch {
    $("#status-dot-12")?.classList.add("offline");
    $("#status-dot-12")?.classList.remove("online");
  }

  // Layer 3-7
  try {
    const r = await fetch(`${API_L37}/api/v1/health`, { cache: "no-store" });
    if (r.ok) {
      $("#status-dot-37")?.classList.add("online");
      $("#status-dot-37")?.classList.remove("offline");
    } else throw 0;
  } catch {
    $("#status-dot-37")?.classList.add("offline");
    $("#status-dot-37")?.classList.remove("online");
  }
}

checkHealth();
setInterval(checkHealth, 15000);

// ═══════════════════════════════════════════════════════════
//  TAB NAVIGATION
// ═══════════════════════════════════════════════════════════

$$(".nav-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    $$(".nav-tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    $$(".tab-content").forEach(p => p.classList.remove("active"));
    const panel = $(`#panel-${tab.dataset.tab}`);
    if (panel) panel.classList.add("active");
  });
});

// ═══════════════════════════════════════════════════════════
//  DASHBOARD — Load Stats & Detections
// ═══════════════════════════════════════════════════════════

async function loadDashboard() {
  // Summary stats
  try {
    const r = await fetch(`${API_L37}/api/v1/dashboard/summary`);
    if (r.ok) {
      const d = (await r.json()).data || {};
      animateCounter("stat-total", d.total_detections || 0);
      animateCounter("stat-piracy", d.piracy_count || 0);
      animateCounter("stat-suspicious", d.suspicious_count || 0);
      animateCounter("stat-takedowns", d.takedowns_executed || 0);
    }
  } catch (e) { console.warn("Dashboard stats failed:", e); }

  // Detection events
  try {
    const r = await fetch(`${API_L37}/api/v1/dashboard/detections`);
    if (r.ok) {
      const data = await r.json();
      allDetections = data.data || data.results || data || [];
      if (Array.isArray(allDetections)) renderDetections(allDetections);
    }
  } catch (e) { console.warn("Detections load failed:", e); }
}

function animateCounter(id, target) {
  const el = $(`#${id}`);
  if (!el) return;
  const start = parseInt(el.textContent) || 0;
  if (start === target) return;
  const duration = 600;
  const startTime = performance.now();
  function tick(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (target - start) * eased);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// ─── Render Detection Cards ───

function renderDetections(detections) {
  if (!detectionsGrid) return;

  const filtered = currentFilter === "all"
    ? detections
    : detections.filter(d => d.verdict === currentFilter);

  if (filtered.length === 0) {
    detectionsGrid.innerHTML = "";
    if (emptyState) emptyState.style.display = "block";
    return;
  }

  if (emptyState) emptyState.style.display = "none";

  detectionsGrid.innerHTML = filtered.map((d, i) => {
    const verdict = d.verdict || "SAFE";
    const similarity = d.similarity || 0;
    const risk = d.risk || "LOW";
    const action = d.action || "IGNORE";
    const url = d.url || "";

    const verdictClass = verdict === "PIRACY" ? "piracy" : verdict === "SUSPICIOUS" ? "suspicious" : "safe";
    const simPercent = Math.round(similarity * 100);
    const simClass = similarity > 0.8 ? "sim-high" : similarity > 0.5 ? "sim-medium" : "sim-low";
    const riskClass = risk === "HIGH" ? "high" : risk === "MEDIUM" ? "medium" : "low";

    return `
      <div class="detection-card verdict-${verdict}" style="animation-delay: ${i * 0.05}s">
        <div class="det-header">
          <a href="${url}" target="_blank" rel="noopener" class="det-url" title="${url}">${truncateUrl(url)}</a>
          <span class="badge badge--${verdictClass}">${verdict}</span>
        </div>

        <div class="sim-bar-wrap">
          <div class="sim-label">
            <span>Similarity</span>
            <span>${simPercent}%</span>
          </div>
          <div class="sim-bar">
            <div class="sim-fill ${simClass}" style="width: ${simPercent}%"></div>
          </div>
        </div>

        <div class="det-meta">
          <span class="badge badge--${riskClass}">Risk: ${risk}</span>
          <span class="det-action">${action}</span>
          ${d.watermark_id ? `<span class="badge badge--blue" title="Watermark">${d.watermark_id.substring(0, 12)}…</span>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

// ─── Filter Chips ───

$$(".filter-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    $$(".filter-chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    currentFilter = chip.dataset.filter;
    renderDetections(allDetections);
  });
});

// ─── Refresh Button ───
$("#btn-refresh-dash")?.addEventListener("click", () => {
  loadDashboard();
  showToast("Dashboard refreshed");
});

// ═══════════════════════════════════════════════════════════
//  UPLOAD TAB — File Selection & Protection
// ═══════════════════════════════════════════════════════════

const dropzone = $("#dropzone");
const fileInput = $("#file-input");
const filePreview = $("#file-preview");

// Drag & Drop
if (dropzone) {
  dropzone.addEventListener("dragover", e => { e.preventDefault(); dropzone.classList.add("drag-over"); });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag-over"));
  dropzone.addEventListener("drop", e => {
    e.preventDefault(); dropzone.classList.remove("drag-over");
    const f = e.dataTransfer.files?.[0];
    if (f) selectFile(f);
  });
}

if (fileInput) fileInput.addEventListener("change", () => { if (fileInput.files[0]) selectFile(fileInput.files[0]); });
$("#remove-file")?.addEventListener("click", clearFile);
document.addEventListener("click", e => { if (e.target?.matches(".browse-link")) fileInput?.click(); });

function selectFile(f) {
  selectedFile = f;
  if (filePreview) filePreview.hidden = false;
  $("#file-name").textContent = f.name;
  $("#file-size").textContent = formatSize(f.size);
}

function clearFile() {
  selectedFile = null;
  if (filePreview) filePreview.hidden = true;
  if (fileInput) fileInput.value = "";
}

// ─── Pipeline Steps ───

function resetPipelineSteps() {
  ["step-drm", "step-wm", "step-fp"].forEach(id => {
    const el = $(`#${id}`);
    if (el) { el.classList.remove("done", "active"); }
  });
  const steps = $("#pipeline-steps");
  if (steps) steps.hidden = true;
}

function setStepActive(id) { $(`#${id}`)?.classList.add("active"); }
function setStepDone(id) { const el = $(`#${id}`); if (el) { el.classList.remove("active"); el.classList.add("done"); } }

// ─── Submit Protection ───

const protectForm = $("#protect-form");
if (protectForm) {
  protectForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!selectedFile) { showToast("Please choose a media file"); return; }
    const ownerId = ($("#owner_id")?.value || "").trim();
    if (!ownerId) { showToast("Owner ID is required"); $("#owner_id")?.focus(); return; }

    const submitBtn = $("#submit-btn");
    const submitLabel = $("#submit-label");
    submitBtn.disabled = true;
    submitLabel.innerHTML = '<span class="spinner"></span> Protecting…';
    resetPipelineSteps();
    $("#pipeline-steps").hidden = false;

    const contentId = ($("#content_id")?.value || "").trim();
    const userId = ($("#user_id")?.value || "").trim();

    const fd = new FormData();
    fd.append("file", selectedFile);
    fd.append("content_id", contentId);
    fd.append("owner_id", ownerId);
    fd.append("user_id", userId);

    // Animated pipeline steps
    setTimeout(() => setStepActive("step-drm"), 300);
    setTimeout(() => { setStepDone("step-drm"); setStepActive("step-wm"); }, 3000);
    setTimeout(() => { setStepDone("step-wm"); setStepActive("step-fp"); }, 8000);

    try {
      const res = await fetch(`${API_L12}/process`, { method: "POST", body: fd });
      const data = await (res.ok ? res.json() : res.text().then(t => { throw new Error(t || res.status); }));

      // All steps done
      setStepDone("step-drm"); setStepDone("step-wm"); setStepDone("step-fp");

      $("#result-json").textContent = JSON.stringify(data, null, 2);
      pushActivity(selectedFile.name, "Protected", true);
      showToast("Protection complete!");

      // Refresh dashboard in background
      setTimeout(loadDashboard, 1000);

    } catch (err) {
      const msg = err?.message || "Error";
      $("#result-json").textContent = JSON.stringify({ error: msg }, null, 2);
      pushActivity(selectedFile?.name || "upload", "Failed", false);
      showToast("Processing failed");
    } finally {
      submitBtn.disabled = false;
      submitLabel.textContent = "Protect Content";
    }
  });
}

// ─── Copy JSON ───
$("#copy-json")?.addEventListener("click", () => {
  const txt = $("#result-json")?.textContent;
  if (txt) navigator.clipboard.writeText(txt).then(() => showToast("Copied to clipboard"));
});

// ─── Activity List ───

function pushActivity(name, status, success) {
  if (!activityList) return;
  const el = document.createElement("div");
  el.className = "activity-item";
  el.innerHTML = `
    <div>
      <div class="act-name">${name}</div>
      <div class="act-time">${new Date().toLocaleString()}</div>
    </div>
    <div class="act-status ${success ? "ok" : "fail"}">${status}</div>
  `;
  activityList.prepend(el);
  // Keep max 10 items
  while (activityList.children.length > 10) activityList.lastChild.remove();
}

// ═══════════════════════════════════════════════════════════
//  SCAN TAB — Trigger Detection Scan
// ═══════════════════════════════════════════════════════════

$("#btn-run-scan")?.addEventListener("click", async () => {
  const contentId = ($("#scan-content-id")?.value || "").trim();
  if (!contentId) { showToast("Content ID is required"); $("#scan-content-id")?.focus(); return; }

  const keywords = ($("#scan-keywords")?.value || "").split(",").map(k => k.trim()).filter(Boolean);

  const btn = $("#btn-run-scan");
  const label = $("#scan-label");
  btn.disabled = true;
  label.innerHTML = '<span class="spinner"></span> Scanning internet…';

  try {
    // First fetch content info from Layer 3-4
    let payload = {
      content_id: contentId,
      metadata: { keywords: keywords.length ? keywords : ["sports", "highlights"] }
    };

    try {
      const info = await fetch(`${API_L37}/api/v1/layers/3-4/content/${contentId}`);
      if (info.ok) {
        const d = await info.json();
        payload.fingerprint_hash = d.fingerprint_hash;
        payload.watermark_id = d.watermark_id;
        payload.ownership_verified = d.ownership_verified;
        payload.blockchain_tx_hash = d.blockchain_tx_hash;
        payload.owner_id = d.owner_id || "unknown";
      }
    } catch { /* proceed without enrichment */ }

    const r = await fetch(`${API_L37}/api/v1/layer56/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await r.json();
    const results = data.results || data.data || [];

    // Show results section
    const section = $("#scan-results-section");
    if (section) section.hidden = false;

    const countEl = $("#scan-count");
    if (countEl) countEl.textContent = `${results.length} result${results.length !== 1 ? "s" : ""}`;

    const grid = $("#scan-results-grid");
    if (grid && results.length > 0) {
      // Reuse existing renderDetections format
      const tmpDetections = results;
      const tmpGrid = grid;
      tmpGrid.innerHTML = tmpDetections.map((d, i) => {
        const verdict = d.verdict || "SAFE";
        const similarity = d.similarity || 0;
        const risk = d.risk || "LOW";
        const action = d.action || "IGNORE";
        const url = d.url || "";
        const verdictClass = verdict === "PIRACY" ? "piracy" : verdict === "SUSPICIOUS" ? "suspicious" : "safe";
        const simPercent = Math.round(similarity * 100);
        const simClass = similarity > 0.8 ? "sim-high" : similarity > 0.5 ? "sim-medium" : "sim-low";
        const riskClass = risk === "HIGH" ? "high" : risk === "MEDIUM" ? "medium" : "low";

        return `
          <div class="detection-card verdict-${verdict}" style="animation-delay: ${i * 0.08}s">
            <div class="det-header">
              <a href="${url}" target="_blank" rel="noopener" class="det-url" title="${url}">${truncateUrl(url)}</a>
              <span class="badge badge--${verdictClass}">${verdict}</span>
            </div>
            <div class="sim-bar-wrap">
              <div class="sim-label"><span>Similarity</span><span>${simPercent}%</span></div>
              <div class="sim-bar"><div class="sim-fill ${simClass}" style="width: ${simPercent}%"></div></div>
            </div>
            <div class="det-meta">
              <span class="badge badge--${riskClass}">Risk: ${risk}</span>
              <span class="det-action">${action}</span>
            </div>
          </div>
        `;
      }).join("");
    } else if (grid) {
      grid.innerHTML = `<div class="empty-state"><h3>No piracy detected</h3><p>All scanned content appears to be safe.</p></div>`;
    }

    showToast(`Scan complete — ${results.length} URLs analyzed`);
    loadDashboard(); // refresh stats

  } catch (err) {
    showToast("Scan failed: " + (err.message || "unknown error"));
  } finally {
    btn.disabled = false;
    label.textContent = "Run Detection Scan";
  }
});

// ═══════════════════════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════════════════════

(function init() {
  pushActivity("System", "Ready", true);
  loadDashboard();
})();
