# NexusChat

<div align="center">

**A ChatGPT-like web interface for local and cloud AI models**

*Supports Ollama (local), OpenAI, and Anthropic with real-time streaming*

</div>

---

## Features

- 🔒 **Secure** — JWT auth, bcrypt passwords, input sanitization

- **Multi-Provider Support** — Ollama, OpenAI, Anthropic in one interface
- **Real-time Streaming** — Token-by-token response streaming via SSE
- **Conversation Management** — Persistent chat history with SQLite
- **Dark/Light Theme** — Toggle between themes
- **Markdown Rendering** — Full GFM support with syntax highlighting
- **Code Highlighting** — Copy code blocks with one click
- **System Prompts** — Per-conversation custom system prompts
- **Multi-User** — Individual accounts with separate settings and API keys
- **Responsive** — Works on desktop and mobile
- **Self-Hosted** — Runs entirely on your machine

## Quick Start

> **Requirements:** Python 3.11+, pip

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) (for local models, optional)
- OpenAI/Anthropic API keys (for cloud models, optional)

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
# Edit .env with your settings
```

### Running

```bash
# Start the server
python main.py

# Or with uvicorn directly
uvicorn server.app:create_app --factory --host 0.0.0.0 --port 8080
```

Open **http://localhost:8080** in your browser.

### Using with Ollama

```bash
# Install and start Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# Pull a model
ollama pull llama3.2

# NexusChat auto-detects running Ollama instances
```

### Using with OpenAI / Anthropic

1. Open Settings (gear icon in sidebar)
2. Enter your API key under **Providers**
3. Select the provider from the dropdown in the top bar
4. Choose a model and start chatting

## Architecture

```
nexuschat/
├── main.py                 # Entry point
├── config.py               # Configuration management
├── server/
│   ├── app.py              # FastAPI application factory
│   ├── routes/
│   │   ├── auth.py         # Authentication (register/login)
│   │   ├── chat.py         # Chat & conversation CRUD
│   │   ├── models.py       # Model listing & provider status
│   │   └── settings.py     # User settings & API keys
│   ├── providers/
│   │   ├── base.py         # Abstract provider interface
│   │   ├── ollama_provider.py    # Ollama local inference
│   │   ├── openai_provider.py    # OpenAI API
│   │   ├── anthropic_provider.py # Anthropic Claude API
│   │   └── registry.py    # Provider discovery & management
│   └── database/
│       ├── models.py       # SQLAlchemy models
│       └── manager.py      # Database connection manager
├── static/
│   ├── css/style.css       # Full dark/light theme
│   └── js/app.js           # Frontend SPA logic
└── templates/
    ├── index.html          # Main chat interface
    └── login.html          # Auth page
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI + Uvicorn |
| **Database** | SQLite via SQLAlchemy (async) |
| **Frontend** | Vanilla JS + Marked.js + Highlight.js |
| **Auth** | JWT (python-jose) + bcrypt |
| **HTTP Client** | httpx (async) |
| **Streaming** | Server-Sent Events (SSE) |

## API Endpoints

### Auth
- `POST /api/auth/register` — Create account
- `POST /api/auth/login` — Get JWT token
- `GET /api/auth/me` — Current user info

### Chat
- `POST /api/chat/send` — Send message (supports streaming)
- `GET /api/chat/conversations` — List conversations
- `GET /api/chat/conversations/:id` — Get conversation with messages
- `PUT /api/chat/conversations/:id` — Update title/system prompt
- `DELETE /api/chat/conversations/:id` — Delete conversation

### Models
- `GET /api/models/available` — List all available models
- `GET /api/models/status` — Check provider availability

### Settings
- `GET /api/settings/` — Get user settings
- `PUT /api/settings/` — Update settings (API keys, defaults, theme)

## Adding New Providers

Implement the `BaseProvider` interface:

```python
from server.providers.base import BaseProvider, ChatMessage, ChatResponse, ModelInfo

class MyProvider(BaseProvider):
    name = "myprovider"
    display_name = "My Provider"

    async def chat(self, messages, model, system_prompt="", temperature=0.7, max_tokens=4096):
        # Implement non-streaming chat
        ...

    async def chat_stream(self, messages, model, system_prompt="", temperature=0.7, max_tokens=4096):
        # Implement streaming chat (yield tokens)
        ...

    async def list_models(self):
        # Return available models
        ...

    async def is_available(self):
        # Check if provider is configured and reachable
        ...
```

Then register it in `server/providers/registry.py`.

## Star History

If you find NexusChat useful, consider giving it a ⭐

## License

MIT License — see [LICENSE](LICENSE)

---

<div align="center">
Made with ❤️ by <a href="https://github.com/abhi-maybe">Abhi</a>
</div> — see [LICENSE](LICENSE)
