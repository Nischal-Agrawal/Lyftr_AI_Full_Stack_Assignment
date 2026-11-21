# 🎬 DEMO VIDEO PLAYBOOK (2.5 MINUTES TIME-BOXED)

> **Time Target:** 2 minutes 30 seconds  
> **Format:** Screen recording with voiceover (Loom / OBS / QuickTime)  
> **Key Goal:** Showcase live frontend, multi-turn conversation, cross-session response caching, deterministic key failover via `X-Simulate-Failure`, clean 503 error handling, and SQLite persistence.

---

### Phase 1: Overview & Stack Architecture (0:00 – 0:30)
- **Visual:** Open browser on the deployed frontend (or `http://localhost:3000`).
- **Script:**
  > *"Hi team, welcome to the demo of my Lyftr AI Full-Stack submission: an enterprise-resilient LLM Gateway with deterministic key failover and LiteLLM response caching.
  > The frontend is built in React 18, Vite, and Tailwind CSS. The backend runs FastAPI on Python 3.11 with LiteLLM and SQLite with WAL mode inside a Docker volume.
  > In the top bar, you can see our live gateway health indicator reporting that the gateway is online with 2 configured API keys and active response caching."*

---

### Phase 2: Live Inference & Per-Request Token Tracking (0:30 – 1:00)
- **Action:** Click one of the starter prompts (e.g., *"What is the capital of France?"*) or type a message and press **Enter**.
- **Visual:** The reply appears instantly. Point cursor to the metadata badges under the message.
- **Script:**
  > *"Let's send our first message: 'What is the capital of France?'. Notice how the chat input cleared immediately.
  > Under the assistant reply, we see our strict contract metadata:
  > - Resolution source: `LIVE_INFERENCE`
  > - Model: `gemini/gemini-2.0-flash`
  > - Latency: `~780 ms`
  > - Input Tokens: `42`, Output Tokens: `9` (tracked per-request, never a cumulative sum)
  > - Key ID: `key_1` with 0 fallback attempts."*

---

### Phase 3: Response Caching Across Sessions (1:00 – 1:30)
- **Action:** In the left sidebar, click the **"New Session"** button. The chat view clears and a brand-new `session_id` is generated.
- **Action:** Click the same starter prompt *"What is the capital of France?"* and press **Enter**.
- **Visual:** The response returns in 1–3 milliseconds with an emerald `LLM_CACHE` pill!
- **Script:**
  > *"Now let's test LiteLLM's built-in caching. I'll click 'New Session' in the sidebar to generate a brand-new session ID.
  > I send the exact same prompt again.
  > Look at the metadata pill: it instantly displays `LLM_CACHE`.
  > Notice three critical things:
  > 1. The reply text and token counts are identical to the original inference call.
  > 2. Latency dropped from ~800ms down to just 2ms!
  > 3. `key_id` is null and `fallback_attempts` is 0, exactly as required by the contract."*

---

### Phase 4: Deterministic Failover Lab & Error Handling (1:30 – 2:15)
- **Action:** Expand the **"Interactive Failover Lab"** panel at the top.
- **Action 1:** Select preset `Simulate key_1 = 429 (Rate Limit)` (which injects `X-Simulate-Failure: key_1=429`).
- **Action 2:** Send a new prompt (e.g., *"Explain LLM response caching in 2 sentences."*).
- **Visual:** Reply succeeds, but the metadata badges display `key_2` and an amber pill: `Failover: 1 retry -> key_2`.
- **Script:**
  > *"Next, let's demonstrate automatic key failover without exhausting real provider quotas.
  > In our Interactive Failover Lab, I select 'Simulate key_1 = 429'. This sends `X-Simulate-Failure: key_1=429`.
  > I send a new message. Notice the gateway caught the simulated rate limit on `key_1`, automatically failed over to `key_2`, and returned `LIVE_INFERENCE` on `key_2` with `fallback_attempts: 1`. The user never experienced a glitch.
  > Now, let's simulate total provider failure by selecting `* = 429` (all keys down).
  > I send a message: the backend returns HTTP 503 with `detail: 'all providers unavailable'`, rendered gracefully as an in-stream alert banner. Zero corrupt data was saved to SQLite."*

---

### Phase 5: Multi-Turn State & SQLite Verification (2:15 – 2:30)
- **Action:** Select a previous session from the **Recent Sessions** list in the sidebar. Show how multi-turn history is restored.
- **Script:**
  > *"Finally, each turn is atomically stored in SQLite using WAL mode. Selecting any recent session loads the full multi-turn conversation from `GET /sessions/{session_id}/messages` in chronological order without the system prompt.
  > Everything starts with a single command: `make up`. Thank you!"*
