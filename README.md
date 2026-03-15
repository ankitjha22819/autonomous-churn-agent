# Autonomous Churn Agent

The **Autonomous Churn Agent** is designed to transform how SaaS companies handle customer retention by moving from **reactive** to **predictive** and **prescriptive** support.

Instead of waiting for a "Cancel Subscription" click, this system uses a "crew" of specialized AI agents to spot red flags early and automatically execute a plan to keep the customer.

---

## Core Objectives

- **Predictive Risk Detection:** Rather than looking at static dashboards, the system monitors live "signals"—like a 30% drop in login frequency, repeated failed payment attempts, or negative sentiment in support tickets—to identify at-risk accounts 30–90 days before they actually leave.

- **Root Cause Analysis:** Using GPT-4o’s reasoning, the agents don't just say _who_ will churn, but _why_. It can distinguish between a technical friction point (e.g., "the user can't find the export button") and a value-gap issue (e.g., "the user isn't using the premium features they pay for").

- **Hyper-Personalized Playbooks:** Most companies send generic "Please don't go" emails. This project aims to generate **Retention Playbooks** tailored to the specific user's history.
- _Example:_ If an admin hasn't logged in since a key power user left the company, the agent drafts a playbook to offer free training for the new team members.

- **Autonomous Execution & Escalation:** Through FastAPI, the system can trigger real-world actions—sending an automated email, flagging a high-value account for a human Customer Success Manager (CSM) to call, or offering a targeted discount code in-app.

---

## Project Structure

```
autonomous-churn-agent/
├── backend/
│   ├── config/
│   │   ├── agents.yaml
│   │   └── tasks.yaml
│   ├── src/churn_agent/
│   │   ├── api/                  ← was main.py
│   │   │   ├── router.py         # route definitions only
│   │   │   ├── sse.py            # StreamingResponse + event emitter
│   │   │   └── dependencies.py   # FastAPI Depends() injectables
│   │   ├── core/
│   │   │   ├── config.py         # pydantic-settings Settings class
│   │   │   └── logging.py        # structlog setup
│   │   ├── schemas/              ← new
│   │   │   ├── events.py         # SSEEvent, ThinkingEvent, FinalEvent
│   │   │   └── customer.py       # CustomerRow, AnalysisRequest
│   │   ├── crew.py
│   │   ├── tools/
│   │   └── main.py               # just: app = FastAPI(); app.include_router(...)
│   ├── tests/                    
│   │   ├── unit/test_tools.py
│   │   ├── unit/test_schemas.py
│   │   └── integration/test_sse_endpoint.py
│   ├── .env
│   ├── .env.example              
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/                
│   │       └── events.ts         # mirrors backend schemas/events.py
│   └── package.json
├── docker/                       
│   ├── Dockerfile.backend
│   └── docker-compose.yml
├── docs/
│   └── architecture.mermaid
├── .gitignore
└── README.md
```
