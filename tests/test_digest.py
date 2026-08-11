"""Discord digest text. Always posts; flags and unclears listed; failures named."""

from briefpulse.models import RuleResult
from briefpulse.notify import Flag, build_digest


def flag(creator: str, title: str, rule: str, verdict: str, reason: str) -> Flag:
    return Flag(
        creator=creator,
        video_title=title,
        video_id="vid1",
        result=RuleResult(rule=rule, source="code", verdict=verdict, reason=reason, evidence=""),
    )


def test_all_clear_digest_still_says_something() -> None:
    text = build_digest("2026-08-12", checked=10, creators=2, flags=[], failures=[])
    assert "2026-08-12" in text
    assert "checked 10 posts across 2 creators" in text
    assert "all clear" in text
    assert "Failures this run: none" in text


def test_flags_grouped_one_line_per_video() -> None:
    flags = [
        flag(
            "Pokimane",
            "my morning routine",
            "disclosure",
            "fail",
            "missing #ad or #sponsored disclosure",
        ),
        flag("Pokimane", "my morning routine", "hashtag", "fail", "missing campaign hashtag"),
        Flag(
            creator="Pokimane",
            video_title="my morning routine",
            video_id="vid1",
            result=RuleResult(
                rule="talking_points",
                source="llm",
                verdict="fail",
                reason="guarantee not covered",
                evidence="",
            ),
        ),
    ]
    text = build_digest("2026-08-12", checked=10, creators=2, flags=flags, failures=[])
    assert "1 flagged" in text
    # one grouped line: hard rules by name, LLM rules with their reason
    assert (
        "⚠️ Pokimane — “my morning routine” — disclosure, hashtag, talking_points (guarantee not covered)"
        in text
    )
    assert text.count("my morning routine") == 1


def test_video_with_only_unclear_rules_gets_question_marker() -> None:
    flags = [
        Flag(
            creator="xQc",
            video_title="serum reaction",
            video_id="vid2",
            result=RuleResult(
                rule="banned_claims",
                source="llm",
                verdict="unclear",
                reason="text too short",
                evidence="",
            ),
        )
    ]
    text = build_digest("2026-08-12", checked=5, creators=1, flags=flags, failures=[])
    assert "❔ xQc — “serum reaction” — banned_claims (text too short)" in text


def test_failures_are_listed_by_creator() -> None:
    text = build_digest(
        "2026-08-12", checked=5, creators=2, flags=[], failures=["@xQcOW: HTTP 403 from YouTube"]
    )
    assert "Failures this run:" in text
    assert "@xQcOW: HTTP 403 from YouTube" in text
    assert "none" not in text.split("Failures this run:")[1]
