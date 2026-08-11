"""Hard compliance rules. Deterministic, no I/O — the LLM never sees these."""

import re

from .models import Campaign, RuleResult, Video

_DISCLOSURE_RE = re.compile(r"#(ad|sponsored)\b", re.IGNORECASE)


def run_hard_checks(video: Video, campaign: Campaign) -> list[RuleResult]:
    text = f"{video.title}\n{video.description}"
    results: list[RuleResult] = []

    if campaign.required_disclosure:
        m = _DISCLOSURE_RE.search(text)
        results.append(
            RuleResult(
                rule="disclosure",
                source="code",
                verdict="pass" if m else "fail",
                reason="disclosure found" if m else "missing #ad or #sponsored disclosure",
                evidence=m.group(0) if m else "",
            )
        )

    hashtag = campaign.required_hashtag
    # \B# would reject mid-word '#', but YouTube hashtags are whitespace-delimited; substring
    # match with a boundary after the tag is enough (avoids #glowuppartnerx matching).
    tag_re = re.compile(re.escape(hashtag) + r"\b", re.IGNORECASE)
    tag_match = tag_re.search(text)
    results.append(
        RuleResult(
            rule="hashtag",
            source="code",
            verdict="pass" if tag_match else "fail",
            reason=f"{hashtag} found" if tag_match else f"missing campaign hashtag {hashtag}",
            evidence=tag_match.group(0) if tag_match else "",
        )
    )

    mention = campaign.required_mention
    found = mention.casefold() in text.casefold()
    results.append(
        RuleResult(
            rule="mention",
            source="code",
            verdict="pass" if found else "fail",
            reason=f"brand '{mention}' mentioned" if found else f"brand '{mention}' not mentioned",
            evidence=mention if found else "",
        )
    )
    return results
