# Fix Dashboard Flickering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the dashboard flickering bug caused by out-of-sync folder state across multi-worker setups.

**Architecture:** Force the `OCRDashboardModel` to dynamically fetch the latest `input_dir` and `output_dir` from the central configuration (`user_settings.json`) at the start of the `ambil_statistik` method.

**Tech Stack:** Python, Flask

## Global Constraints

- Must rely on `services.settings_service.load_settings` for fetching the settings.
- Do not reset or wipe database records.
- Preserve existing logic for file size and page counts.

---

### Task 1: Update dashboard_model.py

**Files:**
- Modify: `models/dashboard_model.py`

**Interfaces:**
- Consumes: `services.settings_service.load_settings()`
- Produces: Updated `self.input_dir` and `self.output_dir` in `ambil_statistik()`

- [ ] **Step 1: Write the failing test / manual verification plan**

Run the app locally and verify the flickering happens when changing folders.
Since this is a Flask worker state issue, a programmatic unit test is complex, so we rely on manual verification after the change.

- [ ] **Step 2: Write minimal implementation**

Modify `models/dashboard_model.py`. Find the `ambil_statistik` method and add the settings fetch right at the beginning (before it queries the DB).

```python
    def ambil_statistik(self, force_refresh=False):
        import time
        from services.settings_service import load_settings
        
        # --- NEW CODE: Fetch dynamic settings ---
        settings = load_settings()
        self.input_dir = settings.get("input_dir", self.input_dir)
        self.output_dir = settings.get("output_dir", self.output_dir)
        # --- END NEW CODE ---

        now = time.time()
        if not force_refresh and hasattr(self, '_stats_cache') and self._stats_cache and hasattr(self, '_stats_cache_time') and (now - self._stats_cache_time < 1.5):
            return self._stats_cache
            
        # ... rest of the existing code remains unchanged ...
```

- [ ] **Step 3: Run app to verify fix**

```bash
# Run the flask app
flask run
```
Expected: Changing the folder in the UI immediately applies, and the dashboard stops flickering.

- [ ] **Step 4: Commit**

```bash
git add models/dashboard_model.py
git commit -m "fix(dashboard): resolve folder flickering by dynamically resolving input_dir from settings"
```
