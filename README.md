# Visual2Code A/B Evaluation Machine — Pilot v0.2

This pilot implements the machine we want ready when prompts are available:

`prompt + references -> Claude/Codex -> artifacts -> render -> browser QA -> shareable URL -> evaluator UI -> export`

The main SA decision is that rendering is a **service contract**, not a Netlify requirement. The MVP uses a local renderer so the full flow can be tested now. Production can swap in isolated Docker/VM/container infrastructure without changing the generation or evaluation interfaces.

## Works now
- Sample prompt and prompt-specific rubric.
- A/B pair schema and state tracking.
- Claude/Codex command adapters with configurable templates.
- Mock adapters for full end-to-end testing without model access.
- Static browser-accessible rendering.
- Evaluator UI with pairwise, 1-5 scores, awardability, rationales, difficulty, and rubric fields.
- JSONL evaluation export.

## Quick start

```bash
python3 -m app.cli demo
python3 -m app.cli serve --host 0.0.0.0 --port 8080
```

Open `http://localhost:8080/`.

## Real-model flow later

```bash
python3 -m app.cli run-pair --pair-id sample_fluxboard_001 --models claude,codex
```

If the approved company CLI commands differ, use `CLAUDE_EXEC_TEMPLATE` and `CODEX_EXEC_TEMPLATE` in the environment.

## Important
The guideline does not define the final model list/licensing owner, final prompt-strategy choice, or commercial Geo Tier. Keep those as configuration/decision items rather than assumptions.

## Browser QA (optional)

Install Playwright in the execution environment and run Chromium:

```bash
pip install playwright
playwright install chromium
python scripts/run_browser_qa.py http://localhost:8080/renders/sample_fluxboard_001/a/
```

## Production renderer helper

`scripts/build_node_renderer.sh` contains an experimental container build helper for Node-based generated apps. It is **not** a completed production isolation boundary and has not been validated in this environment because Docker is unavailable here. See `docs/PRODUCTIONIZATION.md`.
