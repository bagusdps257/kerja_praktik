# Design Spec: Fix Dashboard Flickering and Deploy to Linux

## 1. Overview
The dashboard currently flickers between displaying old folder stats and new folder stats when the input folder is changed. This happens because Flask worker processes hold onto the old `db_model.input_dir` in memory and do not synchronize state when one worker updates it. 

## 2. Approach
Implement a "Dynamic Folder Resolution" approach. We will force the `OCRDashboardModel` to fetch the current folder configurations from the filesystem-backed `user_settings.json` on every request to `ambil_statistik()`.

## 3. Changes Required
- **Target File**: `models/dashboard_model.py`
- **Method**: `ambil_statistik(self, force_refresh=False)`
- **Logic Addition**: 
  Import `load_settings` from `services.settings_service`.
  Fetch settings and override `self.input_dir` and `self.output_dir` before executing the stats calculation loop.

## 4. Deployment to Ubuntu Linux
After the fix is implemented and verified locally, the updated version must be moved to the Ubuntu server. 
The steps will involve:
1. Pushing changes via Git (if using version control) OR transferring the updated `dashboard_model.py` via SCP/SFTP.
2. Restarting the Flask/Gunicorn service on the Ubuntu server to apply the code changes.
3. No database reset is necessary.

## 5. Self-Review
- **Placeholders**: None.
- **Consistency**: The approach solves the multi-worker memory isolation issue by relying on the single source of truth (`user_settings.json`).
- **Scope**: Narrowly scoped to just the stat calculation method. Deployment steps are clear.
- **Ambiguity**: The deployment method will offer both Git and SCP paths based on user preference.
