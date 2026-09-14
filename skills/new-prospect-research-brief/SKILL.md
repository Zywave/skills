---
name: new-prospect-research-brief
description: Research a new company or household prospect and produce a research brief before outreach.
category: prospecting
audience: producer
mcp_tools:
  - discovery_company_search
  - discovery_household_search
  - discovery_company_contacts_get
  - discovery_household_contact_get
  - research_brief_generate
  - research_brief_get
---

# New Prospect Research Brief

## When to use this skill

Use this when a producer has a lead — a company or a household — that isn't yet a managed
account, and wants a research brief to prepare for first outreach.

## Steps

1. **Confirm what kind of prospect this is.** A business (has a company name) uses the
   company tools below; a household/individual uses the household tools.

2. **Find the prospect in Market Discovery.**
   - Company: call `discovery_company_search` with the company name (and location, if
     known, to narrow results). Company MSIDs start with `M`.
   - Household: call `discovery_household_search` with the name and location. Household
     MSIDs start with `H`.
   - If more than one plausible match comes back, show the candidates to the producer
     (name, location, any distinguishing detail) and ask which one before continuing.
   - If nothing comes back, tell the producer no match was found and ask if the name or
     location should be adjusted, rather than guessing.

3. **Pull the contacts.**
   - Company: call `discovery_company_contacts_get` with the MSID from step 2.
   - Household: call `discovery_household_contact_get` with the MSID from step 2.

4. **Generate the research brief.** Call `research_brief_generate` with the MSID. This
   kicks off the brief, but it isn't ready right away — you'll get a tracking reference
   for it.

5. **Poll until the brief is ready.** Check back on it every so often using
   `research_brief_get` until it finishes or comes back as failed; don't report anything
   to the producer until you know which one it is. If it's taking longer than expected,
   let the producer know rather than checking silently forever.

6. **Present the result.**
   - If `complete`: summarize the brief for the producer, include the contacts from step 3,
     and suggest a next step (e.g. starting an outreach sequence with this MSID).
   - If `failed`: tell the producer the brief generation failed and offer to retry once,
     rather than silently giving up.

## Notes

- Don't confuse this with Account Management — this skill is for prospects that aren't in
  the producer's book of business yet. If the name the producer gives you turns out to
  already be a managed account, say so and suggest using account search instead.
- MSIDs from discovery can be passed directly to account tools later if this prospect
  converts into a client.
