"""Render a name as a vector 'signature' using TeX Gyre Chorus glyph outlines,
with per-glyph jitter so it reads as handwriting rather than typeset text."""

import math, random
from fontTools.ttLib import TTFont as FTFont
from fontTools.pens.recordingPen import RecordingPen

FONT = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrechorus-mediumitalic.otf"


class SignatureRenderer:
    def __init__(self, font_path=FONT, seed=1974):
        self.f = FTFont(font_path)
        self.gs = self.f.getGlyphSet()
        self.upem = self.f["head"].unitsPerEm
        self.cmap = self.f.getBestCmap()
        self.hmtx = self.f["hmtx"]
        self.rng = random.Random(seed)

    def _glyph(self, ch):
        name = self.cmap.get(ord(ch))
        if name is None:
            return None, 0
        pen = RecordingPen()
        self.gs[name].draw(pen)
        adv = self.hmtx[name][0]
        return pen.value, adv

    def measure(self, text, size):
        s = size / self.upem
        w = 0.0
        for ch in text:
            _, adv = self._glyph(ch)
            w += adv * s * (0.86 if ch != " " else 0.55)
        return w

    def draw(self, c, text, x, y, size,
             slant=0.16, jitter_y=0.55, jitter_rot=1.6, tighten=0.86):
        """Draw `text` as filled vector outlines onto reportlab canvas `c`."""
        s = size / self.upem
        pen_x = x
        drift_phase = self.rng.uniform(0, math.pi)
        for i, ch in enumerate(text):
            segs, adv = self._glyph(ch)
            step = adv * s * (tighten if ch != " " else 0.55)
            if segs is None or ch == " ":
                pen_x += step
                continue

            dy = (self.rng.uniform(-jitter_y, jitter_y)
                  + math.sin(drift_phase + i * 0.55) * 0.5)
            rot = math.radians(self.rng.uniform(-jitter_rot, jitter_rot))
            cosr, sinr = math.cos(rot), math.sin(rot)

            def tx(px, py):
                # scale -> rotate about glyph origin -> slant -> translate
                gx, gy = px * s, py * s
                rx = gx * cosr - gy * sinr
                ry = gx * sinr + gy * cosr
                return pen_x + rx + ry * slant, y + ry + dy

            p = c.beginPath()
            started = False
            for op, pts in segs:
                if op == "moveTo":
                    if started:
                        p.close()
                    p.moveTo(*tx(*pts[0]))
                    started = True
                elif op == "lineTo":
                    p.lineTo(*tx(*pts[0]))
                elif op == "curveTo":
                    if len(pts) == 3:
                        a, b, e = pts
                        p.curveTo(*tx(*a), *tx(*b), *tx(*e))
                    else:  # quadratic fallback
                        for j in range(len(pts) - 1):
                            p.lineTo(*tx(*pts[j]))
                        p.lineTo(*tx(*pts[-1]))
                elif op == "qCurveTo":
                    prev = None
                    for j in range(len(pts) - 1):
                        cpt, npt = pts[j], pts[j + 1]
                        if npt is None:
                            continue
                        p.curveTo(*tx(*cpt), *tx(*cpt), *tx(*npt))
                    if pts[-1] is not None:
                        p.lineTo(*tx(*pts[-1]))
                elif op == "closePath":
                    p.close()
                    started = False
            if started:
                p.close()
            c.drawPath(p, stroke=0, fill=1)
            pen_x += step
        return pen_x - x

    def flourish(self, c, x, y, width, size, lw=None):
        """A hand-drawn underline swoosh beneath the signature."""
        c.saveState()
        c.setLineWidth(lw or max(0.5, size * 0.026))
        c.setLineCap(1)
        p = c.beginPath()
        y0 = y - size * 0.16
        p.moveTo(x - size * 0.06, y0 + size * 0.05)
        p.curveTo(x + width * 0.22, y0 - size * 0.14,
                  x + width * 0.55, y0 + size * 0.13,
                  x + width * 0.86, y0 - size * 0.02)
        p.curveTo(x + width * 0.98, y0 - size * 0.09,
                  x + width * 1.02, y0 + size * 0.02,
                  x + width * 1.06, y0 + size * 0.10)
        c.drawPath(p, stroke=1, fill=0)
        c.restoreState()


    # ---- raw PDF content-stream emission (for AcroForm appearance streams) ----
    def emit_ops(self, text, x, y, size, slant=0.16, jitter_y=0.55,
                 jitter_rot=1.6, tighten=0.86, rgb=(0.0, 0.0, 0.0), flourish=False):
        """Return (ops_string, drawn_width) as PDF path operators."""
        import math
        self.rng = random.Random(1974)          # deterministic
        s = size / self.upem
        out = [f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} rg",
               f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} RG"]
        pen_x = x
        drift = self.rng.uniform(0, math.pi)
        for i, ch in enumerate(text):
            segs, adv = self._glyph(ch)
            step = adv * s * (tighten if ch != " " else 0.55)
            if segs is None or ch == " ":
                pen_x += step
                continue
            dy = (self.rng.uniform(-jitter_y, jitter_y)
                  + math.sin(drift + i * 0.55) * 0.5)
            rot = math.radians(self.rng.uniform(-jitter_rot, jitter_rot))
            cosr, sinr = math.cos(rot), math.sin(rot)

            def tx(px, py):
                gx, gy = px * s, py * s
                rx = gx * cosr - gy * sinr
                ry = gx * sinr + gy * cosr
                return pen_x + rx + ry * slant, y + ry + dy

            open_sub = False
            for op, pts in segs:
                if op == "moveTo":
                    if open_sub:
                        out.append("h")
                    a = tx(*pts[0]); out.append(f"{a[0]:.3f} {a[1]:.3f} m")
                    open_sub = True
                elif op == "lineTo":
                    a = tx(*pts[0]); out.append(f"{a[0]:.3f} {a[1]:.3f} l")
                elif op == "curveTo" and len(pts) == 3:
                    a, b, e = (tx(*q) for q in pts)
                    out.append(f"{a[0]:.3f} {a[1]:.3f} {b[0]:.3f} {b[1]:.3f} "
                               f"{e[0]:.3f} {e[1]:.3f} c")
                elif op == "closePath":
                    out.append("h"); open_sub = False
            if open_sub:
                out.append("h")
            out.append("f")
            pen_x += step
        w = pen_x - x

        # optional flourish (off by default: agency signatures are a plain mark)
        if not flourish:
            return "\n".join(out), w
        y0 = y - size * 0.16
        out.append("q")
        out.append(f"{max(0.5, size*0.026):.2f} w 1 J")
        out.append(f"{x - size*0.06:.3f} {y0 + size*0.05:.3f} m")
        out.append(f"{x + w*0.22:.3f} {y0 - size*0.14:.3f} "
                   f"{x + w*0.55:.3f} {y0 + size*0.13:.3f} "
                   f"{x + w*0.86:.3f} {y0 - size*0.02:.3f} c")
        out.append(f"{x + w*0.98:.3f} {y0 - size*0.09:.3f} "
                   f"{x + w*1.02:.3f} {y0 + size*0.02:.3f} "
                   f"{x + w*1.06:.3f} {y0 + size*0.10:.3f} c")
        out.append("S")
        out.append("Q")
        return "\n".join(out), w
