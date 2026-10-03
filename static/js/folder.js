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

// ==============================================================================
// TARGET SUBFOLDER SCOPE LOADER & SELECTION PERSISTENCE
// ==============================================================================
function perbaruiStatusCakupan(selectedVal, isRunning = false) {
    const badgeEl = document.getElementById('target-scope-badge');
    const descEl = document.getElementById('target-scope-desc');

    if (selectedVal) {
        localStorage.setItem('ocr_target_subfolder', selectedVal);
        if (badgeEl) {
            badgeEl.className = 'badge border px-2.5 py-1 rounded-1 fw-bold text-primary';
            badgeEl.style.background = '#eff6ff';
            badgeEl.style.borderColor = '#bfdbfe !important';
            badgeEl.innerHTML = `<i class="bi bi-filter-circle-fill me-1 text-primary"></i>Target: ${selectedVal}`;
        }
        if (descEl) {
            descEl.innerHTML = `Mode terarah aktif: Sistem <strong>hanya memproses berkas di dalam subfolder "${selectedVal}"</strong>. Berkas di luar folder ini tidak akan disentuh.`;
        }
    } else {
        localStorage.setItem('ocr_target_subfolder', '');
        if (badgeEl) {
            badgeEl.className = 'badge border px-2 py-0.5 rounded-1 text-muted fw-normal';
            badgeEl.style.background = '#ffffff';
            badgeEl.style.borderColor = '#cbd5e1 !important';
            badgeEl.textContent = 'Semua Subfolder';
        }
        if (descEl) {
            descEl.innerHTML = `Sistem memindai <strong>seluruh subfolder</strong> di dalam direktori input secara komprehensif.`;
        }
    }
}

function muatDaftarSubfolder(forcedVal) {
    const selectEl = document.getElementById('target_subfolder');
    if (!selectEl) return;

    const inputDirInput = document.getElementById('input_dir');
    const inputDir = inputDirInput ? inputDirInput.value.trim() : '';

    // Prioritas nilai: forcedVal -> selectEl.value -> localStorage -> ""
    const savedVal = forcedVal !== undefined
        ? forcedVal
        : (selectEl.value || localStorage.getItem('ocr_target_subfolder') || '');

    const btnScan = document.getElementById('btn-scan-subfolders');
    if (btnScan) {
        btnScan.disabled = true;
        const icon = btnScan.querySelector('i');
        if (icon) icon.className = 'bi bi-arrow-clockwise spinner-border spinner-border-sm text-primary';
    }

    fetch(`/api/subfolders?input_dir=${encodeURIComponent(inputDir)}&ts=${Date.now()}`)
        .then(res => res.json())
        .then(data => {
            selectEl.innerHTML = '<option value="">Seluruh Direktori Input (Semua Subfolder) — Default</option>';

            let foundMatch = false;
            if (data.status === 'success' && data.subfolders && data.subfolders.length > 0) {
                data.subfolders.forEach(sf => {
                    const opt = document.createElement('option');
                    opt.value = sf.name;
                    opt.textContent = `Subfolder: ${sf.name} (${sf.file_count} berkas)`;
                    if (sf.name === savedVal) {
                        opt.selected = true;
                        foundMatch = true;
                    }
                    selectEl.appendChild(opt);
                });
            }

            if (!foundMatch && savedVal === '') {
                selectEl.value = '';
            }

            perbaruiStatusCakupan(selectEl.value);
        })
        .catch(err => {
            console.error('Error loading subfolders:', err);
        })
        .finally(() => {
            if (btnScan) {
                btnScan.disabled = false;
                const icon = btnScan.querySelector('i');
                if (icon) icon.className = 'bi bi-arrow-clockwise text-primary';
            }
        });
}

document.addEventListener('DOMContentLoaded', () => {
    const selectEl = document.getElementById('target_subfolder');
    if (selectEl) {
        selectEl.addEventListener('change', (e) => {
            perbaruiStatusCakupan(e.target.value);
        });
    }

    // Inisialisasi daftar subfolder
    muatDaftarSubfolder();

    // Handle AJAX submission of form-jalankan to prevent full page reload and preserve UX state
    const formJalankan = document.getElementById('form-jalankan');
    if (formJalankan) {
        formJalankan.addEventListener('submit', function(e) {
            e.preventDefault();

            const targetVal = selectEl ? selectEl.value : '';
            localStorage.setItem('ocr_target_subfolder', targetVal);

            const formData = new FormData(formJalankan);
            const submitBtn = formJalankan.querySelector('button[type="submit"]');

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span><span>Memulai Pemrosesan...</span>';
            }

            fetch('/jalankan', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => {
                if (!res.ok) throw new Error('Gagal memulai OCR');
                return res.json();
            })
            .then(data => {
                if (typeof updateProgress === 'function') updateProgress();
                if (typeof updateDashboard === 'function') updateDashboard();
                if (typeof showToast === 'function') {
                    const msg = targetVal
                        ? `Pemrosesan subfolder "${targetVal}" dimulai.`
                        : 'Pemrosesan seluruh berkas dimulai.';
                    showToast(msg, 'success');
                }
            })
            .catch(err => {
                console.error('Error starting OCR process:', err);
                if (typeof showToast === 'function') {
                    showToast('Gagal mengirim sinyal mulai ke server.', 'danger');
                }
            })
            .finally(() => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="bi bi-play-circle-fill me-2 fs-5"></i><span>Mulai Pemrosesan Berkas</span>';
                }
            });
        });
    }
});