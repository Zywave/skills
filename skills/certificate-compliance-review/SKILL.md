---
name: certificate-compliance-review
description: Run a compliance review comparing a contract's insurance requirements against the insured's actual policies, and produce a three-tab Excel workbook — Summary with the overall verdict and blockers, Compliance Matrix with formula-driven pass/fail per requirement, and Source Data showing every extracted value and the document it came from. Use this whenever someone asks to review, check, verify, audit, or validate a certificate of insurance or COI against contract requirements; asks whether coverage is compliant, sufficient, or meets a contract; asks for a compliance matrix, coverage comparison, gap analysis, or requirements-vs-policy comparison; asks "can we issue this cert" or "what's missing"; or uploads a contract and policy documents together. Also use it as the natural follow-up after issuing a certificate with the acord-25-new-coi skill, and whenever someone mentions additional insured verification, waiver of subrogation checks, carrier rating requirements, or certificate holder review.
---

# Certificate Compliance Review

Compare what a contract requires against what the policies actually provide, and produce a
workbook a risk manager or account manager can act on.

The value of this review is that it can be trusted in both directions. A missed gap gets someone
onto a job site without coverage. A false finding sends a producer chasing an endorsement that
already exists and teaches them to ignore the next review. Both failures cost the same trust, so
the matrix has to include the requirements that pass as well as the ones that don't.

## Workflow

1. Get or build `coi_data.json`
2. Build the requirements list
3. Determine status for each requirement
4. Generate the workbook and recalculate
5. Report the verdict in chat

---

## 1. Get or build coi_data.json

**If the acord-25-new-coi skill already ran**, `coi_data.json` is in the working directory. Use it.
Do not re-extract from the source PDFs — re-extraction is how the review ends up contradicting
the certificate that was just issued, and there is no way for a reader to tell which one is right.

**If running standalone**, build it now. Read `references/data_schema.md` for the structure. You
need the `contract`, `insured`, `certificate_holder`, `insurers` and `policies` sections; the
`certificate` section is optional but populates the Summary header.

The one extraction rule that changes the output: **a coverage with no policy document gets
`null`**, not an empty object. `null` means no such policy is in force, which is a finding. An
empty object means the extraction failed, which is a bug.

---

## 2. Build the requirements list

Walk `references/requirement_checklist.md` and populate `contract.requirements`. Each entry is one
row of the matrix.

Include every requirement the contract imposes — including the ones that pass. A matrix of only
failures gives the reader no way to distinguish a thorough review from a superficial one, and no
control against false positives.

Do not include requirements the contract doesn't impose. If it never mentions umbrella coverage,
there are no UM rows.

Cite the contract location in `contract_ref` (`9.4(a)`, `Ex. C`) and the policy location in
`evidence_source` (`NGS-GL-4471982 Sec. I`, `Forms schedule`). A finding a producer can't trace
back to a document is a finding they can't act on or challenge.

---

## 3. Determine status

The workbook computes status by formula. Your job is to populate the inputs correctly.

**Numeric limit comparisons** — populate both `required_amount` and `actual_amount`, leave `met`
empty. The formula tests `actual >= required`. Where no policy exists, leave `actual_amount` null
and the row correctly fails.

**Everything else** — leave both amounts null and set `met` to `Y`, `N`, or `PARTIAL`.

Use `PARTIAL` when a requirement is genuinely half-met, not as a way to avoid deciding. "Four of
five required endorsements can be attached" is partial. "Probably fine" is not.

Judgment calls worth getting right:

- **Additional insured scope.** A CG 20 10 alone satisfies ongoing operations and fails completed
  operations. Two separate rows, two separate answers. Check the endorsement's `scope`.
- **Consequential findings.** No auto policy means the auto waiver of subrogation can't be
  evidenced either. Record both, but point the second at the first in `action` so the blockers list
  doesn't repeat itself.
- **Unevidenced vs. absent.** If a declarations page doesn't state the A.M. Best rating, the
  finding is that it isn't evidenced — `N`, Medium severity, action to verify. Not `N` Critical as
  though the carrier were unrated, and not `Y` because the name sounds established.
- **Reverse comparisons.** A deductible must be *below* a threshold. Use `met`, since the amount
  formula tests `>=`.

Set `severity` on every row — `Low` on passing rows. Leave `action` empty on passing rows, since
Critical and High rows carrying an `action` are what populate the Summary blockers list.

---

## 4. Generate the workbook

```bash
python3 scripts/build_compliance_workbook.py coi_data.json <output.xlsx>
python3 /mnt/skills/public/xlsx/scripts/recalc.py <output.xlsx>
```

**The recalc step is not optional.** openpyxl writes formulas with no cached values, so until
LibreOffice evaluates them the Status column reads as blank to Excel previewers, pandas, and
anything else reading cached values. Confirm `total_errors: 0` before delivering.

Then verify the computed result matches what you intended — a clean recalc proves the formulas
*evaluate*, not that they're *right*:

```bash
python3 -c "
import openpyxl, collections
wb=openpyxl.load_workbook('<output.xlsx>',data_only=True)
m=wb['Compliance Matrix']
print(collections.Counter(m.cell(row=r,column=11).value
      for r in range(5,500) if m.cell(row=r,column=1).value))"
```

If the counts don't match your reading of the documents, fix `coi_data.json` and rebuild rather
than editing the workbook. The JSON is the source of truth.

The three tabs:

- **Summary** — parties, dates, counts by status with percentages, Critical and High tallies,
  overall determination, and the blockers list built from Critical/High rows with actions
- **Compliance Matrix** — one row per requirement, filterable, frozen header, conditional
  formatting, landscape print setup, and a blue reviewer-input column so someone can correct a
  judgment call and watch the verdict update
- **Source Data** — every extracted value with the document and section it came from, including
  explicit "no policy in force" sections for absent coverages

---

## 5. Report the verdict

State in chat, briefly:

- The overall determination and the counts behind it
- Each Critical finding in plain language, and what it blocks
- What passes cleanly — the reader needs to know the review was thorough, not just alarming
- Any finding that is a judgment call rather than a fact, flagged as such

If a deadline or mobilization date appears in the request, say what the findings mean against that
date. "Not compliant" is much more useful as "not compliant, and the crew is due on site Monday."

Where the review contradicts an assumption in the request — the holder believed a coverage existed,
or believed one was missing — say so directly. Independently confirming or correcting the holder's
suspicion is the most valuable output of the whole exercise.

---

## Failure modes worth avoiding

**Re-extracting when coi_data.json already exists.** Produces a review that disagrees with the
certificate.

**Only listing failures.** No false-positive control, and no signal of thoroughness.

**Manufacturing requirements the contract doesn't impose.** Every invented row costs credibility
on the real ones.

**Hardcoding status text.** Status is a formula so the workbook recalculates when someone corrects
an input. Writing "COMPLIANT" as a literal breaks that and hides the reasoning.

**Skipping recalc.** Ships a workbook whose Status column reads blank in most tools.

**Grading the certificate instead of the policies.** The certificate is a summary; the policies and
their endorsement schedules are the evidence. Where they disagree, the policy wins and the
certificate is the finding.

---

## Bundled resources

- `references/data_schema.md` — the `coi_data.json` contract, shared with acord-25-new-coi.
- `references/requirement_checklist.md` — standard requirement taxonomy, severity definitions, and
  the findings most reviews miss. Read before building the requirements list.
- `scripts/build_compliance_workbook.py` — generates the three-tab workbook.
