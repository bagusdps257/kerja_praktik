// ===============================
// PROGRESS OCR
// ===============================

function updateProgress(){

    fetch("/progress")

    .then(res => res.json())

    .then(progress => {

        document.getElementById("progress-bar").style.width =
            progress.persen + "%";

        document.getElementById("progress-bar").innerHTML =
            progress.persen + "%";

        document.getElementById("progress-persen").innerHTML =
            progress.persen + "%";

        document.getElementById("progress-selesai").innerHTML =
            progress.selesai;

        document.getElementById("progress-total").innerHTML =
            progress.total;

        document.getElementById("progress-file").innerHTML =
            progress.current_file;

        let badgeClass = "badge-soft-secondary";

        if(progress.status=="RUNNING")
            badgeClass="badge-soft-primary";

        if(progress.status=="FINISHED")
            badgeClass="badge-soft-success";

        if(progress.status=="STOPPED")
            badgeClass="badge-soft-warning";

        if(progress.status=="ERROR")
            badgeClass="badge-soft-danger";

        document.getElementById("progress-status").innerHTML =
            'Status : <span class="badge ' + badgeClass + ' px-3 py-1.5 rounded-pill fw-bold text-uppercase">' + progress.status + '</span>';

    });

}