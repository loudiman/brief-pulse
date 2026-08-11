"""Discord digest. Always posts — silence would be indistinguishable from breakage."""

from dataclasses import dataclass

import requests

from .models import RuleResult

_MARKER = {"fail": "⚠️", "unclear": "❔"}
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
    summary = f"checked {checked} posts across {creators} creators"
    lines.append(f"{summary} — {len(flags)} flags" if flags else f"{summary} — all clear ✅")
    for f in flags:
        marker = _MARKER.get(f.result.verdict, "⚠️")
        lines.append(
            f"{marker} {f.creator} — “{f.video_title}” — {f.result.rule}: {f.result.reason}"
        )
    if failures:
        lines.append("Failures this run:")
        lines.extend(f"  {f}" for f in failures)
    else:
        lines.append("Failures this run: none")
    return "\n".join(lines)


def post_digest(webhook_url: str, text: str) -> None:
    if len(text) > _DISCORD_LIMIT:
        text = text[: _DISCORD_LIMIT - 20] + "\n…(truncated)"
    response = requests.post(webhook_url, json={"content": text}, timeout=20)
    response.raise_for_status()
