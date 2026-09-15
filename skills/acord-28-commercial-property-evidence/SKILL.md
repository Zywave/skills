---
name: acord-28-commercial-property-evidence
description: Issue an ACORD 28 Evidence of Commercial Property Insurance from a lender request. Takes a loan agreement or requirements exhibit plus the insured's commercial property policy, pulls the blank ACORD 28 from the Zywave content library, answers the form's Yes/No/N-A coverage questionnaire, and produces a filled evidence form — fillable and flattened — dated today and signed. Use this whenever a commercial mortgage lender, loan servicer, CMBS servicer, escrow officer, or title company asks for evidence of commercial property insurance, an ACORD 28, or proof of coverage on a commercial building; whenever a lender asks about terrorism, ordinance or law, agreed value, coinsurance, equipment breakdown, earth movement, or wind/hail coverage; or whenever they mention a lender servicing agent, contract of sale interest, or blanket reported values. For residential or single-policy evidence use acord-27-property-evidence; for a commercial property certificate use acord-24-property-cert.
---

# ACORD 28 Evidence of Commercial Property Insurance

Issue an ACORD 28 from a commercial lender request.

This form is not a certificate with a remarks box. It is a **questionnaire**, and the answers
are the disclosure. Seventy-six of its 159 fields are Yes / No / N/A checkboxes, and a
commercial mortgage lender or CMBS servicer reads them line by line because each one maps to a
covenant in the loan agreement.

That changes where the risk sits. On an ACORD 25 the danger is an overstated Y in a coverage
column. Here the danger is subtler: **answering `N/A` where the truthful answer is `No`.** N/A
reads as "this question doesn't apply." No reads as "this exposure is uninsured." A lender
funding against a Zone AE building needs the second answer, and nothing on the face of the
document reveals which one you meant.

## Scope — is this the right form?

| Situation | Form |
|---|---|
| Commercial building, lender needs the full coverage questionnaire answered | **ACORD 28** — this skill |
| Residential or single-policy lender evidence | ACORD 27 — `acord-27-property-evidence` |
| Commercial property certificate across several policies (property + IM + crime + boiler) | ACORD 24 — `acord-24-property-cert` |
| Liability certificate for a GC or contract | ACORD 25 — `acord-25-new-coi` |

If the lender's request enumerates coverages — terrorism, ordinance or law, agreed value,
coinsurance — they want the ACORD 28. If they just want proof of hazard insurance on one
policy, the 27 is less work for the same result.

## Workflow

1. Collect the inputs
2. Extract into `commercial_evidence_data.json`
3. Resolve and pull the blank ACORD 28 from Zywave
4. Answer every line the policy speaks to
5. Fill, sign, and deliver
6. Report the gaps in chat

---

## 1. Collect the inputs

| Input | What it gives you |
|---|---|
| Loan agreement / mortgage commitment / insurance exhibit | Required coverages, interest type, servicing agent, loan number, closing date |
| Request email | Who is asking, deadline, whether it replaces prior evidence |
| Commercial property policy (dec pages + endorsement schedule) | What coverage actually exists |

**The endorsement schedule matters more here than on any other certificate form.** Ordinance or
law, terrorism, agreed value, equipment breakdown and the fungus provisions all live in
endorsements, not on the dec page face. Without the schedule you will end up guessing at a
dozen questionnaire lines, which is exactly the failure this form is designed to prevent.

If you only have a dec page, say so and answer only the lines it supports. Leaving lines blank
and disclosing that is honest; filling them from assumption is not.

---

## 2. Extract into commercial_evidence_data.json

Read `references/commercial_evidence_data_schema.md` and build the file in the working
directory.

Extraction rules that matter here:

- **Every line takes `yes`, `no`, or `na`.** No default, no guessing. An unrecognized value
  aborts the fill.
- **Reach for `no` before `na`.** `na` is for questions the policy genuinely cannot answer — a
  rental value question on an owner-occupied building. If the coverage simply isn't there, that
  is `no`.
- **Answer both wind questions.** `included` and `subject_to_provisions` are independent.
- **Strings for non-numeric limits and deductibles.** `"INCLUDED"`, `"2% OF TIV"`,
  `"5% NAMED STORM"`. Percentage wind deductibles are the norm on commercial property and
  forcing them to a number destroys the basis.
- **The lender servicing agent is not the lender.** Separate block, separate company. Omit it
  if there isn't one rather than duplicating the lender.

Set `certificate.issue_date` to today, read from the system. Set `meta.specimen` to `true` for
demo or training data.

---

## 3. Resolve and pull the blank ACORD 28 from Zywave

| | |
|---|---|
| Form | ACORD 28 — Evidence of Commercial Property Insurance |
| Exact library title | `ACORD 28 - Evidence of Commercial Property Insurance` |
| Content ID, last verified 2026-09-10 | `239006` |
| Edition this field map was built against | 2016/03 |

**Resolve the form by title, then verify the ID.** `content_search` does index these forms and
does return them by form number. Search is the lookup; the content ID above is the cross-check,
not the other way round. The ID is a Zywave library identifier and can move when content is
re-indexed or a new edition is loaded. The form number never changes — ACORD 28 is always the
Evidence of Commercial Property Insurance — which is what makes the title a safe key.

```
Zywave:content_search(query="ACORD 28 evidence of commercial property insurance form")
```

Resolve the result in this order. Do not skip ahead to the download.

1. **Match the title exactly** — `ACORD 28 - Evidence of Commercial Property Insurance`. Do not take the
   highest-scoring result.
   Relevance scores tie between sibling forms: a search for ACORD 27 returns ACORD 27 and
   ACORD 28 at identical scores, so rank alone will hand you the wrong form. Exact title is the
   only safe selector.
2. **Ignore duplicate rows.** The same form comes back more than once with different scores.
   Distinct `contentId` values are what matter, not the row count.
3. **Cross-check the resolved ID against the table above.** If it matches, proceed. If it
   differs, the library has been re-indexed or a new edition loaded — proceed with the ID search
   returned, and say so in chat, because the field map may no longer apply.
4. **If nothing matches the title exactly**, fall back to `contentId=239006` and verify hard at
   step 6. Do not settle for a near-miss title: ACORD 24, 27 and 29 are different forms,
   not variants of this one.

```
Zywave:content_download(contentId=<resolved ID>, convertToPdf=true)
```

That returns a presigned `downloadUrl`. Download it to the working directory as `acord28.pdf`.
Some search results also carry a `fileDownloadUrl` and some do not, so `content_download` is the
reliable path.

Three checks before filling:

5. Confirm the download is a real PDF (`file acord28.pdf`). An expired presigned URL returns an
   error page, not a form.
6. **Confirm the returned `fileName` contains "ACORD 28."** A wrong content ID returns a
   *different form*, not an error — without this check an agent will fill an ACORD 27 with
   commercial property data and produce a document that looks finished and is false.
7. `fill_acord28.py` validates every field name and aborts on a mismatch. That is the last
   gate, not the first. If title and filename were both right and field validation still fails,
   the library holds a **newer edition** than the 2016/03 this map was built against. Stop and
   report that. Do not edit the field map to make the run pass.

Carry the resolved content ID, the returned `fileName` and the edition into what you report in
chat, so an issued form can be traced to the exact artifact it was built from.

---

## 4. Answer every line the policy speaks to

Work the questionnaire against the endorsement schedule, line by line. The lines that most often
decide whether a lender funds:

- **Terrorism.** Three separate questions: is terrorism coverage in force, is there a
  terrorism-specific exclusion, is domestic terrorism excluded. They are not redundant, and
  answering only the first leaves a CMBS servicer unsatisfied.
- **Ordinance or law.** Three sublimits — undamaged portion, demolition costs, increased cost of
  construction. Lenders on older buildings require all three and check each.
- **Agreed value and coinsurance.** Usually mutually exclusive in practice; a lender wants
  agreed value `yes` and coinsurance `no`.
- **Earth movement and flood.** The two that get evidence rejected. If either is excluded,
  answer `no` — not `na`.
- **Wind/hail and named windstorm.** Percentage deductibles on coastal and convective-storm
  exposures are a live underwriting issue; state the basis as a string.
- **Subrogation waiver in favour of the mortgage holder.** Frequently a loan covenant.

The script reports which lines you left unanswered. Read that list before delivering and decide
each one deliberately.

**There is no remarks box on this form.** Anything the questionnaire cannot express goes on an
attached ACORD 101 and into your chat report — see step 6, which carries more weight here than
on the other certificate forms.

---

## 5. Fill, sign, deliver

```bash
python3 scripts/fill_acord28.py acord28.pdf commercial_evidence_data.json <output_dir>
```

Produces:

- `ACORD28_<insured>_FILLABLE.pdf` — AcroForm intact, every field editable
- `ACORD28_<insured>.pdf` — flattened, renders identically in any viewer

The script generates an explicit appearance stream for every populated field and sets
`NeedAppearances = false`, so the fillable copy renders correctly everywhere rather than
depending on viewer behaviour. It prints the count of unanswered coverage lines and warns if no
interest type was checked.

The authorized-representative signature is drawn in black as vector outlines via
`scripts/signature.py`, with no underline flourish, so it embeds with no font dependency.
**It is a graphic, not an e-signature** — no identity verification, no audit trail, no
tamper-evidence. Its authority comes from the agency's issuance controls, not the mark.

Deliver both files with `present_files`.

---

## 6. Report the gaps

This form has no remarks box, so the chat report is the only narrative the producer gets. State:

- Which lines you answered `no` and what loan requirement each one fails
- Which lines you left unanswered, and why — missing endorsement schedule, or genuinely
  inapplicable
- The interest type you checked and what supports it
- Whether a servicing agent was identified
- Anything you assumed

If the evidence doesn't satisfy the loan covenants, say so plainly. A commercial closing that
stalls on a terrorism exclusion nobody flagged is an expensive phone call to have late.

---

## Failure modes worth avoiding

**Answering `na` where the truthful answer is `no`.** The signature failure of this form. N/A
hides an uninsured exposure behind a shrug.

**Leaving lines blank because the dec page didn't say.** Get the endorsement schedule. A blank
line is a question the lender will come back and ask.

**Answering only the first terrorism question.** There are three, and they mean different things.

**Copying the lender into the servicing agent block.** Different company, different notice
address.

**Checking loss payee when the loan requires mortgagee or lender's loss payable.** Strips the
holder's protection against the insured's own acts.

**Printing a fungus exclusion form number beside a `no` answer.** The script aborts; the form
only asks for it on `yes`.

**Asserting both an expiration date and continued-until-terminated.** The script aborts.

**Trusting a renderer that shows a blank form.** If verifying with pypdfium2, call
`pdf.init_forms()` and render with `may_draw_forms=True`, or form fields won't be drawn and you
will "fix" a file that was never broken.

---

## Bundled resources

- `references/commercial_evidence_data_schema.md` — the data contract. Read before extracting.
- `references/acord28_field_map.md` — all 159 field names, including the full tri-state table
  and the asymmetric wind-row naming.
- `references/example_commercial_evidence_data.json` — a worked warehouse example.
- `scripts/fill_acord28.py` — mapping and CLI.
- `scripts/acord_fill.py` — shared fill engine, identical across the ACORD 24, 27 and 28 skills.
  Keep changes backward-compatible.
- `scripts/signature.py` — vector signature renderer, shared with `acord-25-new-coi`.

## Related skills

- **acord-27-property-evidence** — ACORD 27, residential and single-policy evidence.
- **acord-24-property-cert** — ACORD 24, multi-line commercial property certificates.
- **acord-25-new-coi** — ACORD 25, liability certificates.
