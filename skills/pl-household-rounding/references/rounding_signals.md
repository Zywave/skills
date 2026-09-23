# Rounding signals — thresholds and rationale

Household records carry: `msid` (H-prefixed), `street`, `city`, `state`, `zipcode`,
`totalPropertyValue`, `numberOfProperties`, `numberOfOwners`, `incomeRange {min,max}`,
`netWorthRange {min,max}`, `hasEmail`. The state on the record is where the matched property
sits, which may differ from the account's mailing state.

| Signal | Rule | Weight | Why this threshold |
|---|---|---|---|
| Multiple properties | `numberOfProperties >= 2` | 1 | A second dwelling is either scheduled or uninsured. Either way it's a conversation. |
| Out-of-state property | `numberOfProperties >= 2` and record state != account state | 2 | Non-resident dwelling coverage is frequently missing and frequently written by a different carrier. Highest-value rounding conversation in PL. |
| Umbrella threshold | `totalPropertyValue >= 750000` **or** `netWorthRange.min >= 1000000` | 2 | Above roughly $750K of exposed assets, underlying auto/home limits are routinely insufficient. Umbrella is the classic round. |
| High-value home | `totalPropertyValue >= 1500000` and `numberOfProperties == 1` | 1 | Standard-market HO policies under-serve this tier; the high-value market (Chubb, PURE, Cincinnati, etc.) is the conversation. |
| Income step-up | `incomeRange.min >= 250000` | 1 | Higher income → higher liability targets → umbrella limit review. |

Score = sum of weights. Rank by score desc, then `totalPropertyValue` desc.

## Portfolio guard

Even inside the book, a "client" record can match a household that is really an entity:
`numberOfProperties > 5` or `numberOfOwners > 2`. Flag these as **portfolio — review commercially**
rather than scoring them for PL rounding; they may belong on the commercial side.

## What the record cannot tell you

- Whether the client already carries an umbrella, a second-home policy, or scheduled property.
  That lives in the AMS/policy system, not in the CRM or the household database.
- Auto exposure (vehicles, drivers). Not in the household record.
- Whether a second property is a rental (dwelling fire) or a second home (HO). The suggestion
  says "second property"; the account manager determines which.

Phrase every suggestion accordingly: "worth reviewing," never "missing."

## Adjusting thresholds

The Method tab of the workbook records the thresholds used. Producers in high-cost markets
(coastal CA, NYC metro) will want the property-value thresholds roughly doubled; rural Midwest
producers may halve them. Change the numbers in this file and the skill follows.
