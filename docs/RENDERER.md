# Renderer contract

The MVP proves the contract with static files served locally. The contract is intentionally independent of Netlify/Vercel/etc.

## Input
- pair_id
- output key A/B
- generated source workspace

## Output
- status
- render URL
- published artifact location
- QA metadata

## MVP renderer
- Static `index.html` is directly published.
- `dist/` or `build/` is preferred when present.
- The evaluator server exposes `/renders/<pair_id>/<output_key>/`.

## Production renderer
Use isolated containers/VMs for arbitrary Node/Vite/Next/server-side applications. Build and run with no credentials mounted into the generated app, restricted egress, CPU/memory/process limits, timeouts, and cleanup.

## Shareability
When deployed to a VM/service reachable by the team, set the public/base URL so the evaluator receives URLs everyone on the project can open. Localhost is development-only.
