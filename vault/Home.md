# Northern Michigan Deal Finder

**AI-powered acquisition lead discovery and outreach.**

Deployed at: deal-finder7.streamlit.app

---

## Navigation

- [[leads/]] — All leads (auto-generated when agents run)
- [[_hubs/]] — Cities, deal types, and owner hubs (graph cluster nodes)

---

## Deal Types

| Type | What It Is |
|---|---|
| [[seller_finance]] | Seller acts as the bank — no traditional lender needed |
| [[subject_to]] | Take over existing mortgage payments |
| [[lease_option]] | Lease with right to buy — no ownership yet |
| [[dscr]] | Bank lends based on property income, not personal income |
| [[sba_plus_seller_carry]] | SBA covers 90%, seller carries 10% — near-zero down |
| [[sba_7a]] | Bank finances 90% based on business cashflow |

---

## Scoring Rubric

Leads scored 1-10. Higher = better deal with less money down and less bank involvement.

| Score | Meaning |
|---|---|
| 9-10 | Sell immediately, near-zero down, no bank needed |
| 7-8 | Strong motivation, creative structure viable |
| 5-6 | Average — some motivation, some bank involvement |
| 3-4 | Weak signals, likely needs conventional financing |
| 1-2 | Not worth pursuing — bank only, large down, no urgency |

---

## Cities Covered

[[Traverse City, MI]] · [[Petoskey, MI]] · [[Charlevoix, MI]] · [[Elk Rapids, MI]]
[[Boyne City, MI]] · [[Cadillac, MI]] · [[Bellaire, MI]] · [[Suttons Bay, MI]]

---

## How This Vault Works

Every time the Real Estate or Business agent runs and saves a lead, a markdown note
is automatically written to `leads/`. Wikilinks to cities, deal types, and owners
create the graph you see in Obsidian's Graph View.

Add your own notes in the **My Notes** section of any lead file — they persist
across agent runs (only the auto-generated sections get updated).
