# AGENTS — Agent Orchestration System
Multi-agent runtime with tool use (custom + MCP), short-term + semantic memory, and human-in-the-loop approval gates.

| Component | Choice |
|---|---|
| Language | Python 3.11+ |
| Orchestration | LangGraph (state machine, checkpointed, interruptible) |
| LLMs | OpenAI + Anthropic, routed per step, offline fallback |
| Tools | Custom registry + MCP adapters |
| Memory | PostgreSQL (checkpoints/events) + ChromaDB (semantic) |
| Queue | Redis + Celery |
| UI | Live mission-control dashboard (frontend/index.html) |
| Infra | Docker + docker-compose |

## Designed and Developed by 
# **NIKHIL CHARY SRIRAMOJU**
BTech CSE (Final Year)

- GitHub: [Nikhil-creat](https://github.com/Nikhil-creat)
- LinkedIn: [nikhil-chary-sriramoju](https://in.linkedin.com/in/nikhil-chary-sriramoju-95041b38a)
- Email: sriramojunikhil66@gmail.com
- Instagram: [@nikhil__sriramoju](https://www.instagram.com/nikhil__sriramoju)
- Facebook: [Profile](https://www.facebook.com/profile.php?id=100079201124141)

## Run
```
cp .env.example .env   # add OPENAI_API_KEY / ANTHROPIC_API_KEY (optional: offline mode works)
docker compose up --build
open http://localhost:8000
```
## Flow
recall → plan → guard (HITL interrupt on risky plans) → execute (tools) → critic (loops back if weak) → synthesize → remember
Approve/reject in the UI → `POST /runs/{id}/resume` → graph resumes from its Postgres checkpoint.

## Upgrades in this master version
- Specialist agents (researcher / analyst / operator) execute plan steps **in parallel**
- Prompt-injection sanitizer on every tool result
- Prometheus metrics at `:9100/metrics`, `/health` endpoint, CORS enabled
- pytest suite + GitHub Actions CI, auto-deploy of the dashboard to GitHub Pages

## GitHub Pages
The dashboard in `frontend/` is static. On `*.github.io` it runs in **demo mode** (simulated agents).
To drive a real backend, run `docker compose up` locally and paste `http://localhost:8000` into the API box on the page.
