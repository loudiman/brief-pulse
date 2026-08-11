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


def test_flags_are_listed_with_creator_title_and_reason() -> None:
    flags = [
        flag(
            "Pokimane",
            "my morning routine",
            "disclosure",
            "fail",
            "missing #ad or #sponsored disclosure",
        ),
        flag("xQc", "serum reaction", "talking_points", "unclear", "model returned no verdict"),
    ]
    text = build_digest("2026-08-12", checked=10, creators=2, flags=flags, failures=[])
    assert "2 flags" in text
    assert (
        "⚠️ Pokimane — “my morning routine” — disclosure: missing #ad or #sponsored disclosure"
        in text
    )
    assert "❔ xQc" in text  # unclear gets its own marker


def test_failures_are_listed_by_creator() -> None:
    text = build_digest(
        "2026-08-12", checked=5, creators=2, flags=[], failures=["@xQcOW: HTTP 403 from YouTube"]
    )
    assert "Failures this run:" in text
    assert "@xQcOW: HTTP 403 from YouTube" in text
    assert "none" not in text.split("Failures this run:")[1]
