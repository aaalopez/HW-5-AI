# Dashboard design

v1 built against the Problem 7 backend; a v2 styling pass followed once the mechanics were proven live; a v3 pass added the border dots. Every section below is split into **What** (the choice) and **Why** (the reasoning), so each one is easy to scan on its own.

## Layout

**What:** Two columns — a ticket list on the left (always visible), and a detail panel on the right for whatever's relevant to the selected ticket. **v2:** reordered so Resolution sits directly under the ticket header, above the activity feed, and Activity / Customer Service Draft became two tabs below it instead of both being always-rendered inline.

**Why:** The ticket list stays visible so switching tickets is one click, not a navigation. Resolution moved up because it's the answer to "is this done" — it shouldn't require scrolling past a live log to find. Activity and the draft became tabs because the customer-service draft needs room to be read in full before a human decides to send it, which doesn't fit as a truncated line in a shared summary list; splitting them keeps either one readable without the other crowding it out.

## Agent colors

**What:** Used the `dataviz` skill's validated categorical palette rather than picking hues by eye. Each agent gets a fixed slot, never re-ordered or reused for anything else:

| Agent | Color | Slot |
|---|---|---|
| Boss | blue `#2a78d6` | 1 |
| Inventory | orange `#eb6834` | 2 |
| Accounting | aqua `#1baf7a` | 3 |
| Facilities | yellow/gold `#eda100` | 4 |
| Customer Service | magenta `#e87ba4` | 5 |

Ran the palette validator (`validate_palette.js`) on these 5 hexes for both light and dark surfaces — all pass the adjacent colorblind-separation and normal-vision floors.

**Why:** A fixed slot per agent means "Boss is blue" is a fact you learn once and can rely on everywhere — feed, legend, summary, next ticket, next session — instead of colors being reshuffled per ticket and re-decoded every time. The validator (rather than eyeballing contrast) exists because colorblind-safety is a computable, checkable property, not a judgment call. Three of the five colors (aqua, yellow, magenta) fall below 3:1 text-contrast on the light surface, which the skill calls the "relief rule" — whenever that happens, color can't be the only way to identify something, so every colored element pairs the color with the agent's name as plain text (never a colored badge or colored body text with no label), and a legend stays visible above the feed so the mapping never has to be memorized.

## Ticket status

**What:** A separate fixed, non-categorical palette for status (the skill's reserved good/warning/serious/critical colors), always with a dot **and** a text label — `resolved`/`draft_ready` are green, `needs_human_approval` is amber, `open`/`blocked` are red. **v2:** the tint also washes the whole ticket card background, not just the small badge, and `open`/`blocked` deliberately share the same red family.

**Why:** Status colors are a different, dedicated palette from the agent colors specifically so a ticket badge is never mistaken for an agent tag — the two color systems mean two different things and shouldn't visually overlap. The full-card tint (v2) makes the whole ticket list scannable at a glance — which tickets still need attention vs. are done — without reading every badge individually. `open` and `blocked` share red on purpose: both mean "not done, needs a run," and the badge text still distinguishes them precisely for anyone who looks closer.

**v2 bug fix, found while wiring this up:** Resolution is now *derived* from the events list (the latest `boss` `run_end`) instead of kept in separate React state that only got set right after a fresh run, and the pre-existing "what each agent said" summary was fixed alongside it.

**Why:** The old approach meant revisiting an already-resolved ticket (e.g. after a page reload) showed nothing until it was re-run, even though the real answer already existed in the audit history — deriving from events fixes that for free. Fixing it surfaced that the agent summary had the same class of bug in reverse: it was quietly picking each agent's *oldest* matching event instead of the newest, because events arrive newest-first from the API and the original code kept overwriting a map entry with each match instead of keeping the first (newest) one seen.

## Live agent feed — polling, not streaming

**What:** The dashboard polls `GET /events/recent?ticket_id=` every 1.5s while a run is active, rather than streaming over a websocket. Each raw audit event is translated into one short plain-English line (`src/eventText.ts`) instead of showing raw JSON.

**Why polling:** `POST /tickets/{id}/resolve` is a single long synchronous call (a full multi-agent run can take 30–90+ seconds) and the backend has no streaming route — but `backend/audit.py` writes each step to `output/audit_trail.json` **as it happens**, synchronously, while that request is still in flight, and FastAPI/uvicorn can serve other concurrent requests while the resolve call is awaiting a model response. So polling genuinely sees progress as it happens (delegations, tool calls, stops), not just a result at the very end — confirmed live, watching Boss delegate to Facilities, hop back, then Accounting hit the `max_hops` cap, all before the run finished.

**Why plain English, not raw JSON:** the audit log is accurate but written for debugging, not for a shop employee watching the board — translating it means someone can tell who acted and roughly what they did without parsing tool names and argument dicts.

## "What each agent said" (the summary requirement)

**What:** A per-ticket, per-agent recap built from each agent's **last** `run_end` event, pulling the structured output's `summary`/`recommendation`/`notes`/`draft_message` field (whichever that agent's output type has). One row per agent, same fixed color/order as the legend.

**Why a separate recap at all:** the Activity feed is a transcript — accurate, but you'd have to read every delegation and tool call to piece together each agent's actual conclusion. This recap answers "what did each agent decide" directly, without re-deriving it from the full chronological log.

**Why the *last* `run_end` specifically:** an agent can be invoked more than once in a single ticket resolution (delegated to, and delegated to again), so only the most recent invocation reflects what it actually concluded by the end of the run — an earlier one could already be outdated.

**Why pull from the structured fields instead of summarizing the text:** those fields are exactly what the agent itself reported as its finding, through its own typed output (e.g. `AccountingFinding.recommendation`) — showing that verbatim keeps the recap faithful to what the agent actually said, rather than introducing a second, possibly-lossy paraphrase of it.

## Approving a payment — real numbers, not agent prose

**What:** Once a ticket's status is `needs_human_approval`, the panel reads the ticket's own `invoice_id`/`lease_id` field and fetches the real amount from two small routes (`GET /invoices/{id}`, `GET /leases/{id}`), rather than parsing a dollar amount out of the agent's free-text resolution. The human must type their own name (required) before the Approve button enables. **v2:** the whole form sits behind a "Review & approve payment" button instead of always being expanded.

**Why read real numbers instead of parsing prose:** `TicketResolution.summary` is free text — parsing a dollar amount or invoice id out of it would be fragile and genuinely unsafe for something that moves real money. The ticket's own `invoice_id`/`lease_id` fields are already known and structured (from `GET /tickets`), so fetching the real row directly is both simpler and safer than text-parsing.

**Why the approver name is required:** `payments.approved_by` is the actual accountability record for who signed off — a blank or placeholder approver would defeat the entire point of requiring a human approval in the first place.

**Why approving doesn't auto-resolve the ticket:** paying off a blocking invoice doesn't necessarily mean every other aspect of the ticket is handled. Conflating "payment went through" with "ticket resolved" would hide follow-up work rather than surface it — the ticket's own status only changes when the agent team is actually re-run.

**Why the button-gated form (v2):** a payment form sitting open by default, the moment a ticket needs approval, read as presumptuous for something that moves real money. Requiring one explicit click to even *look* at the form adds a small, deliberate beat of friction before the lower-friction (but still name-gated) approve step inside it.

## Cash balance

**What:** Always visible top-right, refreshed after every resolve run and every payment approval; turns red if a refresh shows a lower balance than last seen. **v2:** added a sibling "Funds spent" pill right next to it, showing the running total of every real payment ever made (`GET /payments`, backed by a new `list_payments()` MCP tool).

**Why pinned top-right instead of per-ticket:** affordability isn't about any one ticket — a human approving a payment needs to see it at a glance from wherever they are on the board, without navigating away first.

**Why it turns red on a drop:** a quick, honest signal that money just left the account — confirmed live after approving a $2,400 rent payment (balance flipped from $3,400 to $1,000, shown in red).

**Why add "Funds spent" (v2):** checking balance answers "what do we have"; funds spent answers "what have we actually paid out." Shown together, they're a quick sanity check that the balance drop and the cumulative spend agree with each other.

## Border dots — making "the team is thinking" feel alive (v3)

**What:** While a ticket is running, a handful of dots travel clockwise around the entire page's border, each colored by whichever agent was most recently active (`src/components/BorderDots.tsx`, reading the same live-polled events the Activity tab already shows). Only appears while a run is genuinely active.

**Why, functionally:** the only other signal that something is happening during a run is the static "Running…" button label, easy to stop noticing during a 30–90 second wait. A moving, color-shifting ring around the whole page is readable in peripheral vision without looking directly at the feed — and because the colors are driven by real agent activity rather than a generic spinner, it stays informative: a glance tells you the team is actively handing off work, not stalled.

**Why, for feel:** a dashboard that's otherwise all cards, badges, and tables can read as purely utilitarian. Letting the "thinking" moment spill out past the content area and around the whole page turns a background process into something closer to a small performance — the one place the UI is allowed to be a little playful. It deliberately reuses the exact same validated agent palette from the legend/feed rather than inventing new "fun" colors, so the delight comes from motion and color-coded meaning working together, not from a second, unvalidated color system. And it only appears during genuine activity so it stays a signal worth noticing instead of becoming wallpaper you tune out.

## What's intentionally plain right now

**What:** No theming toggle beyond the OS-level light/dark media query, no empty-state illustrations, no animation anywhere except the border dots.

**Why:** The v2 pass was about information architecture — what's visible by default, what needs a click, what persists across page reloads — not visual polish. The border dots are the first and so far only piece of pure "make it feel enjoyable" work; more is still open for a future round.
