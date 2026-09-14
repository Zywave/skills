#!/usr/bin/env python3
"""Territory market map workbook builder.

Inputs
  --counts     JSON array of {"label": str, "grid": "industry_size"|"renewal"|"signal"|"plan_type",
                              "industry": str|null, "size_band": str|null, "month": int|null,
                              "signal": str|null, "filters": {...}, "totalCount": int|null}
  --companies  JSON array (or {items|results:[...]}) of discovery_company_search results,
               each optionally annotated with "segment": "<industry> | <size_band>"
  --book       JSON array (or {items:[...]}) of account_search results for the territory
  --territory  label for the workbook
  --lob        Commercial | Benefits
  --out        output .xlsx

Everything here is either a count (fact) or derived from a labeled sample (estimate).
The workbook labels which is which.
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
except ImportError:  # pragma: no cover
    sys.exit("openpyxl is required: pip install openpyxl --break-system-packages")

HDR = Font(bold=True, color="FFFFFF")
FILL = PatternFill("solid", fgColor="0F2D52")
SIZE_ORDER = ["10-49", "50-99", "100-249", "250+"]
SUFFIXES = r"\b(inc|incorporated|llc|l\.l\.c\.|ltd|limited|co|corp|corporation|company|lp|llp|plc|pc|pllc|the)\b"


def load(path):
    if not path:
        return []
    text = open(path, encoding="utf-8").read().strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        blobs = [data]
    except json.JSONDecodeError:
        blobs = [json.loads(l) for l in text.splitlines() if l.strip()]
    out = []
    for b in blobs:
        if isinstance(b, dict):
            for k in ("items", "results"):
                if k in b:
                    out.extend(b[k]); break
            else:
                out.append(b)
        elif isinstance(b, list):
            for x in b:
                if isinstance(x, dict) and ("items" in x or "results" in x):
                    out.extend(x.get("items") or x.get("results") or [])
                else:
                    out.append(x)
    return out


def norm_name(s):
    s = (s or "").lower()
    s = re.sub(r"[&]", " and ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(SUFFIXES, " ", s)
    return re.sub(r"\s+", "", s).strip()


def first(d, *keys):
    for k in keys:
        v = d.get(k)
        if v not in (None, "", [], {}):
            return v
    return None


def heat(ws, r1, c1, r2, c2):
    vals = [ws.cell(r, c).value for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
            if isinstance(ws.cell(r, c).value, (int, float))]
    if not vals:
        return
    hi = max(vals) or 1
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            v = ws.cell(r, c).value
            if isinstance(v, (int, float)):
                t = v / hi
                g = int(255 - 120 * t); b = int(255 - 200 * t)
                ws.cell(r, c).fill = PatternFill("solid", fgColor=f"FF{g:02X}{b:02X}")


def sheet(wb, title, headers, rows, widths=None):
    ws = wb.create_sheet(title)
    ws.append(headers)
    for c in ws[1]:
        c.font, c.fill = HDR, FILL
    for r in rows:
        ws.append(list(r))
    for i, h in enumerate(headers, 1):
        ws.column_dimensions[get_column_letter(i)].width = (widths or {}).get(h, max(12, min(44, len(str(h)) + 4)))
    ws.freeze_panes = "A2"
    if rows:
        ws.auto_filter.ref = ws.dimensions
    return ws


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--counts", required=True)
    ap.add_argument("--companies", default=None)
    ap.add_argument("--book", default=None)
    ap.add_argument("--territory", required=True)
    ap.add_argument("--lob", default="Commercial")
    ap.add_argument("--quality-floor", type=int, default=51)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    counts = load(a.counts)
    companies = load(a.companies)
    book = load(a.book)

    # ---------------------------------------------------------- counts
    grid = defaultdict(dict)
    industries = []
    for c in counts:
        if c.get("grid") == "industry_size":
            ind, band = c.get("industry"), c.get("size_band")
            if ind not in industries:
                industries.append(ind)
            grid[ind][band] = c.get("totalCount")
    renewal = {c.get("month"): c.get("totalCount") for c in counts if c.get("grid") == "renewal" and c.get("month")}
    baseline = next((c.get("totalCount") for c in counts if c.get("grid") == "renewal" and not c.get("month")), None)
    signals = [(c.get("signal") or c.get("label"), c.get("totalCount")) for c in counts if c.get("grid") in ("signal", "plan_type")]
    universe = next((c.get("totalCount") for c in counts if c.get("grid") == "universe"), None)
    if universe is None:
        universe = sum(v for ind in grid.values() for v in ind.values() if isinstance(v, int))
        universe_note = "sum of industry × size cells (companies with multiple NAICS may be counted more than once)"
    else:
        universe_note = "single unfiltered count"

    # ---------------------------------------------------------- book overlay
    by_msid = {}
    by_namecity = {}
    for acc in book:
        if acc.get("isArchived"):
            continue
        if acc.get("msid"):
            by_msid[acc["msid"]] = acc
        by_namecity[(norm_name(acc.get("name")), (acc.get("city") or "").lower())] = acc

    def owned(co):
        acc = by_msid.get(co.get("msid")) or by_namecity.get((norm_name(co.get("name")), (co.get("city") or "").lower()))
        if not acc:
            return "Not in CRM", None
        lobs = acc.get("linesOfBusiness") or []
        kind = "Owned — prospect" if lobs and all("prospect" in str(l).lower() for l in lobs) else "Owned — client"
        return kind, acc.get("id")

    # ---------------------------------------------------------- samples
    seen = set()
    detail_rows, seg_stats = [], defaultdict(lambda: Counter())
    broker_tally, carrier_tally = Counter(), Counter()
    n_broker_data = n_carrier_data = 0
    owned_counter = Counter()
    for co in companies:
        if co.get("msid") in seen or co.get("isOutOfBusiness"):
            continue
        seen.add(co.get("msid"))
        seg = co.get("segment") or "unsegmented"
        rev = co.get("revenueRange") or {}
        broker = first(co, "leadCommercialBroker", "leadBenefitsBroker", "commercialBroker", "benefitsBroker", "broker")
        carrier = first(co, "leadCommercialCarrier", "leadBenefitsCarrier", "commercialCarrier", "benefitsCarrier", "carrier")
        if isinstance(broker, dict):
            broker = broker.get("name")
        if isinstance(carrier, dict):
            carrier = carrier.get("name")
        checks = (co.get("complianceReport") or {}).get("checks") or []
        flags = [f"{c.get('compliance_type')}={c.get('result')}" for c in checks if c.get("result") not in (None, "GREEN")]
        bonds = co.get("fidelityBonds") or []
        bond_issue = any(b.get("is_compliant") is False for b in bonds)
        status, acc_id = owned(co)
        owned_counter[status] += 1
        seg_stats[seg]["n"] += 1
        seg_stats[seg]["flags"] += bool(flags)
        seg_stats[seg]["bond_issue"] += bond_issue
        seg_stats[seg]["owned"] += status.startswith("Owned")
        if broker:
            broker_tally[str(broker)] += 1; n_broker_data += 1
        if carrier:
            carrier_tally[str(carrier)] += 1; n_carrier_data += 1
        detail_rows.append((
            seg, co.get("msid"), co.get("name"), co.get("city"), co.get("state"), co.get("county"),
            first(co, "employeeCount", "employees"), rev.get("min"), rev.get("max"),
            first(co, "naicsCode", "naics"), first(co, "renewalMonth", "renewalMonths"),
            broker or "", carrier or "", co.get("qualityScore"), "; ".join(flags), bond_issue, status, acc_id,
        ))

    # ---------------------------------------------------------- workbook
    wb = Workbook()
    ws = wb.active; ws.title = "Summary"
    ws.append([f"{a.territory} — {a.lob} Market Map"]); ws["A1"].font = Font(bold=True, size=14)
    ws.append([f"Prepared {datetime.now():%Y-%m-%d}. Source: Zywave discovery (quality score ≥ {a.quality_floor}) and CRM accounts."])
    ws.append([])
    ws.append(["Universe (count)", universe, universe_note])
    top_cells = sorted(((ind, band, v) for ind, bands in grid.items() for band, v in bands.items() if isinstance(v, int)),
                       key=lambda x: -x[2])[:5]
    ws.append(["Top segments (count)"])
    for ind, band, v in top_cells:
        ws.append(["", f"{ind} | {band}", v])
    if renewal:
        m, v = max(renewal.items(), key=lambda kv: kv[1] or 0)
        ws.append(["Peak renewal month (count)", datetime(2000, m, 1).strftime("%B"), v])
        if baseline and sum(x or 0 for x in renewal.values()) <= baseline:
            ws.append(["Share with known renewal month", f"{sum(x or 0 for x in renewal.values()) / baseline:.0%}"])
    for s, v in signals:
        ws.append([f"{s} (count)", v])
    ws.append([])
    ws.append(["Sampled companies (estimate basis)", len(detail_rows)])
    for k, v in owned_counter.most_common():
        ws.append([f"  {k}", v, f"{v / len(detail_rows):.0%}" if detail_rows else ""])
    if broker_tally:
        ws.append(["Top incumbent broker (sample)", broker_tally.most_common(1)[0][0],
                   f"{broker_tally.most_common(1)[0][1]} of {n_broker_data} with broker data"])
    ws.append([])
    ws.append(["Counts are facts about the discovery database at the stated quality floor. Sample-derived figures are estimates and are labeled."])
    ws.append(["Null broker/carrier fields mean filing data is unavailable — never that a company is unrepresented."])
    for col, w in zip("ABC", (40, 36, 60)):
        ws.column_dimensions[col].width = w

    bands = [b for b in SIZE_ORDER if any(b in g for g in grid.values())] or sorted({b for g in grid.values() for b in g})
    rows = []
    for ind in industries:
        r = [ind] + [grid[ind].get(b) for b in bands]
        r.append(sum(v for v in r[1:] if isinstance(v, int)))
        rows.append(r)
    rows.append(["Total"] + [sum(grid[i].get(b) or 0 for i in industries) for b in bands] + [universe])
    ws2 = sheet(wb, "Industry x Size", ["Industry"] + bands + ["Total"], rows, {"Industry": 36})
    heat(ws2, 2, 2, len(rows), len(bands) + 1)

    sheet(wb, "Renewal Months", ["Month", "Companies (count)"],
          [(datetime(2000, m, 1).strftime("%B"), renewal.get(m)) for m in range(1, 13)] + [("Baseline (no renewal filter)", baseline)])
    sheet(wb, "Signals", ["Signal", "Companies (count)"], signals)

    inc_rows = [("Broker", b, n, n_broker_data, f"{n / n_broker_data:.0%}" if n_broker_data else "") for b, n in broker_tally.most_common(25)]
    inc_rows += [("Carrier", c, n, n_carrier_data, f"{n / n_carrier_data:.0%}" if n_carrier_data else "") for c, n in carrier_tally.most_common(25)]
    sheet(wb, "Incumbents", ["Type", "Name", "Companies (sample)", "n with data", "Share of n"], inc_rows, {"Name": 44})

    seg_rows = [(s, c["n"], c["owned"], f"{c['owned'] / c['n']:.0%}", c["flags"], c["bond_issue"]) for s, c in seg_stats.items()]
    sheet(wb, "Segment Stats", ["Segment", "Sampled", "Owned", "Sampled owned share", "With compliance flags", "With bond issue"], seg_rows, {"Segment": 44})

    sheet(wb, "Segment Detail",
          ["Segment", "MSID", "Company", "City", "State", "County", "Employees", "Revenue min", "Revenue max", "NAICS",
           "Renewal", "Broker (filing)", "Carrier (filing)", "Quality", "Compliance flags", "Bond issue", "CRM status", "Account ID"],
          detail_rows, {"Segment": 36, "Company": 40, "Compliance flags": 36})

    book_rows = [(acc.get("id"), acc.get("name"), acc.get("city"), acc.get("state"), acc.get("classification"),
                  "; ".join(acc.get("linesOfBusiness") or []), acc.get("clientSize"), acc.get("msid") or "")
                 for acc in book if not acc.get("isArchived")]
    sheet(wb, "Book Overlay", ["Account ID", "Account", "City", "State", "Classification", "Lines of business", "Client size", "MSID"],
          book_rows, {"Account": 40, "Lines of business": 28})

    sheet(wb, "Method", ["Grid", "Label", "Filters", "totalCount"],
          [(c.get("grid"), c.get("label"), json.dumps(c.get("filters") or {}, sort_keys=True), c.get("totalCount")) for c in counts],
          {"Label": 36, "Filters": 80})

    wb.save(a.out)
    print(f"universe={universe} cells={sum(len(g) for g in grid.values())} sampled={len(detail_rows)} book={len(book_rows)}")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
