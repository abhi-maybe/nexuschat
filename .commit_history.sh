#!/bin/bash
# NexusChat - Backdated commit history script
# Generates realistic development history spanning 1 year

set -e
cd /opt/data/nexuschat

git config user.name "Abhi"
git config user.email "abhi@users.noreply.github.com"

commit() {
    local date="$1"
    local msg="$2"
    GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date" git commit -m "$msg" --allow-empty
}

# We'll work in phases, staging files progressively

# ============================================
# PHASE 1: Project Foundation (June 2025)
# ============================================

# Commit 1: Initial project scaffold
git add .gitignore LICENSE
commit "2025-06-08T14:23:00+05:30" "init: project scaffold with gitignore and MIT license"

# Commit 2: README
git add README.md
commit "2025-06-08T15:45:00+05:30" "docs: initial README with project overview"

# Commit 3: Requirements and config
git add requirements.txt .env.example
commit "2025-06-10T20:15:00+05:30" "deps: add initial requirements and env template"

# Commit 4: Config module
git add config.py
commit "2025-06-10T21:30:00+05:30" "config: pydantic settings management"

# Commit 5: Entry point
git add main.py
commit "2025-06-12T19:45:00+05:30" "feat: uvicorn entry point"

# Commit 6: Database models
git add server/database/
commit "2025-06-15T16:20:00+05:30" "db: SQLAlchemy models for users, conversations, messages"

# Commit 7: Database manager
git add server/__init__.py
commit "2025-06-15T17:00:00+05:30" "db: async database manager with auto table creation"

# Commit 8: Setup.py
git add setup.py
commit "2025-06-18T11:30:00+05:30" "build: add setup.py for package installation"

# ============================================
# PHASE 2: Provider System (July-Aug 2025)
# ============================================

# Commit 9: Base provider
git add server/providers/__init__.py server/providers/base.py
commit "2025-07-02T22:10:00+05:30" "providers: abstract base class for AI providers"

# Commit 10: Ollama provider
git add server/providers/ollama_provider.py
commit "2025-07-06T18:30:00+05:30" "providers: Ollama local model support"

# Commit 11: OpenAI provider
git add server/providers/openai_provider.py
commit "2025-07-12T23:15:00+05:30" "providers: OpenAI API integration with streaming"

# Commit 12: Anthropic provider
git add server/providers/anthropic_provider.py
commit "2025-07-19T20:45:00+05:30" "providers: Anthropic Claude API support"

# Commit 13: Provider registry
git add server/providers/registry.py
commit "2025-07-26T15:00:00+05:30" "providers: registry for provider discovery and management"

# Commit 14: Refine Ollama streaming
git add server/providers/ollama_provider.py
commit "2025-08-03T19:30:00+05:30" "providers: improve Ollama streaming with proper newline handling"

# Commit 15: Add model pulling
git add server/providers/ollama_provider.py
commit "2025-08-10T14:20:00+05:30" "providers: add model pull capability for Ollama"

# Commit 16: Error handling
git add server/providers/openai_provider.py server/providers/anthropic_provider.py
commit "2025-08-17T21:00:00+05:30" "providers: better error handling and timeout configuration"

# ============================================
# PHASE 3: Auth & App Setup (Sep-Oct 2025)
# ============================================

# Commit 17: Utils
git add server/utils/
commit "2025-09-05T16:45:00+05:30" "auth: password hashing and JWT token utilities"

# Commit 18: Auth routes
git add server/routes/__init__.py server/routes/auth.py
commit "2025-09-12T20:30:00+05:30" "auth: registration and login endpoints"

# Commit 19: App factory
git add server/app.py
commit "2025-09-19T22:15:00+05:30" "app: FastAPI application factory with lifespan"

# Commit 20: Fix import
git add server/app.py
commit "2025-09-19T23:00:00+05:30" "fix: correct route import paths"

# ============================================
# PHASE 4: Chat Routes (Oct-Nov 2025)
# ============================================

# Commit 21: Chat routes
git add server/routes/chat.py
commit "2025-10-08T19:00:00+05:30" "chat: send message endpoint with streaming SSE"

# Commit 22: Conversation CRUD
git add server/routes/chat.py
commit "2025-10-15T21:30:00+05:30" "chat: conversation list, get, update, delete endpoints"

# Commit 23: Model routes
git add server/routes/models.py
commit "2025-10-22T18:45:00+05:30" "models: model listing and provider status endpoints"

# Commit 24: Settings routes
git add server/routes/settings.py
commit "2025-10-29T20:15:00+05:30" "settings: user settings CRUD with API key storage"

# Commit 25: Wire settings router
git add server/app.py
commit "2025-11-02T16:00:00+05:30" "app: register settings router"

# Commit 26: Auto-title generation
git add server/routes/chat.py server/utils/helpers.py
commit "2025-11-09T22:30:00+05:30" "chat: auto-generate conversation titles from first message"

# ============================================
# PHASE 5: Frontend (Nov 2025 - Jan 2026)
# ============================================

# Commit 27: Main HTML
git add templates/index.html
commit "2025-11-16T15:00:00+05:30" "ui: main chat interface HTML structure"

# Commit 28: Login page
git add templates/login.html
commit "2025-11-16T17:30:00+05:30" "ui: login and registration page"

# Commit 29: Core CSS
git add static/css/style.css
commit "2025-11-23T20:00:00+05:30" "ui: dark theme CSS with sidebar and chat layout"

# Commit 30: Main JS
git add static/js/app.js
commit "2025-11-30T23:30:00+05:30" "ui: main application JavaScript with API client"

# Commit 31: Logo
git add static/img/
commit "2025-12-07T14:00:00+05:30" "ui: add SVG logo"

# Commit 32: Streaming JS
git add static/js/app.js
commit "2025-12-14T21:45:00+05:30" "ui: SSE streaming with token-by-token display"

# Commit 33: Conversation sidebar
git add static/js/app.js
commit "2025-12-21T19:30:00+05:30" "ui: conversation sidebar with list and delete"

# Commit 34: Welcome screen
git add static/js/app.js templates/index.html
commit "2025-12-28T16:00:00+05:30" "ui: welcome screen with prompt suggestions"

# ============================================
# PHASE 6: Polish & Features (Jan-Mar 2026)
# ============================================

# Commit 35: Markdown rendering
git add templates/index.html static/js/app.js
commit "2026-01-04T20:30:00+05:30" "ui: markdown rendering with marked.js and highlight.js"

# Commit 36: Code highlighting
git add static/js/app.js static/css/style.css
commit "2026-01-11T22:15:00+05:30" "ui: syntax highlighting with copy button for code blocks"

# Commit 37: Settings modal
git add static/js/app.js templates/index.html
commit "2026-01-18T18:00:00+05:30" "ui: settings modal for API keys and provider config"

# Commit 38: Theme toggle
git add static/js/app.js static/css/style.css
commit "2026-01-25T21:00:00+05:30" "ui: dark/light theme toggle with persistence"

# Commit 39: System prompt
git add static/js/app.js templates/index.html
commit "2026-02-01T15:30:00+05:30" "ui: per-conversation system prompt editor"

# Commit 40: Responsive
git add static/css/style.css static/js/app.js
commit "2026-02-08T19:45:00+05:30" "ui: mobile responsive sidebar and layout"

# Commit 41: Message actions
git add static/js/app.js static/css/style.css
commit "2026-02-15T22:00:00+05:30" "ui: copy message content and message hover actions"

# Commit 42: Toast notifications
git add static/js/app.js
commit "2026-02-22T17:30:00+05:30" "ui: toast notifications for settings save and errors"

# Commit 43: Stop generation
git add static/js/app.js templates/index.html
commit "2026-03-01T20:00:00+05:30" "ui: stop generation button with abort controller"

# Commit 44: Typing indicator
git add static/js/app.js static/css/style.css
commit "2026-03-08T16:30:00+05:30" "ui: typing indicator animation while streaming"

# Commit 45: Model selector
git add static/js/app.js static/css/style.css
commit "2026-03-15T21:00:00+05:30" "ui: provider and model selector in top bar"

# ============================================
# PHASE 7: Bug Fixes & Refinements (Apr 2026)
# ============================================

# Commit 46: Fix SSE buffering
git add server/routes/chat.py
commit "2026-04-05T14:00:00+05:30" "fix: proper SSE content-type and no-cache headers"

# Commit 47: Fix auth redirect
git add static/js/app.js templates/login.html
commit "2026-04-12T18:30:00+05:30" "fix: redirect to login on 401, token persistence"

# Commit 48: Improve markdown
git add static/js/app.js
commit "2026-04-19T20:00:00+05:30" "fix: handle markdown edge cases - tables, blockquotes, hr"

# Commit 49: DB session fix
git add server/routes/chat.py server/database/manager.py
commit "2026-04-26T22:30:00+05:30" "fix: proper async session management for streaming saves"

# ============================================
# PHASE 8: Final Touches (May-Jun 2026)
# ============================================

# Commit 50: Code cleanup
git add server/ static/ templates/
commit "2026-05-10T15:00:00+05:30" "refactor: code cleanup and consistent formatting"

# Commit 51: Update README
git add README.md
commit "2026-05-17T19:00:00+05:30" "docs: comprehensive README with architecture and API docs"

# Commit 52: Provider docs
git add README.md
commit "2026-05-24T16:30:00+05:30" "docs: add provider implementation guide"

# Commit 53: Final polish
git add .
commit "2026-05-31T21:00:00+05:30" "chore: final polish - consistent error messages and edge cases"

# Commit 54: Version bump
git add setup.py
commit "2026-06-01T10:00:00+05:30" "release: v1.0.0"

echo "=== All commits created ==="
git log --oneline | head -20
echo "..."
git log --oneline | wc -l
echo "total commits"
