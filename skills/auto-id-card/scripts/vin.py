#!/usr/bin/env python3
"""VIN format and check-digit validation.

A wrong VIN on an ID card is worse than no card: the document looks finished and is
useless at the roadside. North American VINs from 1981 on carry a check digit in
position 9, so a transcription slip is usually catchable before anything is printed.
That makes this the cheapest high-value guard in the whole workflow.

Usage:
    python3 vin.py 1FTFW1ED5NFA12345 3C6UR5DL8NG123456
    # or: from vin import check
"""
import sys

TRANSLIT = {**{c: i for i, c in enumerate("0123456789")},
            "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
            "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
            "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9}
WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
CONFUSABLE = {"O": "0", "I": "1", "Q": "0"}


def check(vin):
    """Return (ok, message). ok is False only when the VIN is certainly wrong."""
    v = (vin or "").strip().upper().replace(" ", "").replace("-", "")
    if not v:
        return False, "empty"
    if len(v) != 17:
        return False, f"length {len(v)}, expected 17"
    bad = sorted(set(v) & set("IOQ"))
    if bad:
        hint = ", ".join(f"{c} looks like {CONFUSABLE[c]}" for c in bad)
        return False, f"contains {', '.join(bad)}, which never appear in a VIN ({hint})"
    if any(c not in TRANSLIT for c in v):
        junk = sorted({c for c in v if c not in TRANSLIT})
        return False, f"invalid character(s): {', '.join(junk)}"
    total = sum(TRANSLIT[c] * w for c, w in zip(v, WEIGHTS))
    expect = total % 11
    expect = "X" if expect == 10 else str(expect)
    if v[8] != expect:
        return False, f"check digit is {v[8]}, computed {expect} (likely a transcription error)"
    return True, "ok"


def normalize(vin):
    return (vin or "").strip().upper().replace(" ", "").replace("-", "")


if __name__ == "__main__":
    fail = 0
    for a in sys.argv[1:]:
        ok, msg = check(a)
        print(f"{'PASS' if ok else 'FAIL'}  {normalize(a)}  {msg}")
        fail += 0 if ok else 1
    sys.exit(1 if fail else 0)
