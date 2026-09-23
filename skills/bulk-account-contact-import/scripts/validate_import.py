#!/usr/bin/env python3
"""Dry-run validator for bulk account + contact import.

Inputs
  --input     the spreadsheet (.csv, .xlsx, .xls)
  --mapping   JSON: {"<target field>": "<source column>", ...}; may include the pseudo-targets
              "_name" (full name to split), "_account_id", "_msid", "_company", "_company_city",
              "_company_state"
  --accounts  JSON: {"<company key>": {"accountId": 123, "name": "...", "city": "...", "ambiguous": false}}
              keyed by normalized company name, or by "id:<n>" / "msid:<M...>" when the file carries those.
              Companies in the file that are NOT in this map are proposed for creation (phase 1).
  --discovery optional JSON: {"<company key>": {"msid": "M...", "name": "...", "address": "...", "city": "...",
              "state": "..", "zip": "...", "phone": "...", "naics": "...", "employees": 140}} — market-data
              firmographics for companies to be created; used to populate the account payload
  --lob       line-of-business value for new accounts, e.g. "Commercial Lines Prospect" (default)
  --existing  JSON array of existing CRM contacts for the resolved accounts (items from
              account_contact_search), used for duplicate detection
  --out       .xlsx dry-run report

Writes nothing to Zywave. Contact outcome per row: create | create_with_new_account | update |
skip_duplicate | fail | ambiguous_account. Account outcome per distinct company: existing |
create | ambiguous. Stdout prints the counts.
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

try:
    import pandas as pd
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError:  # pragma: no cover
    sys.exit("pandas and openpyxl are required: pip install pandas openpyxl --break-system-packages")

LIMITS = {
    "firstName": 50, "lastName": 50, "emailAddress": 100, "title": 100, "salutation": 50,
    "workPhoneNumber": 50, "mobilePhoneNumber": 50, "homePhoneNumber": 50, "faxNumber": 50,
    "primaryAddressLine1": 255, "primaryAddressLine2": 255, "primaryAddressLine3": 100,
    "primaryAddressCity": 75, "primaryAddressState": 4, "primaryAddressPostalCode": 50,
    "primaryAddressCountry": 2,
}
BOOLS = {"isPrimaryContact", "isEmailAllowed", "isActive"}
ENUMS = {"gender": {"Male", "Female"},
         "maritalStatus": {"Single", "Married", "Separated", "Divorced", "Widowed"}}
PHONES = {"workPhoneNumber", "mobilePhoneNumber", "homePhoneNumber", "faxNumber"}
SUFFIXES = r"\b(inc|incorporated|llc|l\.l\.c\.|ltd|limited|co|corp|corporation|company|lp|llp|plc|pc|pllc|the)\b"
TRUE = {"y", "yes", "true", "1", "x", "t"}


def s(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return re.sub(r"\s+", " ", str(v)).strip()


def norm_company(v):
    v = s(v).lower().replace("&", " and ")
    v = re.sub(r"[^a-z0-9 ]", " ", v)
    v = re.sub(SUFFIXES, " ", v)
    return re.sub(r"\s+", "", v)


def norm_name(v):
    return re.sub(r"[^a-z]", "", s(v).lower())


def to_bool(v):
    return s(v).lower() in TRUE


def read_input(path):
    if path.lower().endswith(".csv"):
        return pd.read_csv(path, dtype=str, keep_default_na=False)
    return pd.read_excel(path, dtype=str).fillna("")


def split_name(full):
    parts = s(full).split(" ")
    if len(parts) < 2:
        return "", "", "name has one token"
    if len(parts) > 2 or re.search(r"\b(jr|sr|ii|iii|iv)\.?$", full, re.I):
        return parts[0], " ".join(parts[1:]), "multi-token name; split assumed"
    return parts[0], parts[1], ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--mapping", required=True)
    ap.add_argument("--accounts", required=True)
    ap.add_argument("--existing", default=None)
    ap.add_argument("--discovery", default=None)
    ap.add_argument("--lob", default="Commercial Lines Prospect")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    df = read_input(a.input)
    mapping = json.load(open(a.mapping))
    accounts = json.load(open(a.accounts))
    existing = json.load(open(a.existing)) if a.existing else []
    discovery = json.load(open(a.discovery)) if a.discovery else {}
    new_accounts = {}   # company key -> proposed account payload
    if isinstance(existing, dict):
        existing = existing.get("items", [])

    by_acct = defaultdict(list)
    for c in existing:
        if not c.get("isArchived"):
            by_acct[c.get("accountId")].append(c)

    rows, primaries_seen = [], set()
    for i, r in df.iterrows():
        rec, notes, errors = {}, [], []
        for target, col in mapping.items():
            if target.startswith("_") or col not in df.columns:
                continue
            rec[target] = s(r[col])

        if "_name" in mapping and mapping["_name"] in df.columns and not (rec.get("firstName") and rec.get("lastName")):
            f, l, n = split_name(r[mapping["_name"]])
            rec["firstName"], rec["lastName"] = f, l
            if n:
                notes.append(n)

        # ---- account resolution
        acct, outcome = None, None
        key = None
        if mapping.get("_account_id") in df.columns and s(r[mapping["_account_id"]]):
            key = "id:" + s(r[mapping["_account_id"]])
        elif mapping.get("_msid") in df.columns and s(r[mapping["_msid"]]):
            key = "msid:" + s(r[mapping["_msid"]])
        elif mapping.get("_company") in df.columns:
            key = norm_company(r[mapping["_company"]])
        hit = accounts.get(key) if key else None
        new_acct = False
        if not hit:
            company_label = s(r[mapping["_company"]]) if mapping.get("_company") in df.columns else ""
            if key and company_label and not key.startswith(("id:", "msid:")):
                d = discovery.get(key, {})
                new_accounts.setdefault(key, {
                    "name": d.get("name") or company_label, "msid": d.get("msid", ""),
                    "primaryAddressLine1": d.get("address", ""), "primaryAddressCity": d.get("city", ""),
                    "primaryAddressState": d.get("state", ""), "primaryAddressPostalCode": d.get("zip", ""),
                    "workPhoneNumber": d.get("phone", ""), "naicsCodes": [d["naics"]] if d.get("naics") else [],
                    "numberOfEmployees": d.get("employees"), "linesOfBusiness": [a.lob],
                    "classification": "Personal" if "Personal" in a.lob else "Commercial",
                    "source": "market data" if d else "file only", "rows": 0,
                })
                new_accounts[key]["rows"] += 1
                acct = {"accountId": f"NEW:{key}", "name": new_accounts[key]["name"]}
                new_acct = True
            else:
                outcome = "unknown_account"
        elif hit.get("ambiguous"):
            outcome = "ambiguous_account"
        else:
            acct = hit

        # ---- field validation
        if not rec.get("firstName"):
            errors.append("firstName missing")
        if not rec.get("lastName"):
            errors.append("lastName missing")
        for k, lim in LIMITS.items():
            if rec.get(k) and len(rec[k]) > lim:
                errors.append(f"{k} > {lim} chars")
        em = rec.get("emailAddress", "")
        if em:
            rec["emailAddress"] = em.lower()
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", rec["emailAddress"]):
                errors.append("emailAddress malformed")
        for k in PHONES:
            if rec.get(k):
                digits = re.sub(r"\D", "", rec[k])
                if len(digits) < 10:
                    errors.append(f"{k} has {len(digits)} digits")
        if rec.get("primaryAddressState"):
            rec["primaryAddressState"] = rec["primaryAddressState"].upper()
        if rec.get("primaryAddressCountry"):
            c = rec["primaryAddressCountry"].upper()
            rec["primaryAddressCountry"] = "US" if c in ("USA", "UNITED STATES", "U.S.", "US") else c
            if len(rec["primaryAddressCountry"]) != 2:
                errors.append("primaryAddressCountry not ISO alpha-2")
        for k, allowed in ENUMS.items():
            if rec.get(k):
                cap = rec[k].capitalize()
                if cap in allowed:
                    rec[k] = cap
                else:
                    errors.append(f"{k} not one of {sorted(allowed)}")
        for k in BOOLS:
            if k in rec:
                rec[k] = to_bool(rec[k])
        if rec.get("birthDate"):
            try:
                rec["birthDate"] = pd.to_datetime(rec["birthDate"]).strftime("%Y-%m-%dT00:00:00Z")
            except Exception:
                errors.append("birthDate unparseable")

        if rec.get("isPrimaryContact") and acct:
            if acct["accountId"] in primaries_seen:
                rec["isPrimaryContact"] = False
                notes.append("second primary on account; demoted")
            else:
                primaries_seen.add(acct["accountId"])

        # ---- duplicate check
        dup_of = None
        if acct and not errors:
            for c in by_acct.get(acct["accountId"], []):
                if rec.get("emailAddress") and s(c.get("emailAddress")).lower() == rec["emailAddress"]:
                    dup_of = c
                    break
                if norm_name(c.get("firstName")) == norm_name(rec["firstName"]) and \
                        norm_name(c.get("lastName")) == norm_name(rec["lastName"]):
                    dup_of = c
                    break

        if errors:
            outcome = "fail"
        elif outcome is None:
            if new_acct:
                outcome = "create_with_new_account"
            elif dup_of:
                changed = (rec.get("emailAddress") and s(dup_of.get("emailAddress")).lower() != rec["emailAddress"]) or \
                          any(rec.get(k) and s(dup_of.get(k)) != rec[k] for k in ("title", "workPhoneNumber", "mobilePhoneNumber"))
                outcome = "update" if changed else "skip_duplicate"
            else:
                outcome = "create"

        rows.append({
            "row": i + 2, "outcome": outcome,
            "accountId": acct["accountId"] if acct else "",
            "account": acct["name"] if acct else (s(r[mapping["_company"]]) if mapping.get("_company") in df.columns else key or ""),
            "existingContactId": dup_of.get("id") if dup_of else "",
            "errors": "; ".join(errors), "notes": "; ".join(notes),
            **rec,
        })

    counts = Counter(x["outcome"] for x in rows)

    # ---- workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.append(["Bulk account and contact import — dry run"]); ws["A1"].font = Font(bold=True, size=14)
    ws.append([f"Generated {datetime.now():%Y-%m-%d %H:%M}. Nothing has been written to Zywave."])
    ws.append([])
    ws.append(["PHASE 1 — accounts"])
    ws.append(["accounts to create", len(new_accounts)])
    ws.append(["  populated from market data", sum(1 for v in new_accounts.values() if v["source"] == "market data")])
    ws.append(["  file data only (no market-data match)", sum(1 for v in new_accounts.values() if v["source"] == "file only")])
    ws.append(["existing accounts matched", len({x["accountId"] for x in rows if x["accountId"] and not str(x["accountId"]).startswith("NEW:")})])
    ws.append([])
    ws.append(["PHASE 2 — contacts"])
    for k in ("create", "create_with_new_account", "update", "skip_duplicate", "fail", "unknown_account", "ambiguous_account"):
        ws.append([k, counts.get(k, 0)])
    ws.append(["total rows", len(rows)])

    wa = wb.create_sheet("Accounts to create")
    ahdr = ["key", "name", "msid", "linesOfBusiness", "classification", "primaryAddressLine1", "primaryAddressCity",
            "primaryAddressState", "primaryAddressPostalCode", "workPhoneNumber", "naicsCodes", "numberOfEmployees",
            "source", "contact rows"]
    wa.append(ahdr)
    for c in wa[1]:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="0F2D52")
    for k, v in sorted(new_accounts.items(), key=lambda kv: -kv[1]["rows"]):
        wa.append([k, v["name"], v["msid"], "; ".join(v["linesOfBusiness"]), v["classification"],
                   v["primaryAddressLine1"], v["primaryAddressCity"], v["primaryAddressState"],
                   v["primaryAddressPostalCode"], v["workPhoneNumber"], "; ".join(v["naicsCodes"]),
                   v["numberOfEmployees"], v["source"], v["rows"]])
    for i, h in enumerate(ahdr, 1):
        wa.column_dimensions[get_column_letter(i)].width = max(12, min(40, len(h) + 4))
    wa.freeze_panes = "A2"
    ws.column_dimensions["A"].width = 28

    fields = ["row", "outcome", "accountId", "account", "existingContactId", "errors", "notes"] + \
             sorted({k for x in rows for k in x if k not in ("row", "outcome", "accountId", "account", "existingContactId", "errors", "notes")})
    fills = {"create": "E2EFDA", "create_with_new_account": "C6E0B4", "update": "DDEBF7", "skip_duplicate": "EDEDED", "fail": "FFC7CE",
             "unknown_account": "FFEB9C", "ambiguous_account": "FFEB9C"}
    for tab, keep in (("All rows", None), ("Needs review", {"fail", "unknown_account", "ambiguous_account"})):
        w = wb.create_sheet(tab)
        w.append(fields)
        for c in w[1]:
            c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="0F2D52")
        for x in rows:
            if keep and x["outcome"] not in keep:
                continue
            w.append([x.get(f, "") for f in fields])
            w.cell(w.max_row, 2).fill = PatternFill("solid", fgColor=fills.get(x["outcome"], "FFFFFF"))
        for i, f in enumerate(fields, 1):
            w.column_dimensions[get_column_letter(i)].width = max(10, min(40, len(f) + 4))
        w.freeze_panes = "A2"
        if w.max_row > 1:
            w.auto_filter.ref = w.dimensions
    wb.save(a.out)

    print(json.dumps({"rows": len(rows), "accounts_to_create": len(new_accounts), **counts}, indent=2))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
