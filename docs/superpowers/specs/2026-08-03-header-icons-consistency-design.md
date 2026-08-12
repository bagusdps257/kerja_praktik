# Header Icons Visual Consistency Design

## 1. Overview & Goal
The main page titles across the application exhibited visual inconsistency: while `Analytics` and `Settings` featured styled Bootstrap Icons in their `<h1>` page headers, `Dashboard`, `Documents`, and `OCR Monitoring` lacked header icons.

The goal of this design is to harmonize all 5 main page headers across the application by adding standardized Bootstrap Icons (`color:#6366f1; me-2`) next to `<h1>` titles in `index.html`, `documents.html`, and `monitoring.html`.

## 2. Architecture & File Scope
- `templates/index.html`: Update header to include `<i class="bi bi-grid-1x2 me-2" style="color:#6366f1;"></i>`.
- `templates/documents.html`: Update header to include `<i class="bi bi-folder2-open me-2" style="color:#6366f1;"></i>`.
- `templates/monitoring.html`: Update header to include `<i class="bi bi-activity me-2" style="color:#6366f1;"></i>`.

## 3. Specification Matrix

| Page | File | Title | Icon | Color & Spacing |
| :--- | :--- | :--- | :--- | :--- |
| Dashboard | `templates/index.html` | System Overview | `bi bi-grid-1x2` | `style="color:#6366f1;" class="me-2"` |
| Documents | `templates/documents.html` | Documents Management | `bi bi-folder2-open` | `style="color:#6366f1;" class="me-2"` |
| OCR Monitoring | `templates/monitoring.html` | OCR Monitoring | `bi bi-activity` | `style="color:#6366f1;" class="me-2"` |
| Analytics | `templates/analytics.html` | Analytics Overview | `bi bi-bar-chart-line` | `style="color:#6366f1;" class="me-2"` |
| Settings | `templates/settings.html` | System Settings | `bi bi-gear-wide-connected` | `style="color:#6366f1;" class="me-2"` |

## 4. Verification & Testing Plan
- Test template rendering for `index.html`, `documents.html`, `monitoring.html`, `analytics.html`, and `settings.html` using Flask Jinja test rendering to ensure no template syntax errors exist.
- Verify visual consistency across all endpoints in browser testing.
