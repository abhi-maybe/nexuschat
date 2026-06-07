/* ============================================
   NexusChat — Utility Functions
   ============================================ */

const Utils = {
    /**
     * Escape HTML special characters to prevent XSS.
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Debounce a function call by `delay` ms.
     */
    debounce(fn, delay = 300) {
        let timer;
        return function (...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    },

    /**
     * Throttle a function to at most once every `limit` ms.
     */
    throttle(fn, limit = 100) {
        let inThrottle = false;
        return function (...args) {
            if (!inThrottle) {
                fn.apply(this, args);
                inThrottle = true;
                setTimeout(() => (inThrottle = false), limit);
            }
        };
    },

    /**
     * Format a date/time string for display.
     * - Today: "2:30 PM"
     * - This year: "Mar 15"
     * - Other: "Mar 15, 2024"
     */
    formatTime(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const now = new Date();
        const isToday = date.toDateString() === now.toDateString();
        const isThisYear = date.getFullYear() === now.getFullYear();

        if (isToday) {
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        if (isThisYear) {
            return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
        }
        return date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    },

    /**
     * Generate a random ID string.
     */
    randomId(length = 9) {
        return Math.random().toString(36).substring(2, 2 + length);
    },

    /**
     * Show a toast notification.
     */
    showToast(message, type = 'success', duration = 3000) {
        // Remove existing toasts
        document.querySelectorAll('.nexuschat-toast').forEach((t) => t.remove());

        const toast = document.createElement('div');
        toast.className = `nexuschat-toast nexuschat-toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // Trigger animation
        requestAnimationFrame(() => toast.classList.add('show'));

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    /**
     * Simple markdown-safe link detection (used for linkifying plain text).
     */
    linkify(text) {
        if (!text) return '';
        const urlPattern = /(https?:\/\/[^\s<]+)/g;
        return text.replace(urlPattern, '<a href="$1" target="_blank" rel="noopener">$1</a>');
    },

    /**
     * Copy text to clipboard and optionally update a button.
     */
    async copyToClipboard(text, btnEl) {
        try {
            await navigator.clipboard.writeText(text);
            if (btnEl) {
                const orig = btnEl.textContent;
                btnEl.textContent = 'Copied!';
                setTimeout(() => (btnEl.textContent = orig), 2000);
            }
            return true;
        } catch {
            // Fallback
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.cssText = 'position:fixed;opacity:0';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            if (btnEl) {
                const orig = btnEl.textContent;
                btnEl.textContent = 'Copied!';
                setTimeout(() => (btnEl.textContent = orig), 2000);
            }
            return true;
        }
    },

    /**
     * Auto-resize a textarea to fit its content.
     */
    autoResize(textarea, maxH = 200) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, maxH) + 'px';
        textarea.style.overflowY = textarea.scrollHeight > maxH ? 'auto' : 'hidden';
    },

    /**
     * Smooth scroll an element to bottom.
     */
    scrollToBottom(el) {
        if (!el) return;
        requestAnimationFrame(() => {
            el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
        });
    },
};

// Make Utils globally available
window.Utils = Utils;

// Backward-compat global helpers
function escapeHtml(text) {
    return Utils.escapeHtml(text);
}

function showToast(message, type, duration) {
    return Utils.showToast(message, type, duration);
}

function copyCode(id) {
    const el = document.getElementById(id);
    if (el) {
        const btn = el.closest('pre')?.querySelector('.code-header button');
        Utils.copyToClipboard(el.textContent, btn);
    }
}
window.copyCode = copyCode;
