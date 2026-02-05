# Project Plan: AI-Powered Telegram Content System

## Executive Summary
This project aims to evolve an existing Telegram archiving tool into a full-cycle content engine. By leveraging a modular architecture and free-tier AI APIs, we will transform raw historical data into actionable insights and generate original content. The approach focuses on extending the current Python-based `collector` with distinct `analyzer` and `generator` modules within a Monorepo structure.

The critical decision here is to adopt a **Monorepo** strategy to simplify shared database access and code reuse. We will use **Google Gemini (via Google AI Studio)** as the primary AI engine due to its generous free tier and large context window, which is ideal for analyzing long channel histories. The system will be orchestrated via a lightweight task queue (using Postgres itself) to keep infrastructure simple and Docker-compatible.

**Estimated Timeline:** 4-6 Weeks for MVP completion.

---

## 1. Architecture Decision: Repository Structure

### Recommendation: **Monorepo**
Given that you are a solo developer (or small team) and the components are tightly coupled via the database, a monorepo is the most efficient choice.

**Reasoning:**
*   **Shared Data Models:** All three phases rely on the same Postgres `messages` table. In a multi-repo setup, you would need to duplicate your SQLAlchemy models or create a private package, adding unnecessary overhead.
*   **Unified Config:** You can share API keys, DB credentials, and logging configurations easily.
*   **Simplified Deployment:** One `docker-compose` file can spin up the collector, analyzer, and generator services.
*   **Code Reuse:** Utility functions like text normalization (`normalize.py`) are useful for both archiving and AI analysis.

### Recommended Structure

We will restructure `tg-parsing/` to separate concerns while keeping the core library accessible.

```text
tg-parsing/
├── core/                   # Shared logic (MOVED from collector/)
│   ├── config.py           # Unified configuration
│   ├── db/                 # Database models & connection logic
│   │   ├── models.py       # SQLAlchemy models (Messages, Analysis, Drafts)
│   │   └── session.py      # DB session factory
│   └── utils.py            # Shared helpers (normalization, date tools)
│
├── collector/              # Phase 1: Archiving (Existing)
│   ├── client.py           # Telethon client
│   ├── consumer.py         # Message consumption
│   └── main.py             # Entry point for collection
│
├── analyzer/               # Phase 2: AI Analysis
│   ├── llm_client.py       # Wrapper for AI APIs (Gemini/HuggingFace)
│   ├── prompts.py          # Prompt templates for analysis
│   ├── processors/         # Logic for specific insights (Trends, Tone)
│   └── main.py             # Entry point for background analysis jobs
│
├── generator/              # Phase 3: Content Creation
│   ├── agents/             # Logic for specific agents
│   │   ├── ideator.py      # Idea Generator Agent
│   │   ├── writer.py       # Content Writer Agent
│   │   └── editor.py       # Moderator Agent
│   ├── workflow.py         # Orchestration logic (LangChain or custom)
│   └── main.py             # Entry point for generation services
│
├── web_ui/                 # Simple Streamlit/FastAPI dashboard for approvals
│   └── app.py
│
├── docker-compose.yml      # Orchestrates Postgres + 3 Python services
└── requirements.txt        # Unified dependencies
```

---

## 2. Technology Stack

### Core Infrastructure
*   **Language:** Python 3.10+ (Async/Await)
*   **Database:** PostgreSQL 14+ (Existing)
*   **ORM:** SQLAlchemy (Async) or Tortoise-ORM (Good for async). *Stick to what you currently use in `storage.py` if it works well.*
*   **Queue/Broker:** **Postgres-based Queue**.
    *   *Why?* You don't need the complexity of Redis/Celery yet. A simple table `task_queue` polled by workers is sufficient for 10-50 channels and keeps the stack simple (no extra Docker container).

### Phase 2: Analysis (AI Stack)
*   **Primary API (Free):** **Google Gemini 1.5 Flash** (via Google AI Studio).
    *   *Why:* Massive context window (1M tokens) allows you to feed *months* of channel history in a single prompt to find trends. Extremely fast and free tier is generous.
*   **Secondary API (Backup/Specific Tasks):** **Hugging Face Inference API**.
    *   *Models:* `bart-large-cnn` for summarization, `distilbert` for simple sentiment if Gemini is rate-limited.

### Phase 3: Generation (AI Stack)
*   **Creative Writing:** **Google Gemini Pro** or **Groq (Llama 3)**.
    *   *Why:* Groq offers incredibly fast inference for free (currently), making multi-turn agent conversations feel real-time.
*   **Orchestration:** **LangChain** (Lite usage) or **Simple Function Calling**.
    *   *Recommendation:* Don't overengineer with LangGraph yet. Use simple Python classes for agents.

---

## 3. Data Architecture

We need to extend your schema to support analysis and the content generation workflow.

### New Tables (SQLAlchemy Models)

**1. `channel_stats` (Phase 2)**
Stores aggregated insights to avoid re-analyzing raw messages constantly.
*   `channel_id` (FK)
*   `analysis_date` (Date)
*   `top_topics` (JSONB) - e.g., `["AI News", "Crypto", "Python"]`
*   `avg_engagement` (Float)
*   `posting_schedule_heatmap` (JSONB) - Best times to post.

**2. `content_ideas` (Phase 3 - Ideator)**
*   `id` (PK)
*   `source_channel_id` (FK) - Which channel inspired this?
*   `topic` (String)
*   `summary` (Text)
*   `status` (Enum: `new`, `approved`, `rejected`)

**3. `post_drafts` (Phase 3 - Writer/Editor)**
*   `id` (PK)
*   `idea_id` (FK)
*   `content_text` (Text)
*   `version` (Int)
*   `agent_notes` (Text) - Comments from the Editor agent.
*   `status` (Enum: `draft`, `review_pending`, `human_approval`, `scheduled`, `posted`)
*   `scheduled_time` (Datetime)

---

## 4. Phase 2 Implementation Plan (Analysis)

### Step 1: The "Context Loader"
Create a utility in `analyzer/` that fetches messages efficiently for the LLM.
*   **Input:** `channel_id`, `days_back` (e.g., 30 days).
*   **Action:** Query Postgres, format messages into a single text block: `[Date] Sender: Message`.
*   **Optimization:** Truncate very long messages to save tokens.

### Step 2: The LLM Client
Create `analyzer/llm_client.py` using `google-generativeai` library.

```python
# analyzer/llm_client.py
import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

async def analyze_text(prompt, context_data):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = await model.generate_content_async(
        f"{prompt}\n\nDATA:\n{context_data}"
    )
    return response.text
```

### Step 3: Analysis Scripts
Create prompts in `analyzer/prompts.py` for different jobs:
1.  **Topic Extraction:** "Identify the top 5 recurring topics in this telegram channel history."
2.  **Style Analysis:** "Analyze the writing style (formal/informal, emoji usage, length) of these messages."

### Step 4: Storage
Save the JSON output from Gemini into the `channel_stats` table.

---

## 5. Phase 3 Implementation Plan (Generation & Posting)

### Workflow Overview
1.  **Trigger:** Cron job (e.g., daily at 9 AM).
2.  **Ideator Agent:** Reads `channel_stats` + last 24h news (optional) -> Inserts into `content_ideas`.
3.  **Human:** Reviews ideas in Web UI (Streamlit) -> Clicks "Generate Draft".
4.  **Writer Agent:** Reads selected idea -> Creates `post_drafts`.
5.  **Editor Agent:** Critiques draft -> Updates `post_drafts`.
6.  **Human:** Final Approval -> Status changes to `scheduled`.
7.  **Poster:** Crontab checks for `scheduled` posts -> Sends via Telethon.

---

## 6. AI Agent Architecture

We will use a **Sequential Chain** pattern.

### Agent 1: The Ideator (Trend Spotter)
*   **Role:** Look at what performed well last week vs. what is happening now.
*   **Model:** Gemini 1.5 Flash (Large context).
*   **Input:** Last 50 messages from tracked channels + High performing keywords from DB.
*   **Prompt:** "Based on these recent high-engagement posts, suggest 3 original post ideas that fit the channel's theme."

### Agent 2: The Writer (Content Creator)
*   **Role:** Draft the actual text.
*   **Model:** Groq (Llama 3 70B) or Gemini Pro.
*   **Input:** Selected Idea + Style Guide (derived from Phase 2 analysis).
*   **Prompt:** "Write a Telegram post about [Topic]. Use this specific style: [Style Guidelines]. Include relevant hashtags."

### Agent 3: The Editor (Quality Control)
*   **Role:** Critic and refiner.
*   **Model:** Gemini Pro.
*   **Input:** The Draft from Agent 2.
*   **Prompt:** "Review this draft. Check for: 1. Clarity. 2. Tone consistency. 3. Prohibited words. If issues exist, rewrite the bad parts. Output JSON: {status: 'ok'/'revised', content: '...'}"

---

## 7. Integration Guide

### How to modify existing `collector` code
1.  **Move DB Logic:** Move your `storage.py` and models to `core/db/` so the new folders can import them.
2.  **Refactor Imports:** Update `collector/consumer.py` to import from `core.db`.
3.  **No Logic Change:** The collector logic itself (FloodWait, normalization) stays exactly the same. It just writes to the shared DB.

---

## 8. Similar Projects to Study

1.  **Auto-GPT / BabyAGI:**
    *   *Link:* [GitHub - Significant-Gravitas/Auto-GPT](https://github.com/Significant-Gravitas/Auto-GPT)
    *   *Takeaway:* Learn how they structure "Thought -> Plan -> Action" loops. Note: These are complex; keep yours simpler.
2.  **LangChain Templates (Research Assistant):**
    *   *Link:* [LangChain Templates](https://github.com/langchain-ai/langchain)
    *   *Takeaway:* Look for the "Summarization" and "Extraction" chains.
3.  **Telethon Examples:**
    *   *Link:* [Telethon GitHub](https://github.com/LonamiWebs/Telethon)
    *   *Takeaway:* Review `interactive_telegram_client.py` for sending messages safely.

---

## 9. Development Roadmap

### Week 1: Foundation & Refactoring
*   [ ] Create Monorepo structure (`core`, `collector`, `analyzer`).
*   [ ] Move `storage.py` to `core/db` and ensure `collector` still runs.
*   [ ] Create the `channel_stats` DB model.
*   [ ] Get a Google Gemini API Key.

### Week 2: Phase 2 (Analysis)
*   [ ] Build `analyzer/llm_client.py` connecting to Gemini.
*   [ ] Write the "Context Loader" to fetch and format 1000 messages.
*   [ ] Run first manual script to extract "Top Topics" and print to console.
*   [ ] Save insights to `channel_stats`.

### Week 3: Phase 3 (Agents & drafts)
*   [ ] Create `content_ideas` and `post_drafts` tables.
*   [ ] Build **Agent 1 (Ideator)** to populate the ideas table.
*   [ ] Build a minimal **Streamlit UI** (`pip install streamlit`) to view DB rows (Ideas/Drafts).

### Week 4: Completion
*   [ ] Build **Agent 2 & 3 (Writer/Editor)**.
*   [ ] Implement the "Poster" service (checks DB for `scheduled` posts -> calls Telethon `send_message`).
*   [ ] Dockerize the new services.

---

## 10. Next Immediate Steps (Start TODAY)

1.  **Refactor Folder Structure:** Create the `core/` directory and move your `config.py` and `storage.py` there. Fix imports in `collect.py` to ensure the existing archiver still works.
2.  **API Key:** Sign up for [Google AI Studio](https://aistudio.google.com/) and generate a free API key.
3.  **Test Script:** Write a simple Python script (outside the main app) that connects to your local Postgres, fetches the last 50 messages, and sends them to Gemini with the prompt: *"Summarize these messages in 3 bullet points."*

This confirms your data pipeline (DB -> Python -> LLM) works before you build the complex architecture.