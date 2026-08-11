"""Hard rules: deterministic text checks against title + description."""

from briefpulse.checks import run_hard_checks
from briefpulse.models import Campaign, Creator, Video

CAMPAIGN = Campaign(
    name="GlowUp Serum Launch",
    brand="GlowUp",
    required_disclosure=True,
    required_hashtag="#glowuppartner",
    required_mention="GlowUp",
    talking_points=["30-day money-back guarantee"],
    banned_claims=["cures any medical condition"],
    creators=[Creator(handle="@pokimane", name="Pokimane")],
)


def video(title: str, description: str) -> Video:
    return Video(
        video_id="abc123",
        title=title,
        description=description,
        published_at="2026-08-10T09:00:00Z",
        creator_name="Pokimane",
    )


def by_rule(results):
    return {r.rule: r for r in results}


def test_compliant_video_passes_all_three_rules() -> None:
    v = video(
        "GlowUp serum honest review #ad",
        "Trying the GlowUp serum for 30 days. #glowuppartner",
    )
    results = by_rule(run_hard_checks(v, CAMPAIGN))
    assert results["disclosure"].verdict == "pass"
    assert results["hashtag"].verdict == "pass"
    assert results["mention"].verdict == "pass"


def test_missing_disclosure_fails() -> None:
    v = video("GlowUp serum review", "Loving the GlowUp serum #glowuppartner")
    r = by_rule(run_hard_checks(v, CAMPAIGN))["disclosure"]
    assert r.verdict == "fail"
    assert "#ad" in r.reason


def test_sponsored_counts_as_disclosure() -> None:
    v = video("GlowUp review #sponsored", "#glowuppartner GlowUp")
    assert by_rule(run_hard_checks(v, CAMPAIGN))["disclosure"].verdict == "pass"


def test_hashtag_prefix_does_not_count_as_disclosure() -> None:
    # "#adventure" must not satisfy the #ad rule
    v = video("GlowUp #adventure vlog", "GlowUp #glowuppartner")
    assert by_rule(run_hard_checks(v, CAMPAIGN))["disclosure"].verdict == "fail"


def test_checks_are_case_insensitive() -> None:
    v = video("glowup review #AD", "#GlowUpPartner all the glowup facts")
    results = by_rule(run_hard_checks(v, CAMPAIGN))
    assert all(r.verdict == "pass" for r in results.values())


def test_missing_hashtag_and_mention_fail() -> None:
    v = video("serum review #ad", "great serum, link below")
    results = by_rule(run_hard_checks(v, CAMPAIGN))
    assert results["hashtag"].verdict == "fail"
    assert results["mention"].verdict == "fail"


def test_disclosure_rule_skipped_when_not_required() -> None:
    campaign = Campaign(
        name="Organic collab",
        brand="GlowUp",
        required_disclosure=False,
        required_hashtag="#glowuppartner",
        required_mention="GlowUp",
        talking_points=[],
        banned_claims=[],
        creators=[],
    )
    v = video("GlowUp #glowuppartner", "no disclosure here")
    rules = [r.rule for r in run_hard_checks(v, campaign)]
    assert "disclosure" not in rules
