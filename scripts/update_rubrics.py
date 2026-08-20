from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIR_FILE = ROOT / "data" / "prompts" / "pairs.json"

RUBRICS = {
    "direct_recreation": [
        {
            "id": "dr01",
            "text": "Does the overall layout and composition faithfully match the reference, including section structure, sizing, positioning, spacing, and visual hierarchy?",
            "dimension": "visual_craft",
            "importance": "essential",
            "requires_interaction": False,
        },
        {
            "id": "dr02",
            "text": "Does the typography faithfully match the reference in type style, scale, weight, hierarchy, and treatment?",
            "dimension": "visual_craft",
            "importance": "essential",
            "requires_interaction": False,
        },
        {
            "id": "dr03",
            "text": "Do the colors, imagery, backgrounds, and other significant visual treatments faithfully match the reference?",
            "dimension": "visual_craft",
            "importance": "essential",
            "requires_interaction": False,
        },
        {
            "id": "dr04",
            "text": "Are the major visible content areas and navigation structure reproduced faithfully, without material omissions, substitutions, or unsupported additions?",
            "dimension": "prompt_adherence",
            "importance": "essential",
            "requires_interaction": False,
        },
        {
            "id": "dr05",
            "text": "Does the page avoid unsupported redesign or creative reinterpretation of what is shown in the reference?",
            "dimension": "prompt_adherence",
            "importance": "essential",
            "requires_interaction": False,
        },
        {
            "id": "dr06",
            "text": "Do navigation, scrolling behavior, motion, transitions, and other observable interactions faithfully match the supplied reference materials where they can be observed?",
            "dimension": "interaction_navigation",
            "importance": "essential",
            "requires_interaction": True,
        },
    ],
    "inspiration_brief:mid": [
        {
            "id": "im01",
            "text": "Does the page preserve the defining visual characteristics evident in the supplied inspiration, such as its layout approach, visual hierarchy, imagery, spacing, and UI treatment where applicable?",
            "dimension": "visual_craft",
            "importance": "essential",
            "requires_interaction": False,
        },
        {
            "id": "im02",
            "text": "Does the page implement the specific content, page structure, and creative direction explicitly requested in the prompt without material omissions or contradictions?",
            "dimension": "prompt_adherence",
            "importance": "essential",
            "requires_interaction": False,
        },
        {
            "id": "im03",
            "text": "Does the page appropriately adapt the inspiration to the new brand rather than simply recreating the reference or replacing it with an unrelated aesthetic?",
            "dimension": "prompt_adherence",
            "importance": "essential",
            "requires_interaction": False,
        },
        {
            "id": "im04",
            "text": "Where navigation, motion, or interactive behavior is specified in the prompt or observable in the supplied references, does the page carry it through appropriately?",
            "dimension": "interaction_navigation",
            "importance": "essential",
            "requires_interaction": True,
        },
    ],
    "inspiration_brief:structured": [
        {
            "id": "is01",
            "text": "Does the page faithfully execute the prompt's specified typography, color, spacing, layout, imagery, and UI treatments where those elements are defined?",
            "dimension": "visual_craft",
            "importance": "essential",
            "requires_interaction": False,
        },
        {
            "id": "is02",
            "text": "Does the page preserve the defining visual character of the supplied inspiration while applying the adaptations specified for the new brand?",
            "dimension": "visual_craft",
            "importance": "essential",
            "requires_interaction": False,
        },
        {
            "id": "is03",
            "text": "Does the page implement the requested content, structure, features, and other explicit requirements without material omissions or contradictions?",
            "dimension": "prompt_adherence",
            "importance": "essential",
            "requires_interaction": False,
        },
        {
            "id": "is04",
            "text": "Does the page respect explicit negative constraints and avoid elements or treatments the prompt specifically says not to use?",
            "dimension": "prompt_adherence",
            "importance": "essential",
            "requires_interaction": False,
        },
        {
            "id": "is05",
            "text": "Where navigation, motion, transitions, or interactive behaviors are specified in the prompt or observable in the supplied references, does the page reproduce or adapt them as directed?",
            "dimension": "interaction_navigation",
            "importance": "essential",
            "requires_interaction": True,
        },
    ],
}


def rubric_for(pair: dict) -> list[dict]:
    strategy = pair.get("strategy", "")
    complexity = pair.get("complexity", "")

    if strategy == "direct_recreation":
        key = "direct_recreation"
    elif strategy == "inspiration_brief":
        key = f"inspiration_brief:{complexity}"
    else:
        raise ValueError(
            f"Unsupported strategy/complexity: {strategy}/{complexity}"
        )

    return RUBRICS[key]


data = json.loads(PAIR_FILE.read_text(encoding="utf-8"))

for pair in data.get("pairs", []):
    pair["rubric"] = rubric_for(pair)

PAIR_FILE.write_text(
    json.dumps(data, indent=2),
    encoding="utf-8",
)

print(f"Updated {len(data.get('pairs', []))} pair rubrics.")
for pair in data.get("pairs", []):
    print(
        f"{pair['pair_id']}: "
        f"{pair['strategy']}/{pair['complexity']} "
        f"-> {len(pair['rubric'])} items"
    )
