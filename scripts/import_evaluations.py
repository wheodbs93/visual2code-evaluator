from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

import psycopg


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/import_evaluations.py <csv-path>")
        return 1

    csv_path = Path(sys.argv[1]).expanduser()

    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        return 1

    database_url = os.getenv("DATABASE_URL", "").strip()

    if not database_url:
        print("DATABASE_URL is not set.")
        return 1

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    print(f"Found {len(rows)} CSV evaluations.")

    if not rows:
        print("Nothing to import.")
        return 0

    with psycopg.connect(database_url) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluations (
                id BIGSERIAL PRIMARY KEY,
                pair_id TEXT NOT NULL,
                evaluator_id TEXT NOT NULL,
                submitted_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )

        existing = conn.execute(
            "SELECT COUNT(*) FROM evaluations"
        ).fetchone()[0]

        print(f"Postgres currently contains {existing} evaluations.")

        inserted = 0
        skipped = 0

        for row in rows:
            pair_id = (row.get("pair_id") or "").strip()
            evaluator_id = (row.get("evaluator_id") or "").strip()
            submitted_at = (row.get("submitted_at") or "").strip()

            if not pair_id or not evaluator_id or not submitted_at:
                print("Skipping malformed row:", row.get("id", ""))
                skipped += 1
                continue

            exists = conn.execute(
                """
                SELECT 1
                FROM evaluations
                WHERE pair_id = %s
                  AND evaluator_id = %s
                  AND submitted_at = %s
                LIMIT 1
                """,
                (pair_id, evaluator_id, submitted_at),
            ).fetchone()

            if exists:
                skipped += 1
                continue

            answers = {}

            for key, value in row.items():
                if key in {
                    "id",
                    "pair_id",
                    "evaluator_id",
                    "submitted_at",
                }:
                    continue

                if value not in (None, ""):
                    answers[key] = value

            payload = {
                "pair_id": pair_id,
                "evaluator_id": evaluator_id,
                "submitted_at": submitted_at,
                "answers": answers,
                "migrated_from_csv": True,
            }

            conn.execute(
                """
                INSERT INTO evaluations (
                    pair_id,
                    evaluator_id,
                    submitted_at,
                    payload_json
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    pair_id,
                    evaluator_id,
                    submitted_at,
                    json.dumps(payload, ensure_ascii=False),
                ),
            )

            inserted += 1

        conn.commit()

        total = conn.execute(
            "SELECT COUNT(*) FROM evaluations"
        ).fetchone()[0]

        print(f"Inserted: {inserted}")
        print(f"Skipped existing/malformed: {skipped}")
        print(f"Postgres total: {total}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
