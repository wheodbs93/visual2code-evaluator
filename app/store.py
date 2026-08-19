from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from .models import PairRecord, OutputRecord, rubric_from_dict

ROOT = Path(__file__).resolve().parents[1]

PROMPT_FILE = ROOT / "data/prompts/pairs.json"

DB_PATH = Path(
    os.getenv(
        "DATABASE_PATH",
        str(ROOT / "data" / "visual2code.db"),
    )
)


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        DB_PATH,
        timeout=30,
        check_same_thread=False,
    )

    conn.execute("PRAGMA journal_mode=WAL;")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pair_id TEXT NOT NULL,
            evaluator_id TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )

    conn.commit()
    return conn


def load_pairs(
    path: Path = PROMPT_FILE,
) -> dict[str, PairRecord]:

    raw = json.loads(
        path.read_text()
    ) if path.exists() else {"pairs": []}

    out = {}

    for x in raw.get("pairs", []):
        outputs = {
            k: OutputRecord(**v)
            for k, v in x.get("outputs", {}).items()
        }

        p = PairRecord(
            pair_id=x["pair_id"],
            prompt_id=x["prompt_id"],
            prompt=x["prompt"],
            category=x.get("category", ""),
            complexity=x.get("complexity", ""),
            difficulty=int(x.get("difficulty", 3)),
            strategy=x.get("strategy", ""),
            quality_tier=x.get("quality_tier", ""),
            reference_site_url=x.get("reference_site_url", ""),
            reference_input_dir=x.get("reference_input_dir", ""),
            reference_assets=x.get("reference_assets", []),
            rubric=rubric_from_dict(
                x.get("rubric", [])
            ),
            outputs=outputs,
            status=x.get("status", "NEW"),
        )

        out[p.pair_id] = p

    return out


def save_pairs(
    pairs: dict[str, PairRecord],
    path: Path = PROMPT_FILE,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            {
                "pairs": [
                    p.to_dict()
                    for p in pairs.values()
                ]
            },
            indent=2,
        )
    )


def append_evaluation(data: dict):
    conn = _connect()

    try:
        conn.execute(
            """
            INSERT INTO evaluations (
                pair_id,
                evaluator_id,
                submitted_at,
                payload_json
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                data.get("pair_id", ""),
                data.get("evaluator_id", ""),
                data.get("submitted_at", ""),
                json.dumps(
                    data,
                    ensure_ascii=False,
                ),
            ),
        )

        conn.commit()

    finally:
        conn.close()


def export_evaluations():
    conn = _connect()

    try:
        rows = conn.execute(
            """
            SELECT
                id,
                pair_id,
                evaluator_id,
                submitted_at,
                payload_json
            FROM evaluations
            ORDER BY id
            """
        ).fetchall()

        return [
            {
                "id": row[0],
                "pair_id": row[1],
                "evaluator_id": row[2],
                "submitted_at": row[3],
                "payload": json.loads(row[4]),
            }
            for row in rows
        ]

    finally:
        conn.close()
