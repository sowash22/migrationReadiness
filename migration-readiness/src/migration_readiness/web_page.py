"""Static HTML shell for the migration readiness preview."""

DEFAULT_REQUEST = (
    "Prepare Shopify merchant ABC for migration to the new payment integration."
)

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Migration Readiness Preview</title>
  <style>
    :root {
      --bg: #f3f6f2;
      --panel: #ffffff;
      --ink: #14201a;
      --muted: #5b6b63;
      --line: #d5ddd6;
      --accent: #0f6b4c;
      --good: #0f6b4c;
      --warn: #9a6700;
      --bad: #b42318;
      --font: "Source Serif 4", "Iowan Old Style", Georgia, serif;
      --sans: "IBM Plex Sans", "Segoe UI", sans-serif;
      --mono: "IBM Plex Mono", ui-monospace, monospace;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: var(--sans);
      color: var(--ink);
      background:
        linear-gradient(180deg, #e7efe8 0%, transparent 28%),
        repeating-linear-gradient(
          -12deg,
          transparent,
          transparent 11px,
          rgba(15, 107, 76, 0.035) 11px,
          rgba(15, 107, 76, 0.035) 12px
        ),
        var(--bg);
    }
    main {
      max-width: 960px;
      margin: 0 auto;
      padding: 40px 20px 64px;
    }
    .brand {
      font-size: 13px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--accent);
      margin: 0 0 10px;
    }
    h1 {
      font-family: var(--font);
      font-size: clamp(32px, 5vw, 48px);
      line-height: 1.05;
      margin: 0 0 12px;
      font-weight: 600;
    }
    .lede {
      color: var(--muted);
      max-width: 46rem;
      margin: 0 0 28px;
      font-size: 16px;
      line-height: 1.5;
    }
    form, .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      margin-bottom: 18px;
    }
    label {
      display: block;
      font-size: 13px;
      color: var(--muted);
      margin-bottom: 8px;
    }
    textarea {
      width: 100%;
      min-height: 96px;
      resize: vertical;
      border-radius: 6px;
      border: 1px solid var(--line);
      background: #f8fbf8;
      color: var(--ink);
      padding: 12px 14px;
      font: 14px/1.45 var(--mono);
    }
    .row {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      align-items: center;
      margin-top: 14px;
    }
    button {
      appearance: none;
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: white;
      font: 600 14px var(--sans);
      padding: 10px 16px;
      cursor: pointer;
    }
    button.example {
      background: transparent;
      color: var(--accent);
      border: 1px solid color-mix(in srgb, var(--accent) 45%, var(--line));
      font-weight: 500;
      padding: 8px 12px;
    }
    button:disabled { opacity: 0.6; cursor: wait; }
    .hint { color: var(--muted); font-size: 13px; }
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .stat {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: var(--panel);
    }
    .stat .k { color: var(--muted); font-size: 12px; margin-bottom: 6px; }
    .stat .v { font-size: 24px; font-weight: 650; }
    .band-ready { color: var(--good); }
    .band-at_risk { color: var(--warn); }
    .band-not_ready { color: var(--bad); }
    h2 { font-size: 16px; margin: 0 0 12px; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td {
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }
    th { color: var(--muted); font-weight: 500; font-size: 12px; }
    .pill {
      display: inline-block;
      border-radius: 4px;
      padding: 2px 7px;
      font-size: 12px;
      border: 1px solid var(--line);
      background: #f3f7f4;
    }
    .sev-blocker { color: var(--bad); border-color: color-mix(in srgb, var(--bad) 50%, var(--line)); }
    .sev-high { color: var(--warn); }
    .mono { font-family: var(--mono); font-size: 12px; color: var(--muted); }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      background: #f8fbf8;
      border-radius: 6px;
      padding: 12px;
      border: 1px solid var(--line);
      font: 12px/1.45 var(--mono);
      max-height: 320px;
      overflow: auto;
    }
    .empty { color: var(--muted); }
    .err { color: var(--bad); white-space: pre-wrap; }
    .scenarios {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 10px;
      margin: 0 0 18px;
    }
    .scenario {
      text-align: left;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      cursor: pointer;
      font: inherit;
      color: inherit;
    }
    .scenario:hover { border-color: var(--accent); }
    .scenario .t { font-weight: 650; margin-bottom: 4px; }
    .scenario .s { color: var(--muted); font-size: 12px; line-height: 1.4; }
  </style>
</head>
<body>
  <main>
    <p class="brand">Migration Readiness</p>
    <h1>Payment migration preview</h1>
    <p class="lede">
      Click a scenario to load and run it. Demo merchants:
      <strong>ABC</strong> (not ready), <strong>RISK</strong> (at risk),
      <strong>ACME</strong> (ready). Unknown names fail at intake.
    </p>

    <div class="scenarios" id="scenarios"></div>

    <form id="run-form">
      <label for="request">Merchant request</label>
      <textarea id="request" name="request">__DEFAULT_REQUEST__</textarea>
      <div class="row">
        <button type="submit" id="run-btn">Run migration readiness</button>
        <span class="hint">Auto-approves cutover validation for this preview.</span>
      </div>
    </form>

    <div id="status" class="hint">Ready.</div>
    <div id="results"></div>
  </main>
  <script>
    const form = document.getElementById("run-form");
    const status = document.getElementById("status");
    const results = document.getElementById("results");
    const btn = document.getElementById("run-btn");
    const scenariosEl = document.getElementById("scenarios");

    function esc(s) {
      return String(s)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    function bandClass(band) {
      return "band-" + (band || "not_ready");
    }

    function render(data) {
      const r = data.readiness || {};
      const blockers = data.blockers || [];
      const agents = data.agents || [];
      results.innerHTML = `
        <div class="stats">
          <div class="stat"><div class="k">Case</div><div class="v">${esc(data.case_id)}</div></div>
          <div class="stat"><div class="k">Stage</div><div class="v">${esc(data.stage)}</div></div>
          <div class="stat"><div class="k">Score</div><div class="v ${bandClass(r.band)}">${esc(r.score ?? "—")}</div></div>
          <div class="stat"><div class="k">Band</div><div class="v ${bandClass(r.band)}">${esc(r.band || "—")}</div></div>
        </div>
        <div class="panel">
          <h2>Summary</h2>
          <p>${esc(r.summary || "No readiness summary.")}</p>
          <p class="mono">Report: ${esc(data.report_path || "n/a")}</p>
        </div>
        <div class="panel">
          <h2>Blockers</h2>
          ${blockers.length === 0 ? '<p class="empty">No blockers.</p>' : `
          <table>
            <thead><tr><th>ID</th><th>Area</th><th>Issue</th><th>Remediation</th></tr></thead>
            <tbody>
              ${blockers.map(b => `
                <tr>
                  <td><span class="pill sev-blocker">${esc(b.id)}</span></td>
                  <td>${esc(b.area)}</td>
                  <td>${esc(b.description)}</td>
                  <td>${esc(b.remediation)}</td>
                </tr>`).join("")}
            </tbody>
          </table>`}
        </div>
        <div class="panel">
          <h2>Agent run</h2>
          <table>
            <thead><tr><th>Agent</th><th>Summary</th></tr></thead>
            <tbody>
              ${agents.map(a => `
                <tr>
                  <td><span class="pill">${esc(a.agent)}</span></td>
                  <td>${esc(a.summary)}</td>
                </tr>`).join("")}
            </tbody>
          </table>
        </div>
        <div class="panel">
          <h2>Report preview</h2>
          <pre>${esc(data.report_preview || "")}</pre>
        </div>
      `;
    }

    async function runRequest(request) {
      btn.disabled = true;
      status.textContent = "Running agents…";
      results.innerHTML = "";
      try {
        const res = await fetch("/api/run", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ request, auto_approve: true }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Request failed");
        status.textContent = "Done.";
        render(data);
      } catch (err) {
        status.innerHTML = `<span class="err">${esc(err.message || err)}</span>`;
      } finally {
        btn.disabled = false;
      }
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      await runRequest(document.getElementById("request").value);
    });

    async function loadScenarios() {
      const res = await fetch("/api/scenarios");
      const data = await res.json();
      scenariosEl.innerHTML = (data.scenarios || []).map((s) => `
        <button type="button" class="scenario" data-request="${esc(s.request)}">
          <div class="t">${esc(s.title)}</div>
          <div class="s">${esc(s.summary)}</div>
        </button>
      `).join("");
      scenariosEl.querySelectorAll("button.scenario").forEach((el) => {
        el.addEventListener("click", async () => {
          const request = el.dataset.request || "";
          document.getElementById("request").value = request;
          await runRequest(request);
        });
      });
    }
    loadScenarios();
  </script>
</body>
</html>
""".replace("__DEFAULT_REQUEST__", DEFAULT_REQUEST)
