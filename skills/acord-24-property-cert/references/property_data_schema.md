# property_data.json — data contract

The extraction artifact for the ACORD 24. Same top-level shape as `coi_data.json` from the
**acord-25-new-coi** skill, so the header blocks are interchangeable — an agency issuing both a
liability and a property certificate for one account extracts the parties once.

Write it to the working directory as `property_data.json`.

```json
{
  "meta": { ... },
  "certificate": { ... },
  "producer": { ... },
  "insured": { ... },
  "certificate_holder": { ... },
  "insurers": [ ... ],
  "policies": { ... },
  "location_description": [ ... ],
  "remarks": [ ... ]
}
```

---

## meta, certificate, producer, insured, certificate_holder, insurers

Identical to `coi_data.json`. See `acord-25-new-coi/references/data_schema.md`.

`certificate.issue_date` is **today** in MM/DD/YYYY, read from the system (`date +%m/%d/%Y`),
not copied from a source document.

`producer.customer_id` is new here — it fills the PRODUCER CUSTOMER ID box, which the ACORD 25
does not have. Optional.

For a mortgagee or lender holder, the name almost always carries **ISAOA/ATIMA** ("its
successors and/or assigns, as their interests may appear"). Copy the loan document's wording
character for character; lenders reject certificates over this as readily as GCs do.

---

## policies

Keys: `property`, `inland_marine`, `crime`, `boiler_machinery`, `other`.

**Set a key to `null` when no policy exists.** Load-bearing, same as the COI: `null` means "no
such policy in force," which is a different statement from "we didn't extract it," and it is
what makes the fill script leave the whole section blank.

### property

```json
"property": {
  "insurer_letter": "A",
  "policy_number": "NGS-CP-8841027",
  "effective": "03/01/2026",
  "expiration": "03/01/2027",
  "perils": ["special"],
  "other_perils": [],
  "deductibles": [25000],
  "limits": {
    "building": 14500000,
    "personal_property": 2200000,
    "business_income": 3000000,
    "extra_expense": 500000,
    "rental_value": null
  },
  "blanket": [{"type": "building_and_pp", "amount": 16700000}],
  "other_coverages": [{"description": "ORDINANCE OR LAW A/B/C", "amount": 1000000}]
}
```

- `perils` — any of `basic`, `broad`, `special`, `earthquake`, `wind`, `flood`. **Only list a
  peril the policy actually covers.** Earthquake and flood are the two that matter most: they
  are commonly excluded and commonly required, and checking one that isn't in force is the
  single most damaging error available on this form.
- `other_perils` — free text, max 2, for causes of loss with no checkbox.
- `deductibles` — in form order. Slot 1 is BUILDING, slot 2 is CONTENTS, remainder unlabeled.
  Plain integers are formatted with separators; pass a string for anything else
  (`"2% WIND/HAIL"`, `"$25,000 / 5% NAMED STORM"`).
- `limits` — a `null` or omitted key leaves both the checkbox and the amount blank.
- `blanket[].type` — `building`, `personal_property`, or `building_and_pp`. Required; an
  unrecognized value aborts the fill rather than guessing a line.

### inland_marine

```json
"inland_marine": {
  "insurer_letter": "A", "policy_number": "...", "effective": "...", "expiration": "...",
  "named_perils": false,
  "causes_of_loss": "SPECIAL FORM",
  "coverages": [{"description": "CONTRACTORS EQUIPMENT", "amount": 750000}]
}
```

Up to 4 coverage rows.

### crime

```json
"crime": {
  "insurer_letter": "B", "policy_number": "...", "effective": "...", "expiration": "...",
  "type": "COMMERCIAL CRIME - LOSS SUSTAINED",
  "coverages": [{"description": "EMPLOYEE THEFT", "amount": 500000}]
}
```

Up to 3 coverage rows.

### boiler_machinery

```json
"boiler_machinery": {
  "insurer_letter": "B", "policy_number": "...", "effective": "...", "expiration": "...",
  "coverages": [{"description": "EQUIPMENT BREAKDOWN", "amount": 14500000}]
}
```

Up to 2 coverage rows.

### other

```json
"other": {
  "insurer_letter": "C", "description": "BUILDERS RISK",
  "policy_number": "...", "effective": "...", "expiration": "...",
  "coverages": [{"description": "SOFT COSTS", "amount": 250000}]
}
```

---

## location_description

Array of paragraphs for the LOCATION OF PREMISES / DESCRIPTION OF PROPERTY box. It is a small
box — roughly two lines. Keep it to the address and the identifying construction facts a
lender or holder needs:

```json
"location_description": [
  "LOC 1: 8875 Riverside Commerce Way, Aurora, IL 60502 - 142,000 SF single-story distribution warehouse, JM/Class A construction, built 2019, fully sprinklered (ESFR)."
]
```

If there are more locations than fit, say so here and attach an ACORD 101.

## remarks

Array of paragraphs for the SPECIAL CONDITIONS / OTHER COVERAGES box (roughly six lines).
Cover, in this order:

1. **Loan or agreement reference**, and the holder's interest — mortgagee, loss payee, or
   additional insured — with the endorsement form that grants it
2. **Valuation and form basis** — replacement cost vs. ACV, agreed value, coinsurance waiver,
   blanket arrangement
3. **Coverages not provided** that the loan or lease requires, each named plainly
4. **Separately-carried coverages** and which policy holds them

A paragraph beginning `***` renders in warning red and bold, in both output copies. Use it for
uncovered perils and unmet requirements — a lender skimming the certificate should not be able
to miss a flood exclusion on a Zone AE building.

Write in the plain declarative voice: "FLOOD IS NOT COVERED under this policy," not "flood may
not extend to the described premises."

The box auto-fits down to 4.8pt and no further. If the text overflows, tighten the prose or
attach an ACORD 101 — never drop a disclosure to make it fit.
