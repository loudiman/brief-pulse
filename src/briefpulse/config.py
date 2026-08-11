"""Load and validate campaigns.yaml. Fail loudly with the exact missing key."""

from pathlib import Path

import yaml

from .models import Campaign, Creator

DEFAULT_CONFIG_PATH = Path("campaigns.yaml")


class ConfigError(Exception):
    pass


def _require(entry: dict, key: str, campaign_name: str) -> object:
    if key not in entry:
        raise ConfigError(f"campaign '{campaign_name}': missing required key '{key}'")
    return entry[key]


def load_campaigns(path: Path) -> list[Campaign]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("campaigns"), list):
        raise ConfigError(f"{path}: expected a top-level 'campaigns' list")

    campaigns: list[Campaign] = []
    for entry in raw["campaigns"]:
        name = entry.get("name", "<unnamed>")
        creators_raw = _require(entry, "creators", name)
        if not isinstance(creators_raw, list) or not creators_raw:
            raise ConfigError(f"campaign '{name}': 'creators' must be a non-empty list")
        campaigns.append(
            Campaign(
                name=str(_require(entry, "name", name)),
                brand=str(_require(entry, "brand", name)),
                required_disclosure=bool(entry.get("required_disclosure", True)),
                required_hashtag=str(_require(entry, "required_hashtag", name)),
                required_mention=str(_require(entry, "required_mention", name)),
                talking_points=[str(t) for t in entry.get("talking_points", [])],
                banned_claims=[str(b) for b in entry.get("banned_claims", [])],
                creators=[
                    Creator(
                        handle=str(_require(c, "handle", name)),
                        name=str(c.get("name", c.get("handle", "?"))),
                    )
                    for c in creators_raw
                ],
            )
        )
    if not campaigns:
        raise ConfigError(f"{path}: 'campaigns' list is empty")
    return campaigns
