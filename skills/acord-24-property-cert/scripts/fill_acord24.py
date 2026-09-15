#!/usr/bin/env python3
"""
Fill an ACORD 24 Certificate of Property Insurance from property_data.json.

Usage:
    python3 fill_acord24.py <blank_acord24.pdf> <property_data.json> <outdir>
                            [--flat-only|--fillable-only]

Produces:
    <outdir>/ACORD24_<insured>_FILLABLE.pdf   AcroForm intact, all fields editable
    <outdir>/ACORD24_<insured>.pdf            flattened, renders anywhere

A coverage section whose key is null in property_data.json is left completely blank.
Never populate a section for a policy that does not exist.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acord_fill import FormSpec, money, render_both

SIG = "Producer_AuthorizedRepresentative_Signature_A"
DESC_BOX = "CertificateOfLiabilityInsurance_ACORDForm_RemarkText_A"   # location/description
REMARK_BOX = "CertificateOfLiabilityInsurance_ACORDForm_RemarkText_B"  # remarks
ON = "/1"

# perils checkbox -> field, driven by policies.property.perils[]
PERILS = {
    "basic": "Policy_PolicyType_BasicIndicator_A",
    "broad": "Policy_PolicyType_BroadIndicator_A",
    "special": "Policy_PolicyType_SpecialIndicator_A",
    "earthquake": "CommercialPropertyCoverage_EarthquakeOption_IncludedIndicator_A",
    "wind": "Policy_PolicyType_WindIndicator_A",
    "flood": "CommercialPropertyCoverage_Flood_YesIndicator_A",
}

# property coverage line -> (checkbox, limit field)
PROP_COVERAGES = {
    "building": ("Property_Building_CoverageIndicator_A",
                 "Property_Building_LimitAmount_A"),
    "personal_property": ("Property_PersonalProperty_CoverageIndicator_A",
                          "Property_PersonalProperty_LimitAmount_A"),
    "business_income": ("CommercialPropertyCoverage_BusinessIncomeOption_IncludedIndicator_A",
                        "CommercialPropertyCoverage_BusinessIncome_LimitAmount_A"),
    "extra_expense": ("CommercialPropertyCoverage_ExtraExpenseOption_IncludedIndicator_A",
                      "CommercialPropertyCoverage_ExtraExpense_LimitAmount_A"),
    "rental_value": ("CommercialPropertyCoverage_RentalValueOption_IncludedIndicator_A",
                     "CommercialPropertyCoverage_RentalValue_LimitAmount_A"),
}

BLANKET_TYPES = {          # blanket[].type -> form slot
    "building": "A",              # BLANKET BUILDING
    "personal_property": "B",     # BLANKET PERS PROP
    "building_and_pp": "C",       # BLANKET BLDG & PP
}
OTHER_PROP_SLOTS = ["A", "B"]
IM_OTHER_SLOTS = ["A", "B", "C", "D"]
CRIME_SLOTS = ["A", "B", "C"]
BM_SLOTS = ["A", "B"]
OTHERPOL_SLOTS = ["A", "B"]


def addr(v, d, prefix, keys):
    for fid, key in keys:
        if d.get(key):
            v[prefix + fid] = d[key]


def build_values(d):
    """property_data.json -> {field_name: value}. Checkbox values are '/1'."""
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
        ("Producer_CustomerIdentifier_A", "customer_id"),
        (SIG, "authorized_representative"),
    ]:
        if p.get(key):
            v[fid] = p[key]

    for who, prefix in (("insured", "NamedInsured"), ("certificate_holder", "CertificateHolder")):
        src = d.get(who, {})
        for fid, key in [
            ("_FullName_A", "name"),
            ("_MailingAddress_LineOne_A", "address1"),
            ("_MailingAddress_LineTwo_A", "address2"),
            ("_MailingAddress_CityName_A", "city"),
            ("_MailingAddress_StateOrProvinceCode_A", "state"),
            ("_MailingAddress_PostalCode_A", "zip"),
        ]:
            if src.get(key):
                v[prefix + fid] = src[key]

    for ins in d.get("insurers", []):
        L = ins.get("letter")
        if L in list("ABCDEF"):
            if ins.get("name"):
                v[f"Insurer_FullName_{L}"] = ins["name"]
            if ins.get("naic"):
                v[f"Insurer_NAICCode_{L}"] = ins["naic"]

    pol = d.get("policies", {}) or {}

    # ---------------------------------------------------------------- property
    prop = pol.get("property")
    if prop:
        v["Property_InsurerLetterCode_A"] = prop.get("insurer_letter", "")
        v["Policy_PolicyType_PropertyIndicator_A"] = ON
        v["Policy_Property_PolicyNumberIdentifier_A"] = prop.get("policy_number", "")
        v["Policy_Property_EffectiveDate_A"] = prop.get("effective", "")
        v["Policy_Property_ExpirationDate_A"] = prop.get("expiration", "")

        for peril in prop.get("perils", []):
            fid = PERILS.get(peril)
            if fid:
                v[fid] = ON
        for i, other in enumerate(prop.get("other_perils", [])[:2]):
            slot = "A" if i == 0 else "B"
            v[f"Policy_PolicyType_OtherIndicator_{slot}"] = ON
            v[f"Policy_PolicyType_OtherDescription_{slot}"] = other

        for i, ded in enumerate(prop.get("deductibles", [])[:7]):
            v[f"CommercialProperty_Premises_DeductibleAmount_{'ABCDEFG'[i]}"] = (
                money(ded) if isinstance(ded, (int, float)) else str(ded))

        limits = prop.get("limits", {}) or {}
        for key, (cb, lf) in PROP_COVERAGES.items():
            if limits.get(key) is not None:
                v[cb] = ON
                v[lf] = money(limits[key])

        for bl in prop.get("blanket", []):
            t = bl.get("type")
            s = BLANKET_TYPES.get(t)
            if not s:
                raise SystemExit(
                    f"blanket type {t!r} is not one of {sorted(BLANKET_TYPES)}. "
                    "Guessing the slot would print the limit on the wrong line of the form.")
            v[f"CommercialProperty_Blanket_YesIndicator_{s}"] = ON
            v[f"CommercialProperty_Blanket_LimitAmount_{s}"] = money(bl.get("amount"))

        for i, oc in enumerate(prop.get("other_coverages", [])[:2]):
            s = OTHER_PROP_SLOTS[i]
            v[f"PropertyCoverage_OtherOption_IncludedIndicator_{s}"] = ON
            v[f"PropertyCoverage_Other_CoverageDescription_{s}"] = oc.get("description", "")
            v[f"PropertyCoverage_Other_LimitAmount_{s}"] = money(oc.get("amount"))

    # ----------------------------------------------------------- inland marine
    im = pol.get("inland_marine")
    if im:
        v["CommercialInlandMarineLineOfBusiness_InsurerLetterCode_A"] = im.get("insurer_letter", "")
        v["Policy_PolicyType_InlandMarineIndicator_A"] = ON
        v["Policy_InlandMarine_PolicyNumberIdentifier_A"] = im.get("policy_number", "")
        v["Policy_InlandMarine_EffectiveDate_A"] = im.get("effective", "")
        v["Policy_InlandMarine_ExpirationDate_A"] = im.get("expiration", "")
        if im.get("named_perils"):
            v["CommercialInlandMarineCoverage_Option_NamedPerilsIndicator_A"] = ON
        if im.get("causes_of_loss"):
            v["Policy_PolicyType_OtherDescription_C"] = im["causes_of_loss"]
        for i, oc in enumerate(im.get("coverages", [])[:4]):
            s = IM_OTHER_SLOTS[i]
            v[f"CommercialInlandMarineCoverage_Other_CoverageIndicator_{s}"] = ON
            v[f"CommercialInlandMarineCoverage_Other_CoverageDescription_{s}"] = oc.get("description", "")
            v[f"CommercialInlandMarineCoverage_Other_LimitAmount_{s}"] = money(oc.get("amount"))

    # ------------------------------------------------------------------ crime
    crime = pol.get("crime")
    if crime:
        v["CrimeLineOfBusiness_InsurerLetterCode_A"] = crime.get("insurer_letter", "")
        v["CrimeLineOfBusiness_CoverageIndicator_A"] = ON
        v["Policy_Crime_PolicyNumberIdentifier_A"] = crime.get("policy_number", "")
        v["Policy_Crime_EffectiveDate_A"] = crime.get("effective", "")
        v["Policy_Crime_ExpirationDate_A"] = crime.get("expiration", "")
        if crime.get("type"):
            v["Policy_PolicyType_OtherDescription_E"] = crime["type"]
        for i, oc in enumerate(crime.get("coverages", [])[:3]):
            s = CRIME_SLOTS[i]
            v[f"CrimeCoverage_OtherCoverage_CoverageIndicator_{s}"] = ON
            v[f"CrimeCoverage_OtherCoverage_CoverageDescription_{s}"] = oc.get("description", "")
            v[f"CrimeCoverage_OtherCoverage_LimitAmount_{s}"] = money(oc.get("amount"))

    # ---------------------------------------------------- boiler and machinery
    bm = pol.get("boiler_machinery")
    if bm:
        v["BoilerAndMachineryLineOfBusiness_InsurerLetterCode_A"] = bm.get("insurer_letter", "")
        v["BoilerAndMachineryLineOfBusiness_CoverageIndicator_A"] = ON
        v["Policy_BoilerAndMachineryEquipmentBreakdown_PolicyNumberIdentifier_A"] = bm.get("policy_number", "")
        v["Policy_BoilerAndMachinery_EffectiveDate_A"] = bm.get("effective", "")
        v["Policy_BoilerAndMachinery_ExpirationDate_A"] = bm.get("expiration", "")
        for i, oc in enumerate(bm.get("coverages", [])[:2]):
            s = BM_SLOTS[i]
            v[f"BoilerAndMachineryCoverage_OtherCoverage_CoverageIndicator_{s}"] = ON
            v[f"BoilerAndMachineryCoverage_OtherCoverage_CoverageDescription_{s}"] = oc.get("description", "")
            v[f"BoilerAndMachineryCoverage_OtherCoverage_LimitAmount_{s}"] = money(oc.get("amount"))

    # ------------------------------------------------------------ other policy
    other = pol.get("other")
    if other:
        v["OtherPolicy_InsurerLetterCode_A"] = other.get("insurer_letter", "")
        v["OtherPolicy_OtherPolicyDescription_A"] = other.get("description", "")
        v["OtherPolicy_PolicyNumberIdentifier_A"] = other.get("policy_number", "")
        v["OtherPolicy_PolicyEffectiveDate_A"] = other.get("effective", "")
        v["OtherPolicy_PolicyExpirationDate_A"] = other.get("expiration", "")
        for i, oc in enumerate(other.get("coverages", [])[:2]):
            s = OTHERPOL_SLOTS[i]
            v[f"OtherPolicy_CoverageIndicator_{s}"] = ON
            v[f"OtherPolicy_CoverageDescription_{s}"] = oc.get("description", "")
            v[f"OtherPolicy_CoverageLimitAmount_{s}"] = money(oc.get("amount"))

    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("blank")
    ap.add_argument("data")
    ap.add_argument("outdir")
    ap.add_argument("--flat-only", action="store_true")
    ap.add_argument("--fillable-only", action="store_true")
    a = ap.parse_args()

    d = json.load(open(a.data))
    values = build_values(d)

    spec = FormSpec(sig_field=SIG, prefix="ACORD24", text_boxes={
        DESC_BOX: d.get("location_description", []),
        REMARK_BOX: d.get("remarks", []),
    })

    sig = d.get("producer", {}).get("authorized_representative", "")
    slug = re.sub(r"[^A-Za-z0-9]+", "_",
                  d.get("insured", {}).get("name", "Insured")).strip("_")

    render_both(a.blank, values, spec, sig, slug, a.outdir,
                flat_only=a.flat_only, fillable_only=a.fillable_only)

    blank_sections = [k for k in ("property", "inland_marine", "crime",
                                  "boiler_machinery", "other")
                      if not (d.get("policies", {}) or {}).get(k)]
    if blank_sections:
        print("sections left blank (no policy in force): " + ", ".join(blank_sections))


if __name__ == "__main__":
    main()
