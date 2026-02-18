# Word Translator

Upload Word (.docx) documents and get side-by-side Chinese-English translations.

## Tech Stack

- **Backend**: Python 3.13 + FastAPI + python-docx + OpenAI
- **Frontend**: React 19 + TypeScript + Vite

## Quick Start

### Backend

```bash
cd backend
cp .env.example .env  # Add your OpenAI API key
uv sync
uv run uvicorn src.main:app --reload --port 8888
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:2321`, backend at `http://localhost:8888`.
