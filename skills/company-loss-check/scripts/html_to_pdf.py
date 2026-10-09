#!/usr/bin/env python3
"""Convert the HTML preview to a PDF, using whichever renderer is available.

Usage: python html_to_pdf.py preview.html preview.pdf

Tries, in order: Playwright Chromium, a Chrome or Chromium command, WeasyPrint.
Exits with status 2 and a clear message if none work, so the caller can still
deliver the HTML. The page's print stylesheet forces a light theme and a
Letter page, so the PDF looks the same whatever theme the viewer prefers.
"""
import os
import shutil
import subprocess
import sys


def via_playwright(src, out):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto("file://" + os.path.abspath(src))
        pg.emulate_media(media="print", color_scheme="light")
        pg.pdf(path=out, format="Letter", print_background=True, prefer_css_page_size=True)
        b.close()


def via_cli(src, out):
    exe = next((shutil.which(n) for n in ("chromium", "chromium-browser", "google-chrome", "chrome") if shutil.which(n)), None)
    if not exe:
        raise RuntimeError("no chrome or chromium command")
    subprocess.run([exe, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={os.path.abspath(out)}", "file://" + os.path.abspath(src)],
                   check=True, capture_output=True, timeout=90)


def via_weasyprint(src, out):
    from weasyprint import HTML
    HTML(filename=src).write_pdf(out)


def main(src, out):
    errors = []
    for fn in (via_playwright, via_cli, via_weasyprint):
        try:
            fn(src, out)
            if os.path.exists(out) and os.path.getsize(out) > 1000:
                print(out, f"(via {fn.__name__[4:]})")
                return 0
        except Exception as ex:  # try the next renderer
            errors.append(f"{fn.__name__}: {type(ex).__name__}")
    print("No PDF renderer worked (" + "; ".join(errors) + "). Deliver the HTML preview and say a PDF could not be made here.")
    return 2


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
