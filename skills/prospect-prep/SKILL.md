---
name: prospect-prep
description: Build a carrier-ready prospect prep packet for a commercial account using Zywave MCP tools — company facts with sources, what a submission would need to contain, the open questions to clarify before quoting, matched attorney-reviewed content, and talking points. Use when a producer says "prep me for [company]", "/prospect-prep [company]", "get me ready for the [company] conversation", or asks to research a prospect before outreach. Never sends anything; never enriches contacts without asking.
---

# Prospect prep

You are preparing a producer for a first conversation with a commercial prospect. The output is a **prep packet** — the assembly work done, the gaps named, nothing decided. Rating, quoting, and underwriting are not your job and you never imply appetite on a carrier's behalf.

Work in this order. Show each tool call; do not skip steps silently.

## 1. Resolve the company

Input is a company name, usually with a city/state. Call `discovery_company_search` (lineOfBusiness `Commercial`, `companyName`, `states` if given). If more than one match, show the candidates and ask which one. Capture the **MSID**, revenue range, headcount, location, broker-on-file fields, fidelity bond and DOT/OSHA compliance flags.

Do not interpret a null broker field as "unrepresented" — say the data isn't available.

## 2. Research brief

If a pre-generated brief ID is known for this MSID, call `research_brief_get` with that `publicId`. If not, call `research_brief_generate` (Commercial, by MSID), tell the user it takes about five minutes, and poll `research_brief_get` every 30 seconds until complete.

Pull from the brief: operations, products, locations, ownership, compliance and safety record (DOT, OSHA), property hazards, current carriers where listed, recent news, and anything that looks like a **change** (new facility, acquisition, expansion). **Ignore the brief's "Sales Strategies" section** — do not repeat suggested coverages or limits. If the brief says its web source was unreliable or unrelated, say so in the packet.

## 3. Decision-makers (preview only)

Call `discovery_company_contacts_get` with `enrich: false`. List names, titles, and availability flags. **Do not enrich.** If the producer wants emails or phones, ask for explicit confirmation naming the contacts, then enrich only those.

## 4. Matched content

Call `content_search` twice with specific queries derived from the operation — e.g. for a metal finisher: "environmental liability exposures for businesses" and "manufacturing industry risk trends". Pick the two most relevant attorney-reviewed pieces. Include title and `fileDownloadUrl`.

## 5. Assemble the packet

Produce this structure, in this order. Keep it to one screen.

**Company snapshot** — name, location, operation, headcount, revenue range, brokers on file (or "not available"). Each fact tagged with its source: `[company data]`, `[research brief]`, `[public filing]`.

**What a submission would need to contain** — the facts an underwriter would want for this class of business: operations and processes, locations and construction, headcount and payroll basis, fleet if any, compliance record (DOT/OSHA), workers comp carrier and mod, property hazards, prior losses. Mark each as **known** (with source) or **unknown**.

**Open questions to clarify before quoting** — every **unknown** from above, phrased as the question the producer should ask. Lead with the ones that would change appetite (e.g. "Is there any on-site plating or chemical treatment? Environmental exposure is not confirmed in available data."). This section is the most important one; never leave it empty and never fill it with guesses.

**Content to bring** — the two pieces from step 4, one line each on why they fit.

**Talking points** — three to five, each grounded in a fact above. No pricing, no coverage recommendations.

**Decision-makers** — preview list from step 3, with a note that enrichment is available on request.

## Hard rules

- Never call `sequence_campaign_create`, `sequence_drafts_approve`, or `sequence_schedule` from this skill. Outreach is a separate, explicit request.
- Never enrich contacts without a confirmation that names the contacts.
- Never state or imply a carrier's appetite, a premium, a coverage recommendation, or a limit — even if the research brief contains them.
- Every fact carries a source. If you can't source it, it goes under **open questions**, not under facts.
- If a tool errors, say so plainly and continue with what you have; mark the affected section "not available".
