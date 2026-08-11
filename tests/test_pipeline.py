"""End-to-end pipeline with fake adapters: pull → check → store → notify."""

from pathlib import Path

from briefpulse.cli import run_check
from briefpulse.db import connect, count_results
from briefpulse.models import RuleResult, Video

CONFIG = """
campaigns:
  - name: GlowUp Serum Launch
    brand: GlowUp
    required_hashtag: "#glowuppartner"
    required_mention: "GlowUp"
    talking_points: [30-day money-back guarantee]
    banned_claims: [guaranteed income]
    creators:
      - handle: "@pokimane"
        name: Pokimane
      - handle: "@broken"
        name: Broken
"""

VIDEO = Video(
    video_id="vid1",
    title="GlowUp review #ad",
    description="#glowuppartner 30-day money-back guarantee",
    published_at="2026-08-10T09:00:00Z",
    creator_name="Pokimane",
)


def fake_fetch(api_key: str, handle: str, name: str) -> list[Video]:
    if handle == "@broken":
        raise RuntimeError("HTTP 403 from YouTube")
    return [VIDEO]


def fake_judge(video, campaign, api_key) -> list[RuleResult]:
    return [
        RuleResult("talking_points", "llm", "pass", "covered", ""),
        RuleResult("banned_claims", "llm", "fail", "income promise", "get rich"),
    ]


def test_pipeline_stores_flags_and_isolates_failures(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("YOUTUBE_API_KEY", "x")
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.example/webhook")
    config = tmp_path / "campaigns.yaml"
    config.write_text(CONFIG, encoding="utf-8")
    db_path = tmp_path / "t.db"
    posted: list[str] = []

    exit_code = run_check(
        config,
        db_path,
        dry_run=False,
        fetch=fake_fetch,
        judge_fn=fake_judge,
        post=lambda url, text: posted.append(text),
    )

    assert exit_code == 1  # one creator failed
    assert count_results(connect(db_path)) == 5  # 3 hard + 2 llm rules for one video
    assert len(posted) == 1
    digest = posted[0]
    assert "banned_claims: income promise" in digest
    assert "@broken: HTTP 403 from YouTube" in digest


def test_missing_env_refuses_to_run(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    config = tmp_path / "campaigns.yaml"
    config.write_text(CONFIG, encoding="utf-8")
    assert run_check(config, tmp_path / "t.db", dry_run=True) == 2
