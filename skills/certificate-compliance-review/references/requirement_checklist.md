# Requirement checklist

A starting taxonomy for building `contract.requirements`. Work through it so the review is
consistent run to run, then add anything specific to the contract in front of you.

**Only include requirements the contract actually imposes.** A contract that never mentions
umbrella coverage should not produce UM rows. Inventing requirements manufactures findings and
destroys the reviewer's trust in the rest of the matrix.

Equally: **include the requirements that pass.** A matrix showing only problems gives no way to
tell a thorough review from a lazy one, and no way to catch a false positive.

---

## GL — Commercial General Liability

| ID | Requirement | Compare on |
|---|---|---|
| GL-01 | Each occurrence limit | amounts |
| GL-02 | General aggregate limit | amounts |
| GL-03 | Products & completed operations aggregate | amounts |
| GL-04 | Personal & advertising injury limit | amounts |
| GL-05 | Damage to premises rented to you | amounts |
| GL-06 | Occurrence form (ISO CG 00 01 or equivalent) | Met? |
| GL-07 | Aggregate applies per project | Met? |
| GL-08 | Additional insured — ongoing operations (CG 20 10) | Met? |
| GL-09 | Additional insured — completed operations (CG 20 37) | Met? |
| GL-10 | Primary and non-contributory (CG 20 01) | Met? |
| GL-11 | Waiver of subrogation (CG 24 04) | Met? |
| GL-12 | Completed operations tail maintained N years | Met? |
| GL-13 | Deductible / SIR within disclosure threshold | Met? |

**GL-09 is the row most reviews get wrong.** A policy carrying CG 20 10 but not CG 20 37 grants
additional insured status for ongoing operations only. The distinction is invisible in a limits
table and invisible in the ACORD 25's ADDL INSD column — it lives in the endorsement schedule.
Check the endorsement's `scope` field, not just that some AI endorsement exists.

GL-13 is a reverse comparison: the deductible must be *below* the threshold. Use the Met? column,
not the amount columns, since the amount comparison tests `actual >= required`.

## AU — Business Automobile

| ID | Requirement | Compare on |
|---|---|---|
| AU-01 | Combined single limit each accident | amounts |
| AU-02 | Covered autos basis (any auto / owned, hired, non-owned) | Met? |
| AU-03 | Additional insured | Met? |
| AU-04 | Waiver of subrogation | Met? |

## WC — Workers Compensation

| ID | Requirement | Compare on |
|---|---|---|
| WC-01 | Statutory coverage in every state of operation | Met? |
| WC-02 | Waiver of subrogation | Met? |
| WC-03 | Other states coverage | Met? |

For WC-01, check the states in Item 3.A against where the work is actually performed. A policy
covering only the insured's home state fails when the job site is across a state line — a common
and genuinely serious finding.

For WC-02, check which states the waiver endorsement applies to. A waiver scheduled for one state
does not cover work in another.

## EL — Employers Liability

| ID | Requirement | Compare on |
|---|---|---|
| EL-01 | Bodily injury by accident — each accident | amounts |
| EL-02 | Bodily injury by disease — each employee | amounts |
| EL-03 | Bodily injury by disease — policy limit | amounts |

## UM — Umbrella / Excess

| ID | Requirement | Compare on |
|---|---|---|
| UM-01 | Each occurrence limit | amounts |
| UM-02 | Aggregate limit | amounts |
| UM-03 | Follow-form over underlying coverages | Met? |
| UM-04 | Additional insured | Met? |
| UM-05 | Waiver of subrogation | Met? |

Where the contract states a total limit achievable across primary and excess, compare the
combined tower rather than failing the primary for not reaching it alone.

## GN — General and administrative

| ID | Requirement | Compare on |
|---|---|---|
| GN-01+ | Carrier A.M. Best rating — one row per carrier | Met? |
| GN-0n | Carriers admitted in the state of the work | Met? |
| GN-0n | Notice of cancellation to the certificate holder | Met? |
| GN-0n | Policy periods cover the full contract term | Met? |
| GN-0n | Certificate holder stated verbatim | Met? |
| GN-0n | Endorsement copies accompany the certificate | Met? |

Two of these are quietly failed by most real certificate packages:

**Admitted status** is rarely printed on a declarations page. If the documents don't evidence it,
that is `N` with severity Medium and an action to verify — not `Y` because the carrier sounds
reputable.

**Notice of cancellation** is required by nearly every contract and satisfied by nearly no policy.
Since the 2009 ACORD revisions the cancellation box says only that notice follows policy
provisions, which generally means notice to the *first named insured*, not the holder. Unless an
endorsement names the holder, this is `N`.

---

## Severity

| Severity | Meaning |
|---|---|
| Critical | Blocks issuance or blocks the insured from performing. Missing coverage line, missing required AI endorsement, expired policy. |
| High | Material and must be resolved, but doesn't stop work today. Missing cancellation notice, partially satisfiable requirement. |
| Medium | Real gap needing verification rather than remediation. Unevidenced admitted status. |
| Low | Requirement is satisfied. The normal value for a passing row. |

Severity drives the Summary blockers list, which pulls Critical and High rows that carry an
`action`. Leave `action` empty on passing rows so they don't surface as blockers.

## Writing the action text

Say what to request and from whom. "Request CG 20 37 04 13 from Northgate naming ABC Company;
bind before the 04/06 mobilization" is actionable. "Missing completed operations coverage"
restates the finding and leaves the reader no further along.

Where one finding is a consequence of another, point at the root rather than repeating it — "See
AU-01" — so the blockers list doesn't show the same problem five times.
