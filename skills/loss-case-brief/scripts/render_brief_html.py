#!/usr/bin/env python3
"""Build a self-contained, static one-page HTML brief from a profile JSON.

Usage: python render_brief_html.py profile.json brief.html

No scripts, external fonts, images, or network calls. Light and dark aware;
prints on one Letter portrait page. Components are shown, never summed.
"""
import html
import json
import sys

FOOTER = ("Source: Zywave loss data. A publicly reported loss event, as recorded; wording follows the case's "
          "status and allegations are not findings. Not a legal opinion. Lines of business show the coverage "
          "most likely to respond, not what paid.")

CSS = """
:root{--ink:#1f1f1e;--mut:#6b6a66;--line:#e1e0d9;--bg:#fff;--card:#f6f5f1;--warn:#fff4dc;--warnink:#6b4a00}
@media (prefers-color-scheme:dark){:root{--ink:#f0efec;--mut:#a9a8a0;--line:#383835;--bg:#1a1a19;--card:#242423;--warn:#3a3016;--warnink:#f0d9a0}}
*{box-sizing:border-box}body{margin:0;padding:24px;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,Arial,sans-serif}
main{max-width:820px;margin:0 auto}h1{font-size:22px;margin:0 0 2px;font-weight:600}h2{font-size:14px;margin:18px 0 6px;font-weight:600}
.sub{color:var(--mut);font-size:13px;margin:0 0 14px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}
.card{background:var(--card);border-radius:8px;padding:10px 12px}.card .l{font-size:12px;color:var(--mut)}.card .v{font-size:20px;font-weight:600}.card .d{font-size:12px;color:var(--mut)}
p{margin:0 0 6px}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--line)}
th{font-size:12px;color:var(--mut);font-weight:600}td.n,th.n{text-align:right;white-space:nowrap}ul{padding-left:20px;margin:4px 0}li{margin:3px 0}
.fine{color:var(--mut);font-size:12px;margin:6px 0 0}.note{background:var(--warn);color:var(--warnink);border-radius:8px;padding:8px 12px;margin:10px 0;font-size:14px}
footer{margin-top:20px;padding-top:10px;border-top:1px solid var(--line);color:var(--mut);font-size:12px}
@page{size:Letter;margin:0.45in}
@media print{:root{--ink:#1f1f1e;--mut:#6b6a66;--line:#e1e0d9;--bg:#fff;--card:#f6f5f1;--warn:#fff4dc;--warnink:#6b4a00}
body{padding:0;font-size:11.5px;-webkit-print-color-adjust:exact;print-color-adjust:exact}main{max-width:none}h1{font-size:18px}h2{margin:9px 0 3px}
.card .v{font-size:16px}.card{padding:6px 10px}tr{break-inside:avoid}p{margin:0 0 4px}li{margin:1px 0}footer{margin-top:8px;padding-top:6px;font-size:10px}}
"""


def money(n):
    if n is None:
        return None
    if n >= 1e9:
        return f"${n / 1e9:.2f}B"
    if n >= 1e6:
        return f"${n / 1e6:.1f}M" if n < 1e8 else f"${n / 1e6:.0f}M"
    return f"${n / 1e3:.0f}K" if n >= 1e3 else f"${n:,.0f}"


def e(x):
    return html.escape(str(x))


def section(title, items, as_list=True):
    if not items:
        return ""
    body = "<ul>" + "".join(f"<li>{e(i)}</li>" for i in items) + "</ul>" if as_list else "".join(f"<p>{e(i)}</p>" for i in items)
    return f"<h2>{e(title)}</h2>{body}"


def main(src, out):
    p = json.load(open(src))
    amt = p.get("amount")
    q = f" ({e(p['qualifier'])})" if p.get("qualifier") else ""
    amt_txt = (money(amt) + q) if amt is not None else "None recorded"
    amt_note = e(p.get("nature", "")) if amt is not None else "no dollar amount is recorded for this case"
    parent = p.get("parent")
    sub = f"{e(p.get('company', ''))}" + (f" | Parent: {e(parent)}" if parent and parent != p.get("company") else "") + f" | Case {e(p.get('case_id', ''))} | Data pulled {e(p.get('pulled', ''))}"
    parts = [f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
             f"<title>{e(p['title'])}: case brief</title><style>{CSS}</style></head><body><main>",
             f"<h1>{e(p['title'])}</h1><p class=\"sub\">{sub}</p>",
             "<div class=\"cards\">"
             f"<div class=\"card\"><div class=\"l\">Amount</div><div class=\"v\">{amt_txt}</div><div class=\"d\">{amt_note}</div></div>"
             f"<div class=\"card\"><div class=\"l\">Status</div><div class=\"v\" style=\"font-size:15px\">{e(p.get('status', ''))}</div></div>"
             f"<div class=\"card\"><div class=\"l\">Year</div><div class=\"v\">{e(p.get('year', ''))}</div></div></div>",
             section("What happened", p.get("what_happened", []), as_list=False)]
    cost = p.get("cost", [])
    if cost:
        rows = "".join(f"<tr><td>{e(c['label'])}</td><td class=\"n\">{money(c.get('amount')) or 'n/a'}</td><td>{e(c.get('note', ''))}</td></tr>" for c in cost)
        parts.append("<h2>What it cost</h2><table><thead><tr><th>Component</th><th class=\"n\">Amount</th><th>Note</th></tr></thead><tbody>" + rows + "</tbody></table>"
                     "<p class=\"fine\">The amount above is the all-in figure. Components are parts of it and are not added to it.</p>")
    parts += [section("Where and who", p.get("where_who", [])), section("Cause", p.get("cause", [])),
              section("Related cases", p.get("related", [])), section("Lines of business tagged", p.get("lines", []))]
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
