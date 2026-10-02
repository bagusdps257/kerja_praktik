# Implementation Plan: Authentic Industrial UI/UX Redesign (PT Jawa Satu Power)

## Overview
Merombak seluruh visual antarmuka sistem agar 100% bercirikan aplikasi korporat/industri operasional PT Jawa Satu Power, menghapus efek AI template (gradasi pelangi, animasi loncat/melayang, drop-shadow neon, ikon chip generik), serta menyempurnakan copywriting bahasa Indonesia menjadi istilah teknis operasional.

---

## Tasks

- [ ] Task 1: Refactor CSS Design System (`static/css/style.css`)
  - [ ] Step 1: Hapus keyframes berlebihan (`pulse-green`, `searchPulse`, `spinSlow`, dll.)
  - [ ] Step 2: Hapus semua aturan `transform: translateY(-2px)` dan `translateY(-3px)` pada tombol dan kartu
  - [ ] Step 3: Ganti tombol `.btn-gradient-*` menjadi tombol korporat solid berwibawa:
    - `.btn-primary` & `.btn-gradient-primary`: Solid Navy `#0f3c68`
    - `.btn-destructive`, `.btn-gradient-destructive`, `.btn-gradient-danger`: Solid Brick `#991b1b`
    - `.btn-gradient-excel`, `.btn-gradient-export`: Solid Forest `#166534`
    - `.btn-gradient-backup`, `.btn-gradient-success`: Solid Dark Emerald `#065f46`
  - [ ] Step 4: Rekonstruksi kartu (`.enterprise-card`, `.kpi-card`, `.analytics-card`) menjadi panel solid stabil beraksen garis SCADA
  - [ ] Step 5: Perbarui logo sidebar dan menu aktif menjadi style korporat elegan

- [ ] Task 2: Redesign Sidebar & Topbar Templates
  - [ ] Step 1: Update `templates/partials/sidebar.html` (Branding "PT Jawa Satu Power", PLTGU Jawa-1, ikon operasional)
  - [ ] Step 2: Update `templates/partials/topbar.html` (Placeholder pencarian "Cari dokumen arsip...")
  - [ ] Step 3: Update `templates/partials/navbar.html` (Badge peran "Operator Sistem" & "Staf Operasional")

- [ ] Task 3: Redesign Dashboard & Control Panels
  - [ ] Step 1: Update `templates/index.html` & `templates/partials/engine_control_section.html` (Ganti terminologi: "Panel Eksekusi Konversi OCR", "Direktori Berkas Masuk/Hasil", "Mulai Pemrosesan Berkas", "Hentikan Pemrosesan", ikon `bi-sliders2`)
  - [ ] Step 2: Update `templates/partials/stats_cards.html` & `templates/partials/distribution_section.html` (Terminologi metrik operasional)
  - [ ] Step 3: Update `templates/partials/recent_files_section.html`

- [ ] Task 4: Redesign Documents, Users, and Settings Templates
  - [ ] Step 1: Update `templates/documents.html` (Tombol solid, judul "Daftar Berkas & Arsip Dokumen", modal evaluasi CER teks teknis)
  - [ ] Step 2: Update `templates/users.html` (Judul "Otorisasi & Manajemen Akun Petugas", peran "Operator Sistem" vs "Staf Operasional")
  - [ ] Step 3: Update `templates/monitoring.html`, `templates/analytics.html`, `templates/settings.html`

- [ ] Task 5: Verification & Integration
  - [ ] Step 1: Verifikasi kompilasi seluruh template Jinja
  - [ ] Step 2: Jalankan test suite pytest (21/21 tests pass)
  - [ ] Step 3: Commit dan merge ke master
