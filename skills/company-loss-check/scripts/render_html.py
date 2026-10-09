#!/usr/bin/env python3
"""Build a self-contained, static HTML preview from a profile JSON.

Usage: python render_html.py profile.json preview.html

No scripts, no external fonts, images, or network calls, so the file opens
anywhere and nothing can load or send data. Charts are inline SVG. Neutral
styling, light and dark aware, print friendly. Entity profiles show line and
year charts; family profiles (scope "family") show a table of entities.
"""
import html
import json
import sys

FOOTER = ("Source: Zywave loss data. Publicly reported loss events, generally $1M or more. "
          "Not this company's own loss runs. Smaller companies are underrepresented, so a thin result "
          "is not evidence of a clean history. Lines of business show the coverage most likely to respond, "
          "not what paid.")

CSS = """
:root{--ink:#1f1f1e;--mut:#6b6a66;--line:#e1e0d9;--bg:#fff;--card:#f6f5f1;--bar:#2a78d6;--bar2:#b5d4f4;--warn:#fff4dc;--warnink:#6b4a00}
@media (prefers-color-scheme:dark){:root{--ink:#f0efec;--mut:#a9a8a0;--line:#383835;--bg:#1a1a19;--card:#242423;--bar:#5b9be8;--bar2:#34506f;--warn:#3a3016;--warnink:#f0d9a0}}
*{box-sizing:border-box}body{margin:0;padding:24px;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,Arial,sans-serif}
main{max-width:860px;margin:0 auto}h1{font-size:22px;margin:0 0 4px;font-weight:600}h2{font-size:15px;margin:28px 0 8px;font-weight:600}
.sub{color:var(--mut);font-size:13px;margin:0 0 20px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.card{background:var(--card);border-radius:8px;padding:14px}.card .l{font-size:12px;color:var(--mut)}.card .v{font-size:22px;font-weight:600}.card .d{font-size:12px;color:var(--mut)}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line)}th{font-size:12px;color:var(--mut);font-weight:600}
td.n,th.n{text-align:right}ul{padding-left:20px;margin:6px 0}li{margin:4px 0}.note{background:var(--warn);color:var(--warnink);border-radius:8px;padding:10px 12px;margin:12px 0;font-size:14px}
svg text{fill:var(--ink);font:12px system-ui,Arial,sans-serif}svg .m{fill:var(--mut)}.b1{fill:var(--bar)}.b2{fill:var(--bar2)}.ax{stroke:var(--line)}
footer{margin-top:28px;padding-top:12px;border-top:1px solid var(--line);color:var(--mut);font-size:12px}
@page{size:Letter;margin:0.5in}@media print{:root{--ink:#1f1f1e;--mut:#6b6a66;--line:#e1e0d9;--bg:#fff;--card:#f6f5f1;--bar:#2a78d6;--bar2:#b5d4f4;--warn:#fff4dc;--warnink:#6b4a00}body{padding:0;font-size:13px;-webkit-print-color-adjust:exact;print-color-adjust:exact}h2{margin:16px 0 6px}.card{break-inside:avoid}svg,table{break-inside:avoid}main{max-width:none}}
"""


def money(n):
    if n is None:
        return "n/a"
    if n >= 1e9:
        return f"${n / 1e9:.2f}B"
    if n >= 1e6:
        return f"${n / 1e6:.1f}M"
    if n >= 1e3:
        return f"${n / 1e3:.0f}K"
    return f"${n:,.0f}"


def e(x):
    return html.escape(str(x))


def lob_svg(lines):
    lines = sorted(lines, key=lambda r: r.get("total_loss") or 0, reverse=True)[:6]
    if not lines:
        return ""
    top = max((r.get("total_loss") or 0) for r in lines) or 1
    row_h, left, width = 34, 240, 900
    h = row_h * len(lines) + 8
    out = [f'<svg viewBox="0 0 {width} {h}" width="100%" role="img" aria-label="Total reported loss by line of business">']
    for i, r in enumerate(lines):
        y = i * row_h + 4
        bw = max(2, int((r.get("total_loss") or 0) / top * 300))
        nm = r["name"]
        label = e(nm if len(nm) <= 36 else nm[:35] + "\u2026")
        out.append(f'<text x="0" y="{y + 18}">{label}</text>')
        out.append(f'<rect class="b1" x="{left}" y="{y + 4}" width="{bw}" height="18" rx="3"/>')
        out.append(f'<text x="{left + bw + 8}" y="{y + 18}">{money(r.get("total_loss")) if r.get("total_loss") is not None and r.get("contributing", 0) > 0 else "no amount recorded"}'
                   f'<tspan class="m"> ({r.get("contributing", 0)} of {r.get("cases", 0)} with an amount)</tspan></text>')
    out.append("</svg>")
    return "".join(out)


def year_svg(years):
    years = sorted(years, key=lambda r: r["year"])
    if not years:
        return ""
    top = max(r.get("cases", 0) for r in years) or 1
    width, h, base, bw, gap = 900, 220, 190, 48, 40
    out = [f'<svg viewBox="0 0 {width} {h}" width="100%" role="img" aria-label="Case records by year, split into with and without an amount">']
    out.append(f'<line class="ax" x1="0" y1="{base}" x2="{width}" y2="{base}"/>')
    for i, r in enumerate(years):
        x = 10 + i * (bw + gap)
        tot = r.get("cases", 0)
        wa = min(r.get("contributing", 0), tot)
        th = int(tot / top * 160)
        ah = int(wa / top * 160)
        out.append(f'<rect class="b2" x="{x}" y="{base - th}" width="{bw}" height="{th - ah}"/>')
        out.append(f'<rect class="b1" x="{x}" y="{base - ah}" width="{bw}" height="{ah}"/>')
        out.append(f'<text class="m" x="{x + bw / 2}" y="{base + 16}" text-anchor="middle">{r["year"]}</text>')
        out.append(f'<text x="{x + bw / 2}" y="{base - th - 5}" text-anchor="middle">{tot}</text>')
    out.append('<rect class="b1" x="10" y="2" width="10" height="10"/><text x="26" y="11">With an amount</text>')
    out.append('<rect class="b2" x="140" y="2" width="10" height="10"/><text x="156" y="11">No amount</text>')
    out.append("</svg>")
    return "".join(out)


def main(src, out):
    p = json.load(open(src))
    co, h = p["company"], p["headline"]
    family = p.get("scope") == "family"
    scope = "Corporate family" if family else "Entity"
    disc = f"{h['contributing']:,} of {h['cases']:,} records with an amount"
    none_rec = h.get("total_loss") is None or h.get("contributing", 0) == 0
    cards = [("Case records", f"{h['cases']:,}", "one per organization per case"),
             ("Total reported loss", "None recorded" if none_rec else money(h["total_loss"]), "no dollar amount on any record" if none_rec else disc)]
    if h.get("average") is not None and not family:
        cards.append(("Average", money(h["average"]), "over records with an amount"))
    if h.get("largest") is not None and not family:
        cards.append(("Largest single loss", money(h["largest"]), "one case"))
    parts = [f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
             f"<title>{e(co['name'])}: publicly reported losses</title><style>{CSS}</style></head><body><main>",
             f"<h1>{e(co['name'])}: publicly reported losses</h1>",
             f"<p class=\"sub\">{e(co.get('state', ''))} | Ultimate parent: {e(co.get('ultimate_parent', co['name']))} | Scope: {scope} | Data pulled {e(p.get('pulled', ''))}</p>",
             "<div class=\"cards\">" + "".join(f"<div class=\"card\"><div class=\"l\">{e(a)}</div><div class=\"v\">{e(b)}</div><div class=\"d\">{e(c)}</div></div>" for a, b, c in cards) + "</div>"]
    if family and p.get("entities"):
        parts.append("<h2>Largest entities</h2><table><thead><tr><th>Entity</th><th>State</th><th class=\"n\">Case records</th><th class=\"n\">Total reported loss</th><th class=\"n\">With an amount</th></tr></thead><tbody>")
        for r in p["entities"]:
            parts.append(f"<tr><td>{e(r['name'])}</td><td>{e(r.get('state', ''))}</td><td class=\"n\">{r['cases']:,}</td><td class=\"n\">{money(r.get('total_loss')) if r.get('contributing', 0) > 0 else 'No amount recorded'}</td><td class=\"n\">{r.get('contributing', 0):,} of {r['cases']:,}</td></tr>")
        parts.append("</tbody></table>")
    else:
        parts.append("<h2>Where losses concentrate</h2>" + lob_svg(p.get("lines", [])))
        parts.append("<h2>Case records by year, most recent 10</h2>" + year_svg(p.get("years", [])))
    notes = p.get("notes", [])[:4]
    if notes:
        parts.append("<h2>Worth knowing</h2><ul>" + "".join(f"<li>{e(n)}</li>" for n in notes) + "</ul>")
    parts.append(f"<footer>{e(FOOTER)} Snapshot as of {e(p.get('pulled', ''))}; this page does not update.</footer></main></body></html>")
    open(out, "w").write("".join(parts))
    print(out)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
