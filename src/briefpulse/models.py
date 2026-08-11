"""Shared value types. Frozen dataclasses; no behavior."""

from dataclasses import dataclass

VERDICTS = ("pass", "fail", "unclear")

# code = deterministic text check, llm = Gemini judgment
RULE_SOURCES = ("code", "llm")


@dataclass(frozen=True)
class Creator:
    handle: str  # YouTube handle, e.g. "@pokimane"
    name: str


@dataclass(frozen=True)
class Campaign:
    name: str
    brand: str
    required_disclosure: bool
    required_hashtag: str
    required_mention: str
    talking_points: list[str]
    banned_claims: list[str]
    creators: list[Creator]


@dataclass(frozen=True)
class Video:
    video_id: str
    title: str
    description: str
    published_at: str  # ISO 8601, as YouTube returns it
    creator_name: str


@dataclass(frozen=True)
class RuleResult:
    rule: str
    source: str  # "code" | "llm"
    verdict: str  # "pass" | "fail" | "unclear"
    reason: str
    evidence: str  # quote the verdict is based on, "" if none
