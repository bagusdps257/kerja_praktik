/**
 * ==============================================================================
 * ENTERPRISE APP UX & INTERACTIVITY
 * ==============================================================================
 * 1. Global Keyboard Shortcuts (Ctrl + K / /)
 * 2. 1-Click Copy to Clipboard with Modern Icon Feedback
 * 3. Real-Time Folder Path Validator
 * 4. In-App Quick PDF Viewer Modal
 * 5. Global HTML Sanitizer Utility (escapeHtml)
 */

// 0. GLOBAL HTML ESCAPER UTILITY
window.escapeHtml = function(text) {
    if (text === null || text === undefined) return '';
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
};

// 1. GLOBAL KEYBOARD SHORTCUTS
document.addEventListener('keydown', (e) => {
    const isK = e.key === 'k' || e.key === 'K' || e.code === 'KeyK' || e.keyCode === 75;
    const isSlash = e.key === '/' || e.code === 'Slash' || e.keyCode === 191;
    const isCtrlOrCmd = e.ctrlKey || e.metaKey;

    const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
    const isTyping = activeTag === 'input' || activeTag === 'textarea' || activeTag === 'select';

    if ((isCtrlOrCmd && isK) || (isSlash && !isTyping)) {
        e.preventDefault();
        e.stopPropagation();

        const searchInput = document.getElementById('topbar-search-input') || 
                            document.querySelector('.search-box input') || 
                            document.querySelector('input[name="q"]');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
            searchInput.classList.remove('search-pulse-animation');
            void searchInput.offsetWidth; // Trigger reflow
            searchInput.classList.add('search-pulse-animation');
        }
    }
}, true);

// 2. 1-CLICK COPY TO CLIPBOARD WITH MODERN ICON MORPHING
function copyToClipboard(btnOrText, textIfBtn, label = 'Teks') {
    let btn = null;
    let text = '';

    if (typeof btnOrText === 'string') {
        text = btnOrText;
    } else if (btnOrText instanceof HTMLElement) {
        btn = btnOrText;
        text = textIfBtn;
    }

    if (!text) return;

    function onCopied() {
        if (typeof showToast === 'function') {
            showToast(`${label} berhasil disalin!`, 'success', 2500);
        }
        if (btn) {
            const icon = btn.querySelector('i');
            if (icon) {
                const originalClass = icon.className;
                icon.className = 'bi bi-check2 text-success fw-bold';
                setTimeout(() => {
                    icon.className = originalClass;
                }, 1600);
            }
        }
    }

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(onCopied).catch(() => fallbackCopy(text, label, btn));
    } else {
        fallbackCopy(text, label, btn);
    }
}

function fallbackCopy(text, label, btn) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        document.execCommand('copy');
        if (typeof showToast === 'function') {
            showToast(`${label} berhasil disalin!`, 'success', 2500);
        }
        if (btn) {
            const icon = btn.querySelector('i');
            if (icon) {
                const originalClass = icon.className;
                icon.className = 'bi bi-check2 text-success fw-bold';
                setTimeout(() => {
                    icon.className = originalClass;
                }, 1600);
            }
        }
    } catch (err) {
        if (typeof showToast === 'function') {
            showToast(`Gagal menyalin ${label}.`, 'danger', 2500);
        }
    }
    document.body.removeChild(textArea);
}

// 3. REAL-TIME LIVE FOLDER PATH VALIDATOR
function initFolderValidator() {
    const inputDirInput = document.getElementById('input_dir');
    const outputDirInput = document.getElementById('output_dir');

    if (!inputDirInput && !outputDirInput) return;

    let debounceTimer = null;

    function checkPath(inputEl, statusContainerId, type = 'input') {
        if (!inputEl) return;
        const statusEl = document.getElementById(statusContainerId);
        if (!statusEl) return;

        const val = inputEl.value.trim();
        if (!val) {
            statusEl.innerHTML = '';
            return;
        }

        statusEl.innerHTML = `
            <span class="folder-status-badge checking">
                <span class="spinner-border spinner-border-sm" role="status" style="width: 0.75rem; height: 0.75rem;"></span>
                <span>Memeriksa folder...</span>
            </span>
        `;

        fetch(`/api/check_folder?path=${encodeURIComponent(val)}`)
            .then(res => res.json())
            .then(data => {
                if (data.valid) {
                    statusEl.innerHTML = `
                        <span class="folder-status-badge valid">
                            <i class="bi bi-check-circle-fill"></i>
                            <span>${data.message}</span>
                        </span>
                    `;
                } else {
                    statusEl.innerHTML = `
                        <span class="folder-status-badge invalid">
                            <i class="bi bi-exclamation-triangle-fill"></i>
                            <span>${data.message}</span>
                        </span>
                    `;
                }
            })
            .catch(() => {
                statusEl.innerHTML = `
                    <span class="folder-status-badge checking">
                        <i class="bi bi-info-circle"></i>
                        <span>Belum dapat memverifikasi jalur</span>
                    </span>
                `;
            });
    }

    if (inputDirInput) {
        // Initial check
        checkPath(inputDirInput, 'input-dir-status', 'input');
        inputDirInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => checkPath(inputDirInput, 'input-dir-status', 'input'), 500);
        });
    }

    if (outputDirInput) {
        // Initial check
        checkPath(outputDirInput, 'output-dir-status', 'output');
        outputDirInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => checkPath(outputDirInput, 'output-dir-status', 'output'), 500);
        });
    }
}

// 4. QUICK IN-APP PDF VIEWER MODAL
function openQuickPdfModal(documentKey, fileName) {
    const modalEl = document.getElementById('quickPdfModal');
    if (!modalEl) return;

    const modalTitle = document.getElementById('quickPdfModalTitle');
    const iframe = document.getElementById('quickPdfIframe');
    const newTabBtn = document.getElementById('quickPdfNewTabBtn');
    const downloadBtn = document.getElementById('quickPdfDownloadBtn');

    const pdfUrl = `/lihat_pdf/${encodeURIComponent(documentKey)}`;

    if (modalTitle) modalTitle.textContent = fileName || documentKey;
    if (iframe) iframe.src = pdfUrl;
    if (newTabBtn) newTabBtn.href = pdfUrl;
    if (downloadBtn) downloadBtn.href = pdfUrl;

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

// Auto-clean iframe src on modal hide to save memory
document.addEventListener('DOMContentLoaded', () => {
    initFolderValidator();

    const modalEl = document.getElementById('quickPdfModal');
    if (modalEl) {
        modalEl.addEventListener('hidden.bs.modal', () => {
            const iframe = document.getElementById('quickPdfIframe');
            if (iframe) iframe.src = 'about:blank';
        });
    }
});
