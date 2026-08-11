"""SQLite store. UNIQUE(video_id, rule) + upsert makes daily re-runs idempotent."""

import sqlite3
from pathlib import Path

from .models import RuleResult, Video

_SCHEMA = """
CREATE TABLE IF NOT EXISTS results (
    video_id   TEXT NOT NULL,
    rule       TEXT NOT NULL,
    run_date   TEXT NOT NULL,
    campaign   TEXT NOT NULL,
    creator    TEXT NOT NULL,
    source     TEXT NOT NULL,
    verdict    TEXT NOT NULL,
    reason     TEXT NOT NULL,
    evidence   TEXT NOT NULL,
    UNIQUE (video_id, rule)
);
CREATE TABLE IF NOT EXISTS runs (
    id       INTEGER PRIMARY KEY,
    run_date TEXT NOT NULL,
    checked  INTEGER NOT NULL,
    flags    INTEGER NOT NULL,
    failures INTEGER NOT NULL
);
"""


def connect(path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript(_SCHEMA)
    return conn


def write_results(
    conn: sqlite3.Connection, run_date: str, campaign: str, video: Video, results: list[RuleResult]
) -> None:
    conn.executemany(
        """INSERT INTO results (video_id, rule, run_date, campaign, creator, source, verdict, reason, evidence)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT (video_id, rule) DO UPDATE SET
               run_date = excluded.run_date,
               verdict  = excluded.verdict,
               reason   = excluded.reason,
               evidence = excluded.evidence""",
        [
            (
                video.video_id,
                r.rule,
                run_date,
                campaign,
                video.creator_name,
                r.source,
                r.verdict,
                r.reason,
                r.evidence,
            )
            for r in results
        ],
    )
    conn.commit()


def write_run(
    conn: sqlite3.Connection, run_date: str, checked: int, flags: int, failures: int
) -> None:
    conn.execute(
        "INSERT INTO runs (run_date, checked, flags, failures) VALUES (?, ?, ?, ?)",
        (run_date, checked, flags, failures),
    )
    conn.commit()


def count_results(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
