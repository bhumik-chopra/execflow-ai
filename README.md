# ExecFlow AI - Executive Commitment & Action Copilot

Executive productivity agent for Arjun Malhotra, VP Sales. The existing React /
TypeScript / Vite frontend calls FastAPI. MongoDB Atlas stores sources,
observations, canonical tasks, conversations, and audit logs through PyMongo.
Language processing uses a locally running Ollama model through one service.

No paid AI API key is required. The model runs locally through Ollama.
No Docker or local MongoDB server is required.

## Requirements

- Python 3.11+ with pip and venv: https://www.python.org/downloads/
- Node.js (24 LTS recommended): https://nodejs.org/en/download
- A MongoDB Atlas cluster, database user, and IP access-list entry.
- Ollama installed on the machine: https://ollama.com/download

MongoDB setup: create a database user with read/write permission for `execflow`,
add your current IP under Network Access, then copy your cluster's Python driver
connection string. Substitute credentials and URI-encode reserved characters.
https://www.mongodb.com/docs/atlas/connect-to-database-deployment/

## Manual setup

1. Install Ollama. Open a new terminal after installation so its command is on PATH.
2. Download the model:

```powershell
ollama pull llama3.2:3b
```

3. Start Ollama, unless the Windows app already runs it in the background:

```powershell
ollama serve
```

If the daemon is not running when you pull, start it in another terminal first.
The model download needs internet access and disk space; inference runs locally.

4. Configure `backend/.env`. From the project root, for a fresh setup only:

```powershell
Copy-Item .env.example backend/.env
notepad backend/.env
```

Do not overwrite an existing `.env` containing your credentials. Required values:

```dotenv
MONGODB_URI=your_mongodb_atlas_connection_string
MONGODB_DB=execflow

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

The existing root `.env` is still supported: settings load root `.env` first,
then `backend/.env`; OS environment variables override both. Existing root Atlas
credentials need not be moved. Keep a setting in one file to avoid confusion.
Restart the backend after changes. Both `.env` locations are gitignored.
Never put MongoDB credentials into React or `VITE_` variables.

Optional existing user settings: `EXECUTIVE_USER_NAME` and `EXECUTIVE_USER_ROLE`.
Defaults remain Arjun Malhotra and VP Sales. Model choice is configurable through
`OLLAMA_MODEL`; download the selected model before using it.

5. Start the backend. PowerShell, from the project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

With the virtual environment already activated, the equivalent commands are:

```text
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

6. Start the frontend in another terminal, from the project root:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

On macOS/Linux use `python3 -m venv .venv`, `source .venv/bin/activate`, and `npm`
instead of the Windows executable paths / `npm.cmd`.

7. Open http://localhost:5173. API docs: http://localhost:8000/docs.
Backend health: http://localhost:8000/health. The backend root has no homepage.
Press Ctrl+C in server terminals to stop them.

Ports 8000 and 5173 must be available. Check a conflict in PowerShell with
`Get-NetTCPConnection -LocalPort 8000 -State Listen`. Stop your old development
server in its own terminal. If another application needs port 8000, use Uvicorn
`--port 8001`, update the proxy target in `frontend/vite.config.ts`, and restart
both servers. Do not terminate an unrelated process blindly.

## Preserved backend APIs

- `GET /health`, `GET /context?as_of=...`
- `POST /api/sources?as_of=...`
- `GET /api/sources`, `GET /api/sources/{source_id}`
- `POST /api/sources/{source_id}/process?as_of=...` retries an existing source.
- `GET /api/tasks?as_of=...&classification=...&status=...&owner=...`
- `GET /api/tasks/{task_id}?as_of=...`
- `GET /api/brief?as_of=...`, `GET /api/conflicts?as_of=...`
- `GET /api/audit`, `POST /api/chat`

The unchanged domain pipeline is raw source -> structured observation -> canonical
business task -> deterministic reference-time state -> Daily Brief / grounded Q&A.
The assignment is demo data; new sources use the same generic pipeline. No demo
person or subject is a runtime special case.

Python handles dates, status, overdue rules, calendar overlap, task filtering,
brief generation, and stored-data retrieval without AI. These operations remain
available while the local model is stopped. Calendar occurrence alone never
proves an event happened; completion and ownership require evidence.

Every state calculation uses explicit `as_of`. The default assignment reference
is `2026-09-25T09:00:00`, not the real computer date. Existing datetime normalization
and date-precision assumptions are unchanged.

## Local AI and health

Only `backend/services/llm.py` makes Ollama requests using `httpx.AsyncClient`.
Generic `generate()` / `generate_json()` signatures remain available, including
caller system prompts and existing Pydantic response models.

Structured requests use `POST /api/generate` with `stream:false`, `format:"json"`,
and the required schema in concise instructions. Output is parsed and validated
strictly with Pydantic. Malformed JSON, incomplete output, or schema violations
get exactly one retry; a second invalid result produces a safe HTTP 502 error.
Unreachable service, timeout, or missing model produces a safe HTTP 503. Provider
bodies, prompts, and credentials are not included in application error messages.
Generation uses a 180-second HTTP timeout with a 3-second connection timeout.
Local generation speed depends on your hardware.

`GET /health` uses only `GET /api/tags`, with a 3-second timeout, and checks that
the configured model is installed. It never generates text. Example response:

```json
{"backend":"ok","mongodb":"ok","ollama":"ok","ollama_model":"llama3.2:3b"}
```

If the daemon is down or the model has not been downloaded, `ollama` is
`unavailable`; the backend still returns HTTP 200 from its health endpoint.
An installed-model check is not a guarantee that inference will fit in memory.

A source submitted while local AI is unavailable is retained with
`processing_status=PENDING`. HTTP 503 includes its `source_id`, `raw_source_saved`,
and the message:

> Source saved, but local AI processing is unavailable. Start Ollama and retry processing.

After starting Ollama, retry without re-entering the source:

```powershell
Invoke-RestMethod -Method Post 'http://localhost:8000/api/sources/SOURCE_ID/process?as_of=2026-09-25T09:00:00'
```

Already processed sources return cached tasks without another AI request.
Existing observations are reused when processing resumes. Invalid extraction
never fabricates observations. Syntax/validation failures use `FAILED` so they
can also be retried through this endpoint.

Q&A retrieves a bounded set of relevant tasks and at most 12 relevant raw sources.
It asks for concise answers with exact source citations, never a general-purpose
chat answer. Unrelated database records are not included as fallback context.

## Assignment seed and tests

The existing raw fixture is `backend/seed/data.py`. From `backend`:

```powershell
.\.venv\Scripts\python.exe -m seed.seed
```

This preserves the existing pipeline and idempotent IDs. A successful second run
reuses `PROCESSED` sources and makes zero inference calls. A partially processed
seed resumes pending/failed items, which can require local inference.
No fabricated processed fixture is created by the provider patch; existing Atlas
data is not re-seeded, deleted, or rewritten during migration validation.

Unit tests mock the LLM and use an in-memory MongoDB substitute. They do not need
Ollama, Atlas credentials, or a downloaded model:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest ../tests -q
```

Frontend build, from `frontend`: `npm.cmd run build`.
The current frontend layout is preserved by this patch; its AI health label is
now Local AI. CORS still allows only `http://localhost:5173` for development.

## Data handling

Language processing uses the configured Ollama server, which is local by default.
Raw sources and structured state are stored in MongoDB Atlas. This is not an
entirely offline application: Atlas requires network access. No paid AI API key
is required. No unsupported security or compliance guarantees are claimed.

Ollama references:
https://docs.ollama.com/api/generate
https://docs.ollama.com/api/tags
https://docs.ollama.com/capabilities/structured-outputs
