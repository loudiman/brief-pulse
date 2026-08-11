"""SQLite store: re-running the same day must not duplicate rows."""

from pathlib import Path

from briefpulse.db import connect, count_results, write_results, write_run
from briefpulse.models import RuleResult, Video

VIDEO = Video(
    video_id="abc123",
    title="GlowUp review #ad",
    description="#glowuppartner",
    published_at="2026-08-10T09:00:00Z",
    creator_name="Pokimane",
)

RESULTS = [
    RuleResult(
        rule="disclosure", source="code", verdict="pass", reason="disclosure found", evidence="#ad"
    ),
    RuleResult(rule="hashtag", source="code", verdict="fail", reason="missing tag", evidence=""),
]


def test_rerun_same_day_is_idempotent(tmp_path: Path) -> None:
    conn = connect(tmp_path / "t.db")
    write_results(conn, "2026-08-12", "GlowUp Serum Launch", VIDEO, RESULTS)
    write_results(conn, "2026-08-12", "GlowUp Serum Launch", VIDEO, RESULTS)
    assert count_results(conn) == 2  # one row per rule, not four


def test_rerun_updates_verdict_in_place(tmp_path: Path) -> None:
    conn = connect(tmp_path / "t.db")
    write_results(conn, "2026-08-12", "GlowUp Serum Launch", VIDEO, RESULTS)
    fixed = [
        RuleResult(
            rule="hashtag",
            source="code",
            verdict="pass",
            reason="tag added",
            evidence="#glowuppartner",
        )
    ]
    write_results(conn, "2026-08-12", "GlowUp Serum Launch", VIDEO, fixed)
    row = conn.execute(
        "SELECT verdict FROM results WHERE video_id = ? AND rule = 'hashtag'", (VIDEO.video_id,)
    ).fetchone()
    assert row[0] == "pass"


def test_run_row_records_summary(tmp_path: Path) -> None:
    conn = connect(tmp_path / "t.db")
    write_run(conn, "2026-08-12", checked=10, flags=2, failures=1)
    row = conn.execute("SELECT run_date, checked, flags, failures FROM runs").fetchone()
    assert tuple(row) == ("2026-08-12", 10, 2, 1)
