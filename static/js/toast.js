// ===============================
// TOAST NOTIFICATION SYSTEM
// ===============================

function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const icons = {
        success: 'bi-check-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        danger:  'bi-x-circle-fill',
        info:    'bi-info-circle-fill'
    };

    const colors = {
        success: { bg: '#ecfdf5', border: '#059669', text: '#065f46', icon: '#059669' },
        warning: { bg: '#fffbeb', border: '#d97706', text: '#92400e', icon: '#d97706' },
        danger:  { bg: '#fff1f2', border: '#e11d48', text: '#9f1239', icon: '#e11d48' },
        info:    { bg: '#e0f2fe', border: '#0284c7', text: '#0369a1', icon: '#0284c7' }
    };

    const c = colors[type] || colors.info;
    const iconClass = icons[type] || icons.info;
    const id = 'toast-' + Date.now();

    const toastHtml = `
        <div id="${id}" class="toast align-items-center border-0 shadow-lg mb-2" role="alert"
             style="background: ${c.bg}; border-left: 4px solid ${c.border} !important;
                    min-width: 320px; max-width: 420px; border-radius: 12px;
                    backdrop-filter: blur(10px); animation: slideInRight 0.35s ease-out;"
             data-bs-autohide="true" data-bs-delay="${duration}">
            <div class="d-flex align-items-center px-3 py-2.5">
                <i class="bi ${iconClass} me-2 fs-5" style="color: ${c.icon};"></i>
                <div class="toast-body fw-semibold" style="color: ${c.text}; font-size: 0.9rem;">
                    ${message}
                </div>
                <button type="button" class="btn-close ms-auto" data-bs-dismiss="toast"
                        style="font-size: 0.65rem; filter: opacity(0.5);"></button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHtml);
    const toastEl = document.getElementById(id);
    const toast = new bootstrap.Toast(toastEl);
    toast.show();

    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

function showConfirm(message, onConfirm) {
    const container = document.getElementById('toastContainer');
    if (!container) { if (confirm(message)) onConfirm(); return; }

    const id = 'confirm-' + Date.now();
    const confirmHtml = `
        <div id="${id}" class="toast align-items-center border-0 shadow-lg mb-2" role="alert"
             style="background: #fffbeb; border-left: 4px solid #f59e0b !important;
                    min-width: 340px; max-width: 440px; border-radius: 12px;
                    backdrop-filter: blur(10px); animation: slideInRight 0.35s ease-out;"
             data-bs-autohide="false">
            <div class="px-3 py-3">
                <div class="d-flex align-items-center mb-2">
                    <i class="bi bi-exclamation-triangle-fill me-2 fs-5" style="color: #f59e0b;"></i>
                    <span class="fw-bold" style="color: #92400e; font-size: 0.95rem;">Confirmation</span>
                    <button type="button" class="btn-close ms-auto" data-bs-dismiss="toast"
                            style="font-size: 0.65rem; filter: opacity(0.5);"></button>
                </div>
                <div class="mb-3" style="color: #78350f; font-size: 0.88rem;">${message}</div>
                <div class="d-flex gap-2 justify-content-end">
                    <button class="btn btn-sm px-3 py-1 rounded-pill fw-semibold"
                            style="background: #f3f4f6; color: #374151; border: 1px solid #d1d5db;"
                            data-bs-dismiss="toast">Cancel</button>
                    <button class="btn btn-sm px-3 py-1 rounded-pill fw-semibold"
                            style="background: #ef4444; color: white; border: none;"
                            id="${id}-confirm">Stop Process</button>
                </div>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', confirmHtml);
    const toastEl = document.getElementById(id);
    const toast = new bootstrap.Toast(toastEl);
    toast.show();

    document.getElementById(`${id}-confirm`).addEventListener('click', () => {
        toast.hide();
        onConfirm();
    });

    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}
