# PostgreSQL AI Assistant (Natural Language to SQL Agent)

A conversational agent that lets you query a PostgreSQL database in plain English. Built with LangChain's agentic tool-calling framework, it inspects your database schema on the fly, generates SQL, executes it, and returns a natural-language answer — no SQL knowledge required.

## How it works

1. You ask a question in the Streamlit chat UI (e.g., "which 5 customers spent the most last month?")
2. The agent calls `list_tables` to discover what's in the database
3. It calls `get_schema` on the relevant table(s) to understand columns and types
4. It generates a SQL query and executes it via `execute_query`
5. It turns the raw result into a plain-English answer

## Tech stack

- **LangChain** (`create_agent`) — agent orchestration and tool-calling loop
- **Groq** — low-latency LLM inference for fast, interactive responses
- **PostgreSQL** (`psycopg2`) — target database
- **Streamlit** — chat interface with persistent session state

## Safety

The current version is intentionally **read-only**: the execution tool rejects any query that isn't a `SELECT`, so the agent cannot insert, update, delete, or alter data regardless of what it generates. This is a deliberate scoping decision, not a limitation of the framework — see Roadmap below for how write access will be reintroduced safely.

## Setup

1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file with your database credentials:
   ```
   DB_HOST=your_host
   DB_PORT=5432
   DB_NAME=your_db
   DB_USER=your_user
   DB_PASSWORD=your_password
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Roadmap

- 🚧 Risk-tiered write support (INSERT/UPDATE) gated behind human-in-the-loop confirmation, with impact estimation shown before execution
- 🚧 Transaction wrapper with automatic rollback on validation failure
- 🚧 Immutable audit log of every proposed query, decision, and outcome
- 🚧 Least-privilege database role scoping, separate from the app's own credentials
- 🚧 CSV / Excel / JSON ingestion — upload a file, infer schema, and load it into the database through the same safety layer
- 🚧 Evaluation harness measuring natural-language-to-SQL accuracy on a fixed test set
- 🚫 Destructive/schema-altering operations (DROP, TRUNCATE, ALTER) are intentionally out of scope — these will remain blocked and logged rather than supported, to keep the system's blast radius bounded

## Status

Actively developed. Read-only querying is stable; write support and the safety layer above are in progress.
