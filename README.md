<div align="center">

<img src="static/img/logo.svg" alt="NexusChat Logo" width="100">

# NexusChat

**A modern, open-source ChatGPT-like web interface for local and cloud AI models**

*Supports Ollama, OpenAI, Anthropic, DeepSeek, Xiaomi MiMo, Groq, and OpenRouter with real-time streaming*

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.119+-009688.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](Dockerfile)

</div>

---

## ✨ Features

- 🤖 **Multi-Provider** — Ollama (local), OpenAI, Anthropic, DeepSeek, Xiaomi MiMo, Groq, OpenRouter
- ⚡ **Real-time Streaming** — Token-by-token SSE streaming with stop generation
- 💬 **Conversation Management** — Persistent chat history with SQLite/PostgreSQL
- 🎨 **Dark/Light Theme** — Beautiful dark-first UI with theme toggle
- 📝 **Markdown + Code** — Full GFM rendering with syntax highlighting and copy buttons
- 🔧 **System Prompts** — Per-conversation custom system prompts
- 👥 **Multi-User** — Individual accounts with separate settings and API keys
- 🔒 **Secure** — JWT auth, bcrypt passwords, input sanitization
- 📱 **Responsive** — Works on desktop, tablet, and mobile
- ⌨️ **Keyboard Shortcuts** — Ctrl+Enter send, Ctrl+N new chat, Ctrl+B toggle sidebar
- 🏠 **Self-Hosted** — Runs entirely on your machine or deploy to the cloud
- 🐳 **Docker Ready** — Single command deployment with Docker Compose

## 📸 Screenshots

<div align="center">

### Login
<img src="static/img/screenshots/login.png" alt="Login Page" width="800">

### Chat Interface
<img src="static/img/screenshots/chat.png" alt="Chat Interface" width="800">

### Settings
<img src="static/img/screenshots/settings.png" alt="Settings Modal" width="800">

### Mobile
<img src="static/img/screenshots/mobile.png" alt="Mobile View" width="300">

</div>

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) (for local models, optional)
- API keys for cloud providers (optional)

### Installation

```bash
git clone https://github.com/abhi-maybe/nexuschat.git
cd nexuschat

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Run

```bash
python main.py
# → http://localhost:8080
```

Or run directly with uvicorn:

```bash
uvicorn server.app:create_app --factory --host 0.0.0.0 --port 8080
```

### Using with Ollama (Local)

```bash
# Install and start Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# Pull a model
ollama pull llama3.2

# NexusChat auto-detects running Ollama at http://localhost:11434
```

### Using with Cloud Providers

1. Open **Settings** (gear icon in sidebar)
2. Enter your API key(s) under **Providers**
3. Select the provider from the dropdown in the top bar
4. Choose a model and start chatting

---

## 🐳 Docker

### Quick Start (Docker Compose)

```bash
# Clone and configure
git clone https://github.com/abhi-maybe/nexuschat.git
cd nexuschat
cp .env.example .env
# Edit .env with your SECRET_KEY and API keys

# Build and run
docker compose up -d

# → http://localhost:8080
```

### Docker Only

```bash
docker build -t nexuschat .
docker run -d \
  --name nexuschat \
  -p 8080:8080 \
  -e SECRET_KEY=your-secret-key \
  -v nexuschat-data:/app/data \
  nexuschat
```

### With Ollama (GPU)

Uncomment the Ollama block in `docker-compose.yml` to run both services:

```bash
docker compose up -d
# NexusChat will connect to Ollama at http://host.docker.internal:11434
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `change-me` | JWT signing key (change in production!) |
| `DATABASE_URL` | SQLite | PostgreSQL connection string (optional) |
| `DEFAULT_PROVIDER` | `ollama` | Default AI provider |
| `DEFAULT_MODEL` | `llama3.2` | Default model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `PORT` | `8080` | Server port |

---

## 🏗️ Architecture

```
nexuschat/
├── main.py                    # Entry point
├── config.py                  # Configuration (env-based)
├── Dockerfile                 # Docker build
├── docker-compose.yml         # Docker Compose setup
├── server/
│   ├── app.py                 # FastAPI application factory
│   ├── routes/
│   │   ├── auth.py            # Register / Login / JWT
│   │   ├── chat.py            # Chat & conversations CRUD
│   │   ├── models.py          # Model listing & provider status
│   │   ├── settings.py        # User settings & API keys
│   │   └── health.py          # Health check endpoint
│   ├── providers/
│   │   ├── base.py            # Abstract provider interface
│   │   ├── openai_compatible.py  # Shared base for OpenAI-format APIs
│   │   ├── ollama_provider.py    # Ollama local inference
│   │   ├── openai_provider.py    # OpenAI GPT models
│   │   ├── anthropic_provider.py # Anthropic Claude
│   │   ├── deepseek_provider.py  # DeepSeek
│   │   ├── xiaomi_provider.py    # Xiaomi MiMo
│   │   ├── groq_provider.py      # Groq (fast inference)
│   │   ├── openrouter_provider.py # OpenRouter (200+ models)
│   │   └── registry.py           # Provider discovery & management
│   ├── database/
│   │   ├── models.py          # SQLAlchemy models
│   │   └── manager.py         # Async database manager
│   └── middleware/
│       └── cors.py            # CORS configuration
├── static/
│   ├── css/style.css          # Dark/light theme
│   ├── js/
│   │   ├── app.js             # Main SPA logic
│   │   ├── utils.js           # Utility functions
│   │   └── keyboard.js        # Keyboard shortcuts
│   └── img/
│       ├── logo.svg           # Project logo
│       ├── favicon.svg        # Favicon
│       └── screenshots/       # README screenshots
└── templates/
    ├── index.html             # Chat interface
    └── login.html             # Auth page
```

## 🛠️ Tech Stack

- **Backend:** FastAPI + Uvicorn (async)
- **Database:** SQLite / PostgreSQL via SQLAlchemy (async)
- **Frontend:** Vanilla JS + Marked.js + Highlight.js
- **Auth:** JWT (python-jose) + bcrypt
- **HTTP Client:** httpx (async)
- **Streaming:** Server-Sent Events (SSE)
- **Containerization:** Docker + Docker Compose

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Get JWT token |
| GET | `/api/auth/me` | Current user info |
| POST | `/api/chat/send` | Send message (streaming) |
| GET | `/api/chat/conversations` | List conversations |
| GET | `/api/chat/conversations/:id` | Get conversation |
| PUT | `/api/chat/conversations/:id` | Update conversation |
| DELETE | `/api/chat/conversations/:id` | Delete conversation |
| GET | `/api/models/available` | List available models |
| GET | `/api/models/status` | Provider availability |
| GET | `/api/settings/` | Get user settings |
| PUT | `/api/settings/` | Update settings |
| GET | `/api/health` | Health check |

## 🔌 Adding New Providers

For OpenAI-compatible APIs, extend `OpenAICompatibleProvider`:

```python
from server.providers.openai_compatible import OpenAICompatibleProvider
from server.providers.base import ModelInfo

class MyProvider(OpenAICompatibleProvider):
    name = "myprovider"
    display_name = "My Provider"
    BASE_URL = "https://api.myprovider.com/v1"
    AVAILABLE_MODELS = [
        ModelInfo(id="model-1", name="Model 1", provider="myprovider"),
    ]
```

For non-OpenAI APIs, implement `BaseProvider` directly:

```python
from server.providers.base import BaseProvider, ChatMessage

class MyProvider(BaseProvider):
    name = "myprovider"
    display_name = "My Provider"

    async def chat(self, messages, model, **kwargs):
        ...

    async def chat_stream(self, messages, model, **kwargs):
        ...  # yield tokens

    async def list_models(self):
        ...

    async def is_available(self):
        ...
```

Then register in `server/providers/registry.py`.

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

<div align="center">

Made with ❤️ by [Abhi](https://github.com/abhi-maybe)

</div>
