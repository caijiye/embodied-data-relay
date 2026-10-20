const $ = (id) => document.getElementById(id);

function fmtBytes(value) {
  let n = Number(value || 0);
  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i += 1; }
  return `${i === 0 ? Math.round(n) : n.toFixed(1)} ${units[i]}`;
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[ch]));
}

function pct(part, total) {
  if (!total) return 0;
  return Math.max(0, Math.min(100, (part / total) * 100));
}

function setBar(id, value) {
  const el = $(id);
  if (el) el.style.width = `${Math.max(0, Math.min(100, value))}%`;
}

function setText(id, value) {
  const el = $(id);
  if (el) el.textContent = value;
}

function fmtTime(iso) {
  if (!iso) return "--:--:--";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "--:--:--";
  return d.toLocaleTimeString("zh-CN", { hour12: false });
}

function renderQuality(stats) {
  const q = stats.quality || {};
  const pass = q.pass || 0;
  const review = q.review || 0;
  const quarantine = q.quarantine || 0;
  const total = pass + review + quarantine;
  setBar("q-pass", pct(pass, total));
  setBar("q-review", pct(review, total));
  setBar("q-quarantine", pct(quarantine, total));
  setText("q-pass-n", pass);
  setText("q-review-n", review);
  setText("q-quarantine-n", quarantine);
}

function renderTiers(stats) {
  const t = stats.tiers || {};
  const hot = t.hot || 0;
  const cold = t.cold || 0;
  const incoming = t.incoming || 0;
  const total = hot + cold + incoming;
  setBar("t-hot", pct(hot, total));
  setBar("t-cold", pct(cold, total));
  setBar("t-incoming", pct(incoming, total));
  setText("t-hot-n", hot);
  setText("t-cold-n", cold);
  setText("t-incoming-n", incoming);
}

function renderSessions(sessions) {
  const body = $("sessions-body");
  if (!body) return;
  if (!sessions || sessions.length === 0) {
    body.innerHTML = '<tr><td colspan="7" class="empty">等待采集会话…</td></tr>';
    return;
  }
  body.innerHTML = "";
  for (const s of sessions) {
    const tr = document.createElement("tr");
    const quality = Number(s.avg_quality || 0);
    const status = String(s.status || "unknown");
    const allowed = new Set(["delivered", "packaged", "quarantined", "error", "quality_pass", "discovered", "quality_review"]);
    const statusClass = allowed.has(status) ? status : "";
    const cells = [
      s.name || "-",
      [s.robot_id, s.site].filter(Boolean).join(" / ") || "-",
      String(s.episode_count ?? 0),
      fmtBytes(s.episode_raw_bytes),
      fmtBytes(s.episode_compact_bytes),
      quality ? quality.toFixed(1) : "—",
      null,
    ];
    for (const [idx, value] of cells.entries()) {
      const td = document.createElement("td");
      if (idx === 6) {
        const span = document.createElement("span");
        span.className = `status ${statusClass}`;
        span.textContent = status;
        td.appendChild(span);
      } else {
        td.textContent = value;
      }
      tr.appendChild(td);
    }
    body.appendChild(tr);
  }
}

function renderEvents(events) {
  const list = $("events-list");
  if (!list) return;
  if (!events || events.length === 0) {
    list.innerHTML = '<li class="empty">暂无事件</li>';
    return;
  }
  list.innerHTML = events.map((e) => {
    const level = ["info", "warn", "error"].includes(e.level) ? e.level : "info";
    return `<li><time>${fmtTime(e.ts)}</time><div><span class="level ${level}"></span>${esc(e.message)}</div></li>`;
  }).join("");
}

function renderTelemetry(t) {
  if (!t) return;
  const host = t.host || {};
  const cpu = Number(host.cpu_percent || 0);
  const ram = Number(host.memory_percent || 0);
  const disk = Number(host.disk_percent || 0);
  setBar("cpu-bar", cpu);
  setBar("ram-bar", ram);
  setBar("disk-bar", disk);
  setText("cpu-n", `${cpu.toFixed(0)}%`);
  setText("ram-n", `${ram.toFixed(0)}%`);
  setText("disk-n", `${disk.toFixed(0)}%`);

  const device = t.device || {};
  const temp = device.temperature_c ?? device.temp_c ?? device.temp;
  const fan = device.fan_rpm ?? device.fan;
  const power = device.power_w ?? device.watts;
  setText("device-temp", temp !== undefined ? `${Number(temp).toFixed(1)} °C` : "—");
  setText("device-fan", fan !== undefined ? `${Number(fan).toFixed(0)} rpm` : "—");
  setText("device-power", power !== undefined ? `${Number(power).toFixed(1)} W` : "—");
}

function renderBenchmark(b) {
  const body = $("benchmark-body");
  if (!body) return;
  if (!b || !b.results) {
    body.innerHTML = '<p class="muted small">运行 <code>python scripts/benchmark.py</code> 生成对比数据。</p>';
    return;
  }
  const r = b.results;
  const baseline = r.baseline || {};
  const pipeline = r.pipeline || {};
  body.innerHTML = `
    <div class="bar-row"><span>Baseline</span><div class="bar"><i class="warn" style="width:100%"></i></div><b>${fmtBytes(baseline.bytes)}</b></div>
    <div class="bar-row"><span>Pipeline</span><div class="bar"><i class="ok" style="width:${Math.max(0, Math.min(100, (1 - (pipeline.reduction_ratio || 0)) * 100))}%"></i></div><b>${fmtBytes(pipeline.compact_bytes)}</b></div>
    <p class="small">减量比 <strong>${((pipeline.reduction_ratio || 0) * 100).toFixed(1)}%</strong> · 端到端 <strong>${Number(pipeline.seconds || 0).toFixed(1)} s</strong> · 数据 <strong>${r.dataset?.episodes || 0}</strong> episodes</p>
  `;
}

function renderStats(stats) {
  setText("stat-sessions", stats.sessions ?? 0);
  setText("stat-episodes", stats.episodes ?? 0);
  setText("stat-raw", fmtBytes(stats.raw_bytes));
  setText("stat-compact", fmtBytes(stats.compact_bytes));
  setText("stat-reduction", `${((stats.reduction_ratio || 0) * 100).toFixed(1)}%`);
  setText("stat-delivered", fmtBytes(stats.delivered_bytes));
  setText("stat-latency", `${Number(stats.avg_delivery_hours || 0).toFixed(1)} h`);
  setText("delivery-bytes", fmtBytes(stats.delivered_bytes));
  setText("delivery-latency", `${Number(stats.avg_delivery_hours || 0).toFixed(2)} h`);
  renderQuality(stats);
  renderTiers(stats);
  renderStages(stats);
}

function renderStages(stats) {
  setText("stage-ingest", stats.sessions ?? 0);
  const q = stats.quality || {};
  setText("stage-quality", `${q.pass || 0} / ${q.review || 0} / ${q.quarantine || 0}`);
  setText("stage-compact", fmtBytes(stats.compact_bytes));
  const t = stats.tiers || {};
  setText("stage-tier", `${t.hot || 0} / ${t.cold || 0}`);
  setText("stage-deliver", fmtBytes(stats.delivered_bytes));
}

async function refresh() {
  try {
    const response = await fetch("/api/dashboard", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    renderStats(data.stats || {});
    renderSessions(data.sessions || []);
    renderEvents(data.events || []);
    renderTelemetry(data.telemetry || {});
    renderBenchmark(data.benchmark);
    const status = $("node-status");
    if (status) status.classList.remove("offline");
  } catch (error) {
    const status = $("node-status");
    if (status) status.classList.add("offline");
    console.error("refresh failed", error);
  }
}

function tickClock() {
  const clock = $("clock");
  if (clock) clock.textContent = new Date().toLocaleString("zh-CN", { hour12: false });
}

tickClock();
setInterval(tickClock, 1000);
refresh();
setInterval(refresh, 3000);
