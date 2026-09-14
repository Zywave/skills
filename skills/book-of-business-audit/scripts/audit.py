#!/usr/bin/env python3
"""Book of business audit.

Input: accounts.json and contacts.json — each a JSON array (or JSON-lines) of
records as returned in the `items` arrays of Zywave account_search and
account_contact_search. Output: an .xlsx workbook with Summary, Findings,
Duplicates and Accounts tabs. Read-only; touches nothing in Zywave.

Usage:
  python3 audit.py --accounts accounts.json --contacts contacts.json \
      --out audit.xlsx [--stale-months 18]
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
except ImportError:  # pragma: no cover
    sys.exit("openpyxl is required: pip install openpyxl --break-system-packages")


# ----------------------------------------------------------------- loading

def load_records(path):
    """Accept a JSON array, a {items:[...]} object, or JSON-lines of either."""
    text = open(path, encoding="utf-8").read().strip()
    if not text:
        return []
    out = []
    try:
        data = json.loads(text)
        blobs = [data]
    except json.JSONDecodeError:
        blobs = [json.loads(line) for line in text.splitlines() if line.strip()]
    for b in blobs:
        if isinstance(b, dict) and "items" in b:
            out.extend(b["items"])
        elif isinstance(b, list):
            for x in b:
                if isinstance(x, dict) and "items" in x:
                    out.extend(x["items"])
                else:
                    out.append(x)
        elif isinstance(b, dict):
            out.append(b)
    return out


# ----------------------------------------------------------------- helpers

SUFFIXES = r"\b(inc|incorporated|llc|l\.l\.c\.|ltd|limited|co|corp|corporation|company|lp|llp|plc|pc|pllc|the)\b"


def norm_name(s):
    s = (s or "").lower()
    s = re.sub(r"[&]", " and ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(SUFFIXES, " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_phone(s):
    d = re.sub(r"\D", "", s or "")
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
    return d if len(d) >= 10 else ""


def norm_email(s):
    return (s or "").strip().lower()


def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def is_prospect(acct):
    lobs = acct.get("linesOfBusiness") or []
    return bool(lobs) and all("prospect" in str(l).lower() for l in lobs)


def completeness(acct, contacts):
    score = 0
    for k in ("addressLine1", "city", "state", "postalCode", "primaryPhone", "classification", "msid"):
        if acct.get(k):
            score += 1
    score += min(len(contacts), 5)
    score += 2 if any(c.get("emailAddress") for c in contacts) else 0
    return score


# ------------------------------------------------------------------ checks

SEVERITY = {
    "NO_CONTACT": "High", "NO_EMAIL": "High", "PROSPECT_NO_CONTACT": "High",
    "DUP_ACCOUNT_NAME": "Medium", "DUP_ACCOUNT_PHONE": "Medium", "NO_PRIMARY": "Medium",
    "INACTIVE_NOT_ARCHIVED": "Medium", "DUP_CONTACT": "Medium",
    "EMAIL_NOT_ALLOWED": "Low", "STALE": "Low", "INCOMPLETE_ADDRESS": "Low", "NO_CLASSIFICATION": "Low",
}


def run_checks(accounts, contacts, stale_months):
    accounts = [a for a in accounts if not a.get("isArchived")]
    contacts = [c for c in contacts if not c.get("isArchived")]
    by_acct = defaultdict(list)
    for c in contacts:
        by_acct[c.get("accountId")].append(c)

    findings = []          # (accountId, name, check, severity, detail)
    dup_sets = []          # (set_id, check, key, [accounts])
    acct_rows = []
    have_updated = any(a.get("updatedDateTime") for a in accounts)
    cutoff = datetime.now(timezone.utc) - timedelta(days=30 * stale_months)

    def add(a, check, detail=""):
        findings.append((a.get("id"), a.get("name"), check, SEVERITY[check], detail))

    for a in accounts:
        cs = by_acct.get(a.get("id"), [])
        active = [c for c in cs if c.get("isActive", True)]
        emailed = [c for c in active if norm_email(c.get("emailAddress"))]
        allowed = [c for c in emailed if c.get("isEmailAllowed", True)]
        primary = [c for c in active if c.get("isPrimaryContact")]
        prospect = is_prospect(a)
        flags = []

        if a.get("isActive", True):
            if not active:
                add(a, "PROSPECT_NO_CONTACT" if prospect else "NO_CONTACT"); flags.append("NO_CONTACT")
            else:
                if not primary:
                    add(a, "NO_PRIMARY", f"{len(active)} active contact(s), none primary"); flags.append("NO_PRIMARY")
                if not emailed:
                    add(a, "NO_EMAIL", f"{len(active)} active contact(s), none with email"); flags.append("NO_EMAIL")
                elif not allowed:
                    add(a, "EMAIL_NOT_ALLOWED", f"{len(emailed)} emailed contact(s), all opted out"); flags.append("EMAIL_NOT_ALLOWED")
        else:
            add(a, "INACTIVE_NOT_ARCHIVED"); flags.append("INACTIVE_NOT_ARCHIVED")

        if not (a.get("city") and a.get("state") and a.get("postalCode")):
            missing = [k for k in ("city", "state", "postalCode") if not a.get(k)]
            add(a, "INCOMPLETE_ADDRESS", "missing " + ", ".join(missing)); flags.append("INCOMPLETE_ADDRESS")
        if not a.get("classification"):
            add(a, "NO_CLASSIFICATION"); flags.append("NO_CLASSIFICATION")
        if have_updated:
            dt = parse_dt(a.get("updatedDateTime"))
            if dt and dt < cutoff:
                add(a, "STALE", f"last updated {dt.date()}"); flags.append("STALE")

        # duplicate contacts within the account
        seen_email, seen_name = {}, {}
        for c in active:
            e = norm_email(c.get("emailAddress"))
            n = (norm_name(c.get("firstName")), norm_name(c.get("lastName")))
            if e and e in seen_email:
                add(a, "DUP_CONTACT", f"contacts {seen_email[e]} and {c.get('id')} share email {e}"); flags.append("DUP_CONTACT")
            elif e:
                seen_email[e] = c.get("id")
            if all(n) and n in seen_name:
                add(a, "DUP_CONTACT", f"contacts {seen_name[n]} and {c.get('id')} share name {n[0]} {n[1]}"); flags.append("DUP_CONTACT")
            elif all(n):
                seen_name[n] = c.get("id")

        acct_rows.append({
            "id": a.get("id"), "name": a.get("name"), "classification": a.get("classification"),
            "type": "Prospect" if prospect else "Client", "lob": "; ".join(a.get("linesOfBusiness") or []),
            "city": a.get("city"), "state": a.get("state"), "clientSize": a.get("clientSize"),
            "isActive": a.get("isActive"), "contacts": len(active), "primary": bool(primary),
            "email": bool(emailed), "emailAllowed": bool(allowed),
            "updated": a.get("updatedDateTime", ""), "flags": ", ".join(sorted(set(flags))),
            "_completeness": completeness(a, active),
        })

    # duplicate accounts by normalized name + city/state
    groups = defaultdict(list)
    for a in accounts:
        key = (norm_name(a.get("name")).replace(" ", ""), (a.get("city") or "").lower(), (a.get("state") or "").upper())
        if key[0]:
            groups[key].append(a)
    sid = 0
    for key, grp in groups.items():
        if len(grp) > 1:
            sid += 1
            dup_sets.append((sid, "DUP_ACCOUNT_NAME", f"{key[0]} | {key[1]}, {key[2]}", grp))
            for a in grp:
                add(a, "DUP_ACCOUNT_NAME", f"set {sid}: {len(grp)} accounts named alike in {key[1]}, {key[2]}")

    # duplicate accounts by phone
    phones = defaultdict(list)
    for a in accounts:
        p = norm_phone(a.get("primaryPhone") or a.get("phoneNumber"))
        if p:
            phones[p].append(a)
    for p, grp in phones.items():
        if len(grp) > 1 and len({norm_name(a.get("name")) for a in grp}) > 1:
            sid += 1
            dup_sets.append((sid, "DUP_ACCOUNT_PHONE", p, grp))
            for a in grp:
                add(a, "DUP_ACCOUNT_PHONE", f"set {sid}: {len(grp)} accounts share phone {p}")

    comp = {r["id"]: r["_completeness"] for r in acct_rows}
    return accounts, contacts, findings, dup_sets, acct_rows, comp, have_updated


# ------------------------------------------------------------------ output

HDR = Font(bold=True, color="FFFFFF")
FILL = PatternFill("solid", fgColor="0F2D52")
SEV_FILL = {"High": "FFC7CE", "Medium": "FFEB9C", "Low": "E2EFDA"}


def write_sheet(ws, headers, rows, widths=None, sev_col=None):
    ws.append(headers)
    for c in ws[1]:
        c.font, c.fill = HDR, FILL
        c.alignment = Alignment(vertical="center")
    for r in rows:
        ws.append(list(r))
    if sev_col is not None:
        for row in ws.iter_rows(min_row=2):
            sev = row[sev_col].value
            if sev in SEV_FILL:
                row[sev_col].fill = PatternFill("solid", fgColor=SEV_FILL[sev])
    for i, h in enumerate(headers, 1):
        ws.column_dimensions[get_column_letter(i)].width = (widths or {}).get(h, max(12, min(45, len(str(h)) + 4)))
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions


def build_workbook(out, accounts, contacts, findings, dup_sets, acct_rows, comp, have_updated, stale_months):
    wb = Workbook()
    n_acc = len(accounts)
    n_client = sum(1 for r in acct_rows if r["type"] == "Client")
    n_pros = n_acc - n_client
    counts = Counter(f[2] for f in findings)
    by_type = defaultdict(Counter)
    type_of = {r["id"]: r["type"] for r in acct_rows}
    cls_of = {r["id"]: r["classification"] or "(none)" for r in acct_rows}
    by_cls = defaultdict(Counter)
    for f in findings:
        by_type[f[2]][type_of.get(f[0], "?")] += 1
        by_cls[f[2]][cls_of.get(f[0], "?")] += 1

    ws = wb.active
    ws.title = "Summary"
    ws.append(["Book of Business Audit"]); ws["A1"].font = Font(bold=True, size=14)
    ws.append([f"Generated {datetime.now():%Y-%m-%d %H:%M}. Read-only audit; no records were changed."])
    ws.append([])
    ws.append(["Active accounts", n_acc]); ws.append(["  Clients", n_client]); ws.append(["  Prospects", n_pros])
    ws.append(["Active contacts", len(contacts)])
    ws.append(["Accounts with a finding", len({f[0] for f in findings})])
    ws.append(["Duplicate candidate sets", len(dup_sets)])
    ws.append(["Stale threshold (months)", stale_months if have_updated else "n/a — updatedDateTime not present in data"])
    ws.append([])
    hdr_row = ["Check", "Severity", "Accounts", "% of book", "Clients", "Prospects"]
    classes = sorted({c for ctr in by_cls.values() for c in ctr})
    ws.append(hdr_row + classes)
    for c in ws[ws.max_row]:
        c.font, c.fill = HDR, FILL
    for chk in sorted(SEVERITY, key=lambda k: ({"High": 0, "Medium": 1, "Low": 2}[SEVERITY[k]], k)):
        n = len({f[0] for f in findings if f[2] == chk})
        row = [chk, SEVERITY[chk], n, f"{(n / n_acc * 100) if n_acc else 0:.1f}%",
               by_type[chk]["Client"], by_type[chk]["Prospect"]] + [by_cls[chk][c] for c in classes]
        ws.append(row)
        ws.cell(ws.max_row, 2).fill = PatternFill("solid", fgColor=SEV_FILL[SEVERITY[chk]])
    ws.append([])
    ws.append(["Assumptions"])
    ws.append(["Prospect = every linesOfBusiness value contains 'Prospect'; otherwise Client."])
    ws.append(["Duplicate sets are candidates. Suggested survivor = most complete record. A human decides."])
    ws.append(["Archived records were excluded. Inactive-but-not-archived records were included and flagged."])
    for col, w in zip("ABCDEFGHIJ", (30, 12, 12, 12, 12, 12, 14, 14, 14, 14)):
        ws.column_dimensions[col].width = w

    write_sheet(wb.create_sheet("Findings"),
                ["Account ID", "Account", "Check", "Severity", "Type", "Classification", "State", "Detail"],
                [(f[0], f[1], f[2], f[3], type_of.get(f[0]), cls_of.get(f[0]),
                  next((r["state"] for r in acct_rows if r["id"] == f[0]), ""), f[4]) for f in findings],
                {"Account": 40, "Check": 24, "Detail": 60}, sev_col=3)

    dup_rows = []
    for sid, chk, key, grp in dup_sets:
        best = max(grp, key=lambda a: comp.get(a.get("id"), 0))
        for a in grp:
            dup_rows.append((sid, chk, key, a.get("id"), a.get("name"), a.get("city"), a.get("state"),
                             a.get("primaryPhone") or a.get("phoneNumber"), a.get("isActive"),
                             comp.get(a.get("id"), 0), "SUGGESTED SURVIVOR" if a is best else "candidate"))
    write_sheet(wb.create_sheet("Duplicates"),
                ["Set", "Check", "Match key", "Account ID", "Account", "City", "State", "Phone", "Active",
                 "Completeness", "Suggestion"], dup_rows,
                {"Match key": 40, "Account": 40, "Suggestion": 22})

    write_sheet(wb.create_sheet("Accounts"),
                ["Account ID", "Account", "Type", "Classification", "Lines of business", "City", "State",
                 "Client size", "Active", "Active contacts", "Has primary", "Has email", "Email allowed",
                 "Last updated", "Flags"],
                [(r["id"], r["name"], r["type"], r["classification"], r["lob"], r["city"], r["state"],
                  r["clientSize"], r["isActive"], r["contacts"], r["primary"], r["email"], r["emailAllowed"],
                  r["updated"], r["flags"]) for r in acct_rows],
                {"Account": 40, "Lines of business": 28, "Flags": 50})

    wb.save(out)
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--accounts", required=True)
    ap.add_argument("--contacts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stale-months", type=int, default=18)
    args = ap.parse_args()

    accounts = load_records(args.accounts)
    contacts = load_records(args.contacts)
    res = run_checks(accounts, contacts, args.stale_months)
    counts = build_workbook(args.out, *res, args.stale_months)
    n_acc = len(res[0])
    print(f"accounts={n_acc} contacts={len(res[1])} findings={len(res[2])} dup_sets={len(res[3])}")
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k:24s} {v:6d}  ({v / n_acc * 100 if n_acc else 0:.1f}%)")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
