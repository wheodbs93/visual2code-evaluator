# Productionization checklist

The current repo is an executable pilot, not a production security boundary.

## Generation
- Approved company-owned credentials or API access.
- Model/version allowlist and cost logging.
- Immutable prompt/reference manifest.
- Separate A/B workspaces.
- Capture model metadata and execution logs.

## Rendering
- Isolated container/VM per output.
- No project secrets in generated runtimes.
- Resource/time limits.
- Controlled network egress.
- Unique, authenticated or otherwise controlled URLs if required.
- Automatic cleanup/retention.
- Browser smoke QA before queue admission.

## Evaluation
- Authenticated evaluator access.
- Randomized A/B presentation if required by methodology.
- Evaluator identity and audit timestamps.
- 5-rater assignment logic.
- Golden-set calibration.
- Inter-rater agreement reporting.
- Spot-check/recalibration workflow.

## Delivery
- Stable pair/output IDs.
- Export schema versioning.
- Raw annotations + metadata.
- Final render URLs and artifact references where permitted.
- Delivery manifest and validation report.
