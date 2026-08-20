from __future__ import annotations

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import json
import csv
import io
from pathlib import Path
from .store import load_pairs, append_evaluation, evaluation_count, evaluator_has_submitted

ROOT = Path(__file__).resolve().parents[1]

DIMENSIONS = [
    ("prompt_adherence", "Prompt Adherence"),
    ("visual_craft", "Visual Craft"),
    ("modernity", "Modernity"),
    ("interaction_navigation", "Interaction / Navigation"),
    ("clarity_messaging", "Clarity of Messaging"),
]

HTML = r'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Visual2Code A/B Evaluator</title>

<style>
:root{
  --bg:#f5f5f3;
  --card:#fff;
  --border:#d9d9d5;
  --muted:#666;
  --text:#202020;
  --accent:#111;
}

*{box-sizing:border-box}

body{
  margin:0;
  background:var(--bg);
  color:var(--text);
  font:15px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}

.wrap{
  max-width:1500px;
  margin:0 auto;
  padding:24px;
}

.card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:14px;
  padding:20px;
  margin-bottom:18px;
}

h1,h2,h3{
  margin-top:0;
}

.muted{
  color:var(--muted);
}

.pill{
  display:inline-block;
  padding:4px 9px;
  background:#ededeb;
  border-radius:999px;
  margin:4px 5px 0 0;
  font-size:13px;
}

.prompt-section{
  display:grid;
  grid-template-columns:1fr;
  gap:14px;
}

.prompt-block{
  border:1px solid var(--border);
  border-radius:10px;
  padding:14px;
  background:#fafaf8;
}

.prompt-title{
  font-weight:700;
  margin-bottom:7px;
}

.prompt-text{
  white-space:pre-wrap;
  line-height:1.55;
}

.outputs{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:18px;
}

.output-card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:14px;
  padding:16px;
}

.site{
  width:100%;
  height:650px;
  border:1px solid #ccc;
  border-radius:10px;
  background:white;
}

.output-actions{
  display:flex;
  gap:8px;
  flex-wrap:wrap;
  margin:12px 0;
}

.btn-link{
  display:inline-flex;
  align-items:center;
  gap:5px;
  border:1px solid var(--border);
  border-radius:8px;
  padding:8px 12px;
  color:#111;
  text-decoration:none;
  background:#fff;
  cursor:pointer;
}

.dimension{
  border:1px solid var(--border);
  border-radius:14px;
  padding:20px;
  margin-bottom:18px;
  background:#fff;
}

.dimension-header{
  margin-bottom:14px;
}

.dimension-title{
  font-size:21px;
  font-weight:700;
}

.dimension-description{
  color:var(--muted);
  margin-top:4px;
}

.rubric{
  background:#fafaf8;
  border:1px solid var(--border);
  border-radius:10px;
  padding:14px;
  margin-bottom:16px;
}

.rubric-item{
  padding:9px 0;
  border-bottom:1px solid #e8e8e4;
}

.rubric-item:last-child{
  border-bottom:0;
}

.rubric-label{
  font-weight:600;
}

.rubric-meta{
  margin-top:3px;
  font-size:12px;
  color:var(--muted);
}

.preference-grid{
  display:grid;
  grid-template-columns:220px 1fr 1fr;
  gap:10px;
  align-items:center;
  margin-bottom:16px;
}

.preference-head{
  font-weight:700;
}

.option-cell{
  border:1px solid var(--border);
  border-radius:9px;
  padding:10px;
  background:#fafaf8;
}

.score-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:14px;
  margin-bottom:16px;
}

.score-card{
  border:1px solid var(--border);
  border-radius:10px;
  padding:14px;
}

.score-card select{
  width:100%;
  padding:9px;
  margin-top:6px;
}

.rationale-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:14px;
}

textarea{
  width:100%;
  min-height:110px;
  resize:vertical;
  padding:10px;
  border:1px solid var(--border);
  border-radius:9px;
  font:inherit;
}

.final-section{
  position:sticky;
  bottom:0;
  background:rgba(245,245,243,.96);
  backdrop-filter:blur(8px);
  border-top:1px solid var(--border);
  padding:14px 0;
}

.submit{
  background:var(--accent);
  color:white;
  border:0;
  border-radius:9px;
  padding:12px 18px;
  cursor:pointer;
  font-weight:600;
}

select{
  border:1px solid var(--border);
  border-radius:8px;
  padding:9px;
  background:#fff;
}

@media(max-width:1000px){
  .outputs,
  .score-grid,
  .rationale-grid{
    grid-template-columns:1fr;
  }

  .preference-grid{
    grid-template-columns:1fr;
  }
}
</style>
</head>

<body>
<div class="wrap">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap">
    <div>
      <h1>Visual2Code A/B Evaluator</h1>
      <div id="evaluatorBanner" class="muted"></div>
    </div>

    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <button
        id="changeEvaluator"
        class="btn-link"
        type="button"
        style="display:none">
        Change evaluator
      </button>

      <a class="btn-link" href="/api/evaluations/export">
        Export Results CSV
      </a>
    </div>
  </div>

  <div id="app">Loading...</div>
</div>

<script>
const dims = %DIMS%;

function esc(s){
  return String(s ?? "")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;");
}

function absUrl(path){
  if(/^https?:\/\//.test(path)) return path;
  return window.location.origin + path;
}

async function getJSON(url, opts){
  const r = await fetch(url, opts);
  if(!r.ok) throw new Error(await r.text());
  return r.json();
}

function rubricForDimension(p, id){
  return p.rubric.filter(x => x.dimension === id);
}

function renderPrompt(p){
  return `
    <div class="card">
      <h2>${esc(p.prompt_id)}</h2>

      <div class="prompt-section">
        <div class="prompt-block">
          <div class="prompt-title">Objective</div>
          <div class="prompt-text">
            Recreate the requested website according to the supplied prompt and reference materials.
          </div>
        </div>

        <div class="prompt-block">
          <div class="prompt-title">Prompt Instructions</div>
          <div class="prompt-text">${esc(p.prompt)}</div>
        </div>

        <div class="prompt-block">
          <div class="prompt-title">Metadata</div>
          <div>
            <span class="pill">${esc(p.category)}</span>
            <span class="pill">${esc(p.complexity)}</span>
            <span class="pill">${esc(p.strategy)}</span>
            <span class="pill">${esc(p.quality_tier)}</span>
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderOutputs(p){
  const referenceUrl =
    p.reference_folder_url ||
    "https://drive.google.com/drive/folders/1PY_wVxDio9pYsRVRnl_KT55X-WkJY9oh";

  return `
    <div class="card">
      <h2>Reference Materials</h2>
      <a class="btn-link" href="${esc(referenceUrl)}" target="_blank">
        Open Reference Materials ↗
      </a>
      <div class="muted" style="margin-top:8px">
        Use the supplied screenshots and screen recordings as the reference when evaluating the generated sites.
      </div>
    </div>

    <div class="outputs">

      ${["A","B"].map(k => {
        const o = p.outputs[k];
        const url = absUrl(o.render_url);

        return `
          <div class="output-card">
            <h2>Output ${k}</h2>
            <div class="muted">${esc(o.model)} · ${esc(o.status)}</div>

            <div class="output-actions">
              <a class="btn-link" href="${esc(url)}" target="_blank">
                Open Output ${k} ↗
              </a>

              <button
                class="btn-link"
                type="button"
                onclick="copyUrl('${url}')">
                Copy URL
              </button>
            </div>

            <iframe class="site" src="${esc(o.render_url)}"></iframe>
          </div>
        `;
      }).join("")}

    </div>
  `;
}

function renderRubric(items){
  if(!items.length){
    return `<div class="rubric muted">No prompt-specific rubric items for this dimension.</div>`;
  }

  return `
    <div class="rubric">
      <h3>Evidence / rubric</h3>

      ${items.map(item => `
        <div class="rubric-item">
          <div class="rubric-label">${esc(item.text)}</div>
          <div class="rubric-meta">
            ${esc(item.importance)} ·
            interaction required=${item.requires_interaction ? "yes" : "no"}
          </div>

          <div style="margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:10px">
            <label class="option-cell">
              Output A
              <select name="rub_${item.id}_A" required>
                <option value="">Select</option>
                <option value="pass">Pass</option>
                <option value="fail">Fail</option>
              </select>
            </label>

            <label class="option-cell">
              Output B
              <select name="rub_${item.id}_B" required>
                <option value="">Select</option>
                <option value="pass">Pass</option>
                <option value="fail">Fail</option>
              </select>
            </label>
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

function renderDimension(p, id, label){
  const items = rubricForDimension(p, id);

  return `
    <section class="dimension">

      <div class="dimension-header">
        <div class="dimension-title">${label}</div>
        <div class="dimension-description">
          Complete this dimension before moving to the next one.
        </div>
      </div>

      ${renderRubric(items)}

      <div class="preference-grid">
        <div class="preference-head">Which output is better?</div>

        <label class="option-cell">
          <input
            type="radio"
            name="pref_${id}"
            value="A"
            required>
          Output A
        </label>

        <label class="option-cell">
          <input
            type="radio"
            name="pref_${id}"
            value="B">
          Output B
        </label>
      </div>

      <div class="score-grid">

        <div class="score-card">
          <strong>Output A score</strong>
          <select name="A_${id}" required>
            <option value="">Select score</option>
            ${[1,2,3,4,5].map(n => `<option value="${n}">${n}</option>`).join("")}
          </select>
        </div>

        <div class="score-card">
          <strong>Output B score</strong>
          <select name="B_${id}" required>
            <option value="">Select score</option>
            ${[1,2,3,4,5].map(n => `<option value="${n}">${n}</option>`).join("")}
          </select>
        </div>

      </div>

      <div class="rationale-grid">

        <label>
          <strong>Why did you give Output A this score?</strong>
          <textarea name="rat_A_${id}" required></textarea>
        </label>

        <label>
          <strong>Why did you give Output B this score?</strong>
          <textarea name="rat_B_${id}" required></textarea>
        </label>

      </div>

    </section>
  `;
}

function renderFinal(p){
  return `
    <section class="card">

      <h2>Overall Evaluation</h2>

      <div class="preference-grid">
        <div class="preference-head">Overall preference</div>

        <label class="option-cell">
          <input type="radio" name="overall" value="A" required>
          Output A
        </label>

        <label class="option-cell">
          <input type="radio" name="overall" value="B">
          Output B
        </label>
      </div>

      <div class="score-grid">

        <div class="score-card">
          <strong>Output A — Awardable?</strong>

          <div style="margin-top:8px">
            <label>
              <input type="radio" name="award_A" value="Yes" required>
              Yes
            </label>

            <label style="margin-left:14px">
              <input type="radio" name="award_A" value="No">
              No
            </label>
          </div>
        </div>

        <div class="score-card">
          <strong>Output B — Awardable?</strong>

          <div style="margin-top:8px">
            <label>
              <input type="radio" name="award_B" value="Yes" required>
              Yes
            </label>

            <label style="margin-left:14px">
              <input type="radio" name="award_B" value="No">
              No
            </label>
          </div>
        </div>

      </div>

      <div class="preference-grid">
        <div class="preference-head">Which is more award-worthy?</div>

        <label class="option-cell">
          <input type="radio" name="award_pref" value="A" required>
          Output A
        </label>

        <label class="option-cell">
          <input type="radio" name="award_pref" value="B">
          Output B
        </label>
      </div>

      <label style="display:block;max-width:300px;margin-top:16px">
        <strong>Prompt difficulty</strong>
        <select name="difficulty" required style="width:100%;margin-top:6px">
          ${[1,2,3,4,5].map(n => `
            <option value="${n}" ${n===p.difficulty ? "selected" : ""}>
              ${n}
            </option>
          `).join("")}
        </select>
      </label>

    </section>
  `;
}

async function copyUrl(url){
  try{
    await navigator.clipboard.writeText(url);
    alert("URL copied.");
  }catch{
    alert(url);
  }
}

function getStoredEvaluatorId(){
  return localStorage.getItem("visual2code_evaluator_id") || "";
}

function setEvaluatorId(id){
  id = String(id || "").trim();

  if(!id){
    throw new Error("Evaluator ID is required.");
  }

  localStorage.setItem(
    "visual2code_evaluator_id",
    id
  );

  return id;
}

function renderEvaluatorGate(){
  document.getElementById("app").innerHTML = `
    <div class="card" style="max-width:620px;margin:80px auto">
      <h2>Visual2Code Evaluation</h2>

      <p class="muted">
        Enter your evaluator ID to begin. Your ID will be remembered
        in this browser for future evaluations.
      </p>

      <label style="display:block;margin-top:20px">
        <strong>Evaluator ID</strong>
        <input
          id="evaluatorIdInput"
          type="text"
          autocomplete="off"
          placeholder="e.g. carrie"
          style="width:100%;margin-top:8px;padding:12px;border:1px solid #ccc;border-radius:8px;font:inherit"
        >
      </label>

      <button
        id="startEvaluation"
        class="submit"
        type="button"
        style="margin-top:16px">
        Start evaluation
      </button>
    </div>
  `;

  const input = document.getElementById("evaluatorIdInput");
  const button = document.getElementById("startEvaluation");

  const submit = () => {
    try{
      setEvaluatorId(input.value);
      load();
    }catch(err){
      alert(err.message);
    }
  };

  button.onclick = submit;

  input.addEventListener("keydown", (e) => {
    if(e.key === "Enter"){
      submit();
    }
  });

  input.focus();
}


async function load(){
  const evaluatorId = getStoredEvaluatorId();

  if(!evaluatorId){
    renderEvaluatorGate();
    return;
  }

  const data = await getJSON("/api/pairs");

  const evaluatorBanner =
    document.getElementById("evaluatorBanner");

  if(evaluatorBanner){
    evaluatorBanner.innerHTML =
      `Evaluator: <strong>${esc(evaluatorId)}</strong>`;
  }

  const changeEvaluator =
    document.getElementById("changeEvaluator");

  if(changeEvaluator){
    changeEvaluator.style.display = "inline-flex";
    changeEvaluator.onclick = () => {
      localStorage.removeItem("visual2code_evaluator_id");
      renderEvaluatorGate();
    };
  }

  document.getElementById("app").innerHTML = `
    <div class="card">
      <label>
        Pair
        <select id="pair">
          ${data.map(x =>
            `<option value="${x.pair_id}">
              ${x.pair_id} — ${esc(x.status)}
            </option>`
          ).join("")}
        </select>
      </label>
    </div>

    <div id="pairview"></div>
  `;

  document.getElementById("pair").onchange = render;
  render();
}

async function render(){
  const id = document.getElementById("pair").value;
  const p = await getJSON("/api/pairs/" + encodeURIComponent(id));

  let h = renderPrompt(p);

  const evaluationCount = Number(p.evaluation_count || 0);
  const evaluationLimit = Number(p.evaluation_limit || 5);

  h += `
    <div class="card">
      <strong>Evaluations</strong>
      <span class="pill">${evaluationCount} / ${evaluationLimit}</span>
      ${
        evaluationCount >= evaluationLimit
          ? '<div class="muted" style="margin-top:8px">This pair has reached the maximum of 5 evaluations.</div>'
          : '<div class="muted" style="margin-top:8px">Up to 5 raters can evaluate this pair.</div>'
      }
    </div>
  `;

  h += renderOutputs(p);

  h += `<form id="eval">`;

  for(const [dimId, dimLabel] of dims){
    h += renderDimension(p, dimId, dimLabel);
  }

  h += renderFinal(p);

  h += `
    <div class="final-section">
      <button class="submit" type="submit">
        Submit evaluation
      </button>
    </div>
  `;

  h += `</form>`;

  document.getElementById("pairview").innerHTML = h;

  const evalForm = document.getElementById("eval");

  if(evaluationCount >= evaluationLimit){
    evalForm.querySelectorAll("input, select, textarea, button")
      .forEach(el => el.disabled = true);

    const submitButton = evalForm.querySelector("button.submit");

    if(submitButton){
      submitButton.textContent = "Evaluation limit reached";
    }
  }

  evalForm.onsubmit = async (e) => {
    e.preventDefault();

    const fd = new FormData(e.target);

    const payload = {
      pair_id: id,
      evaluator_id: getStoredEvaluatorId(),
      answers: Object.fromEntries(fd.entries()),
      submitted_at: new Date().toISOString()
    };

    try{
      await getJSON("/api/evaluations", {
        method:"POST",
        headers:{"content-type":"application/json"},
        body:JSON.stringify(payload)
      });

      alert("Saved evaluation.");
    }catch(err){
      alert("Failed: " + err.message);
    }
  };
}

load().catch(err =>
  document.getElementById("app").innerHTML =
    `<div class="card">${esc(err.message)}</div>`
);
</script>
</body>
</html>'''.replace("%DIMS%", json.dumps(DIMENSIONS))


class Handler(SimpleHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            return self.send_text(
                HTML,
                "text/html; charset=utf-8"
            )

        if parsed.path == "/api/pairs":
            pairs = load_pairs()
            return self.send_json([
                {
                    "pair_id": p.pair_id,
                    "status": p.status
                }
                for p in pairs.values()
            ])

        if parsed.path.startswith("/api/pairs/"):
            pid = parsed.path.split("/")[-1]
            pairs = load_pairs()

            if pid not in pairs:
                return self.send_error(404)

            result = pairs[pid].to_dict()
            evaluator_id = ""
            count = evaluation_count(pid)

            result["evaluation_count"] = count
            result["evaluation_limit"] = 5

            return self.send_json(result)

        if parsed.path == "/api/evaluations/export":
            from .store import export_evaluations

            rows = export_evaluations()

            fieldnames = [
                "id",
                "pair_id",
                "evaluator_id",
                "submitted_at",
                "overall",
                "award_A",
                "award_B",
                "award_pref",
                "difficulty",
            ]

            # Gather all answer keys so rubric/dimension fields are included.
            answer_keys = set()

            for row in rows:
                answer_keys.update(
                    row.get("payload", {}).get("answers", {}).keys()
                )

            fieldnames.extend(
                sorted(
                    k for k in answer_keys
                    if k not in fieldnames
                )
            )

            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )
            writer.writeheader()

            for row in rows:
                payload = row.get("payload", {})
                answers = payload.get("answers", {})

                record = {
                    "id": row.get("id", ""),
                    "pair_id": row.get("pair_id", ""),
                    "evaluator_id": row.get("evaluator_id", ""),
                    "submitted_at": row.get("submitted_at", ""),
                }

                record.update(answers)

                writer.writerow(record)

            data = output.getvalue().encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/csv; charset=utf-8"
            )
            self.send_header(
                "Content-Disposition",
                'attachment; filename="visual2code_evaluations.csv"'
            )
            self.send_header(
                "Content-Length",
                str(len(data))
            )
            self.end_headers()
            self.wfile.write(data)
            return

        if parsed.path.startswith("/renders/"):
            rel = parsed.path[len("/renders/"):].lstrip("/")
            path = ROOT / "renders" / rel

            if path.is_dir():
                path = path / "index.html"

            if not path.exists():
                return self.send_error(404)

            return self.send_file(path)

        return self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/evaluations":
            n = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(n)

            try:
                data = json.loads(body)
                append_evaluation(data)
                return self.send_json({"ok": True})
            except Exception as e:
                return self.send_json(
                    {"ok": False, "error": str(e)},
                    500
                )

        return self.send_error(404)

    def send_json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def send_text(self, s, ct):
        b = s.encode()
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def send_file(self, path):
        import mimetypes

        b = path.read_bytes()
        self.send_response(200)
        self.send_header(
            "Content-Type",
            mimetypes.guess_type(str(path))[0]
            or "application/octet-stream"
        )
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)


def serve(host="0.0.0.0", port=8080):
    (ROOT / "renders").mkdir(
        parents=True,
        exist_ok=True
    )

    ThreadingHTTPServer(
        (host, port),
        Handler
    ).serve_forever()


if __name__ == "__main__":
    serve()
