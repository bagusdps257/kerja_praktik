let lastRiwayatHash = "";
// ===============================
// DASHBOARD
// ===============================

function updateDashboard() {

    const filterState = getFilterState();

    fetch("/api/status")

    .then(res => res.json())

    .then(data => {

        // =====================
        // CARD
        // =====================

        const cards =
            document.querySelectorAll(".stat-card h2");

        cards[0].textContent = data.stats.total_input;
        cards[1].textContent = data.stats.total_output;
        cards[2].textContent = data.stats.total_halaman;
        cards[3].textContent = data.stats.pending;
        cards[4].textContent = data.stats.total_gagal;
        cards[5].textContent = data.total_ukuran;

        // =====================
        // LOG
        // =====================

        const logBox =
            document.getElementById("logBox");

        let logHTML = "";

        data.logs.forEach(log => {

            logHTML +=
            `<div class="mb-1">
                <span class="text-secondary">>></span>
                ${log}
            </div>`;

        });

        if (logBox.innerHTML !== logHTML) {

            logBox.innerHTML = logHTML;

        }

        const filterState =
        getFilterState();

        const currentHash =
        JSON.stringify(data.riwayat);

        if(currentHash!==lastRiwayatHash){

            lastRiwayatHash =
            currentHash;

            const tbody =
            document.querySelector("#tabelRiwayat tbody");

            let html="";

            data.riwayat.forEach(baris=>{

                let badge="";

                if(baris.status==="SUKSES"){

                    badge=
                    `<span class="badge bg-success">SUKSES</span>`;

                }

                else if(baris.status==="SKIP"){

                    badge=
                    `<span class="badge bg-secondary">SKIP</span>`;

                }

                else{

                    badge=
                    `<span class="badge bg-danger">GAGAL</span>`;

                }

                html+=`

                <tr>

                <td>${baris.waktu}</td>

                <td>${baris.nama_file}</td>

                <td>${badge}</td>

                <td>${baris.keterangan}</td>

                <td>${baris.file_size}</td>

                <td>${baris.page_count}</td>

                <td>${baris.author}</td>

                <td>${baris.creation_date}</td>

                <td>

                ${
                (baris.status==="SUKSES" ||
                baris.status==="SKIP")

                ?

                `<a
                class="btn btn-sm btn-outline-primary"
                href="/lihat_pdf/${encodeURIComponent(baris.nama_file)}"
                target="_blank">

                Lihat

                </a>`

                :

                `<button
                class="btn btn-sm btn-light"
                disabled>

                N/A

                </button>`

                }

                </td>

                </tr>

                `;

            });

            tbody.innerHTML =
            html;

            restoreFilter(filterState);

        }

        if (tbody.innerHTML !== html) {

            tbody.innerHTML = html;

            tbody.parentElement.scrollTop =
                posisiScroll;

        }

    })

    .catch(err => {

        console.error(err);

    });

}