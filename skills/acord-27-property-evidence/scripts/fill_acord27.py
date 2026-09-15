#!/usr/bin/env python3
"""
Fill an ACORD 27 Evidence of Property Insurance from evidence_data.json.

Usage:
    python3 fill_acord27.py <blank_acord27.pdf> <evidence_data.json> <outdir>
                            [--flat-only|--fillable-only]

Produces:
    <outdir>/ACORD27_<insured>_FILLABLE.pdf   AcroForm intact, all fields editable
    <outdir>/ACORD27_<insured>.pdf            flattened, renders anywhere

The ACORD 27 evidences ONE policy from ONE insurer. There is no insurer A-F grid and no
per-line coverage sections — coverages are ten free-form description/limit/deductible rows.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acord_fill import FormSpec, money, render_both

SIG = "Producer_AuthorizedRepresentative_Signature_A"
DESC_BOX = "EvidenceOfProperty_PropertyDescription_A"
REMARK_BOX = "EvidenceOfProperty_RemarkText_A"
ON = "/1"

COVERAGE_SLOTS = list("ABCDEFGHIJ")          # ten rows

PERILS = {
    "basic": "Policy_PolicyType_BasicIndicator_A",
    "broad": "Policy_PolicyType_BroadIndicator_A",
    "special": "Policy_PolicyType_SpecialIndicator_A",
}

# The interest the additional interest holds. More than one may apply.
INTERESTS = {
    "additional_insured": "AdditionalInterest_Interest_AdditionalInsuredIndicator_A",
    "lenders_loss_payable": "AdditionalInterest_Interest_LendersLossPayableIndicator_A",
    "loss_payee": "AdditionalInterest_Interest_LossPayeeIndicator_A",
    "mortgagee": "AdditionalInterest_Interest_MortgageeIndicator_A",
}


def build_values(d):
    """evidence_data.json -> {field_name: value}. Checkbox values are '/1'."""
    v = {}

    v["Form_CompletionDate_A"] = d.get("certificate", {}).get("issue_date", "")

    # ------------------------------------------------------------- producer
    # Note: the ACORD 27 has no producer contact-NAME field, only phone/fax/email.
    p = d.get("producer", {})
    for fid, key in [
        ("Producer_FullName_A", "name"),
        ("Producer_MailingAddress_LineOne_A", "address1"),
        ("Producer_MailingAddress_LineTwo_A", "address2"),
        ("Producer_MailingAddress_CityName_A", "city"),
        ("Producer_MailingAddress_StateOrProvinceCode_A", "state"),
        ("Producer_MailingAddress_PostalCode_A", "zip"),
        ("Producer_ContactPerson_PhoneNumber_A", "phone"),
        ("Producer_FaxNumber_A", "fax"),
        ("Producer_ContactPerson_EmailAddress_A", "email"),
        ("Producer_CustomerIdentifier_A", "customer_id"),
        ("Insurer_ProducerIdentifier_A", "producer_code"),
        ("Insurer_SubProducerIdentifier_A", "sub_producer_code"),
        (SIG, "authorized_representative"),
    ]:
        if p.get(key):
            v[fid] = p[key]

    # -------------------------------------------------------------- insurer
    # One insurer, with a full mailing address. No A-F letter grid on this form.
    ins = d.get("insurer", {}) or {}
    for fid, key in [
        ("Insurer_FullName_A", "name"),
        ("Insurer_MailingAddress_AddressLineOne_A", "address1"),
        ("Insurer_MailingAddress_AddressLineTwo_A", "address2"),
        ("Insurer_MailingAddress_CityName_A", "city"),
        ("Insurer_MailingAddress_StateOrProvinceCode_A", "state"),
        ("Insurer_MailingAddress_PostalCode_A", "zip"),
    ]:
        if ins.get(key):
            v[fid] = ins[key]

    # -------------------------------------------------------------- insured
    ni = d.get("insured", {}) or {}
    for fid, key in [
        ("NamedInsured_FullName_A", "name"),
        ("NamedInsured_MailingAddress_LineOne_A", "address1"),
        ("NamedInsured_MailingAddress_LineTwo_A", "address2"),
        ("NamedInsured_MailingAddress_CityName_A", "city"),
        ("NamedInsured_MailingAddress_StateOrProvinceCode_A", "state"),
        ("NamedInsured_MailingAddress_PostalCode_A", "zip"),
    ]:
        if ni.get(key):
            v[fid] = ni[key]

    # --------------------------------------------------------------- policy
    pol = d.get("policy", {}) or {}
    if pol.get("policy_number"):
        v["Policy_PolicyNumberIdentifier_A"] = pol["policy_number"]
    if pol.get("effective"):
        v["Policy_EffectiveDate_A"] = pol["effective"]

    # Continuous-until-cancelled and a fixed expiration are mutually exclusive
    # statements about the same policy. Asserting both is incoherent.
    continuous = bool(pol.get("continuous_until_cancelled"))
    if continuous and pol.get("expiration"):
        raise SystemExit(
            "policy.continuous_until_cancelled is true but an expiration date was also given. "
            "A policy is either continuous until cancelled or it expires on a date — pick one.")
    if continuous:
        v["EvidenceOfProperty_ContinuousBasisIndicator_A"] = ON
    elif pol.get("expiration"):
        v["Policy_ExpirationDate_A"] = pol["expiration"]

    if pol.get("prior_evidence_date"):
        v["EvidenceOfProperty_PriorEvidenceDate_A"] = pol["prior_evidence_date"]

    for peril in pol.get("perils", []):
        fid = PERILS.get(peril)
        if fid:
            v[fid] = ON
    if pol.get("other_peril"):
        v["Policy_PolicyType_OtherIndicator_A"] = ON
        v["Policy_PolicyType_OtherDescription_A"] = pol["other_peril"]

    # ------------------------------------------------------------- location
    loc = d.get("property_location", {}) or {}
    for fid, key in [
        ("EvidenceOfProperty_PhysicalAddress_StreetLineOne_A", "address1"),
        ("EvidenceOfProperty_PhysicalAddress_StreetLineTwo_A", "address2"),
        ("EvidenceOfProperty_PhysicalAddress_CityName_A", "city"),
        ("EvidenceOfProperty_PhysicalAddress_CountyName_A", "county"),
        ("EvidenceOfProperty_PhysicalAddress_StateOrProvinceCode_A", "state"),
        ("EvidenceOfProperty_PhysicalAddress_PostalCode_A", "zip"),
    ]:
        if loc.get(key):
            v[fid] = loc[key]

    # ------------------------------------------------------------ coverages
    covs = d.get("coverages", []) or []
    if len(covs) > len(COVERAGE_SLOTS):
        raise SystemExit(
            f"{len(covs)} coverages supplied but the ACORD 27 has only "
            f"{len(COVERAGE_SLOTS)} rows. Attach an ACORD 101 rather than dropping any.")
    for i, c in enumerate(covs):
        s = COVERAGE_SLOTS[i]
        v[f"EvidenceOfProperty_CoverageDescription_{s}"] = c.get("description", "")
        if c.get("limit") is not None:
            v[f"EvidenceOfProperty_LimitAmount_{s}"] = (
                money(c["limit"]) if isinstance(c["limit"], (int, float)) else str(c["limit"]))
        if c.get("deductible") is not None:
            v[f"EvidenceOfProperty_DeductibleAmount_{s}"] = (
                money(c["deductible"]) if isinstance(c["deductible"], (int, float))
                else str(c["deductible"]))

    # --------------------------------------------------- additional interest
    ai = d.get("additional_interest", {}) or {}
    for fid, key in [
        ("AdditionalInterest_FullName_A", "name"),
        ("AdditionalInterest_MailingAddress_LineOne_A", "address1"),
        ("AdditionalInterest_MailingAddress_LineTwo_A", "address2"),
        ("AdditionalInterest_MailingAddress_CityName_A", "city"),
        ("AdditionalInterest_MailingAddress_StateOrProvinceCode_A", "state"),
        ("AdditionalInterest_MailingAddress_PostalCode_A", "zip"),
    ]:
        if ai.get(key):
            v[fid] = ai[key]
    # The form prints the loan number twice — once in the policy header block and once in
    # the additional interest block. One value fills both; exposing two keys would let a
    # certificate contradict itself.
    if ai.get("loan_number"):
        v["AdditionalInterest_AccountNumberIdentifier_A"] = ai["loan_number"]
        v["AdditionalInterest_AccountNumberIdentifier_B"] = ai["loan_number"]

    for interest in ai.get("interests", []):
        fid = INTERESTS.get(interest)
        if not fid:
            raise SystemExit(
                f"interest {interest!r} is not one of {sorted(INTERESTS)} or 'other'. "
                "The interest type determines the holder's rights to loss proceeds — "
                "guessing it is not safe.")
        v[fid] = ON
    if ai.get("other_interest"):
        v["AdditionalInterest_Interest_OtherIndicator_A"] = ON
        v["AdditionalInterest_Interest_OtherDescription_A"] = ai["other_interest"]

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

    spec = FormSpec(sig_field=SIG, prefix="ACORD27", text_boxes={
        DESC_BOX: d.get("property_description", []),
        REMARK_BOX: d.get("remarks", []),
    })

    sig = d.get("producer", {}).get("authorized_representative", "")
    slug = re.sub(r"[^A-Za-z0-9]+", "_",
                  d.get("insured", {}).get("name", "Insured")).strip("_")

    render_both(a.blank, values, spec, sig, slug, a.outdir,
                flat_only=a.flat_only, fillable_only=a.fillable_only)

    ai = d.get("additional_interest", {}) or {}
    if not ai.get("interests") and not ai.get("other_interest"):
        print("WARNING: no interest type checked for the additional interest. "
              "The holder's rights to loss proceeds are undefined on this certificate.")
    print(f"coverage rows used: {len(d.get('coverages', []) or [])} of {len(COVERAGE_SLOTS)}")


if __name__ == "__main__":
    main()
