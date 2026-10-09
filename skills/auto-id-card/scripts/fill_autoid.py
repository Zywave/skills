#!/usr/bin/env python3
"""
Fill an ACORD auto ID card form from autoid_data.json.

Usage:
    python3 fill_autoid.py <blank_form.pdf> <autoid_data.json> <output_dir>
      [--prefix NAME] [--fillable-only|--flat-only]

Produces, per sheet:
    <output_dir>/<prefix>_FILLABLE.pdf   AcroForm intact, every field editable
    <output_dir>/<prefix>.pdf            flattened, renders anywhere

Why it works this way:

  * Slots are discovered from the blank form, never hardcoded. Card sheets repeat the
    same element with different suffixes, and the suffix scheme is not consistent across
    forms: the countrywide 4-up set uses Vehicle_VINIdentifier_A..D for vehicles but
    NamedInsured_FullName_A, _A1, _A2, _A3 for the insured. Sorting each element's own
    suffixes and zipping them to card index handles all 44 forms without a per-form table.

  * Every populated field gets an explicit appearance stream and NeedAppearances is set
    false. A filled AcroForm that relies on the viewer to draw its own appearances looks
    correct in Acrobat and blank in stricter renderers, which is a silent and expensive
    failure for a document that ends up in a glovebox.

  * Text is measured and shrunk to fit before it is drawn. Card fields are narrow and the
    forms declare a fixed 8pt font, so nothing shrinks on its own. An overlong model name
    will otherwise run across the VIN and make the one field that matters unreadable.
"""

import argparse, collections, io, json, os, re, sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (NameObject, TextStringObject, DictionaryObject, ArrayObject,
                           NumberObject, DecodedStreamObject, BooleanObject)
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vin import check as vin_check, normalize as vin_norm

ON = "/1"
SUFFIX = re.compile(r"_([A-Z]\d*)$")
STATE_CODES = frozenset(
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH "
    "NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split())

# Elements that are alternate spellings of the same value. Several forms name the insured
# block differently (Texas uses NamedInsuredOrCoveredPerson_*), so the mapping emits both and
# only one will exist on any given form. Reporting the unused twin as a gap is noise, and noise
# in that list is what makes a real gap easy to miss.
ALIASES = [
    {"NamedInsured_FullName", "NamedInsuredOrCoveredPerson_FullName"},
    {"NamedInsured_MailingAddress_LineOne", "NamedInsuredOrCoveredPerson_MailingAddress_LineOne"},
    {"NamedInsured_MailingAddress_CityName", "NamedInsuredOrCoveredPerson_MailingAddress_CityName"},
    {"NamedInsured_MailingAddress_StateOrProvinceCode",
     "NamedInsuredOrCoveredPerson_MailingAddress_StateOrProvinceCode",
     "NamedInsured_StateOrProvinceName"},
    {"NamedInsured_MailingAddress_PostalCode", "NamedInsuredOrCoveredPerson_MailingAddress_PostalCode"},
    {"Producer_PhoneNumber", "Producer_ContactPerson_PhoneNumber"},
]

# Fields a card can carry that no amount of reading a dec page will produce, because they are
# not on the dec page. A producer has these to hand: this list is what turns "left blank" into
# a question worth asking instead of a silent gap. Text is what to ask for.
ASKABLE = {
    "Vehicle_RegisteredOwner_FullName": "registered owner of the vehicle, if not the named insured",
    "Vehicle_Registration_LicensePlateIdentifier": "license plate number",
    "Vehicle_BodyCode": "body type code",
    "Insurer_ADOTCode": "carrier's Arizona DOT code",
    "Insurer_StateIdentifier": "carrier's state identification number",
    "Loss_LossReport_PhoneNumber": "claims reporting phone number",
    "AdditionalInterest_FullName": "additional interest (lienholder or lessor) name",
    "Insurer_MedicalTreatmentContact_FullName": "carrier's medical treatment contact name",
    "Insurer_MedicalTreatmentContact_AddressLineOne": "medical treatment contact address",
    "Insurer_MedicalTreatmentContact_CityName": "medical treatment contact city",
    "Insurer_MedicalTreatmentContact_StateOrProvinceCode": "medical treatment contact state",
    "Insurer_MedicalTreatmentContact_PostalCode": "medical treatment contact ZIP",
    "Insurer_MedicalTreatmentContact_FaxNumber": "medical treatment contact fax",
    "Insurer_MedicalTreatmentContact_EmailAddress": "medical treatment contact email",
    "Driver_Excluded_Surname": "excluded driver surname, if the policy excludes anyone",
    "Driver_Excluded_GivenName": "excluded driver given name",
    "Driver_Excluded_OtherGivenNameInitial": "excluded driver middle initial",
    "AutomobileIdentificationCard_RemarkText": "any remark the carrier or state requires",
    "Vehicle_PIP_CoverageExistsIndicator": "whether PIP coverage is in force (yes/no)",
    "Vehicle_BodilyInjury_CoverageExistsIndicator": "whether bodily injury coverage is in force (yes/no)",
    "Vehicle_Coverage_NamedDriverIndicator": "whether this is a named-driver policy (yes/no)",
    "Producer_EmergencyContactIndicator": "whether the agency is the emergency contact (yes/no)",
    "Insurer_EmergencyContactIndicator": "whether the carrier is the emergency contact (yes/no)",
}


def esc(s):
    return str(s).replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def suffix_key(s):
    """Sort _A, _B .. then _A1, _A2 so slot order matches visual card order."""
    m = re.match(r"^([A-Z])(\d*)$", s)
    return (int(m.group(2)) if m.group(2) else 0, m.group(1)) if m else (99, s)


# ------------------------------------------------------------------ form introspection
def scan(pdf):
    """Return {element: {suffix: {field, rect, page, type, quad}}} plus page sizes."""
    r = PdfReader(pdf)
    els, pages = {}, []
    for pi, page in enumerate(r.pages):
        box = page.mediabox
        pages.append((float(box.width), float(box.height)))
        for a in (page.get("/Annots") or []):
            try:
                o = a.get_object()
            except Exception:
                continue
            name = o.get("/T")
            if not name:
                continue
            name = str(name)
            m = SUFFIX.search(name)
            el, sx = (name[:m.start()], m.group(1)) if m else (name, "")
            rect = [float(x) for x in o["/Rect"]]
            els.setdefault(el, {})[sx] = dict(
                field=name, page=pi,
                rect=[min(rect[0], rect[2]), min(rect[1], rect[3]),
                      max(rect[0], rect[2]), max(rect[1], rect[3])],
                type=str(o.get("/FT", "/Tx")), quad=int(o.get("/Q", 0) or 0))
    return els, pages


# Forms where two VIN slots are two COPIES of one card, not two cards. Confirmed from each
# form's own text: Michigan labels its columns VEHICLE COPY and SECRETARY OF STATE'S COPY,
# and Kentucky instructs the policyholder to give one copy to the County Clerk and carry the
# other. Filling these as separate cards puts two different vehicles on one physical card.
# Keys are matched against the blank form's filename.
COPY_GROUPS = {
    # Michigan: pages 1 and 2 are a two-vehicle duplex set, each vehicle getting a VEHICLE
    # COPY and a SECRETARY OF STATE'S COPY. Page 3 is a single-vehicle single-sided layout of
    # the same pair, so vehicle 1 also fills C and C1.
    ("50", "MI"): [["A", "A1", "C", "C1"], ["B", "B1"]],
    ("50", "KY"): [["A", "A1"]],
}

# States whose card requires the insured be issued two cards per vehicle. The form gives one
# slot per card, so the producer prints the sheet twice or runs the vehicle twice. This is a
# disclosure, not something to guess at by pairing slots.
TWO_CARD_NOTE = {("50", "CT"), ("50", "MO"), ("50", "NJ"), ("51", "NJ"),
                 ("50", "SD"), ("50", "AZ")}


def form_key(blank_path):
    """(form number, state) from the filename, tolerating either naming convention.

    The library serves these as `ACORD 0050 MI 2019-08 Acroform.pdf`; a saved copy is often
    `ACORD 50 MI - Michigan Certificate of No-Fault Insurance.pdf`. Matching on the raw string
    silently misses one of them, and a missed match here means two different vehicles land on
    what is physically one card.
    """
    name = os.path.basename(blank_path)
    m = re.search(r"ACORD[\s_]*0*(\d+)[\s_]+([A-Z]{2})\b", name, re.I)
    # "WM" is a print variant marker, not a state, and both countrywide watermark forms would
    # otherwise collide on the same key while holding different numbers of cards.
    if m and m.group(2).upper() in STATE_CODES:
        return (m.group(1), m.group(2).upper())
    m2 = re.search(r"ACORD[\s_]*0*(\d+)", name, re.I)
    return (m2.group(1), None) if m2 else (None, None)


def copy_groups_for(blank_path):
    return COPY_GROUPS.get(form_key(blank_path))


def slots_per_sheet(els, groups=None):
    """Vehicles one sheet of this form can carry.

    Capacity is counted PER PAGE, not across the document. Several forms repeat the same card
    on a later page as an alternate print layout: the countrywide ACORD 50 says outright to use
    pages 2 and 3 for two-sided printing, and the Nevada 51/53/54 do the same. Counting every
    VIN widget in the file treats those duplicates as extra capacity, which leaves a blank card
    on the variant page with one vehicle and, with two, prints vehicle 2 on the back of
    vehicle 1's card.
    """
    vin = els.get("Vehicle_VINIdentifier", {})
    if not vin:
        return 1
    if groups:
        return len([g for g in groups if any(sx in vin for sx in g)])
    per_page = collections.Counter(f["page"] for f in vin.values())
    return max(1, max(per_page.values()))


def page_of_slot(els, element, sx):
    return els.get(element, {}).get(sx, {}).get("page")


def slot_order(els, element):
    return sorted(els.get(element, {}), key=suffix_key)


# ------------------------------------------------------------------ data -> field values
def card_values(d, veh):
    """Per-card element -> value. Absent keys are simply not written."""
    ins, car, pol, prod = (d.get(k) or {} for k in ("insured", "carrier", "policy", "producer"))
    v = {
        "Vehicle_ModelYear": veh.get("year"),
        "Vehicle_ManufacturersName": veh.get("make"),
        "Vehicle_ModelName": veh.get("model"),
        "Vehicle_VINIdentifier": vin_norm(veh.get("vin")),
        "Vehicle_Registration_LicensePlateIdentifier": veh.get("plate"),
        "NamedInsured_FullName": ins.get("name"),
        "NamedInsuredOrCoveredPerson_FullName": ins.get("name"),
        "NamedInsured_MailingAddress_LineOne": ins.get("address_line_1"),
        "NamedInsured_MailingAddress_LineTwo": ins.get("address_line_2"),
        "NamedInsured_MailingAddress_CityName": ins.get("city"),
        "NamedInsured_MailingAddress_StateOrProvinceCode": ins.get("state"),
        "NamedInsured_MailingAddress_PostalCode": ins.get("zip"),
        "NamedInsured_StateOrProvinceName": d.get("routing", {}).get("state_name"),
        "NamedInsuredOrCoveredPerson_MailingAddress_LineOne": ins.get("address_line_1"),
        "NamedInsuredOrCoveredPerson_MailingAddress_CityName": ins.get("city"),
        "NamedInsuredOrCoveredPerson_MailingAddress_StateOrProvinceCode": ins.get("state"),
        "NamedInsuredOrCoveredPerson_MailingAddress_PostalCode": ins.get("zip"),
        "Insurer_FullName": car.get("name"),
        "Insurer_NAICCode": car.get("naic"),
        "Insurer_MailingAddress_AddressLineOne": car.get("address_line_1"),
        "Insurer_MailingAddress_CityName": car.get("city"),
        "Insurer_MailingAddress_StateOrProvinceCode": car.get("state"),
        "Insurer_MailingAddress_PostalCode": car.get("zip"),
        "Policy_PolicyNumberIdentifier": pol.get("number"),
        "Policy_EffectiveDate": pol.get("effective_date"),
        "Policy_ExpirationDate": pol.get("expiration_date"),
        "Producer_FullName": prod.get("name"),
        "Producer_MailingAddress_LineOne": prod.get("address_line_1"),
        "Producer_MailingAddress_LineTwo": prod.get("address_line_2"),
        "Producer_MailingAddress_CityName": prod.get("city"),
        "Producer_MailingAddress_StateOrProvinceCode": prod.get("state"),
        "Producer_MailingAddress_PostalCode": prod.get("zip"),
        "Producer_PhoneNumber": prod.get("phone"),
        "Producer_ContactPerson_PhoneNumber": prod.get("phone"),
        # State-specific fields. Each appears on only a handful of forms, and each is something
        # the producer has even when the dec page does not state it.
        # Registered owner is usually the same across a fleet, so it takes a policy-level
        # default. Leaving this per-vehicle only is how a card gets FLEET checked and the
        # owner line blank, which is a visible hole on a statutory form.
        "Vehicle_RegisteredOwner_FullName": (veh.get("registered_owner")
                                             or pol.get("registered_owner")
                                             or (ins.get("name") if pol.get("fleet") else None)),
        "Vehicle_BodyCode": veh.get("body_type"),
        "Insurer_ADOTCode": car.get("adot_code"),
        "Insurer_StateIdentifier": car.get("state_id"),
        "Loss_LossReport_PhoneNumber": car.get("claims_phone"),
        "AdditionalInterest_FullName": veh.get("additional_interest"),
        "AutomobileIdentificationCard_RemarkText": d.get("remark"),
    }
    med = (car.get("medical_treatment_contact") or {})
    for key, el in (("name", "FullName"), ("address_line_1", "AddressLineOne"), ("city", "CityName"),
                    ("state", "StateOrProvinceCode"), ("zip", "PostalCode"),
                    ("fax", "FaxNumber"), ("email", "EmailAddress")):
        if med.get(key):
            v[f"Insurer_MedicalTreatmentContact_{el}"] = med[key]
    exc = (veh.get("excluded_driver") or {})
    if exc.get("surname"):
        v["Driver_Excluded_Surname"] = exc["surname"]
        v["Driver_Excluded_GivenName"] = exc.get("given_name")
        v["Driver_Excluded_OtherGivenNameInitial"] = exc.get("middle_initial")
    for key, el in (("pip", "Vehicle_PIP_CoverageExistsIndicator"),
                    ("bodily_injury", "Vehicle_BodilyInjury_CoverageExistsIndicator"),
                    ("named_driver", "Vehicle_Coverage_NamedDriverIndicator")):
        if veh.get(key) is True:
            v[el] = ON
    lob = (pol.get("line_of_business") or "").lower()
    if lob.startswith("comm"):
        v["Policy_BroadLineOfBusiness_CommercialIndicator"] = ON
    elif lob.startswith("pers"):
        v["Policy_BroadLineOfBusiness_PersonalIndicator"] = ON
    if pol.get("fleet"):
        v["Policy_BroadLineOfBusiness_FleetIndicator"] = ON
    return {k: val for k, val in v.items() if val not in (None, "")}


def alias_covered(el, filled):
    """True when a twin of this element did land on the form."""
    for group in ALIASES:
        if el in group and (group & filled):
            return True
    return False


def plan_sheet(els, data, vehicles, groups=None):
    """Resolve {field_name: value} for one sheet's worth of vehicles.

    Returns the values plus two lists the caller reports:
      dropped  - data supplied that this form has nowhere to put
      unfilled - fields this form DOES carry that no data reached
    The second list is the useful one. A card printing blank where the state asked a question
    is a gap the producer can close from memory, so it deserves a question rather than silence.
    """
    out, wanted, filled = {}, [], set()
    vin_slots = els.get("Vehicle_VINIdentifier", {})
    for i, veh in enumerate(vehicles):
        vals = card_values(data, veh)
        if groups:
            targets = groups[i] if i < len(groups) else []
        else:
            # One slot index per page, so a variant page receives the same vehicle rather than
            # the next one. Slots are ordered within each page.
            by_page = collections.defaultdict(list)
            for sx in slot_order(els, "Vehicle_VINIdentifier"):
                by_page[vin_slots[sx]["page"]].append(sx)
            targets = [sxs[i] for sxs in by_page.values() if i < len(sxs)]
        for el, value in vals.items():
            wanted.append(el)
            order = slot_order(els, el)
            if not order:
                continue
            filled.add(el)
            placed = False
            for sx in targets:
                if sx in els[el]:
                    out[els[el][sx]["field"]] = value
                    placed = True
            if not placed:
                # Element does not share the VIN's suffix scheme on this form. Fall back to
                # positional order, which is right for the single-card and 4-up layouts.
                sx = order[i] if i < len(order) else order[-1]
                out[els[el][sx]["field"]] = value
    dropped = sorted({e for e in wanted if e not in filled and not alias_covered(e, filled)})
    unfilled = sorted(e for e in els if e not in filled
                      and e not in ("Form_EditionIdentifier", "Form_CompletionDate",
                                    "Form_CurrentPageNumber", "Form_TotalPageNumber",
                                    "Producer_CustomerIdentifier", "Location_ProducerIdentifier")
                      and not alias_covered(e, filled))
    return out, dropped, unfilled


# ------------------------------------------------------------------ writers
def fit(txt, wd, cap=8.0, floor=4.6):
    """Shrink, then truncate as a last resort. Returns (text, size, was_truncated).

    The forms declare a fixed 8pt font, so nothing shrinks on its own and an overlong
    value will otherwise run across the field to its right. Shrinking is invisible and
    fine. Truncation changes what the card says, so the caller has to be told: that flag
    is what drives the report the producer reads before delivering.
    """
    size = cap
    while size > floor and stringWidth(txt, "Helvetica", size) > wd - 3:
        size -= 0.2
    truncated = False
    while stringWidth(txt, "Helvetica", size) > wd - 3 and len(txt) > 1:
        txt = txt[:-1]
        truncated = True
    return txt, size, truncated


def specimen_overlay(pw, ph, cards):
    """Diagonal SPECIMEN watermark across every card on the sheet.

    Test and training cards that can pass for real ones are the liability this guards
    against, so the mark goes on the page content where neither flattening nor editing
    the form fields can remove it.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(pw, ph))
    c.setFont("Helvetica-Bold", 22)
    try:
        c.setFillColorRGB(0.85, 0.20, 0.20, alpha=0.28)
    except TypeError:
        c.setFillColorRGB(0.95, 0.65, 0.65)
    spots = cards or [(pw / 2.0, ph / 2.0)]
    for cx, cy in spots:
        c.saveState()
        c.translate(cx, cy)
        c.rotate(28)
        c.drawCentredString(0, 0, "SPECIMEN")
        c.restoreState()
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def card_centres(info, page_index):
    """Rough centre of each card, taken from the VIN field positions on that page."""
    out = []
    for sx in sorted(info.get("Vehicle_VINIdentifier", {}), key=suffix_key):
        f = info["Vehicle_VINIdentifier"][sx]
        if f["page"] != page_index:
            continue
        l, b, r, t = f["rect"]
        out.append(((l + r) / 2.0, (b + t) / 2.0))
    return out


def write_fillable(blank, values, info, out, specimen=False):
    r = PdfReader(blank)
    w = PdfWriter()
    w.append(r)
    acro = w._root_object["/AcroForm"]
    fres = DictionaryObject()
    try:
        fres[NameObject("/Font")] = acro["/DR"]["/Font"]
    except Exception:
        pass
    made, trimmed = 0, []
    for page in w.pages:
        for a in (page.get("/Annots") or []):
            o = a.get_object()
            fid = o.get("/T")
            if fid is None:
                continue
            fid = str(fid)
            if fid not in values:
                continue
            val = str(values[fid])
            x0, y0, x1, y1 = [float(t) for t in o["/Rect"]]
            wd, ht = abs(x1 - x0), abs(y1 - y0)
            if val.startswith("/"):
                o[NameObject("/V")] = NameObject(val)
                o[NameObject("/AS")] = NameObject(val)
                made += 1
                continue
            txt, size, clip = fit(val, wd, cap=min(8.0, ht * 0.70))
            if clip:
                trimmed.append((fid, val, txt))
            tw = stringWidth(txt, "Helvetica", size)
            q = int(o.get("/Q", 0) or 0)
            tx = 2.0 if q == 0 else ((wd - tw) / 2.0 if q == 1 else max(2.0, wd - tw - 2.0))
            ty = (ht - size) / 2.0 + size * 0.20
            content = ("/Tx BMC\nq\nBT\n0 g\n"
                       f"/F2 {size:.2f} Tf\n{tx:.2f} {ty:.2f} Td\n({esc(txt)}) Tj\nET\nQ\nEMC\n")
            st = DecodedStreamObject()
            st.set_data(content.encode("latin-1", "replace"))
            st[NameObject("/Type")] = NameObject("/XObject")
            st[NameObject("/Subtype")] = NameObject("/Form")
            st[NameObject("/FormType")] = NumberObject(1)
            st[NameObject("/BBox")] = ArrayObject([NumberObject(0), NumberObject(0),
                                                   NumberObject(round(wd, 2)), NumberObject(round(ht, 2))])
            if fres:
                st[NameObject("/Resources")] = fres
            ap = DictionaryObject()
            ap[NameObject("/N")] = w._add_object(st)
            o[NameObject("/AP")] = ap
            o[NameObject("/V")] = TextStringObject(txt)
            made += 1
    acro[NameObject("/NeedAppearances")] = BooleanObject(False)
    if specimen:
        for pi, page in enumerate(w.pages):
            box = page.mediabox
            page.merge_page(specimen_overlay(float(box.width), float(box.height),
                                             card_centres(info, pi)))
    with open(out, "wb") as fh:
        w.write(fh)
    return made, trimmed


def write_flat(blank, values, info, pages, out, specimen=False):
    src = PdfReader(blank)
    w = PdfWriter()
    by_page = {}
    for el, slots in info.items():
        for sx, f in slots.items():
            if f["field"] in values:
                by_page.setdefault(f["page"], []).append((f, values[f["field"]]))
    for pi, page in enumerate(src.pages):
        items = by_page.get(pi, [])
        if items:
            pw, ph = pages[pi]
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=(pw, ph))
            c.setFillColorRGB(0, 0, 0)
            for f, val in items:
                l, b, rr, t = f["rect"]
                wd, ht = rr - l, t - b
                val = str(val)
                if val.startswith("/"):
                    c.setFont("Helvetica-Bold", min(8.0, ht * 0.72))
                    c.drawCentredString((l + rr) / 2.0, b + ht * 0.28, "X")
                    continue
                txt, size, _ = fit(val, wd, cap=min(8.0, ht * 0.70))
                c.setFont("Helvetica", size)
                tw = stringWidth(txt, "Helvetica", size)
                q = f["quad"]
                x = l + 2.0 if q == 0 else ((l + (wd - tw) / 2.0) if q == 1 else rr - tw - 2.0)
                c.drawString(x, b + (ht - size) / 2.0 + size * 0.20, txt)
            c.save()
            buf.seek(0)
            page.merge_page(PdfReader(buf).pages[0])
        if specimen:
            pw, ph = pages[pi]
            page.merge_page(specimen_overlay(pw, ph, card_centres(info, pi)))
        w.add_page(page)
    if "/AcroForm" in w._root_object:
        del w._root_object[NameObject("/AcroForm")]
    for p in w.pages:
        if "/Annots" in p:
            del p[NameObject("/Annots")]
    with open(out, "wb") as fh:
        w.write(fh)


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("blank")
    ap.add_argument("data")
    ap.add_argument("outdir")
    ap.add_argument("--prefix", default=None)
    ap.add_argument("--fillable-only", action="store_true")
    ap.add_argument("--flat-only", action="store_true")
    a = ap.parse_args()

    data = json.load(open(a.data))
    vehicles = data.get("vehicles") or []
    if not vehicles:
        sys.exit("no vehicles in data; nothing to issue")
    os.makedirs(a.outdir, exist_ok=True)

    specimen = bool((data.get("meta") or {}).get("specimen"))

    # A key the mapping does not know is silently lost otherwise, which is how a value the
    # producer took the trouble to supply ends up missing from the card with no trace.
    KNOWN = {
        "meta": {"specimen", "source_document", "form_title", "content_id", "form_file", "edition"},
        "insured": {"name", "address_line_1", "address_line_2", "city", "state", "zip"},
        "carrier": {"name", "naic", "address_line_1", "address_line_2", "city", "state", "zip",
                    "adot_code", "state_id", "claims_phone", "medical_treatment_contact"},
        "producer": {"name", "address_line_1", "address_line_2", "city", "state", "zip", "phone"},
        "policy": {"number", "effective_date", "expiration_date", "line_of_business", "fleet",
                   "registered_owner"},
        "routing": {"state", "state_name", "basis", "fallback", "form"},
    }
    VEH = {"year", "make", "model", "vin", "vin_override", "garaging_state", "plate",
           "registered_owner", "body_type", "additional_interest", "excluded_driver",
           "pip", "bodily_injury", "named_driver", "unit"}
    unknown = []
    for sect, allowed in KNOWN.items():
        for k in (data.get(sect) or {}):
            if k not in allowed:
                unknown.append(f"{sect}.{k}")
    for n, veh in enumerate(vehicles, 1):
        for k in veh:
            if k not in VEH:
                unknown.append(f"vehicles[{n}].{k}")
    for k in data:
        if k not in set(KNOWN) | {"vehicles", "remark"}:
            unknown.append(k)
    if unknown:
        print("Keys in the data file the mapping does not recognize. Nothing will be written "
              "from them, so check for a typo or read references/data_schema.md:")
        for k in sorted(set(unknown)):
            print(f"  {k}")
        print()
    els, pages = scan(a.blank)
    if "Vehicle_VINIdentifier" not in els:
        sys.exit(f"{os.path.basename(a.blank)} has no Vehicle_VINIdentifier field. "
                 "This is probably not an auto ID card form. Re-resolve the form by exact title.")
    groups = copy_groups_for(a.blank)
    cap = slots_per_sheet(els, groups)

    # VIN guard. Refuse rather than print an unusable card.
    bad = []
    for v in vehicles:
        ok, msg = vin_check(v.get("vin"))
        if not ok and not v.get("vin_override"):
            bad.append((v.get("vin"), msg))
    if bad:
        print("VIN validation failed. No cards written.")
        for vv, msg in bad:
            print(f"  {vv}: {msg}")
        print('Fix the VIN, or set "vin_override": true on that vehicle to issue anyway.')
        sys.exit(2)

    ins = (data.get("insured") or {}).get("name") or "INSURED"
    stem = a.prefix or re.sub(r"[^A-Za-z0-9]+", "_",
                              f"AutoID_{ins}_{data.get('routing',{}).get('state','')}").strip("_")
    sheets = [vehicles[i:i + cap] for i in range(0, len(vehicles), cap)]
    print(f"form: {os.path.basename(a.blank)}  cards/sheet: {cap}  "
          f"vehicles: {len(vehicles)}  sheets: {len(sheets)}"
          + ("  [SPECIMEN]" if specimen else ""))
    if specimen:
        print("  meta.specimen is true, so every card is watermarked SPECIMEN.")

    written, all_trim, all_skip, all_unfilled = [], [], set(), set()
    for n, chunk in enumerate(sheets, 1):
        tag = "" if len(sheets) == 1 else f"_sheet{n}"
        values, dropped, unfilled = plan_sheet(els, data, chunk, groups)
        all_skip |= set(dropped)
        all_unfilled |= set(unfilled)
        if not a.flat_only:
            p = os.path.join(a.outdir, f"{stem}{tag}_FILLABLE.pdf")
            made, trim = write_fillable(a.blank, values, els, p, specimen=specimen)
            all_trim += trim
            written.append((p, made))
        if not a.fillable_only:
            p = os.path.join(a.outdir, f"{stem}{tag}.pdf")
            write_flat(a.blank, values, els, pages, p, specimen=specimen)
            written.append((p, None))

    for p, made in written:
        print(f"  wrote {os.path.basename(p)}" + (f"  ({made} fields)" if made else "  (flattened)"))
    if all_skip:
        print("\nData supplied that this form has nowhere to put (ignored, not a problem):")
        for e in sorted(all_skip):
            print(f"  {e}")

    ask = sorted(e for e in all_unfilled if e in ASKABLE)
    other = sorted(e for e in all_unfilled if e not in ASKABLE)
    if ask:
        print("\nThis form asks for the following and nothing in the data answered it.")
        print("These are not on a dec page. Ask the producer before delivering:")
        for e in ask:
            print(f"  {e}\n      ask for: {ASKABLE[e]}")
    if other:
        print("\nOther fields on this form left blank:")
        for e in other:
            print(f"  {e}")
    if form_key(a.blank) in TWO_CARD_NOTE:
        print("\nThis state's form says the insured must be issued TWO cards per vehicle. "
              "The form gives one slot per card, so print the sheet twice or say so when you "
              "deliver. Do not pair two slots onto one vehicle to fake it.")
    if groups:
        print(f"\nThis form pairs slots as copies of one card ({groups}), so each vehicle's "
              "data is written to every slot in its group.")
    spare = (cap * len(sheets)) - len(vehicles)
    if spare:
        print(f"\n{spare} unused card slot(s) on the last sheet will print blank. "
              "Say so when you deliver, so nobody reads a blank card as a missing one.")
    if all_trim:
        print("\nTrimmed to fit the field. Confirm these read correctly before delivery:")
        for fid, was, now in all_trim:
            print(f"  {fid}: {was!r} -> {now!r}")


if __name__ == "__main__":
    main()
