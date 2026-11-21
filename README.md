# Lyftr AI Full-Stack Assignment: Resilient LLM Gateway

A production-grade, highly resilient LLM Chatbot application engineered with **FastAPI**, **LiteLLM**, **SQLite (WAL mode)**, and **React + TypeScript + Tailwind CSS**. Built to satisfy 100% of the Lyftr AI Full-Stack evaluation criteria with zero external cloud database dependencies.

---

## 1. Live URLs

| Service | Deployment Target | Live URL |
| :--- | :--- | :--- |
| **Frontend Web App** | Vercel | [https://lyftr-chatbot-frontend.vercel.app](https://lyftr-chatbot-frontend.vercel.app) |
| **Backend API** | Render | [https://lyftr-chatbot-backend.onrender.com](https://lyftr-chatbot-backend.onrender.com) |
| **Health Check Endpoint** | Render Backend Public URL | [https://lyftr-chatbot-backend.onrender.com/health](https://lyftr-chatbot-backend.onrender.com/health) |
| **Interactive API Docs** | Swagger / OpenAPI | [https://lyftr-chatbot-backend.onrender.com/docs](https://lyftr-chatbot-backend.onrender.com/docs) |
| **GitHub Repository** | GitHub | [https://github.com/Nischal-Agrawal/Lyftr_AI_Full_Stack_Assignment](https://github.com/Nischal-Agrawal/Lyftr_AI_Full_Stack_Assignment) |
| **Demo Video (2–3 min)** | Loom / YouTube / Drive | `https://www.loom.com/share/...` *(Insert recorded demo link here)* |

---

## 2. Run locally

### Option A: With Docker (Recommended)

Start the entire multi-service stack with a single command:

```bash
# Clone the repository
git clone https://github.com/Nischal-Agrawal/Lyftr_AI_Full_Stack_Assignment.git
cd Lyftr_AI_Full_Stack_Assignment

# Create .env from template
cp .env.example .env

# Build and start all containers in background
make up
```

- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

To view live container logs:
```bash
make logs
```

To stop and remove containers:
```bash
make down
```

---

### Option B: Without Docker

#### Prerequisites
- Python 3.11+
- Node.js 18+ & npm

#### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows:
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server (starts on http://localhost:8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup
```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite development server (starts on http://localhost:3000)
npm run dev
```

---

## 3. Design decisions

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             REACT + VITE FRONTEND                                │
│  - Strict data-testid elements: chat-input, send-button, assistant-message, etc.  │
│  - Interactive Failover Lab (X-Simulate-Failure selector)                         │
│  - Live Telemetry & Session History Sidebar                                      │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ HTTP REST (CORS)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             FASTAPI BACKEND GATEWAY                              │
│                                                                                  │
│   GET /health             POST /chat               GET /sessions/{id}/messages   │
│   (DB & Key Status)       (Inference & Failover)   (SQLite History)              │
│                                                                                  │
│ ┌──────────────────────────────────────────────────────────────────────────────┐ │
│ │                  LITELLM GATEWAY & FAILOVER ENGINE                           │ │
│ │                                                                              │ │
│ │  1. Simulate Check ──► Header present? ──► Bypass Cache & simulate status    │ │
│ │                                                                              │ │
│ │  2. Cache Lookup ──► Model + Full Messages List ──► Hit? ──► LLM_CACHE (0ms) │ │
│ │                                                                              │ │
│ │  3. Failover Loop ──► key_1 (Try) ──► 429/5xx? ──► key_2 (Failover)         │ │
│ │                                                                              │ │
│ │  4. Token Counter ──► Usage extraction with token_counter fallback           │ │
│ └──────────────────────────────────────────────────────────────────────────────┘ │
│                                         │                                        │
│                        Atomic Turn Write│(Only on Success)                       │
│                                         ▼                                        │
│ ┌──────────────────────────────────────────────────────────────────────────────┐ │
│ │                       SQLITE EMBEDDED STORAGE                                │ │
│ │   - File: /data/app.db (Docker named volume sqlite_data)                     │ │
│ │   - WAL Mode (PRAGMA journal_mode=WAL) + 5000ms busy_timeout                 │ │
│ │   - Tables: messages (with session_id index), sessions (system prompts)      │ │
│ └──────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Deterministic Key Fallback & Request-Scoped Simulation
- **Deterministic Key Sequence:** Keys configured in `LLM_API_KEYS` are parsed and assigned strictly in order: `key_1`, `key_2`, ..., `key_N`.
- **Failover Handling:** Catches provider rate limits (429), quota exhaustion, and server errors (500, 502, 503). On failure, logs a structured JSON audit event (`{"event": "provider_error", "key_id": "key_1"}`) with zero raw API key leakage, increments `fallback_attempts`, and tries the next key immediately. If all keys fail, returns HTTP `503 {"detail": "all providers unavailable"}`.
- **Request-Scoped Test Hook (`X-Simulate-Failure`):**
  - Controlled by `ENABLE_FAILURE_SIMULATION=true`.
  - Supports syntax like `key_1=429`, `key_1=500`, and `*=429`.
  - Critically, simulated failures never contaminate global state or trip long-term circuit breakers: the very next request without the header immediately routes back to `key_1`.

### 3.2 LiteLLM Built-In Response Caching
- **Built-in LiteLLM Cache:** Utilizes `litellm.caching.Cache(type="local")` (or `"disk"`).
- **Exact Cache Key Semantics:** The cache key is computed over `model + [system_prompt, ...history, new_user_message]`.
- **Cross-Session Hits:** Identical first turns across different session IDs hit the cache, returning `resolution_source: "LLM_CACHE"`, `key_id: null`, `fallback_attempts: 0`, identical token usage, and near-zero latency.
- **Failover Interaction:** When `X-Simulate-Failure` is supplied, cache lookups and writes are bypassed (`cache={"no-cache": True}`) so failover simulation checks provider switching rather than short-circuiting on cached results.

### 3.3 SQLite Storage with WAL Mode & Atomic Write-on-Success
- **Concurrency & Resilience:** Database operates under Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) with a 5000ms busy timeout to prevent database lock contention.
- **Atomic Turn Persistence:** User and assistant turns are persisted inside a single transaction **only after** an LLM or cache response is obtained. Failed turns (422, 503) write zero rows to SQLite, preventing state corruption.
- **Container Volume:** Stored at `/data/app.db` backed by a Docker named volume (`sqlite_data`) to survive container redeployments and restarts.

---

## 4. Verification

### 4.1 Automated Live Contract Verifier Script
A comprehensive test script is included in `scripts/verify_contract.py` that verifies every contract requirement against a live server:

```bash
# Run against local server:
python scripts/verify_contract.py --base-url http://localhost:8000

# Run against deployed production backend:
python scripts/verify_contract.py --base-url https://your-backend.onrender.com
```

### 4.2 Individual `curl` Verification Commands

#### 1. Health Check
```bash
curl -s http://localhost:8000/health | jq .
# Expected Output:
# {
#   "status": "ok",
#   "keys_configured": 2,
#   "cache_enabled": true
# }
```

#### 2. Live Inference (Session A)
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-s1", "message": "What is the capital of France?"}' | jq .
# Expected:
# "resolution_source": "LIVE_INFERENCE", "key_id": "key_1", "fallback_attempts": 0
```

#### 3. Cross-Session Cache Hit (Session B, Same Prompt)
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-s2", "message": "What is the capital of France?"}' | jq .
# Expected:
# "resolution_source": "LLM_CACHE", "key_id": null, "fallback_attempts": 0, latency_ms < 10
```

#### 4. Automatic Failover Simulation (`key_1=429`)
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Simulate-Failure: key_1=429" \
  -d '{"session_id": "test-s3", "message": "Tell me a joke."}' | jq .
# Expected:
# "resolution_source": "LIVE_INFERENCE", "key_id": "key_2", "fallback_attempts": 1
```

#### 5. Total Provider Outage (`*=429`)
```bash
curl -s -i -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Simulate-Failure: *=429" \
  -d '{"session_id": "test-s4", "message": "Should return 503."}'
# Expected: HTTP 503 Service Unavailable
# {"detail": "all providers unavailable"}
```

#### 6. Multi-Turn Session History
```bash
curl -s http://localhost:8000/sessions/test-s1/messages | jq .
# Expected: Stored user and assistant messages in chronological order
```

#### 7. Unknown Session 404
```bash
curl -s -i http://localhost:8000/sessions/nonexistent-xyz/messages
# Expected: HTTP 404 Not Found
# {"detail": "session not found"}
```

---

## 5. Setup Used

- **Operating System:** Windows 11 / Linux Alpine (Docker)
- **Editor & Environment:** Antigravity IDE
- **AI Assistive Tooling:** Antigravity Agent
- **Language & Runtime:** Python 3.11+, Node.js v22.22.0
- **Frameworks:** FastAPI 0.138, LiteLLM 1.110, React 18.3, Vite 6.1, Tailwind CSS 3.4
- **Testing:** Pytest 9.1, HTTPX, Starlette TestClient

---

## 6. Bonus features (if any)

1. **Interactive Failover Lab UI:**
   A top control console allowing reviewers to simulate HTTP 429, 500, or total provider outage (`*=429`) with one click, showing real-time failover without manual `curl` commands. Includes a 1-click "Reset to Normal" button.
2. **Session Manager & Live Telemetry Sidebar:**
   - One-click "New Session" generator for effortless demonstration of cross-session caching.
   - Real-time Session Analytics Card displaying Cache Hit Rate %, Average Live Latency vs Average Cache Latency, and total failovers handled.
   - Persistent list of recent session IDs created during browsing.
3. **Gateway Health Indicator:**
   Real-time health pill in the header polling `GET /health` with live status, key count, and cache activity.
4. **Per-Key Multi-Provider Routing (`LLM_MODELS`):**
   Supports mixing providers across keys (e.g. `key_1` on Gemini Flash and `key_2` on Groq Llama-3.3) via the optional `LLM_MODELS` environment variable.
5. **Production Cloud Blueprints:**
   Includes `render.yaml` for 1-click backend deployment with persistent SQLite disk mounts and `vercel.json` for frontend SPA routing.
