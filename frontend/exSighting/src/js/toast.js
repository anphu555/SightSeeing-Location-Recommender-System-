export const ToastManager = {
    getContainer() {
        return document.getElementById('toast-container');
    },

    show(message, type = 'info', duration = 4000) {
        const container = this.getContainer();
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.setAttribute('role', 'status');
        
        const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
        
        const iconSpan = document.createElement('span');
        iconSpan.className = 'toast-icon';
        iconSpan.textContent = icons[type] || icons.info;
        
        const messageSpan = document.createElement('span');
        messageSpan.className = 'toast-message';
        messageSpan.textContent = message;
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'toast-close';
        closeBtn.innerHTML = '×';
        closeBtn.onclick = () => this.remove(toast);
        
        toast.append(iconSpan, messageSpan, closeBtn);
        container.appendChild(toast);
        
        toast._timeoutId = setTimeout(() => this.remove(toast), duration);
    },

    remove(toast) {
        if (!toast.parentElement) return;
        if (toast._timeoutId) clearTimeout(toast._timeoutId);
        
        toast.style.animation = 'fadeOut 0.3s ease-out forwards';
        setTimeout(() => toast.remove(), 300);
    }
};