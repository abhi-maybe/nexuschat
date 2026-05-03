/* ============================================
   NexusChat - Main Application
   ============================================ */

/* API Client */
const API = {
    token: localStorage.getItem('nexuschat_token'),

    headers() {
        return {
            'Content-Type': 'application/json',
            ...(this.token ? { 'Authorization': `Bearer ${this.token}` } : {}),
        };
    },

    /** GET request */
    async get(url) {
        const resp = await fetch(url, { headers: this.headers() });
        if (resp.status === 401) { this.logout(); return null; }
        if (!resp.ok) throw new Error(`GET ${url}: ${resp.status}`);
        return resp.json();
    },

    async post(url, body) {
        const resp = await fetch(url, {
            method: 'POST',
            headers: this.headers(),
            body: JSON.stringify(body),
        });
        if (resp.status === 401) { this.logout(); return null; }
        if (!resp.ok) {
            const data = await resp.json().catch(() => ({}));
            throw new Error(data.detail || `POST ${url}: ${resp.status}`);
        }
        return resp.json();
    },

    async put(url, body) {
        const resp = await fetch(url, {
            method: 'PUT',
            headers: this.headers(),
            body: JSON.stringify(body),
        });
        if (resp.status === 401) { this.logout(); return null; }
        if (!resp.ok) throw new Error(`PUT ${url}: ${resp.status}`);
        return resp.json();
    },

    async del(url) {
        const resp = await fetch(url, {
            method: 'DELETE',
            headers: this.headers(),
        });
        if (resp.status === 401) { this.logout(); return null; }
        if (!resp.ok) throw new Error(`DELETE ${url}: ${resp.status}`);
        return resp.json();
    },

    logout() {
        localStorage.removeItem('nexuschat_token');
        localStorage.removeItem('nexuschat_username');
        window.location.href = '/login';
    },

    /** Streaming POST request via SSE */
    async stream(url, body, onChunk, onDone, onError) {
        const controller = new AbortController();
        try {
            const resp = await fetch(url, {
                method: 'POST',
                headers: this.headers(),
                body: JSON.stringify(body),
                signal: controller.signal,
            });
            if (resp.status === 401) { this.logout(); return controller; }
            if (!resp.ok) {
                const data = await resp.json().catch(() => ({}));
                throw new Error(data.detail || `Stream error: ${resp.status}`);
            }

            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.error) {
                                onError(data.error);
                            } else if (data.done) {
                                onDone(data);
                            } else if (data.content) {
                                onChunk(data.content, data);
                            }
                        } catch (e) { /* skip malformed */ }
                    }
                }
            }
        } catch (err) {
            if (err.name !== 'AbortError') onError(err.message);
        }
        return controller;
    },
};


/* ============================================
   Markdown Renderer (marked + highlight.js)
   ============================================ */
const renderer = new marked.Renderer();

renderer.code = function(code, language) {
    const codeText = typeof code === 'object' ? code.text : code;
    const lang = typeof code === 'object' ? code.lang : language;
    const validLang = lang && hljs.getLanguage(lang) ? lang : 'plaintext';
    const highlighted = hljs.highlight(codeText, { language: validLang }).value;
    const id = 'code-' + Math.random().toString(36).substr(2, 9);
    return `<pre><div class="code-header"><span>${validLang}</span><button onclick="copyCode('${id}')">Copy</button></div><code id="${id}" class="hljs language-${validLang}">${highlighted}</code></pre>`;
};

marked.setOptions({
    renderer: renderer,
    breaks: true,
    gfm: true,
});

function renderMarkdown(text) {
    if (!text) return '';
    return marked.parse(text);
}

function copyCode(id) {
    const el = document.getElementById(id);
    if (el) {
        navigator.clipboard.writeText(el.textContent);
        const btn = el.parentElement.querySelector('button');
        if (btn) {
            btn.textContent = 'Copied!';
            setTimeout(() => btn.textContent = 'Copy', 2000);
        }
    }
}
window.copyCode = copyCode;


/* ============================================
   App State
   ============================================ */
const state = {
    conversations: [],
    currentConversationId: null,
    currentMessages: [],
    isStreaming: false,
    abortController: null,
    systemPrompt: '',
    models: [],
    providers: {},
};


/* ============================================
   DOM Elements
   ============================================ */
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const els = {
    sidebar: $('#sidebar'),
    sidebarToggle: $('#sidebar-toggle'),
    conversationsList: $('#conversations-list'),
    newChatBtn: $('#new-chat-btn'),
    settingsBtn: $('#settings-btn'),
    settingsModal: $('#settings-modal'),
    closeSettings: $('#close-settings'),
    saveSettings: $('#save-settings'),

    providerSelect: $('#provider-select'),
    modelSelect: $('#model-select'),
    systemPromptBtn: $('#system-prompt-btn'),
    systemPromptModal: $('#system-prompt-modal'),
    systemPromptInput: $('#system-prompt-input'),
    saveSystemPrompt: $('#save-system-prompt'),

    chatMessages: $('#chat-messages'),
    welcomeScreen: $('#welcome-screen'),
    chatInput: $('#chat-input'),
    sendBtn: $('#send-btn'),
    stopBtn: $('#stop-btn'),
};


/* ============================================
   Initialization
   ============================================ */
async function init() {
    if (!API.token) {
        window.location.href = '/login';
        return;
    }
    // Check token validity
    try { await API.get('/api/auth/me'); } catch { API.logout(); return; }

    setupEventListeners();
    await loadConversations();
    await loadModels();
    await loadSettings();
    autoResizeTextarea();
}

function setupEventListeners() {
    // Sidebar
    els.sidebarToggle.addEventListener('click', () => els.sidebar.classList.toggle('open'));
    els.newChatBtn.addEventListener('click', startNewChat);

    // Chat input
    els.chatInput.addEventListener('input', () => {
        autoResizeTextarea();
        els.sendBtn.disabled = !els.chatInput.value.trim() || state.isStreaming;
    });
    els.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    els.sendBtn.addEventListener('click', sendMessage);
    els.stopBtn.addEventListener('click', stopStreaming);

    // Provider/Model selection
    els.providerSelect.addEventListener('change', () => loadModels());
    els.modelSelect.addEventListener('change', () => {});

    // Settings
    els.settingsBtn.addEventListener('click', () => els.settingsModal.classList.remove('hidden'));
    els.closeSettings.addEventListener('click', () => els.settingsModal.classList.add('hidden'));
    els.settingsModal.querySelector('.modal-backdrop').addEventListener('click', () => els.settingsModal.classList.add('hidden'));
    els.saveSettings.addEventListener('click', saveSettings);

    // System prompt
    els.systemPromptBtn.addEventListener('click', () => {
        els.systemPromptInput.value = state.systemPrompt;
        els.systemPromptModal.classList.remove('hidden');
    });
    els.systemPromptModal.querySelector('.modal-backdrop').addEventListener('click', () => els.systemPromptModal.classList.add('hidden'));
    els.systemPromptModal.querySelector('.close-modal')?.addEventListener('click', () => els.systemPromptModal.classList.add('hidden'));
    els.saveSystemPrompt.addEventListener('click', () => {
        state.systemPrompt = els.systemPromptInput.value;
        els.systemPromptModal.classList.add('hidden');
    });

    // Welcome cards
    document.addEventListener('click', (e) => {
        const card = e.target.closest('.welcome-card');
        if (card) {
            els.chatInput.value = card.dataset.prompt;
            autoResizeTextarea();
            sendMessage();
        }
    });

    // Theme
    const savedTheme = localStorage.getItem('nexuschat_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
}


/* ============================================
   Conversations
   ============================================ */
async function loadConversations() {
    try {
        const data = await API.get('/api/chat/conversations');
        if (!data) return;
        state.conversations = data.conversations;
        renderConversations();
    } catch (err) {
        console.error('Failed to load conversations:', err);
    }
}

function renderConversations() {
    if (state.conversations.length === 0) {
        els.conversationsList.innerHTML = '<p style="padding:12px;font-size:13px;color:var(--text-muted);text-align:center;">No conversations yet</p>';
        return;
    }

    els.conversationsList.innerHTML = state.conversations.map(c => `
        <div class="conv-item ${c.id === state.currentConversationId ? 'active' : ''}" data-id="${c.id}">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            <span class="conv-title">${escapeHtml(c.title)}</span>
            <button class="conv-delete" data-id="${c.id}" title="Delete">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
        </div>
    `).join('');

    // Click handlers
    els.conversationsList.querySelectorAll('.conv-item').forEach(el => {
        el.addEventListener('click', (e) => {
            if (e.target.closest('.conv-delete')) return;
            openConversation(parseInt(el.dataset.id));
        });
    });

    els.conversationsList.querySelectorAll('.conv-delete').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const id = parseInt(btn.dataset.id);
            if (confirm('Delete this conversation? This cannot be undone.')) {
                await API.del(`/api/chat/conversations/${id}`);
                if (state.currentConversationId === id) {
                    state.currentConversationId = null;
                    showWelcome();
                }
                await loadConversations();
            }
        });
    });
}

async function openConversation(id) {
    try {
        const data = await API.get(`/api/chat/conversations/${id}`);
        if (!data) return;
        state.currentConversationId = id;
        state.currentMessages = data.messages;
        state.systemPrompt = data.system_prompt || '';

        // Update provider/model
        if (data.provider) els.providerSelect.value = data.provider;
        await loadModels();
        if (data.model) els.modelSelect.value = data.model;

        renderMessages();
        renderConversations();
        els.sidebar.classList.remove('open');
    } catch (err) {
        console.error('Failed to open conversation:', err);
    }
}

function startNewChat() {
    state.currentConversationId = null;
    state.currentMessages = [];
    state.systemPrompt = '';
    showWelcome();
    renderConversations();
    els.chatInput.value = '';
    autoResizeTextarea();
    els.sendBtn.disabled = true;
    els.sidebar.classList.remove('open');
}


/* ============================================
   Messages
   ============================================ */
function showWelcome() {
    els.chatMessages.innerHTML = '';
    els.chatMessages.appendChild(els.welcomeScreen.cloneNode(true) || createWelcomeScreen());
    // Re-render welcome
    els.chatMessages.innerHTML = `
        <div class="welcome-screen">
            <div class="welcome-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <h2>NexusChat</h2>
            <p>Chat with local and cloud AI models</p>
            <div class="welcome-cards">
                <div class="welcome-card" data-prompt="Explain quantum computing in simple terms">
                    <span class="card-icon">🔬</span><span>Explain quantum computing</span>
                </div>
                <div class="welcome-card" data-prompt="Write a Python function to sort a list using merge sort">
                    <span class="card-icon">💻</span><span>Write merge sort in Python</span>
                </div>
                <div class="welcome-card" data-prompt="What are the key differences between REST and GraphQL?">
                    <span class="card-icon">🌐</span><span>REST vs GraphQL</span>
                </div>
                <div class="welcome-card" data-prompt="Help me write a creative short story about a time traveler">
                    <span class="card-icon">✍️</span><span>Creative writing help</span>
                </div>
            </div>
        </div>
    `;
}

function renderMessages() {
    els.chatMessages.innerHTML = '';
    for (const msg of state.currentMessages) {
        appendMessage(msg.role, msg.content, false);
    }
    if (state.currentMessages.length === 0) showWelcome();
    scrollToBottom();
}

function appendMessage(role, content, animate = true) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    if (!animate) div.style.animation = 'none';

    const avatar = role === 'user' ? 'U' : 'AI';
    const rendered = role === 'assistant' ? renderMarkdown(content) : `<p>${escapeHtml(content)}</p>`;

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    div.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            ${rendered}
            <div class="message-actions">
                <button onclick="copyMessageContent(this)">Copy</button>
            </div>
        </div>
    `;

    els.chatMessages.appendChild(div);
    scrollToBottom();
    return div;
}

function appendStreamingMessage() {
    const div = document.createElement('div');
    div.className = 'message assistant';
    div.id = 'streaming-message';
    div.innerHTML = `
        <div class="message-avatar">AI</div>
        <div class="message-content">
            <div class="typing-indicator"><span></span><span></span><span></span></div>
        </div>
    `;
    els.chatMessages.appendChild(div);
    scrollToBottom();
    return div;
}

function updateStreamingMessage(content) {
    const el = document.getElementById('streaming-message');
    if (el) {
        const contentEl = el.querySelector('.message-content');
        contentEl.innerHTML = renderMarkdown(content) + '<div class="message-actions"><button onclick="copyMessageContent(this)">Copy</button></div>';
        scrollToBottom();
    }
}

function finalizeStreamingMessage(content) {
    const el = document.getElementById('streaming-message');
    if (el) {
        el.removeAttribute('id');
        const contentEl = el.querySelector('.message-content');
        contentEl.innerHTML = renderMarkdown(content) + '<div class="message-actions"><button onclick="copyMessageContent(this)">Copy</button></div>';
    }
}

function copyMessageContent(btn) {
    const content = btn.closest('.message-content');
    const text = content.textContent.replace('Copy', '').trim();
    navigator.clipboard.writeText(text);
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = 'Copy', 2000);
}
window.copyMessageContent = copyMessageContent;


/* ============================================
   Send Message / Streaming
   ============================================ */
async function sendMessage() {
    const text = els.chatInput.value.trim();
    if (!text || state.isStreaming) return;

    // Hide welcome, show user message
    // Remove welcome screen on first message
    const welcome = els.chatMessages.querySelector('.welcome-screen');
    if (welcome) welcome.remove();

    appendMessage('user', text);
    state.currentMessages.push({ role: 'user', content: text });

    els.chatInput.value = '';
    autoResizeTextarea();
    els.sendBtn.disabled = true;

    const provider = els.providerSelect.value;
    const model = els.modelSelect.value;

    state.isStreaming = true;
    els.sendBtn.classList.add('hidden');
    els.stopBtn.classList.remove('hidden');

    const streamMsg = appendStreamingMessage();
    let fullContent = '';

    state.abortController = await API.stream(
        '/api/chat/send',
        '/api/chat/send',
        {
            conversation_id: state.currentConversationId,
            message: text,
            model: model,
            provider: provider,
            system_prompt: state.systemPrompt,
            stream: true,
        },
        // onChunk
        (chunk, data) => {
            fullContent += chunk;
            if (data.conversation_id && !state.currentConversationId) {
                state.currentConversationId = data.conversation_id;
            }
            updateStreamingMessage(fullContent);
        },
        // onDone - finalize streaming
        async (data) => {
            finalizeStreamingMessage(fullContent);
            state.currentMessages.push({ role: 'assistant', content: fullContent });
            if (data.conversation_id) {
                state.currentConversationId = data.conversation_id;
            }
            finishStreaming();
            await loadConversations();
        },
        // onError - handle stream failure
        (err) => {
            finalizeStreamingMessage(fullContent || `Error: ${err}`);
            finishStreaming();
        }
    );
}

function stopStreaming() {
    if (state.abortController) {
        state.abortController.abort();
    }
    finishStreaming();
}

function finishStreaming() {
    state.isStreaming = false;
    els.sendBtn.classList.remove('hidden');
    els.stopBtn.classList.add('hidden');
    els.sendBtn.disabled = !els.chatInput.value.trim();
}


/* ============================================
   Models
   ============================================ */
async function loadModels() {
    const provider = els.providerSelect.value;
    try {
        const data = await API.get('/api/models/available');
        if (!data) return;

        state.models = data.models;
        const filtered = data.models.filter(m => m.provider === provider);
        filtered.sort((a, b) => a.name.localeCompare(b.name));

        els.modelSelect.innerHTML = '';
        if (filtered.length === 0) {
            els.modelSelect.innerHTML = '<option value="">No models available</option>';
        } else {
            filtered.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.id;
                opt.textContent = m.name;
                els.modelSelect.appendChild(opt);
            });
        }
    } catch (err) {
        els.modelSelect.innerHTML = '<option value="">Failed to load models</option>';
    }
}


/* ============================================
   Settings
   ============================================ */
async function loadSettings() {
    try {
        const data = await API.get('/api/settings/');
        if (!data) return;

        $('#setting-ollama-url').value = data.ollama_base_url || 'http://localhost:11434';
        $('#setting-default-provider').value = data.default_provider || 'ollama';
        $('#setting-system-prompt').value = data.system_prompt || '';
        state.systemPrompt = data.system_prompt || '';

        // Theme
        if (data.theme) {
            document.documentElement.setAttribute('data-theme', data.theme);
        }

        // Set provider select
        els.providerSelect.value = data.default_provider || 'ollama';
        await loadModels();
    } catch (err) {
        console.error('Failed to load settings:', err);
    }
}

async function saveSettings() {
    try {
        await API.put('/api/settings/', {
            ollama_base_url: $('#setting-ollama-url').value,
            openai_api_key: $('#setting-openai-key').value || undefined,
            anthropic_api_key: $('#setting-anthropic-key').value || undefined,
            default_provider: $('#setting-default-provider').value,
            default_model: els.modelSelect.value,
            system_prompt: $('#setting-system-prompt').value,
            theme: $('#setting-theme').value,
        });

        // Apply theme
        const theme = $('#setting-theme').value;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('nexuschat_theme', theme);

        // Update provider
        els.providerSelect.value = $('#setting-default-provider').value;
        await loadModels();

        els.settingsModal.classList.add('hidden');

        // Show toast
        showToast('Settings saved');
    } catch (err) {
        showToast('Failed to save settings: ' + err.message, 'error');
    }
}


/* ============================================
   Utilities
   ============================================ */
function autoResizeTextarea() {
    const ta = els.chatInput;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 200) + 'px';
    // Prevent layout shift
    ta.style.overflowY = ta.scrollHeight > 200 ? 'auto' : 'hidden';
}

function scrollToBottom() {
    const container = $('#chat-container');
    requestAnimationFrame(() => {
        container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'success') {
    // Remove existing toasts
    document.querySelectorAll('.nexuschat-toast').forEach(t => t.remove());
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed; bottom: 20px; right: 20px; z-index: 9999;
        padding: 12px 20px; border-radius: 8px; font-size: 14px;
        color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: fadeIn 0.2s ease;
        background: ${type === 'error' ? 'var(--danger)' : 'var(--success)'};
    `;
    toast.textContent = message;
    toast.classList.add('nexuschat-toast');
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}


/* ============================================
   Boot
   ============================================ */
document.addEventListener('DOMContentLoaded', init);
