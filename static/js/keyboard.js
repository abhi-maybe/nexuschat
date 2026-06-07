/* ============================================
   NexusChat — Keyboard Shortcuts
   ============================================ */

const Keyboard = {
    /**
     * Initialize keyboard shortcuts.
     * Call after DOM is ready.
     */
    init() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Enter — send message
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                if (typeof sendMessage === 'function') {
                    sendMessage();
                }
            }

            // Ctrl/Cmd + N — new chat
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                if (typeof startNewChat === 'function') {
                    startNewChat();
                }
            }

            // Ctrl/Cmd + B — toggle sidebar
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                const sidebar = document.getElementById('sidebar');
                if (sidebar) {
                    sidebar.classList.toggle('open');
                }
            }

            // Ctrl/Cmd + Shift + S — open settings
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'S') {
                e.preventDefault();
                const settingsModal = document.getElementById('settings-modal');
                if (settingsModal) {
                    settingsModal.classList.toggle('hidden');
                }
            }

            // Escape — close modals
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal:not(.hidden)').forEach((m) => {
                    m.classList.add('hidden');
                });
            }

            // / — focus chat input (when not already in an input)
            if (e.key === '/' && !this.isInputFocused()) {
                e.preventDefault();
                const chatInput = document.getElementById('chat-input');
                if (chatInput) chatInput.focus();
            }
        });
    },

    /**
     * Check if the currently focused element is an input/textarea/select.
     */
    isInputFocused() {
        const tag = document.activeElement?.tagName?.toLowerCase();
        return tag === 'input' || tag === 'textarea' || tag === 'select';
    },
};

// Make globally available
window.Keyboard = Keyboard;
