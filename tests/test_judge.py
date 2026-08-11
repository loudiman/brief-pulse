"""LLM verdict parsing: Gemini's structured output → RuleResult, defensively.

The live API call is a thin adapter and is not tested here. These tests pin the
contract: exactly the two LLM rules come back, bad verdicts degrade to 'unclear',
and a missing rule is 'unclear' — never silently 'pass'.
"""

from briefpulse.judge import LLM_RULES, parse_verdicts

GOOD_RESPONSE = [
    {
        "rule": "talking_points",
        "verdict": "fail",
        "reason": "Neither the guarantee nor the formula is mentioned.",
        "evidence_quote": "",
    },
    {
        "rule": "banned_claims",
        "verdict": "pass",
        "reason": "No banned claims present.",
        "evidence_quote": "",
    },
]


def by_rule(results):
    return {r.rule: r for r in results}


def test_good_response_maps_to_rule_results() -> None:
    results = parse_verdicts(GOOD_RESPONSE)
    assert {r.rule for r in results} == set(LLM_RULES)
    assert by_rule(results)["talking_points"].verdict == "fail"
    assert by_rule(results)["banned_claims"].verdict == "pass"
    assert all(r.source == "llm" for r in results)


def test_unknown_verdict_degrades_to_unclear() -> None:
    bad = [dict(GOOD_RESPONSE[0], verdict="maybe"), GOOD_RESPONSE[1]]
    r = by_rule(parse_verdicts(bad))["talking_points"]
    assert r.verdict == "unclear"
    assert "maybe" in r.reason


def test_missing_rule_becomes_unclear_not_pass() -> None:
    only_one = [GOOD_RESPONSE[1]]  # banned_claims only
    r = by_rule(parse_verdicts(only_one))["talking_points"]
    assert r.verdict == "unclear"
    assert "no verdict" in r.reason


def test_unexpected_extra_rule_is_dropped() -> None:
    extra = GOOD_RESPONSE + [dict(GOOD_RESPONSE[0], rule="vibes")]
    assert {r.rule for r in parse_verdicts(extra)} == set(LLM_RULES)


def test_duplicate_rule_keeps_first() -> None:
    dupe = [GOOD_RESPONSE[0], dict(GOOD_RESPONSE[0], verdict="pass"), GOOD_RESPONSE[1]]
    assert by_rule(parse_verdicts(dupe))["talking_points"].verdict == "fail"
