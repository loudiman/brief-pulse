"""Discord digest. Always posts — silence would be indistinguishable from breakage."""

from dataclasses import dataclass

import requests

from .models import RuleResult

_DISCORD_LIMIT = 2000


@dataclass(frozen=True)
class Flag:
    creator: str
    video_title: str
    video_id: str
    result: RuleResult


def build_digest(
    run_date: str, checked: int, creators: int, flags: list[Flag], failures: list[str]
) -> str:
    lines = [f"BriefPulse digest — {run_date}"]
    # one line per video, not per rule — a real sweep flags most non-campaign posts
    # on several rules at once and a per-rule digest drowns the reader
    videos: dict[tuple[str, str, str], list] = {}
    for f in flags:
        videos.setdefault((f.creator, f.video_id, f.video_title), []).append(f.result)
    summary = f"checked {checked} posts across {creators} creators"
    lines.append(f"{summary} — {len(videos)} flagged" if videos else f"{summary} — all clear ✅")
    for (creator, _video_id, title), results in videos.items():
        marker = "⚠️" if any(r.verdict == "fail" for r in results) else "❔"
        parts = ", ".join(
            r.rule if r.source == "code" else f"{r.rule} ({r.reason})" for r in results
        )
        lines.append(f"{marker} {creator} — “{title}” — {parts}")
    if failures:
        lines.append("Failures this run:")
        lines.extend(f"  {f}" for f in failures)
    else:
        lines.append("Failures this run: none")
    return "\n".join(lines)


def post_digest(webhook_url: str, text: str) -> None:
    if len(text) > _DISCORD_LIMIT:
        cut = text.rfind("\n", 0, _DISCORD_LIMIT - 15)
        if cut == -1:
            cut = _DISCORD_LIMIT - 15
        text = text[:cut] + "\n…(truncated)"
    response = requests.post(webhook_url, json={"content": text}, timeout=20)
    response.raise_for_status()
