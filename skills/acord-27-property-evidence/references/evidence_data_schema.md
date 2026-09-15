# evidence_data.json — data contract

The extraction artifact for the ACORD 27. **Deliberately not the same shape as `coi_data.json`
or `property_data.json`**, because the ACORD 27 evidences one policy from one insurer and
addresses an additional interest rather than a certificate holder.

Write it to the working directory as `evidence_data.json`.

```json
{
  "meta": { ... },
  "certificate": { "issue_date": "08/19/2026" },
  "producer": { ... },
  "insurer": { ... },
  "insured": { ... },
  "policy": { ... },
  "property_location": { ... },
  "property_description": [ ... ],
  "coverages": [ ... ],
  "additional_interest": { ... },
  "remarks": [ ... ]
}
```

---

## meta, certificate

```json
"meta": {"specimen": true, "source_documents": ["mortgage_commitment.pdf", "ho3_policy.pdf"],
         "extracted_on": "2026-08-19"},
"certificate": {"issue_date": "08/19/2026"}
```

`issue_date` is **today** in MM/DD/YYYY, read from the system (`date +%m/%d/%Y`), not copied
from a source document. The ACORD 27 has no certificate-number or revision field.

## producer

```json
"producer": {
  "name": "Zywave AI Demo Agency",
  "address1": "10100 W. Innovation Drive", "address2": "Suite 300",
  "city": "Wauwatosa", "state": "WI", "zip": "53226",
  "phone": "(262) 555-0140", "fax": "(262) 555-0141",
  "email": "certificates@zywaveaidemoagency.example",
  "customer_id": "RCH-88412",
  "producer_code": "44127", "sub_producer_code": "008",
  "authorized_representative": "Brett Cleveringa"
}
```

**No `contact_name`.** The ACORD 27 has no producer contact-name box; supplying one is harmless
in the JSON but has nowhere to go.

`producer_code` / `sub_producer_code` are the CODE and SUB CODE boxes — the identifiers the
insurer assigns the agency. Optional.

## insurer

One insurer, with a full mailing address. There is no A–F letter grid on this form.

```json
"insurer": {
  "name": "Northgate Specialty Insurance Company",
  "address1": "One Northgate Plaza", "address2": "Suite 2200",
  "city": "Hartford", "state": "CT", "zip": "06103"
}
```

## insured

```json
"insured": {"name": "Marcus and Elena Rivera", "address1": "4417 Sheridan Oaks Court",
            "city": "Brookfield", "state": "WI", "zip": "53045"}
```

Mailing address. The insured property address goes in `property_location` and is often
different — a rental, a second home, a property held in an LLC.

---

## policy

```json
"policy": {
  "policy_number": "NGS-HO-2249831",
  "effective": "09/01/2026",
  "expiration": "09/01/2027",
  "continuous_until_cancelled": false,
  "perils": ["special"],
  "other_peril": "",
  "prior_evidence_date": ""
}
```

- `perils` — any of `basic`, `broad`, `special`. Only list what the policy actually provides.
- `other_peril` — free text for a causes-of-loss basis with no checkbox.
- `continuous_until_cancelled` — set `true` **and omit `expiration`**. Supplying both aborts
  the fill: a policy either runs to a date or continues until terminated, and a certificate
  asserting both is incoherent.
- `prior_evidence_date` — fills THIS REPLACES PRIOR EVIDENCE DATED. Populate it when reissuing
  a corrected evidence, so the lender knows which document this supersedes.

**There is no flood or earthquake checkbox on this form.** If either is carried, put it in a
coverage row. If either is excluded and the loan requires it, put it in the remarks as a `***`
paragraph.

## property_location

```json
"property_location": {
  "address1": "4417 Sheridan Oaks Court", "address2": "",
  "city": "Brookfield", "county": "Waukesha", "state": "WI", "zip": "53045"
}
```

The insured location. `county` is a real field on this form and some lenders require it.

## property_description

Array of paragraphs for the LOCATION/DESCRIPTION box — roughly two to three lines.

```json
"property_description": [
  "Single-family owner-occupied dwelling, 3,240 SF, frame construction, built 2004, attached 3-car garage. Central station fire and burglar alarm."
]
```

Construction, year built, occupancy and protection are what an underwriter or lender reads here.

---

## coverages

Up to **ten** rows, filled in array order. Each is free text plus a limit and a deductible.

```json
"coverages": [
  {"description": "DWELLING (COVERAGE A) - REPLACEMENT COST", "limit": 685000, "deductible": 2500},
  {"description": "LOSS OF USE (COVERAGE D)", "limit": 137000, "deductible": null},
  {"description": "WIND/HAIL", "limit": "INCLUDED", "deductible": "1% OF COV A"}
]
```

- `limit` / `deductible` — integers are formatted with separators. Pass a **string** for
  anything non-numeric: `"INCLUDED"`, `"1% OF COV A"`, `"2% NAMED STORM"`, `"STATUTORY"`.
- `null` leaves the cell blank.
- More than ten rows aborts the fill. Attach an ACORD 101 rather than truncating — a dropped
  coverage on an evidence form is an omission the lender relies on.

Order them the way the reader expects: primary dwelling or building coverage first, then
supporting coverages, then endorsement-driven extensions.

---

## additional_interest

Replaces the certificate holder, and carries the thing a holder block does not: **what interest
the recipient actually holds.**

```json
"additional_interest": {
  "name": "First Meridian Bank, ISAOA/ATIMA",
  "address1": "Attn: Loan Servicing", "address2": "400 N LaSalle Street, Suite 1200",
  "city": "Chicago", "state": "IL", "zip": "60654",
  "interests": ["mortgagee"],
  "other_interest": "",
  "loan_number": "FMB-RES-2026-4417"
}
```

- `interests` — one or more of `additional_insured`, `lenders_loss_payable`, `loss_payee`,
  `mortgagee`. An unrecognized value aborts the fill.
- `other_interest` — free text; sets the OTHER checkbox and its description.
- `loan_number` — prints in **both** loan-number boxes on the form. There is deliberately no
  way to set them independently.

**Get the interest type right.** Mortgagee, loss payee and lender's loss payable are not
interchangeable — they confer different rights to loss proceeds and different protection when
the insured's own conduct voids coverage. Read the loan document rather than defaulting to
`mortgagee` because the holder is a bank.

Copy the name verbatim, including ISAOA/ATIMA and the attention line.

## remarks

Array of paragraphs for the REMARKS box — the largest box on the form, roughly eight to ten
lines. Cover, in order:

1. **Loan reference** and closing date
2. **The holder's interest** and how it is granted
3. **Valuation and premium status** — replacement cost, extended replacement cost, paid through
4. **Coverages not provided** that the loan requires — one `***` paragraph each

A paragraph beginning `***` renders in warning red and bold in both output copies. Use it for
excluded perils and unmet requirements.

Write plainly: "FLOOD IS NOT COVERED under this policy," not "flood may not extend to the
described premises."

The box auto-fits down to 4.8pt and no further. If text overflows, tighten the prose or attach
an ACORD 101 — never drop a disclosure to make it fit.
