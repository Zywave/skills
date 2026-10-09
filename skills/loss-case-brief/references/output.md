# Output: profile JSON and files

Build one small profile JSON, then render it with whatever the environment supports. The JSON is the stable contract, so the same skill works in Claude, ChatGPT, and Copilot.

```json
{
  "title": "Equifax data breach",
  "company": "Equifax Inc.",
  "parent": "Equifax Inc.",
  "case_id": 1149779,
  "year": 2017,
  "status": "Provision (the company's own recorded total)",
  "amount": 1350000000,
  "qualifier": "provision",
  "nature": "A company's recorded cost of the breach, including a legal accrual",
  "pulled": "2026-10-06",
  "what_happened": ["Two or three plain sentences each"],
  "cost": [{"label": "Financial damages", "amount": 1350000000, "note": "recorded by the company"}],
  "where_who": ["One short line each"],
  "cause": ["One short line each"],
  "related": ["Part of an incident group of 105 cases; do not add their amounts"],
  "lines": ["Cyber"],
  "notes": ["At most four plain bullets"]
}
```

- `amount` may be omitted when no dollar amount is recorded; the files then say "No dollar amount recorded".
- `qualifier` is "est.", "provision", or empty.
- Never put a sum of components anywhere.

## Rendering ladder
1. **HTML preview** (wherever you can write files): `python scripts/render_brief_html.py profile.json brief.html`. One self-contained file, no scripts or network calls, light and dark aware, one portrait page when printed.
2. **PDF:** `python scripts/html_to_pdf.py brief.html brief.pdf`. Tries Playwright Chromium, then a Chrome or Chromium command, then WeasyPrint, and exits with status 2 if none work.
3. **Word handout:** `python scripts/make_brief_docx.py profile.json brief.docx` (python-docx), one unbranded page.
4. **No files:** the chat brief is the deliverable.
