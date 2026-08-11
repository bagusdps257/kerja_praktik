// ===============================
// FILTER TABEL
// ===============================

const searchInput =
document.getElementById("searchInput");

const statusFilter =
document.getElementById("statusFilter");

const tabelRiwayat =
document.querySelector("#tabelRiwayat tbody");

function saringTabel(){

    const keyword =
    searchInput.value.toLowerCase();

    const status =
    statusFilter.value;

    const rows =
    tabelRiwayat.querySelectorAll("tr");

    rows.forEach(tr=>{

        if(tr.querySelector("td") &&
           tr.querySelector("td").colSpan===9)
            return;

        const text =
        tr.textContent.toLowerCase();

        const statusBaris =
        tr.querySelector("td:nth-child(3)")
        .innerText
        .trim()
        .toUpperCase();

        const cocokKeyword =
        text.includes(keyword);

        const cocokStatus =
        status==="SEMUA" ||
        statusBaris===status;

        tr.style.display =
        (cocokKeyword && cocokStatus)
        ? ""
        : "none";

    });

}

function getFilterState(){

    return{

        keyword:
        searchInput.value,

        status:
        statusFilter.value

    };

}

function restoreFilter(state){

    searchInput.value =
    state.keyword;

    statusFilter.value =
    state.status;

    saringTabel();

}

// ===============================
// EVENT
// ===============================

searchInput.addEventListener("input",()=>{

    saringTabel();

    pauseRefresh();

});

statusFilter.addEventListener("change",()=>{

    saringTabel();

    pauseRefresh();

});

// kalau pencarian sudah kosong,
// refresh hidup lagi

function cekRefresh(){

    if(

        searchInput.value.trim()==="" &&

        statusFilter.value==="SEMUA"

    ){

        resumeRefresh();

    }

}

searchInput.addEventListener("blur",cekRefresh);

statusFilter.addEventListener("blur",cekRefresh);