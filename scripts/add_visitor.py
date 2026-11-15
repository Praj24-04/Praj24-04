#!/usr/bin/env python3
"""Handle an "INSERT COIN: ABC" issue: add the visitor's initials to the board.

The issue title is untrusted input. It arrives through the ISSUE_TITLE env var
(never interpolated into shell) and must match exactly three A-Z/0-9 chars.
Prints the reply for the workflow to post as an issue comment.
"""

import datetime as dt
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "data" / "visitors.json"
KEEP = 60  # entries stored; the SVG shows the newest 21

BLOCKED = {"ASS", "FUK", "FUC", "FCK", "FAG", "KKK", "NIG", "SEX", "CUM", "TIT", "DIK", "DIC", "COK", "WTF", "JEW", "GAY", "XXX"}
SECRETS = {  # easter eggs
    "CAT": "Biscuit has reviewed your application and approves. You may pet the README.",
    "MEW": "Biscuit says mew back. That is the highest honour available here.",
    "AAA": "Ah, the classic 'I mashed the button' entry. Respect for tradition.",
    "GIT": "git commit -m 'signed the guestbook'. Clean history, nice.",
    "BUG": "It's not a bug, it's an undocumented high score.",
}
RESERVED = {"PRJ": "Nice try. That slot belongs to the developer.", "BIS": "That slot belongs to the cat. The cat does not share."}


def main():
    title = os.environ.get("ISSUE_TITLE", "")
    user = os.environ.get("ISSUE_USER", "anonymous")
    m = re.fullmatch(r"\s*INSERT COIN\s*:\s*([A-Za-z0-9]{3})\s*", title)
    if not m:
        print("COIN REJECTED. The title has to be exactly `INSERT COIN: ABC` with three letters or digits. Try again?")
        return
    initials = m.group(1).upper()
    if initials in BLOCKED:
        print("COIN REJECTED. The arcade owner's mum reads this board. Pick different initials?")
        return
    if initials in RESERVED:
        print(f"COIN REJECTED. {RESERVED[initials]}")
        return

    board = json.loads(BOARD.read_text())
    players = [p for p in board["players"] if p.get("user") != user]  # one slot per visitor
    returning = len(players) != len(board["players"])
    players.append({"initials": initials, "user": user, "date": dt.date.today().isoformat()})
    board["players"] = players[-KEEP:]
    if not returning:
        board["coins"] = board.get("coins", 0) + 1
    BOARD.write_text(json.dumps(board, indent=2) + "\n")

    msg = f"COIN ACCEPTED. **{initials}** is on the board" + (" (your old entry was replaced)." if returning else ".")
    if initials in SECRETS:
        msg += f"\n\nSECRET FOUND: {SECRETS[initials]}"
    print(msg + "\n\nThanks for playing. The README updates in about a minute.")


if __name__ == "__main__":
    main()
