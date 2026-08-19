from __future__ import annotations
import os, shutil, socket, subprocess, time
from pathlib import Path
from urllib.request import urlopen

class RenderError(RuntimeError):
    pass

ROOT = Path(__file__).resolve().parents[1]
RENDER_ROOT = Path(os.getenv("RENDER_ROOT", ROOT / "renders"))


def free_port(host="127.0.0.1"):
    s = socket.socket(); s.bind((host, 0)); p = s.getsockname()[1]; s.close(); return p


def detect_and_build(workspace: Path):
    if (workspace / "index.html").exists():
        return {"type": "static", "served_path": workspace}
    pkg = workspace / "package.json"
    if pkg.exists():
        return {"type": "node", "served_path": workspace}
    raise RenderError("No index.html or package.json found")


def publish_static(pair_id: str, output_key: str, workspace: Path):
    dest = RENDER_ROOT / pair_id / output_key
    if dest.exists(): shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    source = workspace
    if (workspace / "dist").exists(): source = workspace / "dist"
    elif (workspace / "build").exists(): source = workspace / "build"
    for item in source.iterdir():
        target = dest / item.name
        if item.is_dir(): shutil.copytree(item, target)
        else: shutil.copy2(item, target)
    return dest


def smoke_check(url: str, timeout=10):
    try:
        with urlopen(url, timeout=timeout) as r:
            body = r.read(2000)
            return {"ok": 200 <= r.status < 400, "status": r.status, "bytes_sampled": len(body)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
