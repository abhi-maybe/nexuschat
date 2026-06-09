/* ============================================
   NexusChat — Utility Functions
   ============================================ */

const Utils = {
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    debounce(fn, delay = 300) {
        let timer;
        return function (...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    },

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

    formatTime(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const now = new Date();
        const isToday = date.toDateString() === now.toDateString();
        const isThisYear = date.getFullYear() === now.getFullYear();

        if (isToday) return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        if (isThisYear) return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
        return date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    },

    randomId(length = 9) {
        return Math.random().toString(36).substring(2, 2 + length);
    },

    showToast(message, type = 'success', duration = 3000) {
        document.querySelectorAll('.nexuschat-toast').forEach((t) => t.remove());

        const toast = document.createElement('div');
        toast.className = `nexuschat-toast nexuschat-toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        requestAnimationFrame(() => {
            requestAnimationFrame(() => toast.classList.add('show'));
        });

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 350);
        }, duration);
    },

    async copyToClipboard(text, btnEl) {
        try {
            await navigator.clipboard.writeText(text);
        } catch {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.cssText = 'position:fixed;opacity:0';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
        }
        if (btnEl) {
            const orig = btnEl.textContent;
            btnEl.textContent = 'Copied!';
            setTimeout(() => (btnEl.textContent = orig), 2000);
        }
        return true;
    },

    autoResize(textarea, maxH = 200) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, maxH) + 'px';
        textarea.style.overflowY = textarea.scrollHeight > maxH ? 'auto' : 'hidden';
    },

    scrollToBottom(el) {
        if (!el) return;
        requestAnimationFrame(() => {
            el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
        });
    },
};

window.Utils = Utils;

// Backward-compat global helpers
function escapeHtml(text) { return Utils.escapeHtml(text); }
function showToast(message, type, duration) { return Utils.showToast(message, type, duration); }

function copyCode(id) {
    const el = document.getElementById(id);
    if (el) {
        const btn = el.closest('pre')?.querySelector('.code-header button');
        Utils.copyToClipboard(el.textContent, btn);
    }
}
window.copyCode = copyCode;
