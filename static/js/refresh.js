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
                        '#10b981', // Emerald Green (Processed / Success)
                        '#6366f1', // Indigo (Pending / Waiting)
                        '#ef4444'  // Rose Red (Failed)
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
                        callbacks: {
                            label: function(context) {
                                return ` ${context.label}: ${context.raw} files`;
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
                </td>
                <td>
                    <div class="d-flex align-items-center gap-2.5">
                        <div class="d-flex align-items-center justify-content-center rounded-3" style="background: rgba(99, 102, 241, 0.08); color: #6366f1; width: 34px; height: 34px;">
                            <i class="bi bi-file-earmark-pdf fs-6"></i>
                        </div>
                        <div class="fw-semibold text-dark text-break" style="font-size: .9rem;">
                            ${file.nama_file}
                        </div>
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
            const rate = totalInput > 0 ? Math.round((successCount / totalInput) * 100) : 0;
            const elRateText = document.getElementById('distribution-rate-text');
            if (elRateText) elRateText.textContent = `${rate}%`;

            // Update Distribution Bottom Metrics
            const elProcessed = document.getElementById('dist-files-processed');
            const elPages = document.getElementById('dist-total-pages');
            const elStorage = document.getElementById('dist-storage-used');

            if (elProcessed) elProcessed.textContent = (successCount + failedCount);
            if (elPages) elPages.textContent = data.stats.total_halaman || 0;
            if (elStorage && data.total_ukuran) elStorage.textContent = data.total_ukuran;
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