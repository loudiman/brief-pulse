"""`briefpulse check` — the daily pipeline: pull → check → store → notify.

Per-creator failure isolation: one broken creator never kills the run; it lands
in the digest's failures section instead. Exit code 1 when any creator failed,
so the scheduled GitHub Actions run shows red.
"""

import argparse
import logging
import os
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from . import checks, db, judge, notify, youtube
from .config import DEFAULT_CONFIG_PATH, load_campaigns
from .models import Campaign, RuleResult, Video

log = logging.getLogger("briefpulse")

FetchFn = Callable[[str, str, str], list[Video]]
JudgeFn = Callable[[Video, Campaign, str], list[RuleResult]]
PostFn = Callable[[str, str], None]


def load_env(path: Path = Path(".env")) -> None:
    """Tiny KEY=VALUE loader; never overrides variables already set."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def run_check(
    config_path: Path,
    db_path: Path,
    dry_run: bool,
    fetch: FetchFn = youtube.fetch_latest_videos,
    judge_fn: JudgeFn = judge.judge_video,
    post: PostFn = notify.post_digest,
) -> int:
    youtube_key = os.environ.get("YOUTUBE_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "")
    missing = [
        name
        for name, value in [("YOUTUBE_API_KEY", youtube_key), ("GEMINI_API_KEY", gemini_key)]
        if not value
    ]
    if not dry_run and not webhook_url:
        missing.append("DISCORD_WEBHOOK_URL")
    if missing:
        log.error("missing environment variables: %s (see .env.example)", ", ".join(missing))
        return 2

    campaigns = load_campaigns(config_path)
    conn = db.connect(db_path)
    run_date = datetime.now(UTC).date().isoformat()

    checked = 0
    creator_count = 0
    flags: list[notify.Flag] = []
    failures: list[str] = []

    for campaign in campaigns:
        for creator in campaign.creators:
            creator_count += 1
            try:
                videos = fetch(youtube_key, creator.handle, creator.name)
                for video in videos:
                    results = checks.run_hard_checks(video, campaign)
                    results += judge_fn(video, campaign, gemini_key)
                    db.write_results(conn, run_date, campaign.name, video, results)
                    checked += 1
                    flags.extend(
                        notify.Flag(creator.name, video.title, video.video_id, r)
                        for r in results
                        if r.verdict != "pass"
                    )
                log.info("checked %s: %d videos", creator.handle, len(videos))
            except Exception as exc:  # noqa: BLE001 — isolation boundary: any one creator's failure must reach the digest, not kill the run
                log.warning("creator %s failed: %s", creator.handle, exc)
                failures.append(f"{creator.handle}: {exc}")

    db.write_run(conn, run_date, checked=checked, flags=len(flags), failures=len(failures))
    digest = notify.build_digest(run_date, checked, creator_count, flags, failures)
    if dry_run:
        print(digest)
    else:
        post(webhook_url, digest)
        log.info("digest posted to Discord")
    return 1 if failures else 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_env()
    parser = argparse.ArgumentParser(prog="briefpulse")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="run the daily compliance check")
    check.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    check.add_argument(
        "--db", type=Path, default=Path(os.environ.get("BRIEFPULSE_DB", "briefpulse.db"))
    )
    check.add_argument("--dry-run", action="store_true", help="print the digest instead of posting")
    args = parser.parse_args()
    return run_check(args.config, args.db, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
