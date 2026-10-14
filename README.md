# Campus Customs — Multi-Agent Operations (HW5)

A campus shop's ticket desk, resolved by a 5-agent PydanticAI team (boss, inventory, accounting, facilities, customer_service) backed by an MCP server, a FastAPI backend, and a React dashboard. Full writeup in [output/harness.md](output/harness.md); design rationale in [output/design.md](output/design.md); the real full-run results in [output/desk_tickets.html](output/desk_tickets.html), [output/resolved_tickets.json](output/resolved_tickets.json), and [output/resolved_board.html](output/resolved_board.html).

## Setup

1. **Python deps**: `pip install -r requirements.txt`
2. **Frontend deps**: `cd frontend && npm install`
3. **Credentials**: copy `.env.example` to `.env` and fill in your own `PORTKEY_API_KEY`. Never commit the real `.env`.

## Running it

**1. Copy the original DB to the working copy** whenever you need a clean run:

```bash
cp data/campus_customs.db data/campus_customs_new.db
```

(The backend also exposes `POST /reset` to do this from the dashboard's "Reset database" button.)

**2. Start the MCP server** (`mcp_server/server.py`). In normal use the agents spawn this automatically as a subprocess via `MCPToolset` — you don't need to run it by hand. To run it standalone (e.g. for manual testing), from the project root:

```bash
python mcp_server/server.py
```

**3. Start the FastAPI backend**, from the `backend/` folder:

```bash
uvicorn main:app --reload --port 8000
```

**4. Start the React board**, from the `frontend/` folder:

```bash
npm run dev
```

Then open `http://localhost:5173` — pick a ticket, click "Run agent team," and watch it work.

**5. Reset the DB before a full three-ticket run.** Repeat step 1 right before running all 3 tickets back-to-back, so the run starts from the original seed values rather than whatever state a previous run left behind — this is exactly what the Problem 9 full-run results in `output/` reflect (a reset, then all 3 tickets run for real).

## Project layout

- `mcp_server/` — the FastMCP server (9 tools) that's the only source of shop facts for every agent.
- `backend/` — the 5 PydanticAI agents (`agents.py`), their prompts (`prompts/`), shared config/model setup (`config.py`), the audit logger (`audit.py`), and the FastAPI app (`main.py`).
- `frontend/` — the React + Vite + TypeScript dashboard.
- `data/` — `campus_customs.db` (original seed, never modified) and `campus_customs_new.db` (the working copy every tool/agent/route actually reads and writes).
- `output/` — all the project's written deliverables (see `harness.md` for the full index).
