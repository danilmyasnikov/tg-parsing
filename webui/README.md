# TG-Parsing Web UI

A chat interface for analyzing Telegram channel messages using AI.

## Features

- **Chat Interface**: Modern chatbot-style UI for interacting with your Telegram data
- **Channel Selection**: Select specific channels/senders to include as context
- **Model Selection**: Choose which LLM model to use for analysis
- **Real-time Responses**: Async message handling with loading indicators

## Requirements

Additional dependencies (add to requirements.txt):
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
```

## Running the Web UI

Development (run frontend dev server + backend):

1. Activate your virtualenv and install backend deps:

```powershell
.# from repo root
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn[standard]
```

2. Start backend (from repo root):

```powershell
.\.venv\Scripts\python -m webui.backend
# or with uvicorn (module path includes `webui`):
.\.venv\Scripts\python -m uvicorn webui.backend.app:app --reload --port 8000
```

3. In a second terminal start the frontend dev server:

```powershell
cd webui\frontend
npm install
npm run dev
```

Production (single server): build the frontend into the backend static folder and run the backend only.

```powershell
cd webui\frontend
npm run build   # writes files into webui/backend/static
cd ..
.\.venv\Scripts\python -m webui.backend
```

Open `http://localhost:8000` in your browser. The backend serves built assets from `/static`.

## Environment Variables

- `PG_DSN`: PostgreSQL connection string (default: `postgresql://postgres:postgres@localhost:5432/telegram`)
- `GEMINI_API_KEY` or `GOOGLE_API`: API key for Gemini models

## API Endpoints

- `GET /` - Main chat interface
- `GET /api/senders` - List unique senders from database
- `GET /api/models` - List available LLM models
- `POST /api/chat` - Send a chat message and get response
- `GET /api/health` - Health check

## Usage

1. Start the web server
2. Open `http://localhost:8000` in your browser
3. Click on "All channels" to select specific Telegram channels to analyze
4. Type your question in the input field
5. Press Enter or click the send button to get AI-powered analysis
