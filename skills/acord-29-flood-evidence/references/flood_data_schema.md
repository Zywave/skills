# flood_data.json — data contract

The extraction artifact for the ACORD 29. Its distinguishing feature is that it describes a
**flood tower**: a primary policy plus up to two excess layers, each with its own insurer,
market, form, product type and limits.

Write it to the working directory as `flood_data.json`.

```json
{
  "meta": { ... },
  "certificate": { ... },
  "producer": { ... },
  "insurers": [ ... ],
  "insured": { ... },
  "location": { ... },
  "location_description": [ ... ],
  "risk": { ... },
  "primary": { ... },
  "excess_1": { ... } | null,
  "excess_2": { ... } | null,
  "additional_interest": { ... },
  "remarks": [ ... ]
}
```

---

## certificate

```json
"certificate": {"issue_date": "08/19/2026", "evidence_number": "EOF-2026-00742",
                "revision": "0", "total_pages": "1", "prior_evidence_date": ""}
```

`issue_date` is today, read from the system. This form calls it an **evidence number**, not a
certificate number, and it has a `total_pages` box — bump it when attaching an ACORD 101.

## producer, insured, location

As the other evidence forms. `producer.contact_name` is used here. No county field on the
location.

## insurers

**Three rows maximum**, letters A–C. Each policy block references one by letter.

```json
"insurers": [
  {"letter": "A", "name": "NFIP / Wright National Flood", "naic": "10657"},
  {"letter": "B", "name": "Lexington Surplus Lines Ins Co", "naic": "19437"}
]
```

A letter outside A–C aborts the fill.

---

## risk

The flood-specific underwriting facts. This section is why the form exists.

```json
"risk": {
  "date_of_construction": "2019",
  "current_flood_zone": "AE",
  "rated_zone": "AE",
  "grandfathered": "N",
  "replacement_cost": 14500000,
  "condominium_coverage_for": null,
  "unit_count": null,
  "building_occupancy": "non_residential",
  "occupancy_description": "",
  "contents_coverage_type": "non_residential",
  "contents_other_description": ""
}
```

- `current_flood_zone` / `rated_zone` — **these can legitimately differ.** A grandfathered
  policy is rated on an old zone while the current FIRM shows another. Take both off the dec
  page; do not copy one into the other.
- `grandfathered` — `"Y"` or `"N"`. The form prints the letter in a text box, not a checkbox.
  Anything else aborts.
- `condominium_coverage_for` — `unit_owner` or `association_building`, or `null` if not a condo.
- `building_occupancy` — `single_family`, `two_to_four_family`, `other_residential`,
  `non_residential`, or `other`. `other` requires `occupancy_description`.
- `contents_coverage_type` — `residential`, `non_residential`, or `other`. `other` requires
  `contents_other_description`.

---

## Policy blocks: primary, excess_1, excess_2

All three take the same shape. Set `excess_1` / `excess_2` to `null` when the layer doesn't
exist.

```json
"primary": {
  "insurer_letter": "A",
  "policy_number": "WNF-CF-4471982",
  "effective": "03/01/2026",
  "expiration": "03/01/2027",
  "market": "nfip_wyo",
  "policy_form": "general_property",
  "product_type": "standard",
  "product_other_description": "",
  "programs": [],
  "building": {"limit": 500000, "deductible": 25000},
  "contents": {"limit": 500000, "deductible": 25000}
}
```

Excess layers add two keys:

```json
"excess_1": {
  "...": "as above",
  "following_form": true,
  "time_element": {"business_income": true, "extra_expense": true,
                   "additional_living_expense": false, "ale_limit": null,
                   "actual_loss_sustained": true, "months": 12}
}
```

### Enumerated values

| Key | Values |
|---|---|
| `market` | `nfip_wyo`, `private` |
| `policy_form` | `dwelling`, `general_property`, `rcbap` |
| `product_type` | `standard`, `preferred_risk`, `other` (requires `product_other_description`) |
| `programs[]` | `preferred_risk_eligibility_extension`, `group_flood`, `mortgage_portfolio_protection` |

Anything else aborts the fill. There are no defaults.

### Structural rules the script enforces

- **`excess_2` requires `excess_1`.** Layers sit in order; filling layer 2 while layer 1 is
  empty misstates the tower.
- **Any excess requires `primary`.** Excess flood cannot be evidenced without the underlying
  layer it sits above.
- **`time_element` is excess-only.** The ACORD 29 has no business income / extra expense / ALE
  row on the primary block. Supplying one aborts rather than silently discarding it — if the
  primary carries time-element coverage, state it in `remarks`.

### The NFIP ceiling is the point of this form

NFIP maximum limits are low relative to commercial values — which is why the excess layers
exist and why a lender asks for this form rather than an ACORD 28. Get the split right:
primary at the NFIP maximum, excess above it. A tower shown as one large primary limit is
wrong and a lender or servicer will catch it.

---

## additional_interest

```json
"additional_interest": {
  "name": "First Meridian Bank, ISAOA/ATIMA",
  "address1": "Attn: Loan Servicing", "address2": "400 N LaSalle Street, Suite 1200",
  "city": "Chicago", "state": "IL", "zip": "60654",
  "interests": ["mortgagee"],
  "other_interest": "",
  "loan_number": "FMB-CRE-2026-0918",
  "named_on": ["primary", "excess_1"]
}
```

- `interests` — one or more of `additional_insured`, `lenders_loss_payable`, `loss_payee`,
  `mortgagee`, `unit_owners_mortgagee`.
- **`named_on`** — which layers of the tower the holder is actually named on. Any of `primary`,
  `excess_1`, `excess_2`. Naming a layer whose block is empty aborts the fill; omitting the key
  entirely prints a warning, because a lender cannot otherwise tell whether they are protected
  on the excess layer or only the primary.

`unit_owners_mortgagee` is flood-specific and the form prints "(Does not imply interest)"
beside it. It is not a substitute for `mortgagee`.

**Get the interest type right.** Mortgagee and lender's loss payable protect the holder even
when the insured's own act would void coverage; loss payee grants payment rights only.

## remarks

Array of paragraphs for the REMARKS box — **only about two lines** on this form, far smaller
than the ACORD 27's. Use it for the tower summary and the loan reference:

```json
"remarks": [
  "RE: Loan No. FMB-CRE-2026-0918. NFIP primary at maximum non-residential limits ($500,000 building / $500,000 contents) with excess flood layered above to $14,000,000 building.",
  "Total flood program $14,500,000 building / $2,200,000 contents, satisfying Loan Agreement Sec. 5.4(c)."
]
```

A paragraph beginning `***` renders in warning red and bold. Given how small the box is, attach
an ACORD 101 for anything more than a tower summary and a requirement reference, and increment
`certificate.total_pages`.
