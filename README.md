# CloudOps AI

An autonomous AI Cloud Operations Engineer. Upload infrastructure-as-code
or cloud error logs; four specialist agents independently analyze
security, networking, cost, and reliability; a Report Generator Agent
combines their findings into a single Cloud Health Report with concrete,
corrected configuration.

This is **not** a chatbot wrapper. Each agent reasons independently over
the same input, returns a structured judgement (score + findings), and the
Report Generator Agent acts as a final decision-making layer — that
separation of concerns is what makes this an agentic system rather than a
single prompt.

---

## 1. Architecture

```
                              User
                               │
                               ▼
                  Next.js dashboard (upload UI)
                               │
                     POST /api/analyze (file)
                               ▼
                        FastAPI backend
                               │
                               ▼
                    Parser (routes by file type)
                    ├── Terraform (.tf)      → python-hcl2
                    ├── Kubernetes YAML      → PyYAML
                    ├── Docker Compose       → PyYAML
                    └── Logs (.log/.txt/.json)
                               │
                               ▼
                      Agent Controller
                     (async fan-out/fan-in)
          ┌────────────┬────────────┬────────────┬────────────┐
          ▼            ▼            ▼            ▼
      Security      Network        Cost      Reliability
       Agent         Agent        Agent         Agent
   (independent, run concurrently via asyncio.gather)
          └────────────┴────────────┴────────────┘
                               │
                               ▼
                   Report Generator Agent
        (weighted overall score, dedup + sort findings,
         executive summary, consolidated suggested fix)
                               │
                               ▼
                    CloudHealthReport (JSON)
                               │
                               ▼
                  Dashboard renders score dials,
                  findings feed, and suggested fix
```

**Why multi-agent instead of one big prompt?**
Each specialist agent has its own system prompt narrowly scoped to one
concern (security / network / cost / reliability), so it doesn't get
distracted analyzing things outside its lane, and its output schema is
predictable enough to score and aggregate programmatically. The Report
Generator Agent is the only agent that produces prose for a human — every
other agent speaks strict JSON. If any one specialist agent fails (bad
JSON, API error), `base_agent.py` degrades that agent's result gracefully
instead of crashing the whole pipeline, and the Report Generator still
returns a valid report built from whichever agents succeeded.

---

## 2. Folder structure

```
cloudops-ai/
├── backend/
│   ├── agents/
│   │   ├── base_agent.py        # shared prompt-loading + LLM-call logic
│   │   ├── security_agent.py
│   │   ├── network_agent.py
│   │   ├── cost_agent.py
│   │   ├── reliability_agent.py
│   │   ├── report_agent.py      # final decision-making layer
│   │   └── controller.py        # orchestrates all agents concurrently
│   ├── parsers/
│   │   ├── terraform_parser.py
│   │   ├── yaml_parser.py       # handles both k8s + docker-compose
│   │   ├── log_parser.py
│   │   └── __init__.py          # parse_file() dispatcher
│   ├── api/
│   │   └── routes.py            # POST /api/analyze, GET /api/health
│   ├── models.py                # shared Pydantic schemas
│   ├── llm_client.py            # provider-agnostic LLM wrapper
│   ├── main.py                  # FastAPI app entrypoint
│   ├── requirements.txt
│   └── .env.example
├── prompts/
│   ├── security_prompt.txt
│   ├── network_prompt.txt
│   ├── cost_prompt.txt
│   └── reliability_prompt.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # landing page
│   │   ├── layout.tsx
│   │   ├── globals.css
│   │   └── dashboard/page.tsx   # main upload + report UI
│   ├── components/
│   │   ├── FileUpload.tsx
│   │   └── ReportView.tsx
│   ├── lib/
│   │   ├── types.ts             # mirrors backend/models.py
│   │   └── api.ts               # fetch wrapper for /api/analyze
│   ├── package.json
│   ├── tailwind.config.ts
│   └── .env.example
├── tests/
│   ├── sample_terraform/insecure_infra.tf
│   ├── sample_k8s/deployment.yaml
│   ├── sample_docker-compose.yml
│   └── sample_logs/app-errors.log
└── docs/
    └── example_output_report.json
```

---

## 3. Setup instructions

### Prerequisites
- Python 3.11+
- Node.js 20+
- An Anthropic API key (or OpenAI, if you switch providers)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY=sk-ant-...

uvicorn main:app --reload --port 8000
```

The API is now live at `http://localhost:8000`. Interactive docs (Swagger)
are auto-generated by FastAPI at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install

cp .env.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000 (default is already correct for local dev)

npm run dev
```

Open `http://localhost:3000`, click **Open dashboard**, and drop in one of
the files from `tests/` to see it work end to end.

### Quick smoke test without the frontend

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@../tests/sample_terraform/insecure_infra.tf"
```

---

## 4. Extending this MVP

Ideas for the "room to extend" part of the weekend:
- **Diagram OCR**: add a parser that sends an uploaded architecture
  diagram image to Claude's vision input and asks it to describe the
  resources present, then feeds that description into the same agent
  pipeline as `raw_text`.
- **LangGraph orchestration**: replace `controller.py`'s `asyncio.gather`
  fan-out with a LangGraph state graph if you want conditional routing
  (e.g., skip the Cost Agent entirely for log-only uploads).
- **Persistent history**: add a database (Postgres/SQLite) so past reports
  are stored and you can track a health score trend over time per repo.
- **CI integration**: wrap `/api/analyze` in a GitHub Action that comments
  the report on pull requests that touch `.tf` files.
- **Real pricing data**: replace the Cost Agent's heuristic estimates with
  live lookups against the AWS/Azure/GCP pricing APIs.
