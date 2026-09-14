# Annual notice catalog

Working catalog of group health plan notices, with the `content_search` query that surfaces each in the Zywave library. **Timing and audience below are a starting point; confirm every rule against retrieved library text before it goes in the memo.** Content IDs are hints for confirming a match, not a retrieval path — they change.

## Always include

| Notice | Trigger | Audience | Timing (verify) | Search query | Title pattern to select | ID hint |
|---|---|---|---|---|---|---|
| Medicare Part D creditable coverage disclosure | Plan provides Rx coverage | Part D–eligible individuals (practically: all participants) | Before Oct. 15 each year; also at other events (verify list) | `Medicare Part D creditable coverage disclosure notice model` | "Medicare Part D ... Notices Are Due Before Oct. 15, <year>" (bulletin); "Model ... Creditable Coverage" (notice) | 110448, 8548, 11842 |
| CMS Part D online disclosure | Plan provides Rx coverage | CMS (not employees) | Within 60 days after plan year start (verify) | `Medicare Part D CMS online disclosure form plan sponsor` | "Creditable Coverage Disclosure to CMS" | — |
| CHIP notice | Employees in a state with Medicaid/CHIP premium assistance | All employees in those states | Annually (verify; typically before plan year start or with OE) | `annual CHIP notice health plans premium assistance model notice` | "Annual CHIP Notice for Health Plans" | 37774 |
| WHCRA notice | Plan covers mastectomy | Participants | At enrollment and annually | `WHCRA Women's Health and Cancer Rights Act annual notice` | "WHCRA" / "Women's Health and Cancer Rights Act" | — |
| Newborns' and Mothers' Health Protection Act | Plan covers hospital stays for childbirth | Participants | In SPD; commonly reissued annually | `Newborns and Mothers Health Protection Act notice` | "Newborns'" | — |
| HIPAA notice of privacy practices | Self-funded plan (insured plans: carrier often provides) | Participants | At enrollment; reminder of availability every 3 years (verify) | `HIPAA notice of privacy practices group health plan model` | "Notice of Privacy Practices" | — |
| HIPAA special enrollment rights | All plans | Eligible employees | At or before enrollment; commonly in OE materials | `HIPAA special enrollment rights notice` | "Special Enrollment" | — |
| Summary of Benefits and Coverage (SBC) | All plans | Participants and beneficiaries | With OE materials; on request within 7 business days (verify) | `Summary of Benefits and Coverage SBC distribution requirements` | "SBC" / "Summary of Benefits and Coverage" | — |

## Include if condition met

| Notice | Condition | Audience | Timing (verify) | Search query | Title pattern |
|---|---|---|---|---|---|
| Wellness program notice (ADA/GINA) | Wellness program collects health information (HRA, biometrics) | Employees eligible for the program | Before collection; typically with OE | `wellness program notice ADA GINA model notice` | "Wellness Program Notice" |
| Grandfathered plan notice | Plan is grandfathered under ACA | Participants | In materials describing benefits; annually in practice | `grandfathered plan status disclosure notice model` | "Grandfathered" |
| Patient protections notice | Plan requires or allows PCP designation | Participants | With SPD or plan materials | `patient protections notice primary care provider designation` | "Patient Protections" |
| Summary Annual Report (SAR) | Plan files Form 5500 | Participants | Within 9 months after plan year end (or 2 months after 5500 extension) | `summary annual report SAR distribution requirements` | "Summary Annual Report" |
| Michelle's Law notice | Plan conditions dependent coverage on student status | Participants with dependent students | With certification of student status | `Michelle's Law notice student dependent coverage` | "Michelle's Law" |
| Mental Health Parity (MHPAEA) disclosure | Plan covers MH/SUD benefits | On request; some sponsors distribute proactively | On request; annual comparative analysis duty (verify) | `mental health parity disclosure notice comparative analysis` | "Mental Health Parity" |

## Not annual — list in memo so they aren't presumed missing

| Notice | When owed | Search query |
|---|---|---|
| Marketplace (Exchange) notice | At hire, within 14 days | `Exchange notice Marketplace coverage options model notice new hires` |
| COBRA general (initial) notice | Within 90 days of coverage start | handled by `cobra-notice-packet` |
| Summary Plan Description (SPD) | Within 90 days of becoming a participant; every 5/10 years | `summary plan description SPD requirements timing` |

## The one item to read first

`employee benefit compliance chart notice and disclosure rules` → "Employee Benefit Compliance Chart: Notice and Disclosure Rules" (ID hint 13743). Its full text settles most timing and audience questions in a single read. Pull it before writing any deadline.
