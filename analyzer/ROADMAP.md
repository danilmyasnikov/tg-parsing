### **What is Missing / Can Be Improved?**
1.  **No Execution Entry Point**: You have the library code, but no script (like `analyze.py`) to actually *run* a job.
2.  **Raw String Output**: Your prompts ask for JSON (`"Return a JSON array..."`), but `analyze_text` returns a raw string. You need a parsing layer to convert that string into a Python list/dict.
3.  **No Rate Limit Handling**: The Gemini free tier is generous but strict on RPM (requests per minute). If you analyze 10 channels in a loop, you will hit `429` errors immediately.
4.  **No Result Storage**: You analyze the text, but where do the insights go? You need a database table to store the `topics` or `style_analysis`.

---

### **Roadmap: `analyzer` Package**

Here is your implementation roadmap to complete Phase 2, ordered by dependency.

#### **Step 1: Implement Structured Output (JSON Parsing)**
The LLM returns text that *looks* like JSON. You need to parse it safely.
*   **Task**: Create `analyzer/parser.py`.
*   **Implementation**: Add a function that takes the raw string, strips markdown code blocks (```json ... ```), and runs `json.loads()`.
*   **Upgrade**: Gemini Flash 1.5+ supports "Response Schema" (JSON mode). Update `llm_client.py` to accept a `response_schema` argument to force the LLM to output valid JSON natively.

#### **Step 2: Add Rate Limiting & Retries**
*   **Task**: Update `llm_client.py`.
*   **Tool**: Install `tenacity` (`pip install tenacity`).
*   **Implementation**: Decorate `_call` or `analyze_text` with retry logic for `429 Too Many Requests` errors.
    ```python
    from tenacity import retry, stop_after_attempt, wait_exponential
    
    @retry(wait=wait_exponential(multiplier=1, min=4, max=60), stop=stop_after_attempt(5))
    async def analyze_text(...): ...
    ```

#### **Step 3: Create Analysis Storage (DB Schema)**
*   **Task**: Add a table to store the results.
*   **Schema**:
    ```sql
    CREATE TABLE channel_stats (
        id SERIAL PRIMARY KEY,
        channel_id VARCHAR(255) NOT NULL,
        analyzed_at TIMESTAMPTZ DEFAULT NOW(),
        topics JSONB,          -- Stores ["AI", "Crypto", "Python"]
        style_metrics JSONB,   -- Stores {"tone": "informal", "emoji_count": 5}
        raw_report TEXT        -- Full text summary if needed
    );
    ```

#### **Step 4: Build the Orchestrator (`analyze.py`)**
*   **Task**: Create a CLI script similar to `collect.py`.
*   **Workflow**:
    1.  User runs `python analyze.py @channelname`.
    2.  Script calls `collector.resolve` to get ID.
    3.  Calls `analyzer.load_recent_messages` to get context.
    4.  Calls `analyzer.analyze_text` with `TOPIC_EXTRACTION_PROMPT`.
    5.  Parses result -> Saves to `channel_stats` table.
    6.  Prints summary to console.

#### **Step 5: "Context Window" Management**
*   **Issue**: If a channel has huge messages, 30 days of history might exceed the token limit (Gemini Flash has a huge context, but it costs latency/money eventually).
*   **Task**: In `context_loader.py`, add a simple token estimator (1 token ≈ 4 chars) and truncate the oldest messages if the total string length exceeds ~500,000 chars (safe limit for Flash).

### **Immediate Next Action**
Create `analyzer/parser.py` and a simple `analyze.py` script to test the full pipeline end-to-end on one channel.