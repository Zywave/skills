# Charts and documents

Charts carry two views: where the losses concentrate (lines of business) and the recent trend (by year). Build one small profile JSON, then render it with whatever the environment supports. The JSON is the stable contract, so the same skill works in Claude, ChatGPT, and Copilot.

## Profile JSON

```json
{
  "company": {"name": "Equifax Inc.", "id": 1025384, "ultimate_parent": "Equifax Inc.", "state": "GA"},
  "scope": "entity",
  "pulled": "2026-10-06",
  "headline": {"cases": 665, "total_loss": 3156523055, "contributing": 187,
               "average": 16879802, "largest": 1350000000, "smallest": 0},
  "lines": [{"name": "Cyber", "cases": 145, "total_loss": 2830626439, "contributing": 71}],
  "years": [{"year": 2024, "cases": 2, "contributing": 0}],
  "notes": ["One plain-language bullet each"]
}
```

`contributing` always means "records with an amount". `years` holds the most recent 10 years returned, newest first. Omit `largest` and `smallest` for family scope, where the tool returns no family-wide range.

## Rendering ladder (use the first that works)

1. **claude.ai chat with an inline visual tool:** build a small widget directly from the data: horizontal bars for lines of business (label each bar with "71 of 145 with amount"), and stacked columns by year (records with an amount vs without). Clicking a line of business may ask a follow-up ("show the biggest Cyber cases for this company"). Keep it neutral grays and one accent color, no logo.
2. **HTML preview file (preferred wherever you can write files):** `python scripts/render_html.py profile.json preview.html`. For a family result, put the largest entities in an `entities` array (name, state, cases, total_loss, contributing) and set `"scope": "family"`; the page then shows a table instead of charts.
3. **PDF of the preview:** `python scripts/html_to_pdf.py preview.html preview.pdf`. It tries Playwright Chromium, then a Chrome or Chromium command, then WeasyPrint, and exits with status 2 if none work.
4. **Any environment that can run Python (Claude Code, Cowork, ChatGPT code interpreter, Copilot):** write the profile JSON and run `python scripts/render_charts.py profile.json charts.png`. Show or attach the PNG.
5. **No visuals available:** use a markdown table with a text bar column, for example `Cyber | ██████████ | $2.83B (71 of 145)`.

Chart rules: one y-axis per chart, no dual axes. Never plot a total without its disclosure. The by-year chart shows record counts split into "with amount" and "no amount", because dollar totals per year are mostly gaps and would mislead. Title each chart in plain words, sentence case.

## One-page document

Run `python scripts/make_onepager.py profile.json onepager.docx [charts.png]`. It writes a one-page Word file: title, headline table, lines of business, recent years, notes, the standard footer, and the chart image when given. It has no logo or brand styling. For a PDF, convert with `soffice --headless --convert-to pdf onepager.docx` when LibreOffice is available.
