from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from shutil import which


class GenerationError(RuntimeError):
    pass


class Adapter:
    name = "base"

    def available(self) -> bool:
        return False

    def generate(self, prompt: str, workspace: Path, prompt_file: Path):
        raise NotImplementedError


def _strip_code_fence(text: str) -> str:
    text = text.strip()

    match = re.search(
        r"```(?:html)?\s*(<!DOCTYPE html[\s\S]*?</html>)\s*```",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    doctype = re.search(
        r"(<!DOCTYPE html[\s\S]*?</html>)",
        text,
        flags=re.IGNORECASE,
    )

    if doctype:
        return doctype.group(1).strip()

    html = re.search(
        r"(<html[\s\S]*?</html>)",
        text,
        flags=re.IGNORECASE,
    )

    if html:
        return html.group(1).strip()

    return text


class ClaudeAdapter(Adapter):
    name = "claude"

    def __init__(self):
        self.cmd = os.getenv("CLAUDE_CMD", "claude")

    def available(self) -> bool:
        return which(self.cmd) is not None

    def generate(self, prompt: str, workspace: Path, prompt_file: Path):
        if not self.available():
            raise GenerationError(
                f"Claude CLI not found: {self.cmd}"
            )

        artifact_prompt = f"""
You are generating a landing page for an automated website benchmark.

Follow the user's request exactly.

REFERENCE MATERIALS:
All screenshots, images, videos, and other supplied materials are available
under the local directory:

reference_inputs/

Review all applicable reference materials before generating the page.

IMPORTANT OUTPUT CONTRACT:
You must return the complete website as a SINGLE self-contained HTML document.

Requirements for the HTML:
- Start with <!DOCTYPE html>
- End with </html>
- Inline CSS in <style> blocks.
- Inline JavaScript in <script> blocks.
- Use inline SVG where appropriate.
- Do not rely on external source files.
- Do not rely on external website source code.
- Do not describe the implementation instead of providing it.
- Do not return a prose explanation.
- Do not return a JSON object.
- The final response must contain the complete HTML document only.

The pipeline will save your response to index.html and render it separately.

USER REQUEST:

{prompt}
"""

        cmd = [
            self.cmd,
            "--print",
            "--output-format",
            "json",
        ]

        started = time.time()

        proc = subprocess.run(
            cmd,
            input=artifact_prompt,
            cwd=workspace,
            text=True,
            capture_output=True,
        )

        elapsed = time.time() - started

        meta = {
            "model": self.name,
            "command": cmd,
            "returncode": proc.returncode,
            "elapsed_seconds": round(elapsed, 3),
            "stdout": proc.stdout[-30000:],
            "stderr": proc.stderr[-10000:],
        }

        (workspace / ".generation.json").write_text(
            json.dumps(meta, indent=2),
            encoding="utf-8",
        )

        if proc.returncode != 0:
            raise GenerationError(
                f"Claude generation failed: "
                f"{proc.stderr[-4000:] or proc.stdout[-4000:]}"
            )

        try:
            response = json.loads(proc.stdout)
            result = response.get("result", "")
        except json.JSONDecodeError as exc:
            raise GenerationError(
                f"Claude returned invalid JSON: {exc}"
            )

        html = _strip_code_fence(result)

        if "<html" not in html.lower():
            raise GenerationError(
                "Claude completed successfully but did not return HTML."
            )

        index_path = workspace / "index.html"
        index_path.write_text(
            html,
            encoding="utf-8",
        )

        meta["artifact"] = {
            "type": "html",
            "path": "index.html",
            "bytes": len(html.encode("utf-8")),
        }

        (workspace / ".generation.json").write_text(
            json.dumps(meta, indent=2),
            encoding="utf-8",
        )

        return meta


class CodexAdapter(Adapter):
    name = "codex"

    def __init__(self):
        self.cmd = os.getenv("CODEX_CMD", "codex")

    def available(self) -> bool:
        return which(self.cmd) is not None

    def generate(self, prompt: str, workspace: Path, prompt_file: Path):
        if not self.available():
            raise GenerationError(
                f"Codex CLI not found: {self.cmd}"
            )

        response_file = workspace / ".codex_last_message.txt"

        artifact_prompt = f"""
You are generating a landing page for an automated website benchmark.

Follow the user's request exactly.

REFERENCE MATERIALS:
All screenshots, images, videos, and other supplied materials are available
under the local directory:

reference_inputs/

Review all applicable reference materials before generating the page.

IMPORTANT OUTPUT CONTRACT:
Return the complete website as a SINGLE self-contained HTML document.

Requirements:
- Start with <!DOCTYPE html>
- End with </html>
- Inline CSS in <style> blocks.
- Inline JavaScript in <script> blocks.
- Use inline SVG where appropriate.
- Do not depend on external source files.
- Do not inspect or reproduce reference-site source code.
- Do not return a prose explanation.
- Do not return JSON.
- Your final response must contain the complete HTML document only.

The pipeline will save your final response to index.html and render it separately.

USER REQUEST:

{prompt}
"""

        cmd = [
            self.cmd,
            "exec",
            "--sandbox",
            "workspace-write",
            "--skip-git-repo-check",
            "--cd",
            str(workspace),
            "--output-last-message",
            str(response_file),
        ]

        started = time.time()

        proc = subprocess.run(
            cmd,
            input=artifact_prompt,
            cwd=workspace,
            text=True,
            capture_output=True,
        )

        elapsed = time.time() - started

        meta = {
            "model": self.name,
            "command": cmd,
            "returncode": proc.returncode,
            "elapsed_seconds": round(elapsed, 3),
            "stdout": proc.stdout[-20000:],
            "stderr": proc.stderr[-10000:],
        }

        if proc.returncode != 0:
            (workspace / ".generation.json").write_text(
                json.dumps(meta, indent=2),
                encoding="utf-8",
            )

            raise GenerationError(
                f"Codex generation failed: "
                f"{proc.stderr[-4000:] or proc.stdout[-4000:]}"
            )

        if not response_file.exists():
            raise GenerationError(
                "Codex completed but did not produce "
                f"{response_file.name}"
            )

        result = response_file.read_text(
            encoding="utf-8",
            errors="replace",
        )

        html = _strip_code_fence(result)

        if "<html" not in html.lower():
            raise GenerationError(
                "Codex completed successfully but did not "
                "return HTML."
            )

        index_path = workspace / "index.html"

        index_path.write_text(
            html,
            encoding="utf-8",
        )

        meta["artifact"] = {
            "type": "html",
            "path": "index.html",
            "bytes": len(html.encode("utf-8")),
        }

        (workspace / ".generation.json").write_text(
            json.dumps(meta, indent=2),
            encoding="utf-8",
        )

        return meta


class MockAdapter(Adapter):
    def __init__(self, name: str, html_path: Path):
        self.name = name
        self.html_path = html_path

    def available(self) -> bool:
        return self.html_path.exists()

    def generate(self, prompt: str, workspace: Path, prompt_file: Path):
        site = workspace / "index.html"

        site.write_text(
            self.html_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        meta = {
            "model": self.name,
            "mock": True,
            "source": str(self.html_path),
        }

        (workspace / ".generation.json").write_text(
            json.dumps(meta, indent=2),
            encoding="utf-8",
        )

        return meta


def get_adapter(name: str):
    root = Path(__file__).resolve().parents[1]

    if name == "claude":
        return ClaudeAdapter()

    if name == "codex":
        return CodexAdapter()

    if name == "mock-a":
        return MockAdapter(
            "Claude (mock)",
            root / "demo_sites/a/index.html",
        )

    if name == "mock-b":
        return MockAdapter(
            "Codex (mock)",
            root / "demo_sites/b/index.html",
        )

    raise ValueError(name)
