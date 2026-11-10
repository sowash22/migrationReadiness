"""Local web preview for the migration readiness orchestrator."""

from __future__ import annotations

import json
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from migration_readiness.orchestrator import MigrationOrchestrator
from migration_readiness.state import StateStore

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
  </style>
</head>
<body>
  <main>
    <p class="brand">Migration Readiness</p>
    <h1>Payment migration preview</h1>
    <p class="lede">
      Run the seven-agent workflow against a merchant request. The preview uses
      sample catalog data (ABC / ACME) and auto-approves the human gate so you
      can inspect readiness, blockers, and the generated report.
    </p>

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

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      btn.disabled = true;
      status.textContent = "Running agents…";
      results.innerHTML = "";
      try {
        const request = document.getElementById("request").value;
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
    });
  </script>
</body>
</html>
""".replace("__DEFAULT_REQUEST__", DEFAULT_REQUEST)


def _run_case(request: str, auto_approve: bool = True) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="migration-preview-"))
    store = StateStore(tmp / "state")
    reports_dir = tmp / "reports"
    orch = MigrationOrchestrator(
        store=store,
        reports_dir=reports_dir,
        auto_approve=auto_approve,
    )
    result = orch.run(request)
    report_preview = ""
    if result.state.report_path:
        report_preview = Path(result.state.report_path).read_text(encoding="utf-8")[:4000]
    return {
        "case_id": result.state.case_id,
        "stage": result.state.stage,
        "approved": result.approved,
        "readiness": (
            result.state.readiness.__dict__ if result.state.readiness else None
        ),
        "report_path": result.state.report_path,
        "report_preview": report_preview,
        "agents": [
            {"agent": r.agent, "summary": r.summary, "details": r.details}
            for r in result.results
        ],
        "blockers": [
            g.__dict__ for g in result.state.gaps if g.severity == "blocker"
        ],
    }


class PreviewHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:  # quieter logs
        sys_stderr = __import__("sys").stderr
        sys_stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(body)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            body = PAGE.encode("utf-8")
            self._send(200, body, "text/html; charset=utf-8")
            return
        if path == "/health":
            self._send(200, b'{"ok":true}', "application/json")
            return
        self._send(404, b'{"error":"not found"}', "application/json")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/run":
            self._send(404, b'{"error":"not found"}', "application/json")
            return
        length = int(self.headers.get("content-length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
            request = str(payload.get("request") or DEFAULT_REQUEST)
            auto_approve = bool(payload.get("auto_approve", True))
            data = _run_case(request, auto_approve=auto_approve)
            body = json.dumps(data).encode("utf-8")
            self._send(200, body, "application/json")
        except Exception as exc:  # noqa: BLE001 - surface to UI
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            self._send(500, body, "application/json")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Migration readiness web preview")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), PreviewHandler)
    print(f"Migration readiness preview: http://{args.host}:{args.port}/")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
