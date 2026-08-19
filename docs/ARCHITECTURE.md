# Visual2Code Pilot Architecture

## Target flow
Prompt + references -> Claude/Codex generation -> isolated workspaces -> build/render -> browser QA -> shareable URLs -> evaluator UI -> export.

## Principles
- Generation, rendering, and evaluation are separate contracts.
- Hosting vendor is an implementation detail.
- Generated code is treated as untrusted.
- Evaluators consume live URLs; codebases remain immutable artifacts.
- Pair-level state is the handoff between generation/render and evaluation.
- Rubrics are data-driven so a standard or prompt-specific rubric can be supported.

## Production shape
Use a control plane plus isolated workers. Each output gets its own workspace/runtime. Do not execute generated application code in the control-plane process.

## State machine
NEW -> GENERATING -> RENDERING -> QA -> READY_FOR_EVALUATION -> EVALUATED -> QA_PASSED -> DELIVERED.
Failure states: MODEL_UNAVAILABLE, GENERATION_FAILED, BUILD_FAILED, RENDER_FAILED, QA_FAILED.
