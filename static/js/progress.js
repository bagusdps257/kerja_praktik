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

            if (progress.status === "FINISHED") {
                progressBar.classList.remove("progress-bar-animated");
                progressBar.classList.add("bg-success");
                progressBar.classList.remove("analytics-progress-bar-gradient", "bg-danger", "bg-warning");
            } else if (progress.status === "RUNNING") {
                progressBar.classList.add("progress-bar-animated");
                progressBar.classList.add("analytics-progress-bar-gradient");
                progressBar.classList.remove("bg-success", "bg-danger", "bg-warning");
            } else if (progress.status === "ERROR") {
                progressBar.classList.remove("progress-bar-animated");
                progressBar.classList.add("bg-danger");
                progressBar.classList.remove("analytics-progress-bar-gradient", "bg-success", "bg-warning");
            } else if (progress.status === "STOPPED") {
                progressBar.classList.remove("progress-bar-animated");
                progressBar.classList.add("bg-warning");
                progressBar.classList.remove("analytics-progress-bar-gradient", "bg-success", "bg-danger");
            } else {
                progressBar.classList.remove("progress-bar-animated", "bg-success", "bg-danger", "bg-warning");
                progressBar.classList.add("analytics-progress-bar-gradient");
            }
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

        // Sinkronisasi status tombol dan dropdown Target Subfolder saat proses berjalan
        const formJalankan = document.getElementById("form-jalankan");
        const submitBtn = formJalankan ? formJalankan.querySelector('button[type="submit"]') : null;
        const btnStop = document.getElementById("btn-stop");
        const selectTarget = document.getElementById("target_subfolder");
        const btnScan = document.getElementById("btn-scan-subfolders");

        if (progress.status === "RUNNING") {
            if (submitBtn) {
                submitBtn.disabled = true;
            }
            if (btnStop) {
                btnStop.disabled = false;
            }
            if (selectTarget) {
                selectTarget.disabled = true;
                if (progress.target_subfolder && selectTarget.value !== progress.target_subfolder) {
                    selectTarget.value = progress.target_subfolder;
                    if (typeof perbaruiStatusCakupan === 'function') {
                        perbaruiStatusCakupan(progress.target_subfolder, true);
                    }
                }
            }
            if (btnScan) btnScan.disabled = true;
        } else {
            if (submitBtn) {
                submitBtn.disabled = false;
            }
            if (btnStop) {
                btnStop.disabled = (progress.status !== "RUNNING");
            }
            if (selectTarget) {
                selectTarget.disabled = false;
            }
            if (btnScan) btnScan.disabled = false;
        }
    })
    .catch(err => {
        // Warning logged without throwing uncaught errors to prevent halting intervals
        console.warn("Progres update warning:", err);
    });
}