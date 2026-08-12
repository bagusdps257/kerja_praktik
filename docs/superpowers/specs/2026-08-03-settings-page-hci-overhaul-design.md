# Settings Page HCI & Soft UI Overhaul Design

## 1. Overview & Goal
The Settings page (`templates/settings.html`) currently displays all setting sections stacked vertically in a long scrollable list, while the left sidebar items resemble a tab navigation without actually toggling section visibility. Additionally, several input fields stretch awkwardly across wide viewports, and action buttons float at the bottom without clear visual context.

The goal of this overhaul is to redesign `settings.html` and update CSS in `static/css/style.css` to:
1. Implement a true Bootstrap 5 `nav-pills` & `tab-content` system so clicking a sidebar tab displays only the active section.
2. Restructure form inputs using Bootstrap grid proportions to enforce Hick's Law and Fitts's Law.
3. Add a sticky action bar for primary actions ("Save Settings" & "Reset") and implement a Bootstrap confirmation modal for destructive actions ("Reset History").
4. Harmonize the visual aesthetics with the soft UI design system (16px border-radius, soft elevation shadows, consistent typography and colors matching Analytics/Dashboard).

## 2. Architecture & File Scope
- **Templates**: `templates/settings.html` (Overhaul markup to Bootstrap tab system, grid proportions, sticky footer, and confirmation modal).
- **Styles**: `static/css/style.css` (Add `.settings-nav-link`, `.setting-toggle-card`, `.settings-sticky-footer`, `.settings-card` design tokens).
- **Routes & Controllers**: Unchanged (`routes/dashboard.py` already renders `settings.html` with necessary context).

## 3. UI/UX Component Specifications

### 3.1 Tab Navigation Architecture (Mental Model Fix)
- **Left Sidebar**: 
  - Class: `nav nav-pills flex-column settings-nav p-2 bg-white rounded-4 border`
  - Items: 6 navigation buttons corresponding to `#tab-ocr`, `#tab-folder`, `#tab-monitoring`, `#tab-database`, `#tab-notification`, `#tab-about`.
  - Active style: `.settings-nav-link.active` with soft indigo gradient background (`linear-gradient(135deg, #6366f1, #4f46e5)`), white text, and subtle elevation shadow (`0 4px 12px rgba(99, 102, 241, 0.25)`).
- **Right Container**:
  - Class: `tab-content settings-tab-content`
  - Panes: `<div class="tab-pane fade show active" id="tab-ocr">`, `<div class="tab-pane fade" id="tab-folder">`, etc.

### 3.2 Form Proportions (Hick's & Fitts's Law)
- **OCR Engine Tab (`#tab-ocr`)**:
  - Tesseract Path: `col-12` (full-width)
  - OCR Language: `col-md-6`
  - DPI Render: `col-md-3`
  - Max Retry: `col-md-3`
  - Generate Searchable PDF: Wrapped in `.setting-toggle-card` (`col-12` or `col-md-6`)
- **Folder & Storage Tab (`#tab-folder`)**:
  - Input Folder & Output Folder: `col-12` with styled `input-group` and browse buttons.
  - Storage Warning (%): `col-md-6` with percentage badge display.
  - Auto Cleanup Temporary Files: `col-md-6` in `.setting-toggle-card`.
- **Monitoring Tab (`#tab-monitoring`)**:
  - Refresh Interval: `col-md-6`
  - Enable Auto Refresh, Remember Scroll Position, Pause Refresh During Interaction: Grid of `col-md-6` cards wrapped in `.setting-toggle-card`.
- **Database & Backup Tab (`#tab-database`)**:
  - Database Location: `col-12` readonly field.
  - Action Buttons: `Backup Database` (`btn-primary btn-sm`), `Export CSV` (`btn-outline-success btn-sm`), `Reset History` (`btn-outline-danger btn-sm` with `data-bs-toggle="modal" data-bs-target="#resetHistoryModal"`).
- **Notification Tab (`#tab-notification`)**:
  - Toggles wrapped in `.setting-toggle-card` (`col-md-6` or `col-12`).
- **About System Tab (`#tab-about`)**:
  - Styled info cards (`.setting-info-item`) in a `row g-3` grid (`col-md-6` for version, framework, engine, db, `col-12` for developers).

### 3.3 Sticky Action Bar & Confirmation Modal
- **Sticky Footer Bar**:
  - Positioned at the bottom of the right column inside `.settings-sticky-footer`.
  - CSS: `position: sticky; bottom: 1rem; z-index: 10; background: rgba(255,255,255,0.9); backdrop-filter: blur(8px); border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px 20px; box-shadow: 0 4px 20px rgba(15,23,42,0.08)`.
  - Buttons: `Reset` (`btn-outline-secondary btn-sm px-4`) and `Save Settings` (`btn-primary btn-sm px-4`).
- **Reset History Confirmation Modal (`#resetHistoryModal`)**:
  - Bootstrap centered modal with warning icon, warning message, `Batal` button (`data-bs-dismiss="modal"`), and `Ya, Reset History` submit button pointing to `{{ url_for('dashboard.reset_db') }}`.

### 3.4 Visual Tokens & Styling
- Card border-radius: `16px` (`rounded-4`).
- Card shadow: `0 4px 20px -2px rgba(15, 23, 42, 0.05)`.
- Input focus rings: `#6366f1` (matching Analytics primary accent color).
- Text muted labels: `#64748b` with `.fw-semibold` input labels.

## 4. Verification & Testing Plan
1. **Navigational Verification**: Click through all 6 tabs in the left sidebar to confirm that only the active tab pane is displayed and others fade out smoothly.
2. **Form Layout Verification**: Ensure inputs resize gracefully on desktop (`1200px+`) and mobile (`<768px`) screens without awkward horizontal stretching.
3. **Modal & Action Verification**: Click `Reset History` to verify the confirmation modal opens, and test `Cancel` / `Confirm` actions.
4. **Visual Aesthetics Verification**: Verify border-radius, shadows, colors, and font styles match the Dashboard and Analytics pages.
