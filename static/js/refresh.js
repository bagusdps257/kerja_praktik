// ===============================
// AUTO REFRESH DASHBOARD & STATS
// ===============================

let timerRefresh = null;
let refreshPaused = false;
let distributionChartInstance = null;

const refreshStatus = document.getElementById("refresh-status");

function setRefreshStatus(active) {
    if (!refreshStatus) return;

    if (active) {
        refreshStatus.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i> Auto-refresh Active';
        refreshStatus.className = 'text-success fw-bold';
    } else {
        refreshStatus.innerHTML = '<i class="bi bi-pause-circle me-1"></i> Paused';
        refreshStatus.className = 'text-warning fw-bold';
    }
}

function initDistributionChart(success, pending, failed) {
    const canvas = document.getElementById('distributionChart');
    if (!canvas) return;

    if (typeof Chart === 'undefined') {
        console.warn('Chart.js is not loaded yet.');
        return;
    }

    const ctx = canvas.getContext('2d');

    if (distributionChartInstance) {
        distributionChartInstance.data.datasets[0].data = [success, pending, failed];
        distributionChartInstance.update();
    } else {
        distributionChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Success', 'Pending', 'Failed'],
                datasets: [{
                    data: [success, pending, failed],
                    backgroundColor: [
                        '#059669', // Soft Mint (Processed / Success)
                        '#7c3aed', // Royal Violet (Pending / Waiting)
                        '#e11d48'  // Soft Rose Coral (Failed)
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
                    <div class="fw-semibold">No recent OCR activity available.</div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = recentFiles.map(file => {
        let badge = '';

        if (file.status === 'SUKSES') {
            badge = `
                <span class="badge badge-soft-success px-3 py-1.5 rounded-pill fw-bold">
                    <i class="bi bi-check-circle-fill me-1"></i>
                    Success
                </span>
            `;
        } else if (file.status === 'SKIP') {
            badge = `
                <span class="badge badge-soft-secondary px-3 py-1.5 rounded-pill fw-bold">
                    <i class="bi bi-skip-forward-fill me-1"></i>
                    Skipped
                </span>
            `;
        } else {
            badge = `
                <span class="badge badge-soft-danger px-3 py-1.5 rounded-pill fw-bold">
                    <i class="bi bi-x-circle-fill me-1"></i>
                    Failed
                </span>
            `;
        }

        return `
            <tr class="analytics-user-row">
                <td class="text-muted small fw-medium">
                    ${file.waktu}
                    ${file.updated_waktu && file.updated_waktu !== file.waktu ? `<div class="text-muted" style="font-size: 0.72rem;" title="Terakhir Diproses"><i class="bi bi-arrow-repeat me-1 text-primary"></i>${file.updated_waktu}</div>` : ''}
                </td>
                <td>
                    <div class="d-flex align-items-center gap-2.5">
                        <div class="d-flex align-items-center justify-content-center rounded-3" style="background: rgba(2, 132, 199, 0.08); color: #0284c7; width: 34px; height: 34px;">
                            <i class="bi bi-file-earmark-pdf fs-6"></i>
                        </div>
                        <div class="fw-semibold text-dark text-break" style="font-size: .9rem;">
                            ${file.nama_file}
                        </div>
                        <button type="button" class="btn-copy" onclick="copyToClipboard(this, '${escapeHtml(file.nama_file)}', 'Nama file')" title="Salin nama file">
                            <i class="bi bi-copy"></i>
                        </button>
                    </div>
                </td>
                <td>
                    ${badge}
                </td>
                <td class="text-muted small fw-medium">
                    ${file.keterangan || '-'}
                </td>
            </tr>
        `;
    }).join('');
}

function updateDashboard() {
    fetch('/api/status?ts=' + new Date().getTime(), {
        cache: 'no-store'
    })
    .then(response => response.json())
    .then(data => {
        // Update recent files
        renderRecentFiles(data.recent_files);

        // Update KPI cards
        if (data.stats) {
            const elTotalInput = document.getElementById('stat-total-input');
            const elSuccess = document.getElementById('stat-success');
            const elFailed = document.getElementById('stat-failed');
            const elPending = document.getElementById('stat-pending');

            if (elTotalInput) elTotalInput.textContent = data.stats.total_input;
            if (elSuccess) elSuccess.textContent = data.stats.total_output;
            if (elFailed) elFailed.textContent = data.stats.total_gagal;
            if (elPending) elPending.textContent = data.stats.pending;

            // Update Donut Chart
            const successCount = data.stats.total_output || 0;
            const pendingCount = data.stats.pending || 0;
            const failedCount = data.stats.total_gagal || 0;
            initDistributionChart(successCount, pendingCount, failedCount);

            // Update Success Rate Center Text
            const totalInput = data.stats.total_input || 0;
            const rawRate = totalInput > 0 ? Math.round((successCount / totalInput) * 100) : 0;
            const rate = Math.min(100, Math.max(0, rawRate));
            const elRateText = document.getElementById('distribution-rate-text');
            if (elRateText) elRateText.textContent = `${rate}%`;

            // Update Distribution Section & Storage Details
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
    clearInterval(timerRefresh);
    timerRefresh = null;
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

document.addEventListener('DOMContentLoaded', () => {
    // Initial Chart setup if initial values present
    if (window.initialDistributionData) {
        initDistributionChart(
            window.initialDistributionData.success,
            window.initialDistributionData.pending,
            window.initialDistributionData.failed
        );
    }

    updateDashboard();
    resumeRefresh();
});