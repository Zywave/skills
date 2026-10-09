#!/usr/bin/env python3
"""Build a self-contained, static HTML list of ranked losses from a profile JSON.

Usage: python render_explorer_html.py profile.json list.html

No scripts, external fonts, images, or network calls. Each row carries its own
bar on one linear axis. Light and dark aware; prints on one Letter landscape
page for ten cases. Amounts are ranked, never summed.
"""
import html
import json
import sys

FOOTER = ("Source: Zywave loss data. Publicly reported loss events, generally $1M or more, ranked by "
          "disclosed amount. Not a benchmark or a prediction. Smaller companies are underrepresented. "
          "Lines of business show the coverage most likely to respond, not what paid.")

CSS = """
:root{--ink:#1f1f1e;--mut:#6b6a66;--line:#e1e0d9;--bg:#fff;--card:#f6f5f1;--bar:#2a78d6;--track:#eceae3;--warn:#fff4dc;--warnink:#6b4a00;--acc:#e6f0fb;--accink:#0b4a8f}
@media (prefers-color-scheme:dark){:root{--ink:#f0efec;--mut:#a9a8a0;--line:#383835;--bg:#1a1a19;--card:#242423;--bar:#5b9be8;--track:#2e2e2c;--warn:#3a3016;--warnink:#f0d9a0;--acc:#1c2f45;--accink:#a9cdf5}}
*{box-sizing:border-box}body{margin:0;padding:24px;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,Arial,sans-serif}
main{max-width:1000px;margin:0 auto}h1{font-size:22px;margin:0 0 4px;font-weight:600}h2{font-size:15px;margin:22px 0 8px;font-weight:600}
.sub{color:var(--mut);font-size:13px;margin:0 0 14px}.crit{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}
.counts{display:none}.chip{background:var(--card);border-radius:999px;padding:3px 10px;font-size:12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:0 0 6px}
.card{background:var(--card);border-radius:8px;padding:10px 12px}.card .l{font-size:12px;color:var(--mut)}.card .v{font-size:20px;font-weight:600}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:12px;color:var(--mut);font-weight:600}td.r{color:var(--mut);width:28px}td.a{width:230px}
.amt{font-weight:600;font-size:14px;white-space:nowrap}.track{height:7px;background:var(--track);border-radius:4px;margin-top:4px}.fill{height:7px;background:var(--bar);border-radius:4px}
.meta{color:var(--mut);font-size:12px}.badge{display:inline-block;font-size:11px;padding:1px 6px;border-radius:4px;margin:0 0 0 4px;background:var(--warn);color:var(--warnink)}
.badge.i{background:var(--acc);color:var(--accink)}ul{padding-left:20px;margin:6px 0}li{margin:3px 0}
footer{margin-top:20px;padding-top:10px;border-top:1px solid var(--line);color:var(--mut);font-size:12px}
@page{size:Letter landscape;margin:0.35in}
@media print{:root{--ink:#1f1f1e;--mut:#6b6a66;--line:#e1e0d9;--bg:#fff;--card:#f6f5f1;--bar:#2a78d6;--track:#eceae3;--warn:#fff4dc;--warnink:#6b4a00;--acc:#e6f0fb;--accink:#0b4a8f}
body{padding:0;font-size:10px;-webkit-print-color-adjust:exact;print-color-adjust:exact}main{max-width:none}h1{font-size:17px}h2{margin:6px 0 3px}
th,td{padding:1.5px 6px}td.a{width:165px}.card .v{font-size:15px}.card{padding:4px 10px}.cards{margin:0}.sub{margin:0 0 6px}.crit{margin:0 0 6px}tr{break-inside:avoid}.cards{display:none}.counts{display:block;margin:0 0 4px;font-size:11px}.track{margin-top:2px}.badge{padding:0 5px;font-size:10px}footer{margin-top:6px;padding-top:4px;font-size:9px}ul{margin:2px 0}li{margin:1px 0}}
"""


def money(n):
    if n >= 1e9:
        return f"${n / 1e9:.2f}B"
    if n >= 1e6:
        return f"${n / 1e6:.1f}M" if n < 1e8 else f"${n / 1e6:.0f}M"
    return f"${n / 1e3:.0f}K" if n >= 1e3 else f"${n:,.0f}"


def e(x):
    return html.escape(str(x))


def main(src, out):
    p = json.load(open(src))
    pop, cases = p.get("population", {}), p.get("cases", [])
    top = max((c["amount"] for c in cases), default=1) or 1
    parts = [f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
             f"<title>{e(p['title'])}</title><style>{CSS}</style></head><body><main>",
             f"<h1>{e(p['title'])}</h1>",
             f"<p class=\"sub\">Data pulled {e(p.get('pulled', ''))}</p>",
             "<div class=\"crit\">" + "".join(f"<span class=\"chip\">{e(c)}</span>" for c in p.get("criteria", [])) + "</div>",
             "<div class=\"cards\">"
             f"<div class=\"card\"><div class=\"l\">Cases matching</div><div class=\"v\">{pop.get('matching', 0):,}</div></div>"
             f"<div class=\"card\"><div class=\"l\">Ranked (amount at or above the floor)</div><div class=\"v\">{pop.get('ranked', 0):,}</div></div>"
             f"<div class=\"card\"><div class=\"l\">Shown</div><div class=\"v\">{pop.get('shown', len(cases)):,}</div></div></div>",
             f"<p class=\"counts\"><b>{pop.get('matching', 0):,}</b> cases match | <b>{pop.get('ranked', 0):,}</b> ranked (amount at or above the floor) | <b>{pop.get('shown', len(cases)):,}</b> shown</p>",
             "<h2>Largest losses by disclosed amount</h2>",
             "<table><thead><tr><th>#</th><th>Company and year</th><th>What happened</th><th>Amount</th></tr></thead><tbody>"]
    for c in cases:
        q = f" ({e(c['qualifier'])})" if c.get("qualifier") else ""
        w = max(1, round(c["amount"] / top * 100))
        flags = "".join(f"<span class=\"badge{' i' if f in ('same incident',) else ''}\">{e(f)}</span>" for f in c.get("flags", []))
        parts.append(
            f"<tr><td class=\"r\">{e(c['rank'])}</td>"
            f"<td><b>{e(c['company'])}</b><div class=\"meta\">{e(c['year'])} | {e(c.get('status', ''))}</div></td>"
            f"<td>{e(c['what'])}<div class=\"meta\">{e(c.get('component', ''))} {flags}</div></td>"
            f"<td class=\"a\"><div class=\"amt\">{money(c['amount'])}{q}</div><div class=\"track\"><div class=\"fill\" style=\"width:{w}%\"></div></div></td></tr>")
    parts.append("</tbody></table>")
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
