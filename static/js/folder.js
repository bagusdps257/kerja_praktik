let currentExplorerTarget = null;
let currentExplorerPath = "";

function pilihFolder(idInput) {
    currentExplorerTarget = idInput;
    const modalEl = document.getElementById('folderExplorerModal');
    if (!modalEl) return;
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    loadFolderExplorer("");
    modal.show();
}

function loadFolderExplorer(path) {
    fetch(`/api/folders?path=${encodeURIComponent(path)}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            currentExplorerPath = data.current;
            const pathInput = document.getElementById('explorerCurrentPath');
            if (pathInput) {
                pathInput.value = data.current || "Drives";
            }
            
            const btnUp = document.getElementById('explorerBtnUp');
            if (btnUp) {
                if (data.parent !== null && data.current !== "") {
                    btnUp.onclick = () => loadFolderExplorer(data.parent);
                    btnUp.disabled = false;
                } else {
                    btnUp.onclick = () => loadFolderExplorer("");
                    btnUp.disabled = (data.current === "");
                }
            }
            
            const list = document.getElementById('explorerFolderList');
            if (!list) return;
            list.innerHTML = "";
            data.folders.forEach(f => {
                const a = document.createElement('a');
                a.className = "list-group-item list-group-item-action d-flex align-items-center";
                a.href = "javascript:void(0)";
                
                const icon = document.createElement('i');
                icon.className = "bi bi-folder-fill text-warning me-2";
                a.appendChild(icon);
                a.appendChild(document.createTextNode(f));

                a.onclick = () => {
                    const separator = data.current.endsWith('\\') || data.current.endsWith('/') || data.current === "" ? "" : "/";
                    loadFolderExplorer(data.current + separator + f);
                };
                list.appendChild(a);
            });
        });
}

document.getElementById('explorerBtnSelect')?.addEventListener('click', () => {
    if (!currentExplorerPath) {
        alert("Pilih direktori spesifik.");
        return;
    }
    if (!currentExplorerTarget) return;
    const targetEl = document.getElementById(currentExplorerTarget);
    if (!targetEl) return;
    targetEl.value = currentExplorerPath;
    
    // Save to server
    const csrfTokenEl = document.querySelector('input[name="csrf_token"]');
    const formData = new FormData();
    if (csrfTokenEl) {
        formData.append('csrf_token', csrfTokenEl.value);
    }
    formData.append('field', currentExplorerTarget);
    formData.append('value', currentExplorerPath);
    
    fetch('/update_folder', {
        method: 'POST',
        body: formData
    })
    .then(res => {
        if(res.ok) window.location.reload();
        else alert("Gagal mengupdate folder.");
    });
});

// Support direct path editing in input_dir and output_dir fields
['input_dir', 'output_dir'].forEach(id => {
    document.getElementById(id)?.addEventListener('change', (e) => {
        const val = e.target.value.trim();
        if (!val) return;
        const formData = new FormData();
        formData.append('csrf_token', document.querySelector('input[name="csrf_token"]').value);
        formData.append('field', id);
        formData.append('value', val);
        
        fetch('/update_folder', {
            method: 'POST',
            body: formData
        })
        .then(res => {
            if(res.ok) {
                window.location.reload();
            } else {
                alert("Gagal mengupdate folder. Pastikan folder benar-benar ada.");
                window.location.reload();
            }
        });
    });
});

document.getElementById('form-folder')?.addEventListener('submit', (e) => {
    e.preventDefault();
});