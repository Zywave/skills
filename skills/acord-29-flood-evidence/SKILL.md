---
name: acord-29-flood-evidence
description: Issue an ACORD 29 Evidence of Flood Insurance from a lender, mortgagee, or servicer request. Takes a loan agreement or flood requirement plus the insured's NFIP and excess flood policies, pulls the blank ACORD 29 from the Zywave content library, and produces a filled evidence form — fillable and flattened — dated today and signed. Use this whenever a lender, servicer, escrow officer, or flood determination vendor asks for evidence of flood insurance, an ACORD 29, proof of NFIP coverage, or confirmation of a flood insurance tower; whenever a property sits in a Special Flood Hazard Area and the mandatory purchase requirement must be evidenced; whenever excess or private-market flood sits above an NFIP primary layer; or whenever they mention flood zones, BFE, grandfathering, RCBAP, Preferred Risk Policy, Group Flood, or NFIP maximum limits. For non-flood property evidence use acord-27-property-evidence or acord-28-commercial-property-evidence.
---

# ACORD 29 Evidence of Flood Insurance

Issue an ACORD 29 from a flood evidence request.

Flood is the coverage lenders check hardest, because for a property in a Special Flood Hazard
Area the mandatory purchase requirement is federal law, not a loan covenant. The form exists to
describe something the other evidence forms cannot: **a tower** — an NFIP primary layer at its
statutory maximum, with excess or private-market layers stacked above it.

Getting the tower structure right is the whole job. A tower shown as one large primary limit
misstates what NFIP actually covers, and a servicer will reject it.

## Scope — is this the right form?

| Situation | Form |
|---|---|
| Flood coverage, NFIP and/or excess, lender needs evidence | **ACORD 29** — this skill |
| Commercial property including a flood answer among many | ACORD 28 — `acord-28-commercial-property-evidence` |
| Residential or single-policy property evidence | ACORD 27 — `acord-27-property-evidence` |
| Multi-line commercial property certificate | ACORD 24 — `acord-24-property-cert` |

If flood is one line among twenty coverage questions, the lender wants the ACORD 28. If flood
*is* the request — zones, elevations, layers — this is the form.

## Workflow

1. Collect the inputs
2. Extract into `flood_data.json`
3. Resolve and pull the blank ACORD 29 from Zywave
4. Build the tower correctly
5. Fill, sign, and deliver
6. Report the gaps in chat

---

## 1. Collect the inputs

| Input | What it gives you |
|---|---|
| Loan agreement / flood requirement / determination letter | Required limits, zone determination, interest type, loan number |
| Request email | Who is asking, deadline, closing date |
| NFIP declarations | Primary limits, rated zone, grandfathering, product type, program |
| Excess / private flood declarations | Each layer's insurer, limits, attachment, following-form status |
| Elevation certificate, if available | Lowest floor vs. BFE — useful for the description box |

The NFIP dec page carries facts that appear nowhere else: the **rated zone** (which can differ
from the current FIRM zone), whether the policy is **grandfathered**, and whether it is a
Standard, Preferred Risk, Group Flood or Mortgage Portfolio Protection policy. Without it you
cannot complete the risk section honestly.

If excess layers exist but you only have the NFIP dec, say so and evidence the primary only.
An understated tower is a correctable problem; an invented one is not.

---

## 2. Extract into flood_data.json

Read `references/flood_data_schema.md` and build the file in the working directory.

Extraction rules that matter here:

- **`current_flood_zone` and `rated_zone` can legitimately differ.** A grandfathered policy is
  rated on a superseded zone. Take both from the dec page; never copy one into the other.
- **`grandfathered` is `"Y"` or `"N"`** — the form prints the letter in a text box.
- **Every enumerated value is validated.** `market`, `policy_form`, `product_type`, `programs`,
  `interests`, `named_on`. There are no defaults; an unrecognized value aborts.
- **`time_element` belongs to excess layers only.** The form has no business income / extra
  expense / ALE row on the primary block.
- **`named_on` records which layers the holder is named on.** Not optional in practice.

Set `certificate.issue_date` to today, read from the system. Set `meta.specimen` to `true` for
demo or training data.

---

## 3. Resolve and pull the blank ACORD 29 from Zywave

| | |
|---|---|
| Form | ACORD 29 — Evidence of Flood Insurance |
| Exact library title | `ACORD 29 - Evidence of Flood Insurance` |
| Content ID, last verified 2026-09-10 | `239009` |
| Edition this field map was built against | 2016/03 |

**Resolve the form by title, then verify the ID.** `content_search` does index these forms and
does return them by form number. Search is the lookup; the content ID above is the cross-check,
not the other way round. The ID is a Zywave library identifier and can move when content is
re-indexed or a new edition is loaded. The form number never changes — ACORD 29 is always the
Evidence of Flood Insurance — which is what makes the title a safe key.

```
Zywave:content_search(query="ACORD 29 evidence of flood insurance form")
```

Resolve the result in this order. Do not skip ahead to the download.

1. **Match the title exactly** — `ACORD 29 - Evidence of Flood Insurance`. Do not take the
   highest-scoring result.
   Relevance scores tie between sibling forms: a search for ACORD 27 returns ACORD 27 and
   ACORD 28 at identical scores, so rank alone will hand you the wrong form. Exact title is the
   only safe selector.
2. **Ignore duplicate rows.** The same form comes back more than once with different scores.
   Distinct `contentId` values are what matter, not the row count.
3. **Cross-check the resolved ID against the table above.** If it matches, proceed. If it
   differs, the library has been re-indexed or a new edition loaded — proceed with the ID search
   returned, and say so in chat, because the field map may no longer apply.
4. **If nothing matches the title exactly**, fall back to `contentId=239009` and verify hard at
   step 6. Do not settle for a near-miss title: ACORD 27, 28, 60 and 301 are different forms,
   not variants of this one.

```
Zywave:content_download(contentId=<resolved ID>, convertToPdf=true)
```

That returns a presigned `downloadUrl`. Download it to the working directory as `acord29.pdf`.
Some search results also carry a `fileDownloadUrl` and some do not, so `content_download` is the
reliable path.

Three checks before filling:

5. Confirm the download is a real PDF (`file acord29.pdf`). An expired presigned URL returns an
   error page, not a form.
6. **Confirm the returned `fileName` contains "ACORD 29."** A wrong content ID returns a
   *different form*, not an error — without this check an agent will fill an ACORD 28 with
   flood data and produce a document that looks finished and is false.
7. `fill_acord29.py` validates every field name and aborts on a mismatch. That is the last
   gate, not the first. If title and filename were both right and field validation still fails,
   the library holds a **newer edition** than the 2016/03 this map was built against. Stop and
   report that. Do not edit the field map to make the run pass.

Carry the resolved content ID, the returned `fileName` and the edition into what you report in
chat, so an issued form can be traced to the exact artifact it was built from.

---

## 4. Build the tower correctly

This is the judgment that matters. The NFIP maximum limits are low relative to commercial
values, which is exactly why excess layers exist:

- **Primary** = the NFIP or WYO policy, at its statutory maximum for the occupancy type
- **Excess Policy 1 / 2** = private-market or surplus-lines layers above it, usually
  following-form, attaching at the primary's exhaustion point

Fill each block with **its own** insurer letter, market, form, product type and limits. Do not
aggregate. The script enforces the structural rules — excess 2 requires excess 1, any excess
requires primary — but it cannot tell you whether the split matches the declarations. Read them.

Then answer the question the lender actually cares about: **which layers is the holder named
on?** `named_on` drives the NAMED ON POLICY boxes. A mortgagee named on the primary but not the
excess layer has protection on $500,000 of a $14,500,000 program, and nothing else on the form
reveals that. The script warns when `named_on` is empty and aborts when it references a layer
that isn't described.

Two flood-specific traps:

- **`unit_owners_mortgagee`** is an interest type unique to this form, and the form itself prints
  "(Does not imply interest)" beside it. It is not a substitute for `mortgagee`.
- **The remarks box is tiny** — about two lines, far smaller than the ACORD 27's. Use it for the
  tower summary and the loan reference; attach an ACORD 101 for anything more and increment
  `certificate.total_pages`.

---

## 5. Fill, sign, deliver

```bash
python3 scripts/fill_acord29.py acord29.pdf flood_data.json <output_dir>
```

Produces:

- `ACORD29_<insured>_FILLABLE.pdf` — AcroForm intact, every field editable
- `ACORD29_<insured>.pdf` — flattened, renders identically in any viewer

The script generates an explicit appearance stream for every populated field and sets
`NeedAppearances = false`, so the fillable copy renders correctly everywhere rather than
depending on viewer behaviour. It reports which policy blocks were filled and warns on a missing
`named_on` or interest type.

The authorized-representative signature is drawn in black as vector outlines via
`scripts/signature.py`, with no underline flourish. **It is a graphic, not an e-signature** — no
identity verification, no audit trail, no tamper-evidence. Its authority comes from the agency's
issuance controls, not the mark.

Deliver both files with `present_files`.

---

## 6. Report the gaps

In chat, state:

- The tower as evidenced: each layer's insurer, limits and attachment
- Total building and contents flood limits, against what the loan requires
- Which layers the holder is named on — and flag it explicitly if they are not named on every
  layer
- Zone, rated zone, and whether the policy is grandfathered
- Anything you assumed

If the total program falls short of the requirement, or the holder is named only on the primary,
say so plainly. Flood shortfalls surface at closing or after a loss, and both are worse than a
call today.

---

## Failure modes worth avoiding

**Collapsing the tower into one primary limit.** Misstates NFIP's actual exposure. The most
consequential error on this form.

**Copying the current flood zone into the rated zone.** They differ on grandfathered policies,
and the difference is the reason grandfathering matters.

**Naming the holder on layers they are not on — or omitting `named_on` entirely.** Either leaves
the lender unable to tell what they are protected on.

**Using `unit_owners_mortgagee` as a stand-in for `mortgagee`.** The form says it does not imply
interest.

**Putting `time_element` on the primary block.** The script aborts; there is no such row.

**Overfilling the remarks box.** Two lines. Attach an ACORD 101.

**Trusting a renderer that shows a blank form.** If verifying with pypdfium2, call
`pdf.init_forms()` and render with `may_draw_forms=True`, or form fields won't be drawn and you
will "fix" a file that was never broken.

---

## Bundled resources

- `references/flood_data_schema.md` — the data contract. Read before extracting.
- `references/acord29_field_map.md` — all 146 field names, **including the suffix offset table**
  between block headers and coverage grids. Read that table before touching the mapping.
- `references/example_flood_data.json` — a worked NFIP-plus-excess warehouse example.
- `scripts/fill_acord29.py` — mapping and CLI.
- `scripts/acord_fill.py` — shared fill engine, identical across the ACORD 24, 27, 28 and 29
  skills. Keep changes backward-compatible.
- `scripts/signature.py` — vector signature renderer, black ink, no flourish.

## Related skills

- **acord-28-commercial-property-evidence** — ACORD 28, commercial property questionnaire.
- **acord-27-property-evidence** — ACORD 27, residential and single-policy evidence.
- **acord-24-property-cert** — ACORD 24, multi-line commercial property certificates.
- **acord-25-new-coi** — ACORD 25, liability certificates.
