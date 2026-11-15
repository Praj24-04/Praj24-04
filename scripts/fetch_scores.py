#!/usr/bin/env python3
"""Refresh data/scores.json from the GitHub GraphQL API (stdlib only).

Env:
  GH_TOKEN             required. The workflow's built-in GITHUB_TOKEN is enough.
  MONKEYTYPE_APE_KEY   optional. Adds the TYPING SPEED row (60s personal best).
"""

import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCORES = ROOT / "data" / "scores.json"
LOGIN = json.loads((ROOT / "data" / "profile.json").read_text())["login"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes { name url description stargazerCount pushedAt }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount } }
      }
    }
  }
}
"""


def get_json(url, headers, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "readme-arcade", **headers})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def longest_streak(weeks):
    best = run = 0
    for week in weeks:
        for day in week["contributionDays"]:
            run = run + 1 if day["contributionCount"] else 0
            best = max(best, run)
    return best


def typing_speed(key):
    """Best 60-second WPM from Monkeytype, or None if anything goes wrong."""
    try:
        res = get_json(
            "https://api.monkeytype.com/users/personalBests?mode=time&mode2=60",
            {"Authorization": f"ApeKey {key}"},
        )
        data = res.get("data") or []
        if isinstance(data, dict):  # API returns {"60": [...]} when mode2 is omitted
            data = [pb for group in data.values() for pb in group]
        return round(max(pb["wpm"] for pb in data)) if data else None
    except Exception as e:  # never fail the daily save over a vanity stat
        print(f"monkeytype: skipped ({e})", file=sys.stderr)
        return None


def main():
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GH_TOKEN is not set")
    res = get_json(
        "https://api.github.com/graphql",
        {"Authorization": f"bearer {token}"},
        {"query": QUERY, "variables": {"login": LOGIN}},
    )
    if res.get("errors"):
        sys.exit(f"GraphQL error: {res['errors']}")
    user = res["data"]["user"]
    repos = user["repositories"]
    cal = user["contributionsCollection"]["contributionCalendar"]

    scores = json.loads(SCORES.read_text()) if SCORES.exists() else {}
    scores.update(
        saved=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        contributions=cal["totalContributions"],
        streak=longest_streak(cal["weeks"]),
        repos=repos["totalCount"],
        stars=sum(r["stargazerCount"] for r in repos["nodes"]),
        followers=user["followers"]["totalCount"],
        recent=[
            {"name": r["name"], "url": r["url"], "description": r["description"] or "", "pushed": r["pushedAt"][:10]}
            for r in repos["nodes"] if r["name"].lower() != LOGIN.lower()
        ][:3],
    )
    key = os.environ.get("MONKEYTYPE_APE_KEY")
    if key:
        scores["wpm"] = typing_speed(key) or scores.get("wpm")
    SCORES.write_text(json.dumps(scores, indent=2) + "\n")
    print(json.dumps({k: v for k, v in scores.items() if k != "recent"}))


if __name__ == "__main__":
    main()
