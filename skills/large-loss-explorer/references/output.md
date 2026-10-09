# Output: profile JSON, files, and charts

Build one small profile JSON, then render it with whatever the environment supports. The JSON is the stable contract, so the same skill works in Claude, ChatGPT, and Copilot.

## Profile JSON

```json
{
  "title": "Largest Tech E&O losses since 2016",
  "criteria": ["Tech E&O on any line of business", "Case year 2016 or later", "Disclosed amount of $1M or more"],
  "pulled": "2026-10-06",
  "population": {"matching": 1780, "ranked": 45, "shown": 10},
  "cases": [
    {"rank": 1, "id": 5426532, "company": "Uber B.V.", "year": 2026, "amount": 966000000,
     "qualifier": "", "component": "Fine or penalty", "status": "Settled",
     "what": "Data protection regulator fine over automated driver account deactivations",
     "flags": ["government regulator"]}
  ],
  "notes": ["One plain-language bullet each, at most four"]
}
```

- `what` is one line of about 90 characters at most.
- `matching` is cases that match the criteria without the amount floor; `ranked` is cases at or above the floor; `shown` is the page.
- `qualifier` is "est." for an estimate or "provision" for a company's own total, otherwise empty.
- `flags` is a short list: "estimate", "same incident", "government", "fraud against a program", "insured and uninsured".
- Never put a total or average of the amounts anywhere. Cases are ranked, not summed.

## Rendering ladder (use the first that works)

1. **claude.ai chat with an inline visual tool:** a small widget with one row per case and a bar in each row on a linear axis. Clicking a row may ask for that case's brief. Keep it neutral, no logo, and keep the plain table as the fallback.
2. **HTML preview file (wherever you can write files):** `python scripts/render_explorer_html.py profile.json list.html`. It is one self-contained file with no scripts or network calls, light and dark aware, landscape when printed.
3. **PDF of the preview:** `python scripts/html_to_pdf.py list.html list.pdf`. It tries Playwright Chromium, then a Chrome or Chromium command, then WeasyPrint, and exits with status 2 if none work.
4. **No visuals available:** a markdown table with a text bar column, for example `Uber B.V. | ██████████ | $966M`.

Chart rules: one linear axis, never a log scale, never a total without its disclosure.
