# Header Icons Visual Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize page headers across `index.html`, `documents.html`, and `monitoring.html` by adding Bootstrap Icons matching `analytics.html` and `settings.html`.

**Architecture:** Update `<h1>` title elements in the 3 target template files with `<i class="bi ... me-2" style="color:#6366f1;"></i>`.

**Tech Stack:** HTML5, Jinja2, Bootstrap Icons 1.11.3

## Global Constraints

- Preserve existing `<h1>` text content verbatim.
- Maintain existing wrapper `div` classes (`page-header mb-4`, `d-flex justify-content-between`, etc.).

---

### Task 1: Add Header Icons to `index.html`, `documents.html`, and `monitoring.html`

**Files:**
- Modify: `templates/index.html:8-12`
- Modify: `templates/documents.html:9-12`
- Modify: `templates/monitoring.html:9-12`

**Interfaces:**
- Consumes: Bootstrap Icons CSS
- Produces: Visual header icons across all main pages.

- [ ] **Step 1: Update `templates/index.html`**

Replace lines 8-12 in `templates/index.html`:
```html
<div class="page-header mb-4">
    <h1 class="page-title mb-1">
        <i class="bi bi-grid-1x2 me-2" style="color:#6366f1;"></i>System Overview
    </h1>
    <p class="page-subtitle">
        Real-time metrics for document processing and intelligent routing.
    </p>
</div>
```

- [ ] **Step 2: Update `templates/documents.html`**

Replace lines 9-12 in `templates/documents.html`:
```html
    <div>
        <h1 class="page-title mb-1">
            <i class="bi bi-folder2-open me-2" style="color:#6366f1;"></i>Documents Management
        </h1>
        <p class="page-subtitle mb-0">
            Search, filter, and manage processed OCR documents.
        </p>
    </div>
```

- [ ] **Step 3: Update `templates/monitoring.html`**

Replace lines 9-14 in `templates/monitoring.html`:
```html
    <div>
        <h1 class="page-title mb-1">
            <i class="bi bi-activity me-2" style="color:#6366f1;"></i>OCR Monitoring
        </h1>
        <p class="page-subtitle mb-0">
            Real-time OCR engine status, processing queue, and live terminal logs.
        </p>
    </div>
```

- [ ] **Step 4: Verify template rendering**

Run Python script to verify Jinja template rendering for `index.html`, `documents.html`, and `monitoring.html`.
