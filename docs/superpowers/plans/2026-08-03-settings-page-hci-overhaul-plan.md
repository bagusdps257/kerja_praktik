# Settings Page HCI & Soft UI Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overhaul `templates/settings.html` and `static/css/style.css` to implement true Bootstrap 5 tab navigation, Hick's/Fitts's Law form grid proportions, a sticky action bar, a destructive action confirmation modal, and harmonized Soft UI styling.

**Architecture:** Refactor `templates/settings.html` into a Bootstrap `nav-pills` & `tab-content` system with structured form grids, add custom CSS classes in `static/css/style.css`, and add a Bootstrap modal for database reset.

**Tech Stack:** HTML5, CSS3, Bootstrap 5.3 (Pills, Grid, Modals), Jinja2, Bootstrap Icons

## Global Constraints

- Do not break existing Flask form actions or route URLs (`url_for('dashboard.reset_db')`).
- Preserve all existing setting input fields, names, values, and default options.
- Ensure full responsiveness across desktop, tablet, and mobile viewports.

---

### Task 1: Add Custom Soft UI Settings Styles to `static/css/style.css`

**Files:**
- Modify: `static/css/style.css:610-655`

**Interfaces:**
- Consumes: Design tokens from `static/css/style.css`
- Produces: CSS classes `.settings-card`, `.settings-nav`, `.settings-nav-link`, `.setting-toggle-card`, `.settings-sticky-footer`

- [ ] **Step 1: Inspect existing settings styles in `static/css/style.css`**

View lines 610-655 of `static/css/style.css`.

- [ ] **Step 2: Add upgraded Settings CSS rules**

Append/update `static/css/style.css` under `SETTINGS PAGE` section:
```css
/* ==========================================
   SETTINGS PAGE OVERHAUL (SOFT UI & HCI)
========================================== */

.settings-card {
    border-radius: 16px !important;
    border: 1px solid #eef2ff !important;
    background: #ffffff !important;
    box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05) !important;
    transition: all 0.2s ease;
}

.settings-sidebar-card {
    border-radius: 16px !important;
    border: 1px solid #eef2ff !important;
    background: #ffffff !important;
    box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05) !important;
    padding: 10px;
}

.settings-nav .settings-nav-link {
    display: flex;
    align-items: center;
    padding: 12px 18px;
    border-radius: 12px;
    color: #475569;
    font-weight: 500;
    font-size: 0.92rem;
    border: none;
    background: transparent;
    transition: all 0.2s ease;
    width: 100%;
    text-align: left;
    margin-bottom: 4px;
}

.settings-nav .settings-nav-link:hover {
    background: #f1f5f9;
    color: #0f172a;
}

.settings-nav .settings-nav-link.active {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: #ffffff !important;
    font-weight: 600;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3);
}

.setting-toggle-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 14px 18px;
    height: 100%;
    transition: all 0.2s ease;
}

.setting-toggle-card:hover {
    border-color: #cbd5e1;
    background: #f1f5f9;
}

.setting-toggle-card .form-check-input {
    cursor: pointer;
    width: 2.4em;
    height: 1.25em;
}

.settings-sticky-footer {
    position: sticky;
    bottom: 1rem;
    z-index: 10;
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 12px 20px;
    box-shadow: 0 8px 25px rgba(15, 23, 42, 0.08);
}
```

- [ ] **Step 3: Verify CSS syntax**

Ensure no missing brackets or syntax errors in `static/css/style.css`.

---

### Task 2: Refactor `templates/settings.html` to Bootstrap Tab Navigation & Proportional Grids

**Files:**
- Modify: `templates/settings.html:1-303`

**Interfaces:**
- Consumes: Jinja2 template context (`stats`)
- Produces: Overhauled Settings page with Bootstrap nav-pills, tab panes, proportional inputs, sticky footer, and confirmation modal.

- [ ] **Step 1: Write HTML markup structure for `settings.html`**

Update `templates/settings.html` with:
1. Left sidebar `<div class="nav nav-pills flex-column settings-nav" id="settings-tabs" role="tablist">`:
   - Button 1: `#tab-ocr` (OCR Engine) - `active`
   - Button 2: `#tab-folder` (Folder & Storage)
   - Button 3: `#tab-monitoring` (Monitoring)
   - Button 4: `#tab-database` (Database)
   - Button 5: `#tab-notification` (Notification)
   - Button 6: `#tab-about` (About)
2. Right container `<div class="tab-content" id="settings-tab-content">`:
   - Tab 1 Pane (`#tab-ocr`): Card with OCR Engine settings. Proportions: Language `col-md-6`, DPI `col-md-3`, Retry `col-md-3`, Searchable PDF toggle in `.setting-toggle-card`.
   - Tab 2 Pane (`#tab-folder`): Card with Folder settings. Input/Output full width with Browse button. Storage warning `col-md-6` + Auto cleanup `col-md-6`.
   - Tab 3 Pane (`#tab-monitoring`): Card with Monitoring settings. Refresh interval `col-md-6`, Toggles in grid of `.setting-toggle-card`.
   - Tab 4 Pane (`#tab-database`): Card with Database settings. DB path input, Backup button, Export CSV button, Reset History button triggering `#resetHistoryModal`.
   - Tab 5 Pane (`#tab-notification`): Card with Notification settings. Toggles wrapped in `.setting-toggle-card`.
   - Tab 6 Pane (`#tab-about`): Card with About info. Grid of `.setting-info-item`.
3. Sticky Footer Bar at the bottom of the right column:
   - `<div class="settings-sticky-footer d-flex justify-content-between align-items-center mt-4">`
   - Left side: small info text (`<small class="text-muted"><i class="bi bi-info-circle me-1"></i> Changes apply system-wide</small>`)
   - Right side: `<button type="reset" class="btn btn-outline-secondary btn-sm px-4 me-2">Reset</button>` and `<button type="submit" class="btn btn-primary btn-sm px-4"><i class="bi bi-floppy me-1"></i> Save Settings</button>`.
4. Confirmation Modal (`#resetHistoryModal`):
   - Centered modal with clean icon, warning message, Cancel button (`data-bs-dismiss="modal"`), and submit form pointing to `{{ url_for('dashboard.reset_db') }}`.

- [ ] **Step 2: Save updated `templates/settings.html`**

- [ ] **Step 3: Verification via Python / HTTP render test**

Run a Python check using `.\env\Scripts\python.exe` to parse `templates/settings.html` with Jinja2 and ensure no syntax or template compilation errors occur.
