# AI Prompts Log

This file logs the prompts used while working through HW 5. For each problem: the prompt(s) I typed, and if a follow-up was needed, one sentence on what was lacking in the first prompt.

## Problem 2 — Study the Campus Customs database

**Prompt:**
> open data/campus_customs.db and look through every table and its fields. copy the original file to data/campus_customs_new.db. study the 3 open tickets to see how they link to other tables. start output/harness.md and for each table list the fields and 1 short line on why that table matters for the agents. this fill will keep getting updated later

**Follow-up (if needed):**
> N/A

*What was lacking:* N/A

---

## Problem 3 — Build the MCP server

**Prompt:**
> write an MCP server in mcp_server/ using FastMCP. It'll talk to data/campus_customs_new.db. Dont connect or run it yet. every agent in this hw uses the tools in this MCP server. We'll add more tools later; right now write 3 tools we will definitely need to for the tickets in the db. make sure the names are clear and intuitive. never invent data. only use info from db. in output/harness.md list each of the 3 MCP tools. for every tool include which table it reads, which ticket it helps unlock, and 1 sentence on why that tool is the right one for that ticket. dont be vague on the explanation. add a short mcp_server/README.md file that explains what the MCP server is for, which db file it uses, and the 3 tools it has.

**Follow-up:**
> for problem 3, make sure the output harness clearly addresses which ticket (101, 102, 103) each tool helps unlock — not just mentioned in passing.

*What was lacking:* ticket numbers were already there but buried inline next to the ticket type instead of called out plainly, so reworded each tool's entry to lead with "Ticket 101/102/103".

---

## Problem 4 — Add the MCP server to vibe coder and test each tool

**Prompt:**
> add the MCP server to this project so the vide coder can call the tools. save the connectoin JSON text in .mcp.json at the project root (or whatever is best). with the vibe coder tool connected test each of the three MCP tools. save the evidence in output/mcp_smoke.json. for every tool include: the prompt i asked the vibe coder, the tool name, and the tool output (must match values in data/campus_customs_new.db)

**Follow-up:**
> are you using my gpt luna?

*What was lacking:* the completion summary didn't make clear whether real model/API calls were involved in testing, so clarified that all 3 tool tests were direct Python function calls with zero model or Portkey usage.

---

## Problem 5 — Build the agent team and grow the MCP tools

**Prompt:**
> build the agentic team for campus customs using pydantic AI: boss, inventory, accounting, facilties, and customer service. include prompts, models, and agent loops so they can delegate work to each other with full connectivity. put the agent prompts in backend/prompts/ (one file per agent). put the data types in backend/models.py and the agent files under backend/ (layout can vary as long as the give roles are clear). use my portkey api and only gpt-g-luna for EVERY AGENT. write each prompt in my own tone with all the shop rules we mentioned earlier (repeat them here). make sure the prompt covers all aspects of the agents' work and scope. add any tools the agents need to the MCP server so they can work on open tickets. shop facts come from the MCP server over data/campus_customs_new.db (dont invent a second shop tools layer that bypasses MCP). write the agents so they append to output/audit_trail.json as they run: for each agent loop step record enough to audit later. append to this file dont' wipe it with each run. in output/harness.md list each agent and each MCP tool (including ones we added in this problem) along with wich table the tool uses. also add a short safety section: guardrails a real business would want when agents touch real customers and real money, plus limits to keep token use in check. safety guardrails could be not to make unauthorized purchases, to not lie, to not purchase with authorization, dont abuse customers, only answer questions about the products, dont act like a therapist or external things. update mcp_server/README.md so the tool list matches what we have now

**Follow-up:**
> are there other safety rules you would add to the harness?

*What was lacking:* the original safety list covered honesty, scope, and unauthorized purchases but missed 5 real gaps — untrusted ticket/tool data, silent tool-failure fallback, approval/balance workarounds, cross-ticket leakage, and partial-result honesty — all added to `output/harness.md`'s Safety section.

---

## Problem 6 — Plan the three tickets

**Prompt:**
> before you wire the backend, write down what you expect the team to do on each open ticket in simple terms for a non tehcnicla person. build output/desk_tickets.html (able to double click it with one tab per ticket 101, 102, 103). also add empty Cash and reflection tabs for later problems. leave them blank for now. on each ticket tab fill an expected section only (leave room for an actual section that we'll fill in after the agents run). for each ticket's expected section write 1) who the boss should call first and why 2) all the agent delegations we expect 3) which MCP tools we expect to use. We shouldnt call every specialist every time

**Follow-up (if needed):**
> N/A

*What was lacking:* N/A

---

## Problem 7 — Backend routes

**Prompt:**
> The react front end dashboard (next prob) needs a back end to call. in backend/main.py use FastAPI and add routes that do the folowing: 1) return three tickets and whether each is open or resolved 2) take a ticket id and run your agent team on that ticket 3) return recent agent events - what each agent said and which tools it used so the board can refresh 4) approve a payment or purchase after a human clicks approve (agents cn only prepare the pay) 5) return the current checking balance from cash_accounts 6) reset the database to the original values when you want to try a refresh run. From the backend/ folder start the server with uvicorn main:app --reload --port 8000. this turns on your backend at http://localhost:8000 so the frontend dashboard can call those routes. in output/harness.md list each route in one line (what URL/what it does)

**Follow-up (if needed):**
> N/A

*What was lacking:* N/A

---

## Problem 8 — Agent dashboard

**Prompt:**
> build the front end dashboard in frontend/ with React + Vite + typscript. the page should call the routes from problem 7. at min the board should: list all three tickets, let me pick the one ticket and start the agent team on it, show each agent and waht they are sayng/doing while the ticket runs, mark a ticket resolved when the run finishes, show a short summary of what each agent did on that ticket, let a human approve a pay or purchase when asked, show the checking balance (should drop after an approved pay). Make the dashboard readable and use different colors to distinguish agents. tell the front end to talk ot the backend at http://localhost:8000. on the backnd allow the Vite page origin usually http://localhost:5173 so the browse is allowed to call those routes. starrt the board with npm run dev. this opens the react desk in your browser so you can pick tickets and watch agents. write output/design.md with what we chose for hte dashboard look (put the resolution above the activity, add a funds spent tab next to checking balance, mark a ticket light red when open, make a ticket light green when resolved, add a button for the human approval, add a tab for customer service draft) and why including creating choices.

**Follow-up:**
> make the agents more efficient! It keeps exceeding the usage limit on these ticket runs.

*What was lacking:* every agent had all 8 MCP tools regardless of role and no rule to trust facts it was already given or to stop hunting for info that doesn't exist, fixed by scoping tools per role and adding both rules to every prompt.

---

## Problem 9 — Resolve the tickets

**Prompt:**
> before testing the agents on a full run over the 3 tickets reset the working db data/campus_customs_new.db again to start clean. note the strating checking balance. then run all 3 tickets on the board (101,102,103) until each is resolved. open output/desk_tickets.html from problem 6. on each ticket tab, fill the actual section from this run: which agents worked, what they delegated, and which tools they used. keep your expected section so you can compare the two. on the cash tab of the same output/desk_tickets.html itemize the money: starting checking balance after the reset, for each ticket how cash changed when that ticket resolved and why (which pay/purchase, dollar amount), ending checking balance so it must match cash_accounts in the working db. wrong cash math loses points!! also save 1) output/resolved_tickets.json for each ticket (id, final status, short outcome, what each agent contributed, and any human approvals) 2) output/resolved_board.html (a page you can double click with a screenshot of your react board for each resolved ticket 101, 102, 103). append real runs to output/audit_trail.json. finish output/harness.md so it covers tables, MCP tools, the five agents, API routes, the dashboard, and safety rules.

**Follow-up (if needed):**
> N/A

*What was lacking:* N/A

---

## Problem 10 — Reflection

**Prompt:**
> problem 10 is open output/desk_tickets.html and fill the reflection tab. use my vibe of casual and simple and direct not overexplanatory. answer: how wuld you evaluate the performance of the agents on each ticket and why? for each ticket how did Actual compare to the expected plan from earlier? what would have been simpler as one agent with tools and why? describe 3 new problems cmapus customs might face taht this agent team could solve with the tools you built. describe 3 new problems campus customs might face that this agent team could NOT solve with the tools we built and explain the tools and agents we would need to solve them. tie every answer to this app and the 3 tickets we ran. use the ticket tabs and cash tab on the same page as the evidence. make sure to include campus customs details

**Follow-up:**
> does the reflection do a good job at referencing the ticket and cash tabs as evidence? If not, add more references so it's clearer.

*What was lacking:* the first pass only pointed to the tabs once in general, so added clickable inline citations (e.g. "Cash tab: $3,400.00 → $2,560.00") next to the specific claims they back.

---
