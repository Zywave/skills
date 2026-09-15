#!/usr/bin/env python3
"""
Generic ACORD certificate fill engine.

Shared by every ACORD evidence/certificate skill (24, 27, 28, 29). A per-form script
supplies a FormSpec and a {field_name: value} dict; this module handles appearance
streams, the flattened render, multiline remark boxes, and the signature.

Why explicit appearance streams: setting only /V and relying on NeedAppearances means
the output renders correctly in Acrobat and blank almost everywhere else. Generating an
/AP for every populated field and setting NeedAppearances false makes the fillable copy
render identically in every viewer while staying editable.

Checkbox values are passed as "/1" (ACORD's on-value on these forms); "/Off" is the
off-value and should simply be omitted rather than written.
"""

import io
import os
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (ArrayObject, BooleanObject, DecodedStreamObject,
                           DictionaryObject, NameObject, NumberObject,
                           TextStringObject)
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from signature import SignatureRenderer

ON = "/1"
WARN_PREFIX = "***"          # paragraphs starting with this render in warning red


class FormSpec:
    """Describes one ACORD form for the engine.

    sig_field    field name of the authorized-representative signature
    text_boxes   {field_name: [paragraph, ...]} for multiline boxes (remarks, descriptions)
    prefix       output filename prefix, e.g. "ACORD24"
    """

    def __init__(self, sig_field, prefix, text_boxes=None):
        self.sig_field = sig_field
        self.prefix = prefix
        self.text_boxes = text_boxes or {}


def esc(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def money(v):
    return "" if v in (None, "") else f"{int(v):,}"


def wrap(text, size, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if stringWidth(t, "Helvetica", size) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_paragraphs(paras, width, height, sizes=(6.2, 6.0, 5.8, 5.6, 5.4, 5.2, 5.0, 4.8)):
    """Largest font size from `sizes` whose wrapped lines fit in the box.

    Returns (size, [(line, is_warning), ...]). Never goes below the last size — if the
    text still overflows there, the caller should tighten the prose rather than have the
    engine silently drop a disclosure.
    """
    size, laid = sizes[-1], []
    for s in sizes:
        lead = s * 1.14
        laid = [(ln, p.startswith(WARN_PREFIX)) for p in paras for ln in wrap(p, s, width)]
        if len(laid) * lead <= height:
            size = s
            break
    if not laid:
        laid = [(ln, p.startswith(WARN_PREFIX)) for p in paras for ln in wrap(p, size, width)]
    return size, laid


def field_info(blank):
    """rect + quadding for every named widget, keyed by field name."""
    r = PdfReader(blank)
    info = {}
    for pno, page in enumerate(r.pages):
        for a in page.get("/Annots", []) or []:
            o = a.get_object()
            t = o.get("/T")
            if not t:
                continue
            info[str(t)] = {
                "rect": [float(x) for x in o["/Rect"]],
                "q": int(o.get("/Q", 0) or 0),
                "page": pno,
            }
    return info


def validate(values, spec, info):
    """Return field names the form does not have. Non-empty means the form was revised."""
    wanted = set(values) | set(spec.text_boxes)
    if spec.sig_field:
        wanted.add(spec.sig_field)
    return sorted(w for w in wanted if w not in info)


# ------------------------------------------------------------------ fillable
def write_fillable(blank, values, spec, sig_name, out):
    r = PdfReader(blank)
    w = PdfWriter()
    w.append(r)
    sr = SignatureRenderer()

    acro = w._root_object.get("/AcroForm")
    if acro is None:
        raise SystemExit("blank form has no AcroForm — wrong file")
    acro = acro.get_object()          # may be an IndirectObject; resolve before mutating
    fres = acro.get("/DR")

    made = 0
    for page in w.pages:
        for annot in page.get("/Annots", []) or []:
            o = annot.get_object()
            fid = str(o.get("/T") or "")
            is_box = fid in spec.text_boxes and spec.text_boxes[fid]
            if fid not in values and not is_box:
                continue

            x0, y0, x1, y1 = [float(t) for t in o["/Rect"]]
            wd, ht = x1 - x0, y1 - y0
            val = values.get(fid, "")

            # checkbox
            if str(val).startswith("/"):
                o[NameObject("/V")] = NameObject(val)
                o[NameObject("/AS")] = NameObject(val)
                continue

            if is_box:
                paras = spec.text_boxes[fid]
                pad = 3.0
                aw, ah = wd - 2 * pad, ht - 2 * pad
                size, laid = fit_paragraphs(paras, aw, ah)
                lead = size * 1.14
                L = ["/Tx BMC", "q", f"{pad} {pad} {aw:.2f} {ah:.2f} re W n", "BT",
                     f"/F2 {size:.2f} Tf", f"{lead:.2f} TL",
                     f"{pad:.2f} {ht - pad - size:.2f} Td"]
                for i, (ln, warn) in enumerate(laid):
                    L.append("0.70 0 0.10 rg" if warn else "0 g")
                    L.append(f"({esc(ln)}) Tj")
                    if i < len(laid) - 1:
                        L.append("T*")
                L += ["ET", "Q", "EMC"]
                content = "\n".join(L) + "\n"
                o[NameObject("/V")] = TextStringObject("\n".join(paras))

            elif fid == spec.sig_field:
                size = 17.0
                ops, sw = sr.emit_ops(sig_name, 6.0, 8.0, size)
                while sw > wd - 10 and size > 8:
                    size -= 0.5
                    ops, sw = sr.emit_ops(sig_name, 6.0, 8.0, size)
                content = f"/Tx BMC\nq\n{ops}\nQ\nEMC\n"
                o[NameObject("/V")] = TextStringObject(sig_name)

            else:
                txt = str(val)
                size = min(7.6, ht * 0.66)
                while size > 4.2 and stringWidth(txt, "Helvetica", size) > wd - 4:
                    size -= 0.2
                tw = stringWidth(txt, "Helvetica", size)
                q = int(o.get("/Q", 0) or 0)
                tx = 2.0 if q == 0 else ((wd - tw) / 2.0 if q == 1 else wd - tw - 2.0)
                ty = (ht - size) / 2.0 + size * 0.20
                content = ("/Tx BMC\nq\nBT\n0 g\n"
                           f"/F2 {size:.2f} Tf\n{tx:.2f} {ty:.2f} Td\n({esc(txt)}) Tj\nET\nQ\nEMC\n")
                o[NameObject("/V")] = TextStringObject(txt)

            st = DecodedStreamObject()
            st.set_data(content.encode("latin-1", "replace"))
            st[NameObject("/Type")] = NameObject("/XObject")
            st[NameObject("/Subtype")] = NameObject("/Form")
            st[NameObject("/FormType")] = NumberObject(1)
            st[NameObject("/BBox")] = ArrayObject(
                [NumberObject(0), NumberObject(0),
                 NumberObject(round(wd, 2)), NumberObject(round(ht, 2))])
            if fres is not None:
                st[NameObject("/Resources")] = fres
            ap = DictionaryObject()
            ap[NameObject("/N")] = w._add_object(st)
            o[NameObject("/AP")] = ap
            made += 1

    acro[NameObject("/NeedAppearances")] = BooleanObject(False)
    with open(out, "wb") as fh:
        w.write(fh)
    return made


# ----------------------------------------------------------------- flattened
def write_flat(blank, info, values, spec, sig_name, out):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    sr = SignatureRenderer()

    for fid, val in values.items():
        f = info.get(fid)
        if not f:
            continue
        l, b, r, t = f["rect"]
        if str(val).startswith("/"):
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", min(8.5, (t - b) * 0.72))
            c.drawCentredString((l + r) / 2.0, (b + t) / 2.0 - (t - b) * 0.24, "X")
            continue
        if fid == spec.sig_field:
            continue
        txt = str(val)
        h, wd = t - b, r - l
        size = min(7.6, h * 0.66)
        while size > 4.2 and stringWidth(txt, "Helvetica", size) > wd - 4:
            size -= 0.2
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", size)
        y = b + (h - size) / 2.0 + size * 0.20
        q = f.get("q", 0)
        if q == 2:
            c.drawRightString(r - 2, y, txt)
        elif q == 1:
            c.drawCentredString((l + r) / 2.0, y, txt)
        else:
            c.drawString(l + 2, y, txt)

    for fid, paras in spec.text_boxes.items():
        if not paras or fid not in info:
            continue
        l, b, r, t = info[fid]["rect"]
        x0, y0, x1, y1 = l + 3, b + 3, r - 3, t - 3
        W, H = x1 - x0, y1 - y0
        size, laid = fit_paragraphs(paras, W, H)
        lead = size * 1.14
        y = y1 - size
        for ln, warn in laid:
            if warn:
                c.setFillColorRGB(0.70, 0, 0.10)
                c.setFont("Helvetica-Bold", size)
            else:
                c.setFillColorRGB(0, 0, 0)
                c.setFont("Helvetica", size)
            c.drawString(x0, y, ln)
            y -= lead

    if sig_name and spec.sig_field in info:
        sl, sb, srr, st_ = info[spec.sig_field]["rect"]
        size = 17.0
        sw = sr.measure(sig_name, size)
        while sw > (srr - sl) - 10 and size > 8:
            size -= 0.5
            sw = sr.measure(sig_name, size)
        # Black ink, no underline flourish — matches the fillable copy's appearance
        # stream, which uses the same defaults.
        c.setFillColorRGB(0, 0, 0)
        c.setStrokeColorRGB(0, 0, 0)
        sr.draw(c, sig_name, sl + 6, sb + 8, size)

    c.save()
    buf.seek(0)
    base = PdfReader(blank)
    page = base.pages[0]
    page[NameObject("/Annots")] = ArrayObject()
    page.merge_page(PdfReader(buf).pages[0])
    w = PdfWriter()
    w.add_page(page)
    if "/AcroForm" in w._root_object:
        del w._root_object[NameObject("/AcroForm")]
    with open(out, "wb") as fh:
        w.write(fh)


def render_both(blank, values, spec, sig_name, slug, outdir,
                flat_only=False, fillable_only=False):
    """Validate, then write the fillable and flattened copies. Returns list of paths."""
    info = field_info(blank)
    missing = validate(values, spec, info)
    if missing:
        raise SystemExit(
            "These field names are not on this form revision: " + ", ".join(missing) +
            "\nThe form has been revised, or the wrong blank was downloaded. "
            "Re-derive the field map before filling.")

    os.makedirs(outdir, exist_ok=True)
    written = []
    if not flat_only:
        out = os.path.join(outdir, f"{spec.prefix}_{slug}_FILLABLE.pdf")
        n = write_fillable(blank, values, spec, sig_name, out)
        print(f"fillable : {out}  ({n} appearance streams)")
        written.append(out)
    if not fillable_only:
        out = os.path.join(outdir, f"{spec.prefix}_{slug}.pdf")
        write_flat(blank, info, values, spec, sig_name, out)
        print(f"flattened: {out}")
        written.append(out)
    return written
