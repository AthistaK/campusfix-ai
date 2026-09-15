let allIncidents = [];

async function loadAll() {
  try {
    const [incRes, statsRes] = await Promise.all([
      fetch("/api/incidents"),
      fetch("/api/stats")
    ]);

    if (!incRes.ok) {
      throw new Error("Failed to load incidents");
    }

    if (!statsRes.ok) {
      throw new Error("Failed to load statistics");
    }

    const incidentsData = await incRes.json();
    const statsData = await statsRes.json();

    console.log("CampusFix incidents:", incidentsData);
    console.log("CampusFix stats:", statsData);

    allIncidents = Array.isArray(incidentsData) ? incidentsData : [];

    renderStats(statsData);
    renderIncidents(allIncidents);

  } catch (error) {
    console.error("CampusFix loading error:", error);

    document.getElementById("incidentList").innerHTML = `
      <div class="empty">
        <strong>Unable to load campus incidents.</strong>
        <p>Please refresh the page.</p>
      </div>
    `;
  }
}

function renderStats(s) {
  document.getElementById("stats").innerHTML = `
    <div class="stat"><div class="stat-label">Active Incidents</div><div class="stat-value">${s.active_incidents}</div></div>
    <div class="stat"><div class="stat-label">Critical</div><div class="stat-value">${s.critical}</div></div>
    <div class="stat"><div class="stat-label">Total Reports</div><div class="stat-value">${s.total_reports}</div></div>
    <div class="stat"><div class="stat-label">Resolved</div><div class="stat-value">${s.resolved}</div></div>
  `;
}

function severityClass(sev) {
  return (sev || "low").toLowerCase();
}

function renderIncidents(items) {
  const el = document.getElementById("incidentList");

  if (!Array.isArray(items) || items.length === 0) {
    el.innerHTML = `
      <div class="empty">
        No incidents found.
      </div>
    `;
    return;
  }

  el.innerHTML = items.map(i => `
    <article class="incident" onclick="showIncident(${i.id})">

      <div class="incident-top">

        <div>
          <div class="incident-title">
            ${escapeHtml(i.title)}
          </div>

          <div class="incident-meta">
            ${escapeHtml(i.location)}
            ·
            ${escapeHtml(i.category)}
            ·
            ${escapeHtml(i.status)}
          </div>
        </div>

        <div class="priority ${severityClass(i.severity)}">
          ${i.priority}/100
        </div>

      </div>

      <div class="incident-bottom">

        <span class="pill">
          ${i.report_count} reports
        </span>

        <span class="pill">
          ${escapeHtml(i.severity)} severity
        </span>

        <span class="pill">
          ${escapeHtml(i.status)}
        </span>

      </div>

    </article>
  `).join("");
}

function filterLocation(location) {
  const filtered = allIncidents.filter(i => i.location === location);
  renderIncidents(filtered);
  document.querySelector(".section-head h2").textContent = `${location} Incidents`;
}

async function showIncident(id) {
  const res = await fetch(`/api/incidents/${id}`);
  const data = await res.json();
  const i = data.incident;
  const reportText = data.reports.slice(0, 8).map(r =>
    `<div class="pill">${escapeHtml(r.student_name)}: ${escapeHtml(r.description)}</div>`
  ).join("<br><br>");

  document.getElementById("modal").classList.remove("hidden");
  document.querySelector(".modal-card").innerHTML = `
    <button class="close" onclick="closeModal()">×</button>
    <p class="eyebrow">INCIDENT #${i.id}</p>
    <h2>${escapeHtml(i.title)}</h2>
    <p class="muted">${escapeHtml(i.location)} · ${escapeHtml(i.category)}</p>
    <div class="analysis-grid">
  <div class="analysis-item">
    <small>Priority</small>
    <strong>${i.priority}/100</strong>
  </div>

  <div class="analysis-item">
    <small>Severity</small>
    <strong>${escapeHtml(i.severity)}</strong>
  </div>

  <div class="analysis-item">
    <small>Reports</small>
    <strong>${i.report_count}</strong>
  </div>

  <div class="analysis-item">
    <small>Status</small>
    <strong>${escapeHtml(i.status)}</strong>
  </div>
</div>

<div class="assignment-box">
  <p class="eyebrow">ASSIGNED TO</p>

  <div class="assignment-grid">

    <div>
      <small>Department</small>
      <strong>${escapeHtml(i.assigned_department || "Unassigned")}</strong>
    </div>

    <div>
      <small>Responsible Person</small>
      <strong>${escapeHtml(i.assigned_person || "Not assigned")}</strong>
    </div>

    <div>
      <small>Email</small>
      <strong>${escapeHtml(i.assigned_email || "Not available")}</strong>
    </div>

    <div>
      <small>Phone</small>
      <strong>${escapeHtml(i.assigned_phone || "Not available")}</strong>
    </div>

  </div>
</div>
    <p><strong>AI explanation</strong></p>
    <p class="muted">Priority increases with severity, report volume, location importance and safety signals.</p>
    <p><strong>Related reports</strong></p>
    <div style="max-height:190px;overflow:auto">${reportText}</div>
    <label>Update status</label>
    <select id="statusSelect">
      ${["Reported","Investigating","Assigned","In Progress","Resolved"].map(s => `<option ${s===i.status?"selected":""}>${s}</option>`).join("")}
    </select>
    <button class="primary full" onclick="updateStatus(${i.id})">Save Status</button>
  `;
}

async function updateStatus(id) {
  const status = document.getElementById("statusSelect").value;
  const res = await fetch(`/api/incidents/${id}`, {
    method: "PATCH",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({status})
  });
  if (res.ok) {
    closeModal();
    toast("Incident status updated.");
    loadAll();
  }
}

function openModal() {
  document.body.classList.add("modal-open");
  document.getElementById("modal").classList.remove("hidden");
  location.reload ? null : null;
  document.querySelector(".modal-card").innerHTML = `
    <button class="close" onclick="closeModal()">×</button>
    <p class="eyebrow">NEW REPORT</p>
    <h2>Report a campus problem</h2>
    <p class="muted">Describe it naturally. CampusFix will analyze it.</p>
    <label>Your name</label>
    <input id="studentName" placeholder="e.g. Drishya">
    <label>Where?</label>
    <select id="location">
      <option>CSE Block</option><option>Library</option><option>Hostel A</option><option>Hostel B</option>
      <option>Main Gate</option><option>Cafeteria</option><option>Sports Complex</option><option>Other</option>
    </select>
    <label>What happened?</label>
    <textarea id="description" rows="5" placeholder="Example: Wi-Fi is completely down on the second floor of CSE Block since morning..."></textarea>
    <button class="primary full" onclick="analyzeAndSubmit()">Analyze & Submit</button>
    <div id="analysis" class="analysis hidden"></div>
  `;
}

function closeModal() {
  document.getElementById("modal").classList.add("hidden");
  document.body.classList.remove("modal-open");
}

async function analyzeAndSubmit() {
  const description = document.getElementById("description").value.trim();
  const location = document.getElementById("location").value;
  const student_name = document.getElementById("studentName").value.trim() || "Anonymous Student";
  localStorage.setItem(
    "campusfix_student_name",
    student_name
);
  if (description.length < 8) {
    toast("Please describe the problem in more detail.");
    return;
  }

  const analysis = document.getElementById("analysis");
  analysis.classList.remove("hidden");
  analysis.innerHTML = `<strong>Analyzing...</strong><p class="muted">Detecting category → checking similar incidents → calculating priority</p>`;

  const res = await fetch("/api/analyze", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({description, location, student_name})
  });
  const data = await res.json();
  if (!res.ok) {
    toast(data.error || "Something went wrong.");
    return;
  }

  analysis.innerHTML = `
    <strong>AI Analysis Complete</strong>
    <div class="analysis-grid">
      <div class="analysis-item"><small>Category</small><strong>${escapeHtml(data.category)}</strong></div>
      <div class="analysis-item"><small>Severity</small><strong>${escapeHtml(data.severity)}</strong></div>
      <div class="analysis-item"><small>Priority</small><strong>${data.preview_priority}/100</strong></div>
      <div class="analysis-item"><small>Confidence</small><strong>${Math.round(data.confidence*100)}%</strong></div>
    </div>
    ${data.match ? `<div class="match"><strong>Similar incident detected.</strong><br>${escapeHtml(data.match.title)}<br>Similarity: ${data.similarity}% · Reports: ${data.match.report_count}</div>` : `<div class="match">No matching incident found. A new incident will be created.</div>`}
    <button class="primary full" onclick="confirmReport()">Confirm & Create Incident</button>
  `;

  window.pendingReport = {description, location, student_name};
}

async function confirmReport() {
  const data = window.pendingReport;
  const res = await fetch("/api/reports", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify(data)
  });
  const result = await res.json();
  if (!res.ok) {
    toast(result.error || "Could not create report.");
    return;
  }
  closeModal();
  toast(result.grouped ? "Report grouped into an existing incident." : "New incident created.");
  loadAll();
}

function toast(message) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2800);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));
}
loadAll();
