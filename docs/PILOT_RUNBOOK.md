# Pilot runbook

## 0. Approved access
Confirm approved Claude/Codex access, versions, and execution ownership before using real client prompts.

## 1. Load prompt
Add pair records to `data/prompts/pairs.json`.

## 2. Demo without model access
`python -m app.cli demo`

## 3. Start evaluator
`python -m app.cli serve --host 0.0.0.0 --port 8080`

## 4. Test a real pair
`python -m app.cli run-pair --pair-id <PAIR_ID> --models claude,codex`

## 5. Verify
Both outputs should reach `READY_FOR_EVALUATION`, have working render URLs, and pass the pre-annotation render gate.

## 6. Evaluate
Open the evaluator root, select the pair, interact with A and B, complete the fields, and submit.

## 7. Export
Results are appended to `data/evaluations/results.jsonl`.

## 8. Productionization
Move generation and rendering to isolated workers, centralize pair state, add authentication, durable storage, retention controls, and formal QA/calibration before scaling.
