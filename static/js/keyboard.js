/* ============================================
   NexusChat — Keyboard Shortcuts
   ============================================ */

const Keyboard = {
    init() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Enter — Send message
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                const chatInput = document.getElementById('chat-input');
                if (chatInput && chatInput.value.trim()) {
                    sendMessage();
                }
            }

            // Ctrl+N — New chat
            if (e.ctrlKey && e.key === 'n') {
                e.preventDefault();
                startNewChat();
            }

            // Ctrl+B — Toggle sidebar
            if (e.ctrlKey && e.key === 'b') {
                e.preventDefault();
                toggleSidebar();
            }

            // Ctrl+Shift+S — Open settings
            if (e.ctrlKey && e.shiftKey && e.key === 'S') {
                e.preventDefault();
                document.getElementById('settings-modal')?.showModal();
            }

            // Escape — Close modals
            if (e.key === 'Escape') {
                document.getElementById('settings-modal')?.close();
                document.getElementById('system-prompt-modal')?.close();
            }

            // / — Focus input
            if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
                const active = document.activeElement;
                if (active.tagName !== 'INPUT' && active.tagName !== 'TEXTAREA' && active.tagName !== 'SELECT') {
                    e.preventDefault();
                    document.getElementById('chat-input')?.focus();
                }
            }
        });
    }
};
