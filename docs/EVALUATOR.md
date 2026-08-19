# Evaluator contract

The evaluator renders the prompt, the A/B live sites, and a data-driven prompt-specific rubric.

Required fields from the project guideline:
- Overall A/B preference.
- A/B preference for each of five dimensions.
- 1-5 scores for both outputs across the five dimensions.
- Awardability Yes/No for each output and A/B award preference.
- 10 written rationales.
- Prompt difficulty 1-5.
- Prompt-specific binary rubric checks with dimension, interaction requirement, and importance.

The UI is data-driven so rubric generation/selection can change later without rewriting the evaluator application.
