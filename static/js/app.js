/* ============================================
   NexusChat — Main Application
   ============================================ */

/* ============ API Client ============ */
const API = {
    token: localStorage.getItem('nexuschat_token'),

    headers() {
        return {
            'Content-Type': 'application/json',
            ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
        };
    },

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
        if (!resp.ok) {
            const data = await resp.json().catch(() => ({}));
            throw new Error(data.detail || `PUT ${url}: ${resp.status}`);
        }
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

    async stream(endpoint, body, onChunk, onError, onDone) {
        const controller = new AbortController();
        try {
            const resp = await fetch(endpoint, {
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
                    const trimmed = line.trim();
                    if (!trimmed || !trimmed.startsWith('data:')) continue;

                    const dataStr = trimmed.slice(5).trim();
                    if (dataStr === '[DONE]') { onDone({}); return controller; }

                    try {
                        const data = JSON.parse(dataStr);
                        if (data.error) {
                            onError(data.error);
                        } else if (data.done || data.finish_reason) {
                            onDone(data);
                        } else if (data.token !== undefined) {
                            onChunk(data.token, data);
                        } else if (data.content !== undefined) {
                            onChunk(data.content, data);
                        }
                    } catch (e) { /* skip malformed JSON */ }
                }
            }
        } catch (err) {
            if (err.name !== 'AbortError') onError(err.message);
        }
        return controller;
    },
};


/* ============ Markdown Renderer ============ */
function setupMarkdown() {
    if (typeof marked === 'undefined') return;

    const renderer = new marked.Renderer();

    renderer.code = function (code, language) {
        const codeText = typeof code === 'object' ? code.text : code;
        const lang = typeof code === 'object' ? code.lang : language;
        const validLang = lang && typeof hljs !== 'undefined' && hljs.getLanguage(lang) ? lang : 'plaintext';
        let highlighted;
        try {
            highlighted = hljs.highlight(codeText, { language: validLang }).value;
        } catch {
            highlighted = Utils.escapeHtml(codeText);
        }
        const id = 'code-' + Utils.randomId();
        return `<pre><div class="code-header"><span>${validLang}</span><button onclick="copyCode('${id}')">Copy</button></div><code id="${id}" class="hljs language-${validLang}">${highlighted}</code></pre>`;
    };

    marked.setOptions({ renderer, breaks: true, gfm: true });
}

function renderMarkdown(text) {
    if (!text) return '';
    try { return marked.parse(text); }
    catch { return Utils.escapeHtml(text); }
}


/* ============ App State ============ */
const state = {
    conversations: [],
    currentConversationId: null,
    currentMessages: [],
    isStreaming: false,
    abortController: null,
    systemPrompt: '',
    allModels: [],
    settings: {},
};


/* ============ DOM Elements ============ */
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const els = {
    sidebar: null,
    sidebarOverlay: null,
    sidebarToggle: null,
    conversationsList: null,
    newChatBtn: null,
    settingsBtn: null,
    settingsModal: null,
    closeSettings: null,
    saveSettings: null,

    providerSelect: null,
    modelSelect: null,
    systemPromptBtn: null,
    systemPromptModal: null,
    systemPromptInput: null,
    saveSystemPrompt: null,

    chatContainer: null,
    chatMessages: null,
    chatInput: null,
    charCount: null,
    sendBtn: null,
    stopBtn: null,

    themeToggle: null,
};

function cacheDom() {
    els.sidebar = $('#sidebar');
    els.sidebarOverlay = $('#sidebar-overlay');
    els.sidebarToggle = $('#sidebar-toggle');
    els.conversationsList = $('#conversations-list');
    els.newChatBtn = $('#new-chat-btn');
    els.settingsBtn = $('#settings-btn');
    els.settingsModal = $('#settings-modal');
    els.closeSettings = $('#close-settings');
    els.saveSettings = $('#save-settings');

    els.providerSelect = $('#provider-select');
    els.modelSelect = $('#model-select');
    els.systemPromptBtn = $('#system-prompt-btn');
    els.systemPromptModal = $('#system-prompt-modal');
    els.systemPromptInput = $('#system-prompt-input');
    els.saveSystemPrompt = $('#save-system-prompt');

    els.chatContainer = $('#chat-container');
    els.chatMessages = $('#chat-messages');
    els.chatInput = $('#chat-input');
    els.charCount = $('#char-count');
    els.sendBtn = $('#send-btn');
    els.stopBtn = $('#stop-btn');

    els.themeToggle = $('#theme-toggle');
}


/* ============ Initialization ============ */
async function init() {
    if (!API.token) {
        window.location.href = '/login';
        return;
    }

    cacheDom();
    setupMarkdown();

    try {
        await API.get('/api/auth/me');
    } catch {
        API.logout();
        return;
    }

    setupEventListeners();
    Keyboard.init();
    applyTheme();
    initBackground();

    await Promise.all([loadConversations(), loadModels(), loadSettings()]);

    const username = localStorage.getItem('nexuschat_username');
    const userEl = $('#user-name');
    if (userEl && username) {
        userEl.textContent = username;
        const avatarEl = $('#user-avatar');
        if (avatarEl) avatarEl.textContent = username.charAt(0).toUpperCase();
    }
}

function setupEventListeners() {
    // Sidebar
    els.sidebarToggle?.addEventListener('click', toggleSidebar);
    els.sidebarOverlay?.addEventListener('click', closeSidebar);
    els.newChatBtn?.addEventListener('click', startNewChat);

    // Chat input
    els.chatInput?.addEventListener('input', onInputChange);
    els.chatInput?.addEventListener('keydown', onInputKeydown);
    els.sendBtn?.addEventListener('click', sendMessage);
    els.stopBtn?.addEventListener('click', stopStreaming);

    // Provider change
    els.providerSelect?.addEventListener('change', () => loadModels());

    // Settings
    els.settingsBtn?.addEventListener('click', openSettings);
    els.closeSettings?.addEventListener('click', closeSettings);
    els.saveSettings?.addEventListener('click', saveSettingsHandler);

    // Logout
    document.getElementById('logout-btn')?.addEventListener('click', () => API.logout());

    // Theme menu (delegated)
    document.getElementById('theme-menu')?.addEventListener('click', (e) => {
        const item = e.target.closest('[data-theme-val]');
        if (item) setTheme(item.getAttribute('data-theme-val'));
    });

    // System prompt
    els.systemPromptBtn?.addEventListener('click', () => {
        els.systemPromptInput.value = state.systemPrompt;
        document.getElementById('system-prompt-modal')?.showModal();
    });
    els.saveSystemPrompt?.addEventListener('click', () => {
        state.systemPrompt = els.systemPromptInput.value;
        document.getElementById('system-prompt-modal')?.close();
        showToast('System prompt updated', 'success');
    });

    // Welcome cards (delegated)
    document.addEventListener('click', (e) => {
        const card = e.target.closest('.welcome-card');
        if (card && card.dataset.prompt) {
            els.chatInput.value = card.dataset.prompt;
            Utils.autoResize(els.chatInput);
            sendMessage();
        }
    });

    // Temperature slider
    const tempSlider = $('#setting-temperature');
    const tempValue = $('#temperature-value');
    if (tempSlider && tempValue) {
        tempSlider.addEventListener('input', () => {
            tempValue.textContent = parseFloat(tempSlider.value).toFixed(1);
        });
    }

    // Background grid (single delegated listener)
    setupBgGridListeners();
}


/* ============ Sidebar ============ */
function toggleSidebar() {
    const isOpen = els.sidebar?.classList.toggle('open');
    if (els.sidebarOverlay) {
        els.sidebarOverlay.style.display = isOpen ? 'block' : 'none';
    }
}

function closeSidebar() {
    els.sidebar?.classList.remove('open');
    if (els.sidebarOverlay) {
        els.sidebarOverlay.style.display = 'none';
    }
}


/* ============ Theme ============ */
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('nexuschat_theme', theme);
    API.put('/api/settings/', { theme: theme }).catch(() => {});
}
window.setTheme = setTheme;

function applyTheme() {
    const saved = localStorage.getItem('nexuschat_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
}


/* ============ Conversations ============ */
async function loadConversations() {
    try {
        const data = await API.get('/api/chat/conversations');
        if (!data) return;
        state.conversations = Array.isArray(data) ? data : (data.conversations || []);
        renderConversations();
    } catch (err) {
        console.error('Failed to load conversations:', err);
    }
}

function renderConversations() {
    if (!els.conversationsList) return;

    if (state.conversations.length === 0) {
        els.conversationsList.innerHTML = '<div class="conv-empty">No conversations yet</div>';
        return;
    }

    els.conversationsList.innerHTML = state.conversations
        .map((c) => `
        <div class="conv-item ${c.id === state.currentConversationId ? 'active' : ''}" data-id="${c.id}">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <span class="conv-title">${escapeHtml(c.title)}</span>
            <button class="conv-delete" data-id="${c.id}" title="Delete">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
            </button>
        </div>`)
        .join('');

    // Delegated click handler for conversation items
    els.conversationsList.onclick = (e) => {
        const deleteBtn = e.target.closest('.conv-delete');
        if (deleteBtn) {
            e.stopPropagation();
            handleDeleteConversation(parseInt(deleteBtn.dataset.id));
            return;
        }
        const convItem = e.target.closest('.conv-item');
        if (convItem) openConversation(parseInt(convItem.dataset.id));
    };
}

async function handleDeleteConversation(id) {
    if (!confirm('Delete this conversation? This cannot be undone.')) return;
    await API.del(`/api/chat/conversations/${id}`);
    if (state.currentConversationId === id) {
        state.currentConversationId = null;
        showWelcome();
    }
    await loadConversations();
}

async function openConversation(id) {
    try {
        const data = await API.get(`/api/chat/conversations/${id}`);
        if (!data) return;

        state.currentConversationId = id;
        state.currentMessages = data.messages || [];
        state.systemPrompt = data.system_prompt || '';

        if (data.provider && els.providerSelect) {
            els.providerSelect.value = data.provider;
            await loadModels();
        }
        if (data.model && els.modelSelect) {
            els.modelSelect.value = data.model;
        }

        renderMessages();
        renderConversations();
        closeSidebar();
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
    Utils.autoResize(els.chatInput);
    els.sendBtn.disabled = true;
    updateCharCount();
    closeSidebar();
    els.chatInput.focus();
}


/* ============ Messages ============ */
function showWelcome() {
    if (!els.chatMessages) return;
    els.chatMessages.innerHTML = `
        <div class="welcome-screen">
            <div class="welcome-icon">
                <svg width="48" height="48" viewBox="0 0 32 32" fill="none">
                    <g stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
                        <ellipse cx="16" cy="16" rx="11" ry="4.5"/>
                        <ellipse cx="16" cy="16" rx="11" ry="4.5" transform="rotate(60 16 16)"/>
                        <ellipse cx="16" cy="16" rx="11" ry="4.5" transform="rotate(120 16 16)"/>
                        <circle cx="16" cy="16" r="2.5" fill="currentColor"/>
                    </g>
                </svg>
            </div>
            <h2>NexusChat</h2>
            <p>Chat with local and cloud AI models</p>
            <div class="welcome-cards">
                <div class="welcome-card" data-prompt="Explain quantum computing in simple terms">
                    <span class="card-icon">🔬</span>
                    <span>Explain quantum computing</span>
                </div>
                <div class="welcome-card" data-prompt="Write a Python function to sort a list using merge sort">
                    <span class="card-icon">💻</span>
                    <span>Write merge sort in Python</span>
                </div>
                <div class="welcome-card" data-prompt="What are the key differences between REST and GraphQL?">
                    <span class="card-icon">🌐</span>
                    <span>REST vs GraphQL</span>
                </div>
                <div class="welcome-card" data-prompt="Help me write a creative short story about a time traveler">
                    <span class="card-icon">✍️</span>
                    <span>Creative writing help</span>
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

    const avatarText = role === 'user' ? 'U' : 'AI';
    const rendered = role === 'assistant' ? renderMarkdown(content) : `<p>${escapeHtml(content)}</p>`;

    div.innerHTML = `
        <div class="message-avatar">${avatarText}</div>
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

// Throttled streaming update using requestAnimationFrame
let _streamUpdatePending = false;
let _streamContentBuffer = '';

function updateStreamingMessage(content) {
    _streamContentBuffer = content;
    if (_streamUpdatePending) return;
    _streamUpdatePending = true;

    requestAnimationFrame(() => {
        _streamUpdatePending = false;
        const el = document.getElementById('streaming-message');
        if (!el) return;
        const contentEl = el.querySelector('.message-content');
        contentEl.innerHTML =
            renderMarkdown(_streamContentBuffer) +
            '<div class="message-actions"><button onclick="copyMessageContent(this)">Copy</button></div>';
        scrollToBottom();
    });
}

function finalizeStreamingMessage(content) {
    const el = document.getElementById('streaming-message');
    if (!el) return;
    el.removeAttribute('id');
    const contentEl = el.querySelector('.message-content');
    contentEl.innerHTML =
        renderMarkdown(content) +
        '<div class="message-actions"><button onclick="copyMessageContent(this)">Copy</button></div>';
}

function copyMessageContent(btn) {
    const content = btn.closest('.message-content');
    const text = content.textContent.replace('Copy', '').replace('Copied!', '').trim();
    Utils.copyToClipboard(text, btn);
}
window.copyMessageContent = copyMessageContent;


/* ============ Send Message / Streaming ============ */
async function sendMessage() {
    const text = els.chatInput.value.trim();
    if (!text || state.isStreaming) return;

    const welcome = els.chatMessages.querySelector('.welcome-screen');
    if (welcome) welcome.remove();

    appendMessage('user', text);
    state.currentMessages.push({ role: 'user', content: text });

    els.chatInput.value = '';
    Utils.autoResize(els.chatInput);
    els.sendBtn.disabled = true;
    updateCharCount();

    const provider = els.providerSelect?.value || 'ollama';
    const model = els.modelSelect?.value || '';

    state.isStreaming = true;
    els.sendBtn.classList.add('hidden');
    els.stopBtn.classList.remove('hidden');

    appendStreamingMessage();
    let fullContent = '';

    state.abortController = await API.stream(
        '/api/chat/send',
        {
            conversation_id: state.currentConversationId,
            message: text,
            model: model,
            provider: provider,
            system_prompt: state.systemPrompt,
            stream: true,
        },
        (chunk, data) => {
            fullContent += chunk;
            if (data.conversation_id && !state.currentConversationId) {
                state.currentConversationId = data.conversation_id;
            }
            updateStreamingMessage(fullContent);
        },
        (err) => {
            finalizeStreamingMessage(fullContent || `Error: ${err}`);
            finishStreaming();
            showToast(err, 'error');
        },
        async (data) => {
            finalizeStreamingMessage(fullContent);
            state.currentMessages.push({ role: 'assistant', content: fullContent });
            if (data.conversation_id) {
                state.currentConversationId = data.conversation_id;
            }
            finishStreaming();
            await loadConversations();
        }
    );
}

function stopStreaming() {
    if (state.abortController) state.abortController.abort();
    finishStreaming();
}

function finishStreaming() {
    state.isStreaming = false;
    els.sendBtn.classList.remove('hidden');
    els.stopBtn.classList.add('hidden');
    els.sendBtn.disabled = !els.chatInput.value.trim();
}


/* ============ Input Handlers ============ */
function onInputChange() {
    Utils.autoResize(els.chatInput);
    els.sendBtn.disabled = !els.chatInput.value.trim() || state.isStreaming;
    updateCharCount();
}

function onInputKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
        e.preventDefault();
        sendMessage();
    }
}

function updateCharCount() {
    if (!els.charCount) return;
    const len = els.chatInput.value.length;
    if (len > 100) {
        els.charCount.textContent = len.toLocaleString();
        els.charCount.classList.add('visible');
    } else {
        els.charCount.classList.remove('visible');
    }
}


/* ============ Models ============ */
async function loadModels() {
    const provider = els.providerSelect?.value;
    if (!els.modelSelect) return;

    try {
        const data = await API.get('/api/models/available');
        if (!data) return;

        const allModels = data.models || [];
        state.allModels = allModels;

        const models = allModels.filter(m => m.provider === provider);

        els.modelSelect.innerHTML = '';
        if (models.length === 0) {
            els.modelSelect.innerHTML = '<option value="">No models available</option>';
        } else {
            for (const m of models) {
                const opt = document.createElement('option');
                opt.value = m.id;
                opt.textContent = m.name || m.id;
                els.modelSelect.appendChild(opt);
            }
        }
    } catch {
        els.modelSelect.innerHTML = '<option value="">Failed to load models</option>';
    }
}


/* ============ Settings ============ */
function openSettings() {
    document.getElementById('settings-modal')?.showModal();
}

function closeSettings() {
    document.getElementById('settings-modal')?.close();
}

async function loadSettings() {
    try {
        const data = await API.get('/api/settings/');
        if (!data) return;
        state.settings = data;

        const ollamaUrl = $('#setting-ollama-url');
        const defaultProvider = $('#setting-default-provider');
        const systemPrompt = $('#setting-system-prompt');
        const theme = $('#setting-theme');
        const temperature = $('#setting-temperature');
        const tempVal = $('#temperature-value');

        if (ollamaUrl) ollamaUrl.value = data.ollama_base_url || 'http://localhost:11434';
        if (defaultProvider) defaultProvider.value = data.default_provider || 'ollama';
        if (systemPrompt) systemPrompt.value = data.system_prompt || '';
        if (theme) theme.value = data.theme || 'dark';
        if (temperature) {
            temperature.value = data.temperature || 0.7;
            if (tempVal) tempVal.textContent = parseFloat(temperature.value).toFixed(1);
        }

        // Show placeholder for configured keys
        const keyFields = {
            'setting-openai-key': data.openai_api_key,
            'setting-anthropic-key': data.anthropic_api_key,
            'setting-deepseek-key': data.deepseek_api_key,
            'setting-groq-key': data.groq_api_key,
            'setting-xiaomi-key': data.xiaomi_api_key,
            'setting-openrouter-key': data.openrouter_api_key,
        };
        for (const [id, hasKey] of Object.entries(keyFields)) {
            const el = document.getElementById(id);
            if (el && hasKey) el.placeholder = '•••••••• (configured)';
        }

        state.systemPrompt = data.system_prompt || '';

        if (data.theme) {
            document.documentElement.setAttribute('data-theme', data.theme);
            localStorage.setItem('nexuschat_theme', data.theme);
        }

        if (els.providerSelect) {
            els.providerSelect.value = data.default_provider || 'ollama';
            await loadModels();
        }
    } catch (err) {
        console.error('Failed to load settings:', err);
    }
}

async function saveSettingsHandler() {
    try {
        const payload = {
            ollama_base_url: $('#setting-ollama-url')?.value,
            openai_api_key: $('#setting-openai-key')?.value || undefined,
            anthropic_api_key: $('#setting-anthropic-key')?.value || undefined,
            deepseek_api_key: $('#setting-deepseek-key')?.value || undefined,
            groq_api_key: $('#setting-groq-key')?.value || undefined,
            xiaomi_api_key: $('#setting-xiaomi-key')?.value || undefined,
            openrouter_api_key: $('#setting-openrouter-key')?.value || undefined,
            default_provider: $('#setting-default-provider')?.value,
            default_model: els.modelSelect?.value,
            system_prompt: $('#setting-system-prompt')?.value,
            theme: $('#setting-theme')?.value,
        };

        await API.put('/api/settings/', payload);

        const newTheme = payload.theme || 'dark';
        setTheme(newTheme);

        const activeBg = document.querySelector('#bg-grid .bg-option.active');
        const bgValue = activeBg?.dataset.value || 'none';
        localStorage.setItem('nexuschat_bg', bgValue);

        if (bgValue === 'custom') {
            localStorage.setItem('nexuschat_bg_custom_url', $('#setting-custom-bg-url')?.value || '');
            localStorage.setItem('nexuschat_bg_custom_opacity', parseInt($('#setting-custom-bg-opacity')?.value || '15', 10).toString());
        }

        if (els.providerSelect) {
            els.providerSelect.value = payload.default_provider;
            await loadModels();
        }

        state.systemPrompt = payload.system_prompt || '';

        closeSettings();
        showToast('Settings saved');
    } catch (err) {
        showToast('Failed to save settings: ' + err.message, 'error');
    }
}


/* ============ Background Preset ============ */
function applyBackground(bgName) {
    if (!bgName || bgName === 'none') {
        document.documentElement.removeAttribute('data-bg');
    } else {
        document.documentElement.setAttribute('data-bg', bgName);
    }
}

function applyCustomBgVars(url, opacity) {
    if (url) document.documentElement.style.setProperty('--custom-bg-url', `url("${url}")`);
    document.documentElement.style.setProperty('--custom-bg-opacity', (opacity || 15) / 100);
}

function initBackground() {
    const saved = localStorage.getItem('nexuschat_bg') || 'none';
    const customUrl = localStorage.getItem('nexuschat_bg_custom_url') || '';
    const customOpacity = parseInt(localStorage.getItem('nexuschat_bg_custom_opacity') || '15', 10);

    applyBackground(saved);
    if (saved === 'custom' && customUrl) applyCustomBgVars(customUrl, customOpacity);

    const grid = document.getElementById('bg-grid');
    if (grid) {
        grid.querySelectorAll('.bg-option').forEach(opt => {
            opt.classList.toggle('active', opt.dataset.value === saved);
        });
    }

    const customFields = document.getElementById('custom-bg-fields');
    if (customFields) customFields.classList.toggle('visible', saved === 'custom');

    const urlInput = document.getElementById('setting-custom-bg-url');
    if (urlInput) urlInput.value = customUrl;

    const opacitySlider = document.getElementById('setting-custom-bg-opacity');
    const opacityVal = document.getElementById('custom-bg-opacity-value');
    if (opacitySlider) opacitySlider.value = customOpacity;
    if (opacityVal) opacityVal.textContent = customOpacity + '%';
}

function setupBgGridListeners() {
    const grid = document.getElementById('bg-grid');
    if (!grid) return;

    // Single delegated listener
    grid.addEventListener('click', (e) => {
        const option = e.target.closest('.bg-option');
        if (!option) return;

        grid.querySelectorAll('.bg-option').forEach(o => o.classList.remove('active'));
        option.classList.add('active');

        const value = option.dataset.value;
        applyBackground(value);

        const customFields = document.getElementById('custom-bg-fields');
        if (customFields) customFields.classList.toggle('visible', value === 'custom');

        if (value === 'custom') {
            const url = document.getElementById('setting-custom-bg-url')?.value;
            const opacity = parseInt(document.getElementById('setting-custom-bg-opacity')?.value || '15', 10);
            if (url) applyCustomBgVars(url, opacity);
        }
    });

    // Custom URL live preview
    const urlInput = document.getElementById('setting-custom-bg-url');
    if (urlInput) {
        urlInput.addEventListener('input', () => {
            const opacity = parseInt(document.getElementById('setting-custom-bg-opacity')?.value || '15', 10);
            applyCustomBgVars(urlInput.value, opacity);
        });
    }

    // Opacity slider
    const opacitySlider = document.getElementById('setting-custom-bg-opacity');
    const opacityVal = document.getElementById('custom-bg-opacity-value');
    if (opacitySlider) {
        opacitySlider.addEventListener('input', () => {
            const v = opacitySlider.value;
            if (opacityVal) opacityVal.textContent = v + '%';
            const url = document.getElementById('setting-custom-bg-url')?.value;
            if (url) applyCustomBgVars(url, parseInt(v, 10));
        });
    }
}


/* ============ Utilities ============ */
function scrollToBottom() {
    Utils.scrollToBottom(els.chatContainer);
}


/* ============ Boot ============ */
document.addEventListener('DOMContentLoaded', init);
