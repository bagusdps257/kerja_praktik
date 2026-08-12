// ===============================
// STOP OCR PROCESS
// ===============================

document.addEventListener('DOMContentLoaded', function() {
    const btnConfirmStop = document.getElementById('btn-confirm-stop');
    if (!btnConfirmStop) return;

    btnConfirmStop.addEventListener('click', function() {
        // Close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('stopProcessModal'));
        if (modal) modal.hide();

        // Disable the main stop button
        const btnStop = document.getElementById('btn-stop');
        if (btnStop) {
            btnStop.disabled = true;
            btnStop.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Stopping...';
        }

        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

        fetch("/stop", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                showToast(data.message || "OCR process stopped successfully.", "success");
            } else {
                showToast(data.message || "Could not stop process.", "warning");
            }

            if (typeof updateDashboard === 'function') updateDashboard();
            if (typeof updateProgress === 'function') updateProgress();
        })
        .catch(error => {
            console.error("Stop process error:", error);
            showToast("Failed to send stop signal to server.", "danger");
        })
        .finally(() => {
            if (btnStop) {
                btnStop.disabled = false;
                btnStop.innerHTML = '<i class="bi bi-stop-circle me-2 fs-5"></i><span>Stop</span>';
            }
        });
    });
});