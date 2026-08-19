from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any

DIMENSIONS = [
    "prompt_adherence",
    "visual_craft",
    "modernity",
    "interaction_navigation",
    "clarity_messaging",
]


@dataclass
class RubricItem:
    id: str
    text: str
    dimension: str
    importance: str
    requires_interaction: bool = False


@dataclass
class OutputRecord:
    output_id: str
    model: str
    workspace: str = ""
    source_path: str = ""
    render_url: str = ""
    status: str = "PENDING"
    build_log: str = ""
    qa: dict[str, Any] = field(default_factory=dict)


@dataclass
class PairRecord:
    pair_id: str
    prompt_id: str
    prompt: str
    category: str
    complexity: str
    difficulty: int
    strategy: str
    quality_tier: str
    reference_site_url: str = ""
    reference_input_dir: str = ""
    reference_assets: list[str] = field(default_factory=list)
    rubric: list[RubricItem] = field(default_factory=list)
    outputs: dict[str, OutputRecord] = field(default_factory=dict)
    status: str = "NEW"

    def to_dict(self):
        return asdict(self)


def rubric_from_dict(items):
    return [RubricItem(**x) for x in items]
