from __future__ import annotations

import hashlib
import json
import shutil

from pathlib import Path

from .generation import get_adapter, GenerationError
from .render import detect_and_build, publish_static
from .store import load_pairs, save_pairs

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT / "workspaces"
RENDER_ROOT = ROOT / "renders"


def _file_manifest(root: Path) -> list[dict]:
    items = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        # Don't duplicate runtime metadata generated inside a workspace.
        if path.name in {".generation.json"}:
            continue

        digest = hashlib.sha256(path.read_bytes()).hexdigest()

        items.append(
            {
                "filename": str(path.relative_to(root)),
                "size_bytes": path.stat().st_size,
                "sha256": digest,
            }
        )

    return items


def _stage_inputs(pair, workspace: Path) -> None:
    reference_dir = getattr(pair, "reference_input_dir", None)

    if not reference_dir:
        raise RuntimeError(
            f"Pair {pair.pair_id} has no reference_input_dir configured"
        )

    input_root = ROOT / "data" / "inputs" / reference_dir

    if not input_root.exists():
        raise RuntimeError(
            f"Reference input directory not found: {input_root}"
        )

    staged = workspace / "reference_inputs"
    shutil.copytree(input_root, staged, dirs_exist_ok=True)

    manifest = {
        "pair_id": pair.pair_id,
        "prompt_file": "prompt.md",
        "reference_root": "reference_inputs",
        "source_reference_dir": str(input_root),
        "files": _file_manifest(input_root),
    }

    (workspace / "input_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )


def run_pair(pair_id: str, models=("claude", "codex"), prompt_path=None):
    pairs = load_pairs(
        Path(prompt_path)
        if prompt_path
        else ROOT / "data/prompts/pairs.json"
    )

    if pair_id not in pairs:
        raise KeyError(pair_id)

    pair = pairs[pair_id]
    pair.status = "GENERATING"

    for key, model in zip(("A", "B"), models):
        out = pair.outputs[key]

        workspace = WORKSPACE_ROOT / pair_id / key

        if workspace.exists():
            shutil.rmtree(workspace)

        workspace.mkdir(parents=True)

        prompt_file = workspace / "prompt.md"
        prompt_file.write_text(pair.prompt, encoding="utf-8")

        try:
            _stage_inputs(pair, workspace)
        except Exception as e:
            out.status = "INPUT_STAGING_FAILED"
            out.build_log = str(e)
            continue

        # Add an explicit instruction so model agents know where to look.
        generation_prompt = (
            pair.prompt
            + "\n\n"
            + "Reference materials are available locally in the "
            + "`reference_inputs/` directory. Review all applicable "
            + "screenshots, images, and video there before implementing "
            + "the website. Do not use source code from any reference site."
        )

        prompt_file.write_text(generation_prompt, encoding="utf-8")

        out.workspace = str(workspace)

        adapter = get_adapter(model)

        try:
            if not adapter.available():
                out.status = "MODEL_UNAVAILABLE"
                continue

            adapter.generate(
                generation_prompt,
                workspace,
                prompt_file,
            )

            detect_and_build(workspace)

            render_dir = publish_static(
                pair_id,
                key.lower(),
                workspace,
            )

            out.source_path = str(render_dir)
            out.status = "READY_FOR_EVALUATION"
            out.render_url = (
                f"/renders/{pair_id}/{key.lower()}/"
            )

        except GenerationError as e:
            out.status = "GENERATION_FAILED"
            out.build_log = str(e)

        except Exception as e:
            out.status = "RENDER_FAILED"
            out.build_log = str(e)

    if all(
        pair.outputs[k].status == "READY_FOR_EVALUATION"
        for k in ("A", "B")
    ):
        pair.status = "READY_FOR_EVALUATION"
    else:
        pair.status = "PARTIAL"

    save_pairs(pairs)
    return pair


def demo():
    return run_pair(
        "sample_fluxboard_001",
        ("mock-a", "mock-b"),
    )
