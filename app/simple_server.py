from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from .agent import analyze_sku
from .schemas import AnalyzeSkuRequest


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>跨境电商 Agent 工具网关</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #19202a;
      --muted: #667085;
      --line: #d9dee7;
      --accent: #166534;
      --accent-bg: #e8f5ec;
      --warn: #9a3412;
      --warn-bg: #fff1e7;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, "Microsoft YaHei", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      padding: 20px 28px 14px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    h1 {
      margin: 0;
      font-size: 22px;
      font-weight: 700;
    }
    .sub {
      margin-top: 6px;
      color: var(--muted);
      font-size: 14px;
    }
    main {
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 18px;
      padding: 18px;
      max-width: 1280px;
      margin: 0 auto;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    h2 {
      margin: 0 0 14px;
      font-size: 16px;
    }
    label {
      display: block;
      margin: 12px 0 6px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
    }
    input, textarea, select, button {
      width: 100%;
      font: inherit;
      border-radius: 6px;
    }
    input, textarea, select {
      border: 1px solid var(--line);
      padding: 10px 11px;
      background: #fff;
      color: var(--text);
    }
    textarea {
      min-height: 110px;
      resize: vertical;
    }
    button {
      margin-top: 14px;
      border: 0;
      padding: 11px 12px;
      background: #14532d;
      color: #fff;
      font-weight: 700;
      cursor: pointer;
    }
    button:disabled {
      opacity: .65;
      cursor: wait;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      min-height: 78px;
    }
    .metric span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 8px;
    }
    .metric strong {
      font-size: 18px;
    }
    .badge {
      display: inline-flex;
      padding: 5px 8px;
      border-radius: 999px;
      background: var(--accent-bg);
      color: var(--accent);
      font-size: 12px;
      font-weight: 700;
    }
    .badge.warn {
      background: var(--warn-bg);
      color: var(--warn);
    }
    .summary {
      margin: 8px 0 14px;
      line-height: 1.65;
    }
    ul {
      margin: 8px 0 0;
      padding-left: 20px;
      line-height: 1.7;
    }
    pre {
      overflow: auto;
      white-space: pre-wrap;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fbfcfe;
      font-size: 12px;
      line-height: 1.5;
    }
    .cols {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }
    .empty {
      color: var(--muted);
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 22px;
      text-align: center;
    }
    @media (max-width: 860px) {
      main, .grid, .cols {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <header>
    <h1>跨境电商 Agent 工具网关</h1>
    <div class="sub">Agent Runner → Business Tools → Evidence → Guardrail → Trace / Cost Log</div>
  </header>
  <main>
    <section>
      <h2>SKU 运营诊断</h2>
      <form id="form">
        <label for="sku">SKU</label>
        <select id="sku" name="sku">
          <option>SKU-USB-C-001</option>
          <option>SKU-YOGA-002</option>
          <option>SKU-LAMP-003</option>
          <option>SKU-NOT-FOUND</option>
        </select>
        <label for="marketplace">站点</label>
        <select id="marketplace" name="marketplace">
          <option>US</option>
          <option>UK</option>
        </select>
        <label for="operator_role">角色</label>
        <input id="operator_role" name="operator_role" value="operator">
        <label for="question">运营问题</label>
        <textarea id="question" name="question">这个 SKU 在美国站转化差，帮我分析并给出调价和 listing 优化建议</textarea>
        <button id="submit" type="submit">运行 Agent 分析</button>
      </form>
    </section>
    <section>
      <h2>分析结果</h2>
      <div id="result" class="empty">选择一个 SKU 并运行分析。</div>
    </section>
  </main>
  <script>
    const form = document.querySelector("#form");
    const result = document.querySelector("#result");
    const submit = document.querySelector("#submit");

    function pct(value) {
      return value === null || value === undefined ? "-" : `${(value * 100).toFixed(1)}%`;
    }

    function money(value) {
      return value === null || value === undefined ? "-" : `$${Number(value).toFixed(2)}`;
    }

    function esc(value) {
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[char]));
    }

    function render(data) {
      const evidence = data.evidence || {};
      const badgeClass = data.human_review_required ? "badge warn" : "badge";
      result.className = "";
      result.innerHTML = `
        <div class="grid">
          <div class="metric"><span>状态</span><strong>${esc(data.status)}</strong></div>
          <div class="metric"><span>风险</span><strong>${esc(data.risk_level)}</strong></div>
          <div class="metric"><span>转化率</span><strong>${pct(evidence.conversion_rate)}</strong></div>
          <div class="metric"><span>毛利率</span><strong>${pct(evidence.margin_rate)}</strong></div>
        </div>
        <div class="${badgeClass}">${data.human_review_required ? "需要人工复核" : "可进入运营复盘"}</div>
        <p class="summary">${esc(data.summary)}</p>
        <div class="cols">
          <div>
            <h2>建议</h2>
            <ul>${(data.recommendations || []).map(item => `<li>${esc(item)}</li>`).join("") || "<li>暂无建议</li>"}</ul>
          </div>
          <div>
            <h2>关键证据</h2>
            <ul>
              <li>商品：${esc(evidence.title || "-")}</li>
              <li>退款率：${pct(evidence.refund_rate)}</li>
              <li>退款原因：${esc(evidence.top_refund_reason || "-")}</li>
              <li>单件利润：${money(evidence.unit_margin)}</li>
            </ul>
          </div>
        </div>
        <h2>Trace / Cost</h2>
        <pre>${esc(JSON.stringify({trace: data.trace, cost: data.cost, missing_evidence: data.missing_evidence}, null, 2))}</pre>
      `;
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      submit.disabled = true;
      submit.textContent = "分析中...";
      const payload = Object.fromEntries(new FormData(form).entries());
      try {
        const response = await fetch("/agent/analyze-sku", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });
        render(await response.json());
      } catch (error) {
        result.className = "empty";
        result.textContent = `请求失败：${error}`;
      } finally {
        submit.disabled = false;
        submit.textContent = "运行 Agent 分析";
      }
    });
  </script>
</body>
</html>
"""


class AgentGatewayHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/":
            self._send_html(INDEX_HTML)
            return
        if self.path == "/health":
            self._send_json({"status": "ok"})
            return
        self._send_json({"error": "NOT_FOUND"}, status=404)

    def do_POST(self) -> None:
        if self.path != "/agent/analyze-sku":
            self._send_json({"error": "NOT_FOUND"}, status=404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        request = AnalyzeSkuRequest(
            sku=payload["sku"],
            marketplace=payload["marketplace"],
            question=payload["question"],
            operator_role=payload.get("operator_role", "operator"),
        )
        self._send_json(analyze_sku(request).to_dict())

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, body: dict, status: int = 200) -> None:
        data = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, html: str, status: int = 200) -> None:
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    server = HTTPServer(("127.0.0.1", 8000), AgentGatewayHandler)
    print("Serving Agent gateway on http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
