"""campaigns.yaml loading and validation."""

from pathlib import Path

import pytest

from briefpulse.config import ConfigError, load_campaigns

GOOD = """
campaigns:
  - name: GlowUp Serum Launch
    brand: GlowUp
    required_disclosure: true
    required_hashtag: "#glowuppartner"
    required_mention: "GlowUp"
    talking_points:
      - 30-day money-back guarantee
    banned_claims:
      - guaranteed income
    creators:
      - handle: "@pokimane"
        name: Pokimane
"""


def write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "campaigns.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_loads_a_valid_campaign(tmp_path: Path) -> None:
    campaigns = load_campaigns(write(tmp_path, GOOD))
    assert len(campaigns) == 1
    c = campaigns[0]
    assert c.name == "GlowUp Serum Launch"
    assert c.required_hashtag == "#glowuppartner"
    assert c.creators[0].handle == "@pokimane"


def test_missing_required_key_names_the_key_and_campaign(tmp_path: Path) -> None:
    broken = GOOD.replace('    required_hashtag: "#glowuppartner"\n', "")
    with pytest.raises(ConfigError, match="required_hashtag"):
        load_campaigns(write(tmp_path, broken))


def test_campaign_without_creators_is_rejected(tmp_path: Path) -> None:
    broken = GOOD.split("    creators:")[0]
    with pytest.raises(ConfigError, match="creators"):
        load_campaigns(write(tmp_path, broken))


def test_empty_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="campaigns"):
        load_campaigns(write(tmp_path, ""))
