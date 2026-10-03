// ==============================================================================
// LIVE PROGRESS OCR - PT JAWA SATU POWER
// ==============================================================================

function updateProgress() {
    fetch("/progress?ts=" + Date.now(), { cache: 'no-store' })
    .then(res => {
        if (!res.ok) throw new Error("Gagal mengambil progres: " + res.status);
        return res.json();
    })
    .then(progress => {
        if (!progress) return;

        const progressBar = document.getElementById("progress-bar");
        const progressPersen = document.getElementById("progress-persen");
        const progressSelesai = document.getElementById("progress-selesai");
        const progressTotal = document.getElementById("progress-total");
        const progressFile = document.getElementById("progress-file");
        const progressStatus = document.getElementById("progress-status");

        const pct = progress.persen !== undefined ? progress.persen : 0;

        if (progressBar) {
            progressBar.style.width = pct + "%";
            progressBar.textContent = pct + "%";
        }

        if (progressPersen) {
            progressPersen.textContent = pct + "%";
        }

        if (progressSelesai) {
            progressSelesai.textContent = progress.selesai !== undefined ? progress.selesai : 0;
        }

        if (progressTotal) {
            progressTotal.textContent = progress.total !== undefined ? progress.total : 0;
        }

        if (progressFile) {
            progressFile.textContent = progress.current_file || "-";
            progressFile.title = progress.current_file || "";
        }

        if (progressStatus) {
            let badgeClass = "badge-soft-secondary";
            if (progress.status === "RUNNING") badgeClass = "badge-soft-primary";
            if (progress.status === "FINISHED") badgeClass = "badge-soft-success";
            if (progress.status === "STOPPED") badgeClass = "badge-soft-warning";
            if (progress.status === "ERROR") badgeClass = "badge-soft-danger";

            const safeStatus = (progress.status || 'IDLE').toUpperCase();
            progressStatus.innerHTML =
                'Status : <span class="badge ' + badgeClass + ' px-3 py-1.5 rounded-pill fw-bold text-uppercase">' + safeStatus + '</span>';
        }
    })
    .catch(err => {
        // Warning logged without throwing uncaught errors to prevent halting intervals
        console.warn("Progres update warning:", err);
    });
}