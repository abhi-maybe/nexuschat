/* ============================================
   NexusChat — Keyboard Shortcuts
   ============================================ */

const Keyboard = {
    init() {
        document.addEventListener('keydown', (e) => {
            // Don't handle shortcuts when in input fields (except Escape)
            const isInput = this.isInputFocused();

            // Ctrl/Cmd + Enter — send message
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                if (typeof sendMessage === 'function') sendMessage();
                return;
            }

            // Ctrl/Cmd + N — new chat
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                if (typeof startNewChat === 'function') startNewChat();
                return;
            }

            // Ctrl/Cmd + B — toggle sidebar
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                if (typeof toggleSidebar === 'function') toggleSidebar();
                return;
            }

            // Ctrl/Cmd + Shift + S — open settings
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'S') {
                e.preventDefault();
                const settingsModal = document.getElementById('settings-modal');
                if (settingsModal) settingsModal.classList.toggle('hidden');
                return;
            }

            // Escape — close modals
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal:not(.hidden)').forEach((m) => {
                    m.classList.add('hidden');
                });
                return;
            }

            // / — focus chat input (when not in an input)
            if (e.key === '/' && !isInput) {
                e.preventDefault();
                const chatInput = document.getElementById('chat-input');
                if (chatInput) chatInput.focus();
            }
        });
    },

    isInputFocused() {
        const tag = document.activeElement?.tagName?.toLowerCase();
        return tag === 'input' || tag === 'textarea' || tag === 'select';
    },
};

window.Keyboard = Keyboard;
