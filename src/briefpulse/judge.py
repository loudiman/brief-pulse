"""Gemini judges the fuzzy rules: talking points covered, banned claims present.

Contract: the model must return one verdict per rule in LLM_RULES as structured
JSON. parse_verdicts is deliberately defensive — anything malformed degrades to
'unclear' (human looks at it), never to a silent 'pass'.
"""

import json
import os

from .models import Campaign, RuleResult, Video

LLM_RULES = ("talking_points", "banned_claims")

DEFAULT_MODEL = "gemini-2.5-flash"

_RESPONSE_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "rule": {"type": "STRING"},
            "verdict": {"type": "STRING"},
            "reason": {"type": "STRING"},
            "evidence_quote": {"type": "STRING"},
        },
        "required": ["rule", "verdict", "reason"],
    },
}


def build_prompt(video: Video, campaign: Campaign) -> str:
    points = "\n".join(f"- {p}" for p in campaign.talking_points) or "- (none)"
    banned = "\n".join(f"- {b}" for b in campaign.banned_claims) or "- (none)"
    return f"""You are checking a sponsored YouTube post against a campaign brief.
Only the title and description are available — do not assume anything about the video itself.

CAMPAIGN: {campaign.name} (brand: {campaign.brand})

REQUIRED TALKING POINTS (rule "talking_points" — verdict "pass" only if the text covers ALL of them):
{points}

BANNED CLAIMS (rule "banned_claims" — verdict "pass" only if the text contains NONE of them):
{banned}

POST TITLE: {video.title}
POST DESCRIPTION:
{video.description}

Return a JSON array with exactly one object per rule: "talking_points" and "banned_claims".
Each object: rule, verdict ("pass" | "fail" | "unclear"), reason (one sentence),
evidence_quote (exact quote from the post the verdict rests on, or "").
Use "unclear" whenever the text is insufficient to decide."""


def parse_verdicts(raw: list[dict]) -> list[RuleResult]:
    seen: dict[str, RuleResult] = {}
    for item in raw:
        rule = item.get("rule", "")
        if rule not in LLM_RULES or rule in seen:
            continue
        verdict = item.get("verdict", "")
        reason = str(item.get("reason", ""))
        if verdict not in ("pass", "fail", "unclear"):
            reason = f"model returned unknown verdict '{verdict}': {reason}"
            verdict = "unclear"
        seen[rule] = RuleResult(
            rule=rule,
            source="llm",
            verdict=verdict,
            reason=reason,
            evidence=str(item.get("evidence_quote", "")),
        )
    for rule in LLM_RULES:
        if rule not in seen:
            seen[rule] = RuleResult(
                rule=rule,
                source="llm",
                verdict="unclear",
                reason="model returned no verdict for this rule",
                evidence="",
            )
    return [seen[rule] for rule in LLM_RULES]


def judge_video(video: Video, campaign: Campaign, api_key: str) -> list[RuleResult]:
    """Live Gemini call. Kept thin; parse_verdicts holds the logic."""
    from google import genai  # imported here so tests never need the package configured

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=os.environ.get("GEMINI_MODEL", DEFAULT_MODEL),
        contents=build_prompt(video, campaign),
        config={
            "response_mime_type": "application/json",
            "response_schema": _RESPONSE_SCHEMA,
        },
    )
    return parse_verdicts(json.loads(response.text or "[]"))
