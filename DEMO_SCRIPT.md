# 🎬 DEMO VIDEO PLAYBOOK & AI GENERATION PROMPT (2.5 MINUTES TIME-BOXED)

> **Time Target:** 2 minutes 30 seconds  
> **Format:** Screen recording with voiceover (Loom / OBS / QuickTime / AI Video Generator)  
> **Live Frontend URL:** [https://lyftr-chatbot-frontend.vercel.app](https://lyftr-chatbot-frontend.vercel.app)  
> **Live Backend API:** [https://lyftr-chatbot-backend.onrender.com](https://lyftr-chatbot-backend.onrender.com)  
> **Repository:** [https://github.com/Nischal-Agrawal/Lyftr_AI_Full_Stack_Assignment](https://github.com/Nischal-Agrawal/Lyftr_AI_Full_Stack_Assignment)  

---

## Part 1: Step-by-Step Human Presenter Playbook

### Phase 1: Overview & Stack Architecture (0:00 – 0:30)
- **Visual:** Open browser tab at `https://lyftr-chatbot-frontend.vercel.app`.
- **Action:** Show the header badge displaying `Gateway Online • 2 Keys • Cache Active`.
- **Spoken Script:**
  > *"Hi everyone, this is the demo for the Lyftr AI Full-Stack Assignment: a production-grade, highly resilient LLM Chatbot with deterministic key failover, response caching, and atomic SQLite persistence.
  > The frontend is built in React 18, Vite, TypeScript, and Tailwind CSS, hosted live on Vercel.
  > The backend is built with FastAPI, LiteLLM, and SQLite running Write-Ahead Logging (WAL mode), hosted live on Render.
  > In the top header, the live gateway health monitor confirms the backend is healthy, 2 API keys are loaded in our deterministic pool, and response caching is enabled."*

---

### Phase 2: Live Inference & Per-Request Token Tracking (0:30 – 1:00)
- **Action:** In the chat input, click the starter prompt *"What is the capital of France?"* and press **Enter**.
- **Visual:** The assistant responds instantly with *"The capital of France is Paris."* Point cursor to the metadata badges below the message.
- **Spoken Script:**
  > *"Let's trigger our first inference call by asking: 'What is the capital of France?'.
  > Looking at the metadata beneath the reply:
  > - Resolution Source shows `LIVE_INFERENCE` with a blue badge.
  > - Model is `gemini/gemini-2.5-flash`.
  > - Key ID is `key_1` with 0 fallback attempts.
  > - Latency was approximately 600 milliseconds.
  > - Token tracking displays 18 input tokens and 23 output tokens. Crucially, these tokens are calculated per-request, never accumulated into false running sums."*

---

### Phase 3: Cross-Session Response Caching (1:00 – 1:30)
- **Action:** In the left sidebar, click the **"New Session"** button. The session ID refreshes to a brand-new ID (e.g. `s-9a2c`) and chat window resets.
- **Action:** Submit the exact same message: *"What is the capital of France?"*.
- **Visual:** The reply appears instantly in **1 millisecond** with an emerald badge reading `LLM_CACHE`.
- **Spoken Script:**
  > *"Now let's test LiteLLM built-in response caching across completely different sessions.
  > I click 'New Session' in the sidebar to generate a new session ID and clear the view.
  > I submit the exact same query: 'What is the capital of France?'.
  > Notice the badge instantly flips to emerald `LLM_CACHE`:
  > 1. The latency drops from ~600ms down to just 1 millisecond.
  > 2. The reply text and token counts match the cached turn identically.
  > 3. `key_id` is null and `fallback_attempts` is 0, satisfying the contract.
  > In the sidebar analytics card, our Cache Hit Rate has updated in real-time."*

---

### Phase 4: Deterministic Key Failover via `X-Simulate-Failure` (1:30 – 2:10)
- **Action 1:** Expand the **"Interactive Failover Lab"** panel at the top.
- **Action 2:** Click the preset button: **"Simulate key_1 = 429 (Rate Limit)"** (which injects `X-Simulate-Failure: key_1=429`).
- **Action 3:** Send a new message: *"Explain LLM caching in 2 sentences."*.
- **Visual:** The message succeeds without any user-facing glitch! The metadata badge shows `key_2` and an amber badge reading `Failover: 1 retry -> key_2`.
- **Spoken Script:**
  > *"Now let's verify deterministic key failover using our built-in Failover Lab.
  > I select 'Simulate key_1 = 429'. This sends the header `X-Simulate-Failure: key_1=429`.
  > When I send a message, the gateway intercepts the simulated rate limit on `key_1`, logs an internal audit event without exposing credentials, and seamlessly fails over to `key_2`.
  > Notice the metadata: `key_id` is now `key_2`, and `fallback_attempts` equals 1.
  > Now, let's test total provider exhaustion by selecting `* = 429`.
  > I send a message: the backend immediately returns HTTP 503 with exact JSON `{"detail": "all providers unavailable"}`. The frontend renders this as a clean in-stream error banner, and zero corrupt data is written to SQLite."*

---

### Phase 5: Multi-Turn Conversation & SQLite Persistence (2:10 – 2:30)
- **Action:** Click "Reset to Normal" in the Failover Lab. In the left sidebar, click any prior session from **Recent Sessions**.
- **Visual:** The previous multi-turn conversation instantly re-populates from `GET /sessions/{session_id}/messages`.
- **Spoken Script:**
  > *"Finally, let's verify SQLite persistence. Each successful turn is committed atomically in Write-Ahead Logging (WAL) mode inside a Docker volume.
  > Selecting any previous session from the sidebar reloads the full multi-turn dialogue in chronological order directly from `GET /sessions/{session_id}/messages` without system prompt leakage.
  > The entire project can be run locally with `make up` and passes 100% of the 43 contract verification checks.
  > Thank you!"*

---

## Part 2: Detailed Prompt for Gemini / AI Video Generation

Copy and paste the exact block below into Gemini (or an AI video generation tool such as HeyGen, InVideo AI, Runway, or Loom AI) to generate the video, screen visual storyboard, or audio narration:

```text
Create a professional, modern 2-minute-and-30-second technical product walkthrough video for an engineering assignment submission.

PROJECT OVERVIEW:
- Product Name: Lyftr AI Resilient LLM Gateway Console
- Live Frontend: https://lyftr-chatbot-frontend.vercel.app
- Live Backend API: https://lyftr-chatbot-backend.onrender.com
- GitHub Repo: https://github.com/Nischal-Agrawal/Lyftr_AI_Full_Stack_Assignment
- Tech Stack: React 18, TypeScript, Tailwind CSS, FastAPI, LiteLLM, SQLite (WAL mode), Docker.

VISUAL THEME & STYLE:
- Dark mode developer UI (slate-950 background, emerald-400 accent highlights, crisp JetBrains Mono typography).
- Fluid screen recording style showing a sleek browser interface with sidebar navigation, top health monitor, interactive failover lab, and chat stream with pill badges.
- Voiceover: Confident, articulate, professional senior software engineer voice (natural pacing, clear diction, no fluff).

VIDEO TIMELINE & SCENE BREAKDOWN:

[SCENE 1: 0:00 - 0:30] Introduction & Architecture Overview
- Visual: Full desktop screen recording of https://lyftr-chatbot-frontend.vercel.app. Camera zooms gently toward the top header bar highlighting the green badge "Gateway Online • 2 Keys • Cache Active". Quick overlay diagram showing [React Frontend] -> [FastAPI + LiteLLM Gateway] -> [SQLite WAL Volume].
- Audio / Voiceover:
  "Hi everyone, welcome to the demonstration of my Lyftr AI Full-Stack submission: a production-grade, highly resilient LLM Gateway with deterministic key failover, response caching, and atomic SQLite persistence. The frontend is built in React 18 with TypeScript and Tailwind CSS, hosted live on Vercel. The backend is built with FastAPI, LiteLLM, and SQLite running in Write-Ahead Logging mode on Render. In the header, our gateway health indicator confirms the service is online, 2 API keys are configured, and caching is active."

[SCENE 2: 0:30 - 1:00] Live Inference & Token Accounting
- Visual: Mouse clicks the starter prompt card "What is the capital of France?". The input fills and immediately sends. The assistant responds: "The capital of France is Paris." Camera zooms in on the metadata badges below the message:
  [Source: LIVE_INFERENCE] [Model: gemini/gemini-2.5-flash] [Latency: 606ms] [Key: key_1] [Fallbacks: 0] [Tokens: In 18 | Out 23].
- Audio / Voiceover:
  "Let's execute our first live inference turn: 'What is the capital of France?'. Notice how the prompt input cleared immediately upon submission. Underneath the assistant's reply, our metadata satisfies all contract requirements: resolution source is LIVE_INFERENCE on key_1 with 0 fallback attempts, model is gemini/gemini-2.5-flash, latency was ~600ms, and token tracking shows 18 input tokens and 23 output tokens—tracked per-request rather than as a cumulative sum."

[SCENE 3: 1:00 - 1:30] Cross-Session Response Caching
- Visual: Mouse moves to the left sidebar and clicks the "+ New Session" button. The chat area resets and the active session ID updates to a new ID (e.g., s-8b3f). The user enters the exact same prompt: "What is the capital of France?". The response returns in 1 millisecond. The metadata badge turns bright emerald:
  [Source: LLM_CACHE] [Latency: 1ms] [Key: None] [Fallbacks: 0] [Tokens: In 18 | Out 23].
  In the sidebar, the Telemetry card shows "Cache Hit Rate: 50%".
- Audio / Voiceover:
  "Now let's verify response caching across independent sessions. I click 'New Session' in the sidebar to spawn a completely fresh session ID. I send the exact same query: 'What is the capital of France?'. The response appears in just 1 millisecond with an emerald LLM_CACHE badge. Notice three key contract guarantees: latency dropped to 1ms, reply and tokens match the cached turn, and key_id is null with 0 fallback attempts. The sidebar telemetry card updates our cache hit rate in real time."

[SCENE 4: 1:30 - 2:10] Deterministic Key Failover & Error Handling
- Visual: Mouse clicks "Failover Lab" at the top to expand the testing console. User clicks the button "Simulate key_1 = 429 (Rate Limit)". A banner indicates active header: X-Simulate-Failure: key_1=429. User sends a new message: "Explain LLM caching in 2 sentences."
  The assistant answers cleanly. The metadata badge updates to show:
  [Key: key_2] [Failover: 1 retry -> key_2].
  Next, user clicks "Simulate * = 429 (All Keys Down)" and sends a message. The interface cleanly renders an in-stream red error badge: "HTTP 503: all providers unavailable".
- Audio / Voiceover:
  "Next, let's demonstrate deterministic key failover using our Failover Lab. I select 'Simulate key_1 = 429', injecting the X-Simulate-Failure header. When I submit a new question, the gateway catches the rate limit on key_1, logs an internal audit event without leaking credentials, and automatically fails over to key_2 with fallback_attempts equal to 1. The user experiences zero interruption. When I simulate total outage with '* = 429', the API returns HTTP 503 with exact JSON detail 'all providers unavailable', writing zero corrupt rows to SQLite."

[SCENE 5: 2:10 - 2:30] Multi-Turn State, Verification Suite & Conclusion
- Visual: User clicks "Reset to Normal" and selects a previous session from the "Recent Sessions" sidebar list. The full historical chat re-appears instantly. Split screen reveals a terminal running 'python scripts/verify_contract.py --base-url https://lyftr-chatbot-backend.onrender.com' with green [PASS] checkmarks cascading down. Final slide shows GitHub repo URL and live links.
- Audio / Voiceover:
  "Finally, each conversation turn is saved atomically in SQLite using WAL mode. Selecting any previous session reloads the full conversation history from GET /sessions/{session_id}/messages in chronological order. The complete test suite and verification script confirm all contract checks pass. The repository is available on GitHub and the entire stack starts with 'make up'. Thank you!"
```
