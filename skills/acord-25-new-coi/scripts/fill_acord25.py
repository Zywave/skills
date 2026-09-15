#!/usr/bin/env python3
"""
Fill an ACORD 25 Certificate of Liability Insurance from coi_data.json.

Usage:
    python3 fill_acord25.py <blank_acord25.pdf> <coi_data.json> <output_dir> [--flat-only|--fillable-only]

Produces:
    <output_dir>/ACORD25_<insured>_FILLABLE.pdf   AcroForm intact, all fields editable
    <output_dir>/ACORD25_<insured>.pdf            flattened, renders anywhere

Design notes:
  * Every populated field gets an explicit appearance stream and NeedAppearances is set
    false, so output renders identically in every viewer while staying editable.
  * A policy section whose key is null in coi_data.json is left completely blank. Never
    populate a coverage row for a policy that does not exist.
  * The authorized representative signature is drawn as vector outlines (see signature.py),
    so it embeds with no font dependency.
"""

import argparse, json, os, re, sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (NameObject, TextStringObject, DictionaryObject, ArrayObject,
                           NumberObject, DecodedStreamObject, BooleanObject)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from signature import SignatureRenderer

SIG_FIELD = "Producer_AuthorizedRepresentative_Signature_A"
REMARK = "CertificateOfLiabilityInsurance_ACORDForm_RemarkText_A"
ON = "/1"


def money(v):
    return "" if v in (None, "") else f"{int(v):,}"


def esc(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


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


# ---------------------------------------------------------------- mapping
def build_values(d):
    """coi_data.json -> {field_id: value}. Checkbox values are '/1'."""
    v = {}
    cert = d.get("certificate", {})
    v["Form_CompletionDate_A"] = cert.get("issue_date", "")
    v["CertificateOfInsurance_CertificateNumberIdentifier_A"] = cert.get("number", "")
    v["CertificateOfInsurance_RevisionNumberIdentifier_A"] = str(cert.get("revision", "0"))

    p = d.get("producer", {})
    for fid, key in [
        ("Producer_FullName_A", "name"),
        ("Producer_MailingAddress_LineOne_A", "address1"),
        ("Producer_MailingAddress_LineTwo_A", "address2"),
        ("Producer_MailingAddress_CityName_A", "city"),
        ("Producer_MailingAddress_StateOrProvinceCode_A", "state"),
        ("Producer_MailingAddress_PostalCode_A", "zip"),
        ("Producer_ContactPerson_FullName_A", "contact_name"),
        ("Producer_ContactPerson_PhoneNumber_A", "phone"),
        ("Producer_FaxNumber_A", "fax"),
        ("Producer_ContactPerson_EmailAddress_A", "email"),
        (SIG_FIELD, "authorized_representative"),
    ]:
        if p.get(key):
            v[fid] = p[key]

    ins = d.get("insured", {})
    for fid, key in [
        ("NamedInsured_FullName_A", "name"),
        ("NamedInsured_MailingAddress_LineOne_A", "address1"),
        ("NamedInsured_MailingAddress_LineTwo_A", "address2"),
        ("NamedInsured_MailingAddress_CityName_A", "city"),
        ("NamedInsured_MailingAddress_StateOrProvinceCode_A", "state"),
        ("NamedInsured_MailingAddress_PostalCode_A", "zip"),
    ]:
        if ins.get(key):
            v[fid] = ins[key]

    h = d.get("certificate_holder", {})
    for fid, key in [
        ("CertificateHolder_FullName_A", "name"),
        ("CertificateHolder_MailingAddress_LineOne_A", "address1"),
        ("CertificateHolder_MailingAddress_LineTwo_A", "address2"),
        ("CertificateHolder_MailingAddress_CityName_A", "city"),
        ("CertificateHolder_MailingAddress_StateOrProvinceCode_A", "state"),
        ("CertificateHolder_MailingAddress_PostalCode_A", "zip"),
    ]:
        if h.get(key):
            v[fid] = h[key]

    for i in d.get("insurers", []):
        L = i.get("letter", "").upper()
        if L in "ABCDEF":
            v[f"Insurer_FullName_{L}"] = i.get("name", "")
            v[f"Insurer_NAICCode_{L}"] = str(i.get("naic", "") or "")

    pol = d.get("policies", {})

    # --- General Liability ---
    gl = pol.get("general_liability")
    if gl:
        v["GeneralLiability_CoverageIndicator_A"] = ON
        if gl.get("form_basis") == "claims_made":
            v["GeneralLiability_ClaimsMadeIndicator_A"] = ON
        else:
            v["GeneralLiability_OccurrenceIndicator_A"] = ON
        v["GeneralLiability_InsurerLetterCode_A"] = gl.get("insurer_letter", "")
        v["CertificateOfInsurance_GeneralLiability_AdditionalInsuredCode_A"] = gl.get("additional_insured", "")
        v["Policy_GeneralLiability_SubrogationWaivedCode_A"] = gl.get("subrogation_waived", "")
        v["Policy_GeneralLiability_PolicyNumberIdentifier_A"] = gl.get("policy_number", "")
        v["Policy_GeneralLiability_EffectiveDate_A"] = gl.get("effective", "")
        v["Policy_GeneralLiability_ExpirationDate_A"] = gl.get("expiration", "")
        lim = gl.get("limits", {})
        for fid, key in [
            ("GeneralLiability_EachOccurrence_LimitAmount_A", "each_occurrence"),
            ("GeneralLiability_FireDamageRentedPremises_EachOccurrenceLimitAmount_A", "damage_rented_premises"),
            ("GeneralLiability_MedicalExpense_EachPersonLimitAmount_A", "med_exp"),
            ("GeneralLiability_PersonalAndAdvertisingInjury_LimitAmount_A", "personal_adv_injury"),
            ("GeneralLiability_GeneralAggregate_LimitAmount_A", "general_aggregate"),
            ("GeneralLiability_ProductsAndCompletedOperations_AggregateLimitAmount_A", "products_completed_ops"),
        ]:
            if lim.get(key) is not None:
                v[fid] = money(lim[key])
        agg = (gl.get("aggregate_applies") or "").lower()
        v.update({
            "policy": {"GeneralLiability_GeneralAggregate_LimitAppliesPerPolicyIndicator_A": ON},
            "project": {"GeneralLiability_GeneralAggregate_LimitAppliesPerProjectIndicator_A": ON},
            "loc": {"GeneralLiability_GeneralAggregate_LimitAppliesPerLocationIndicator_A": ON},
        }.get(agg, {}))

    # --- Automobile ---
    au = pol.get("automobile")
    if au:
        v["Vehicle_InsurerLetterCode_A"] = au.get("insurer_letter", "")
        v["CertificateOfInsurance_AutomobileLiability_AdditionalInsuredCode_A"] = au.get("additional_insured", "")
        v["Policy_AutomobileLiability_SubrogationWaivedCode_A"] = au.get("subrogation_waived", "")
        v["Policy_AutomobileLiability_PolicyNumberIdentifier_A"] = au.get("policy_number", "")
        v["Policy_AutomobileLiability_EffectiveDate_A"] = au.get("effective", "")
        v["Policy_AutomobileLiability_ExpirationDate_A"] = au.get("expiration", "")
        for ca in au.get("covered_autos", []):
            fid = {"any_auto": "Vehicle_AnyAutoIndicator_A",
                   "owned": "Vehicle_AllOwnedAutosIndicator_A",
                   "scheduled": "Vehicle_ScheduledAutosIndicator_A",
                   "hired": "Vehicle_HiredAutosIndicator_A",
                   "non_owned": "Vehicle_NonOwnedAutosIndicator_A"}.get(ca)
            if fid:
                v[fid] = ON
        lim = au.get("limits", {})
        for fid, key in [
            ("Vehicle_CombinedSingleLimit_EachAccidentAmount_A", "combined_single_limit"),
            ("Vehicle_BodilyInjury_PerPersonLimitAmount_A", "bodily_injury_per_person"),
            ("Vehicle_BodilyInjury_PerAccidentLimitAmount_A", "bodily_injury_per_accident"),
            ("Vehicle_PropertyDamage_PerAccidentLimitAmount_A", "property_damage_per_accident"),
        ]:
            if lim.get(key) is not None:
                v[fid] = money(lim[key])

    # --- Umbrella / Excess ---
    um = pol.get("umbrella")
    if um:
        if (um.get("policy_type") or "umbrella").lower() == "excess":
            v["Policy_PolicyType_ExcessIndicator_A"] = ON
        else:
            v["Policy_PolicyType_UmbrellaIndicator_A"] = ON
        if um.get("form_basis") == "claims_made":
            v["ExcessUmbrella_ClaimsMadeIndicator_A"] = ON
        else:
            v["ExcessUmbrella_OccurrenceIndicator_A"] = ON
        v["ExcessUmbrella_InsurerLetterCode_A"] = um.get("insurer_letter", "")
        v["CertificateOfInsurance_ExcessLiability_AdditionalInsuredCode_A"] = um.get("additional_insured", "")
        v["Policy_ExcessLiability_SubrogationWaivedCode_A"] = um.get("subrogation_waived", "")
        v["Policy_ExcessLiability_PolicyNumberIdentifier_A"] = um.get("policy_number", "")
        v["Policy_ExcessLiability_EffectiveDate_A"] = um.get("effective", "")
        v["Policy_ExcessLiability_ExpirationDate_A"] = um.get("expiration", "")
        lim = um.get("limits", {})
        if lim.get("each_occurrence") is not None:
            v["ExcessUmbrella_Umbrella_EachOccurrenceAmount_A"] = money(lim["each_occurrence"])
        if lim.get("aggregate") is not None:
            v["ExcessUmbrella_Umbrella_AggregateAmount_A"] = money(lim["aggregate"])
        ret = um.get("retention") or {}
        if ret.get("amount") is not None:
            v["ExcessUmbrella_Umbrella_DeductibleOrRetentionAmount_A"] = money(ret["amount"])
            v["ExcessUmbrella_RetentionIndicator_A" if ret.get("type") == "retention"
              else "ExcessUmbrella_DeductibleIndicator_A"] = ON

    # --- Workers Compensation ---
    wc = pol.get("workers_comp")
    if wc:
        if wc.get("per_statute", True):
            v["WorkersCompensationEmployersLiability_WorkersCompensationStatutoryLimitIndicator_A"] = ON
        v["WorkersCompensationEmployersLiability_InsurerLetterCode_A"] = wc.get("insurer_letter", "")
        v["WorkersCompensationEmployersLiability_AnyPersonsExcludedIndicator_A"] = wc.get("any_excluded", "N")
        v["Policy_WorkersCompensation_SubrogationWaivedCode_A"] = wc.get("subrogation_waived", "")
        v["Policy_WorkersCompensationAndEmployersLiability_PolicyNumberIdentifier_A"] = wc.get("policy_number", "")
        v["Policy_WorkersCompensationAndEmployersLiability_EffectiveDate_A"] = wc.get("effective", "")
        v["Policy_WorkersCompensationAndEmployersLiability_ExpirationDate_A"] = wc.get("expiration", "")
        lim = wc.get("limits", {})
        for fid, key in [
            ("WorkersCompensationEmployersLiability_EmployersLiability_EachAccidentLimitAmount_A", "el_each_accident"),
            ("WorkersCompensationEmployersLiability_EmployersLiability_DiseaseEachEmployeeLimitAmount_A", "el_disease_each_employee"),
            ("WorkersCompensationEmployersLiability_EmployersLiability_DiseasePolicyLimitAmount_A", "el_disease_policy_limit"),
        ]:
            if lim.get(key) is not None:
                v[fid] = money(lim[key])

    return {k: val for k, val in v.items() if val not in (None, "")}


def remark_paragraphs(d):
    paras = list(d.get("description_of_operations") or [])
    if d.get("meta", {}).get("specimen"):
        tag = ("*** SPECIMEN - MOCK CERTIFICATE FOR SOFTWARE DEMONSTRATION - "
               "NOT VALID EVIDENCE OF INSURANCE - NO COVERAGE IS AFFORDED ***")
        if not any(p.startswith("***") for p in paras):
            paras.append(tag)
    return paras


# ---------------------------------------------------------------- writers
def write_fillable(blank, info, values, paras, sig_name, out):
    reader = PdfReader(blank)
    w = PdfWriter()
    w.append(reader)
    page = w.pages[0]
    acro = w._root_object["/AcroForm"]
    fres = DictionaryObject()
    fres[NameObject("/Font")] = acro["/DR"]["/Font"]
    sr = SignatureRenderer()
    made = 0

    for annot in page["/Annots"]:
        o = annot.get_object()
        fid = o.get("/T")
        if fid not in values and not (fid == REMARK and paras):
            continue
        x0, y0, x1, y1 = [float(t) for t in o["/Rect"]]
        wd, ht = x1 - x0, y1 - y0
        val = values.get(fid, "")

        if str(val).startswith("/"):
            o[NameObject("/V")] = NameObject(val)
            o[NameObject("/AS")] = NameObject(val)
            continue

        if fid == REMARK:
            pad = 3.0
            aw, ah = wd - 2 * pad, ht - 2 * pad
            size, laid = 4.8, []
            for s in [6.2, 6.0, 5.8, 5.6, 5.4, 5.2, 5.0, 4.8]:
                lead = s * 1.14
                laid = [(ln, p.startswith("***")) for p in paras for ln in wrap(p, s, aw)]
                if len(laid) * lead <= ah:
                    size = s
                    break
            lead = size * 1.14
            L = ["/Tx BMC", "q", f"{pad} {pad} {aw:.2f} {ah:.2f} re W n", "BT",
                 f"/F2 {size:.2f} Tf", f"{lead:.2f} TL", f"{pad:.2f} {ht - pad - size:.2f} Td"]
            for i, (ln, warn) in enumerate(laid):
                L.append("0.70 0 0.10 rg" if warn else "0 g")
                L.append(f"({esc(ln)}) Tj")
                if i < len(laid) - 1:
                    L.append("T*")
            L += ["ET", "Q", "EMC"]
            content = "\n".join(L) + "\n"
            o[NameObject("/V")] = TextStringObject("\n".join(paras))
        elif fid == SIG_FIELD:
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
            [NumberObject(0), NumberObject(0), NumberObject(round(wd, 2)), NumberObject(round(ht, 2))])
        st[NameObject("/Resources")] = fres
        ap = DictionaryObject()
        ap[NameObject("/N")] = w._add_object(st)
        o[NameObject("/AP")] = ap
        made += 1

    acro[NameObject("/NeedAppearances")] = BooleanObject(False)
    with open(out, "wb") as fh:
        w.write(fh)
    return made


def write_flat(blank, info, values, paras, sig_name, out):
    import io
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    sr = SignatureRenderer()

    for fid, val in values.items():
        f = info[fid]
        l, b, r, t = f["rect"]
        if str(val).startswith("/"):
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", min(8.5, (t - b) * 0.72))
            c.drawCentredString((l + r) / 2.0, (b + t) / 2.0 - (t - b) * 0.24, "X")
            continue
        if fid == SIG_FIELD:
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

    if paras and REMARK in info:
        l, b, r, t = info[REMARK]["rect"]
        x0, y0, x1, y1 = l + 3, b + 3, r - 3, t - 3
        W, H = x1 - x0, y1 - y0
        size, laid = 4.8, []
        for s in [6.2, 6.0, 5.8, 5.6, 5.4, 5.2, 5.0, 4.8]:
            lead = s * 1.14
            laid = [(ln, p.startswith("***")) for p in paras for ln in wrap(p, s, W)]
            if len(laid) * lead <= H:
                size = s
                break
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

    if sig_name and SIG_FIELD in info:
        sl, sb, srr, st_ = info[SIG_FIELD]["rect"]
        size = 17.0
        sw = sr.measure(sig_name, size)
        while sw > (srr - sl) - 10 and size > 8:
            size -= 0.5
            sw = sr.measure(sig_name, size)
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


def field_info(blank):
    """rect + quadding for every named widget on page 1."""
    r = PdfReader(blank)
    info = {}
    for a in r.pages[0].get("/Annots", []):
        o = a.get_object()
        t = o.get("/T")
        if not t:
            continue
        info[t] = {"rect": [float(x) for x in o["/Rect"]], "q": int(o.get("/Q", 0) or 0)}
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("blank")
    ap.add_argument("data")
    ap.add_argument("outdir")
    ap.add_argument("--flat-only", action="store_true")
    ap.add_argument("--fillable-only", action="store_true")
    a = ap.parse_args()

    d = json.load(open(a.data))
    info = field_info(a.blank)
    values = build_values(d)
    unknown = [k for k in values if k not in info]
    if unknown:
        sys.exit("Field names not present in this ACORD 25 revision: " + ", ".join(unknown))

    paras = remark_paragraphs(d)
    sig = d.get("producer", {}).get("authorized_representative", "")
    slug = re.sub(r"[^A-Za-z0-9]+", "_",
                  d.get("insured", {}).get("name", "Insured")).strip("_")
    os.makedirs(a.outdir, exist_ok=True)

    if not a.flat_only:
        out = os.path.join(a.outdir, f"ACORD25_{slug}_FILLABLE.pdf")
        n = write_fillable(a.blank, info, values, paras, sig, out)
        print(f"fillable : {out}  ({n} appearance streams)")
    if not a.fillable_only:
        out = os.path.join(a.outdir, f"ACORD25_{slug}.pdf")
        write_flat(a.blank, info, values, paras, sig, out)
        print(f"flattened: {out}")

    empty = [k for k in ("automobile", "umbrella", "general_liability", "workers_comp")
             if not d.get("policies", {}).get(k)]
    if empty:
        print("coverage rows left blank (no policy in force): " + ", ".join(empty))


if __name__ == "__main__":
    main()
