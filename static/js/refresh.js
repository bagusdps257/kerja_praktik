// ==============================================================================
// AUTO REFRESH DASHBOARD & REAL-TIME STATS - PT JAWA SATU POWER
// ==============================================================================

let timerRefresh = null;
let refreshPaused = false;
let distributionChartInstance = null;

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function getRefreshStatusElement() {
    return document.getElementById("refresh-status");
}

function setRefreshStatus(active) {
    const el = getRefreshStatusElement();
    if (!el) return;

    if (active) {
        el.innerHTML = '<i class="bi bi-arrow-repeat me-1 text-success"></i>Auto-refresh Aktif';
        el.className = 'badge border px-3 py-2 rounded-2 fw-semibold';
        el.style.background = '#ffffff';
        el.style.color = '#166534';
        el.style.borderColor = '#bbf7d0';
        el.style.cursor = 'pointer';
        el.title = 'Auto-refresh aktif setiap 2 detik. Klik untuk menjeda.';
    } else {
        el.innerHTML = '<i class="bi bi-pause-circle me-1 text-warning"></i>Auto-refresh Dijeda';
        el.className = 'badge border px-3 py-2 rounded-2 fw-semibold';
        el.style.background = '#ffffff';
        el.style.color = '#854d0e';
        el.style.borderColor = '#fef08a';
        el.style.cursor = 'pointer';
        el.title = 'Auto-refresh sedang dijeda. Klik untuk melanjutkan.';
    }
}

function initDistributionChart(success, pending, failed) {
    const canvas = document.getElementById('distributionChart');
    if (!canvas) return;

    if (typeof Chart === 'undefined') {
        console.warn('Chart.js is not loaded yet.');
        return;
    }

    // Defensive check: reuse existing chart instance if canvas is already tracked
    if (!distributionChartInstance) {
        const existingChart = Chart.getChart(canvas);
        if (existingChart) {
            distributionChartInstance = existingChart;
        }
    }

    if (distributionChartInstance) {
        distributionChartInstance.data.datasets[0].data = [success, pending, failed];
        distributionChartInstance.update();
    } else {
        const ctx = canvas.getContext('2d');
        distributionChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Selesai', 'Antrean', 'Gagal'],
                datasets: [{
                    data: [success, pending, failed],
                    backgroundColor: [
                        '#166534', // Forest Green (Success)
                        '#475569', // Slate Gray (Pending / Queue)
                        '#991b1b'  // Crimson Brick (Failed)
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '76%',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.92)',
                        titleFont: { family: "'Plus Jakarta Sans', sans-serif", weight: 'bold', size: 12 },
                        bodyFont: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
                        padding: 10,
                        cornerRadius: 10,
                        displayColors: true,
                        boxWidth: 8,
                        boxHeight: 8,
                        boxPadding: 4,
                        callbacks: {
                            label: function(context) {
                                return ` ${context.label}: ${context.raw} dokumen`;
                            }
                        }
                    }
                }
            }
        });
    }
}

function renderRecentFiles(recentFiles) {
    const tbody = document.getElementById('recent-files-body');
    if (!tbody) return;

    if (!recentFiles || recentFiles.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-5 text-muted">
                    <i class="bi bi-inbox fs-1 d-block mb-2 opacity-25"></i>
                    <div class="fw-semibold">Belum ada aktivitas OCR terbaru.</div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = recentFiles.map(file => {
        let badge = '';

        if (file.status === 'SUKSES') {
            badge = `
                <span class="badge badge-soft-success px-2.5 py-1 rounded-1 fw-semibold">
                    <i class="bi bi-check2-circle me-1"></i>
                    Selesai
                </span>
            `;
        } else if (file.status === 'SKIP') {
            badge = `
                <span class="badge badge-soft-secondary px-2.5 py-1 rounded-1 fw-semibold">
                    <i class="bi bi-dash-circle me-1"></i>
                    Dilewati
                </span>
            `;
        } else {
            badge = `
                <span class="badge badge-soft-danger px-2.5 py-1 rounded-1 fw-semibold">
                    <i class="bi bi-exclamation-octagon me-1"></i>
                    Gagal
                </span>
            `;
        }

        const displayTime = file.updated_waktu || file.waktu || '-';
        const hasUpdate = file.updated_waktu && file.waktu && file.updated_waktu !== file.waktu;
        const safeFileName = escapeHtml(file.nama_file || '-');
        const rawFileName = (file.nama_file || '').replace(/'/g, "\\'");
        const safeKeterangan = escapeHtml(file.keterangan || '-');

        return `
            <tr class="analytics-user-row">
                <td class="text-muted small fw-medium">
                    ${escapeHtml(displayTime)}
                    ${hasUpdate ? `<div class="text-muted" style="font-size: 0.72rem;" title="Terakhir Diproses"><i class="bi bi-arrow-repeat me-1 text-primary"></i>${escapeHtml(file.updated_waktu)}</div>` : ''}
                </td>
                <td>
                    <div class="d-flex align-items-center gap-2.5">
                        <div class="d-flex align-items-center justify-content-center rounded-2" style="background: rgba(15, 60, 104, 0.08); color: #0f3c68; width: 34px; height: 34px;">
                            <i class="bi bi-file-earmark-pdf fs-6"></i>
                        </div>
                        <div class="fw-semibold text-dark text-break" style="font-size: .9rem;">
                            ${safeFileName}
                        </div>
                        <button type="button" class="btn-copy" onclick="copyToClipboard(this, '${rawFileName}', 'Nama file')" title="Salin nama file">
                            <i class="bi bi-copy"></i>
                        </button>
                    </div>
                </td>
                <td>
                    ${badge}
                </td>
                <td class="text-muted small fw-medium">
                    ${safeKeterangan}
                </td>
            </tr>
        `;
    }).join('');
}

function updateDashboard() {
    fetch('/api/status?ts=' + Date.now(), {
        cache: 'no-store'
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok: ' + response.status);
        return response.json();
    })
    .then(data => {
        // 1. Update recent files
        if (data.recent_files !== undefined) {
            renderRecentFiles(data.recent_files);
        }

        // 2. Update KPI cards
        if (data.stats) {
            const elTotalInput = document.getElementById('stat-total-input');
            const elSuccess = document.getElementById('stat-success');
            const elFailed = document.getElementById('stat-failed');
            const elPending = document.getElementById('stat-pending');

            if (elTotalInput && data.stats.total_input !== undefined) elTotalInput.textContent = data.stats.total_input;
            if (elSuccess && data.stats.total_output !== undefined) elSuccess.textContent = data.stats.total_output;
            if (elFailed && data.stats.total_gagal !== undefined) elFailed.textContent = data.stats.total_gagal;
            if (elPending && data.stats.pending !== undefined) elPending.textContent = data.stats.pending;

            // 3. Update Donut Chart
            const successCount = data.stats.total_output || 0;
            const pendingCount = data.stats.pending || 0;
            const failedCount = data.stats.total_gagal || 0;
            initDistributionChart(successCount, pendingCount, failedCount);

            // 4. Update Success Rate Center Text
            const totalInput = data.stats.total_input || 0;
            const rawRate = totalInput > 0 ? Math.round((successCount / totalInput) * 100) : 0;
            const rate = Math.min(100, Math.max(0, rawRate));
            const elRateText = document.getElementById('distribution-rate-text');
            if (elRateText) elRateText.textContent = `${rate}%`;

            // 5. Update Distribution Section & Storage Details
            const elInputSize = document.getElementById('dist-input-size');
            const elOutputSize = document.getElementById('dist-output-size');
            const elInputPages = document.getElementById('dist-input-pages');
            const elOutputPages = document.getElementById('dist-output-pages');
            const elUsedPercent = document.getElementById('dist-used-percent');
            const elDiskProgress = document.getElementById('dist-disk-progress');
            const elFreeSpace = document.getElementById('dist-free-space');
            const elWarning = document.getElementById('dist-storage-warning');
            const elWarningText = document.getElementById('dist-storage-warning-text');

            if (elInputSize && data.stats.input_size) elInputSize.textContent = data.stats.input_size;
            if (elOutputSize && data.stats.output_size) elOutputSize.textContent = data.stats.output_size;
            if (elInputPages && data.stats.total_input_pages !== undefined) elInputPages.textContent = data.stats.total_input_pages;
            if (elOutputPages && data.stats.total_output_pages !== undefined) elOutputPages.textContent = data.stats.total_output_pages;

            if (elUsedPercent && data.stats.used_percent !== undefined) {
                elUsedPercent.textContent = `${data.stats.used_percent}%`;
            }
            if (elDiskProgress && data.stats.used_percent !== undefined) {
                const pct = data.stats.used_percent;
                elDiskProgress.style.width = `${pct}%`;
                elDiskProgress.className = 'progress-bar ' + (pct >= 90 ? 'bg-danger' : pct >= 70 ? 'bg-warning' : 'analytics-progress-bar-gradient');
            }
            if (elFreeSpace && data.stats.free_space) {
                elFreeSpace.textContent = data.stats.free_space;
                if (data.stats.free_bytes !== undefined) {
                    const freeGb = data.stats.free_bytes / (1024 ** 3);
                    elFreeSpace.className = 'fw-bold ' + (freeGb > 20 ? 'text-success' : freeGb >= 5 ? 'text-warning' : 'text-danger');

                    if (elWarning) {
                        if (freeGb < 10) {
                            elWarning.style.display = 'block';
                            elWarning.className = 'alert mt-3 mb-0 py-2 px-3 text-start rounded-3 ' + (freeGb < 5 ? 'alert-danger' : 'alert-warning');
                            if (elWarningText) {
                                if (freeGb < 5) {
                                    elWarningText.innerHTML = `<strong>Kritis:</strong> Ruang penyimpanan sangat menipis (sisa ${freeGb.toFixed(1)} GB).`;
                                } else {
                                    elWarningText.innerHTML = `<strong>Peringatan:</strong> Ruang penyimpanan mulai menipis (sisa ${freeGb.toFixed(1)} GB).`;
                                }
                            }
                        } else {
                            elWarning.style.display = 'none';
                        }
                    }
                }
            }
        }
    })
    .catch(error => {
        console.error('Auto refresh error:', error);
    });
}

function pauseRefresh() {
    refreshPaused = true;
    if (timerRefresh) {
        clearInterval(timerRefresh);
        timerRefresh = null;
    }
    setRefreshStatus(false);
}

function resumeRefresh() {
    if (timerRefresh) return;

    refreshPaused = false;
    timerRefresh = setInterval(() => {
        updateDashboard();

        if (typeof updateProgress === 'function') {
            updateProgress();
        }
    }, 2000); // Polling every 2 seconds

    setRefreshStatus(true);
}

function toggleRefresh() {
    if (timerRefresh) {
        pauseRefresh();
    } else {
        resumeRefresh();
        updateDashboard();
        if (typeof updateProgress === 'function') {
            updateProgress();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Initial Chart setup if initial values present
    if (window.initialDistributionData) {
        initDistributionChart(
            window.initialDistributionData.success,
            window.initialDistributionData.pending,
            window.initialDistributionData.failed
        );
    }

    // Attach click handler to status badge for instant toggle
    const statusEl = getRefreshStatusElement();
    if (statusEl) {
        statusEl.addEventListener('click', toggleRefresh);
    }

    updateDashboard();
    resumeRefresh();
});