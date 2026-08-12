# Task 2 Report: Storage Metrics

## Executive Summary
Task 2 has been successfully implemented. The temporary placeholder values for storage metrics in `ambil_data_analitik()` have been replaced with real disk usage calculations and folder size scans.

## Implementation Details
1. **Disk Usage Metrics**:
   - `shutil.disk_usage` scans disk partition hosting `output_dir` (or fallback `.`).
   - Calculates `storage_total_gb`, `storage_used_gb`, `storage_used_percent`, and `storage_free_formatted`.
   - Exception handling ensures safe defaults (`0`, `0.0`, `"0 B"`) if disk access fails.

2. **Folder Size Metrics**:
   - `output_size_formatted`: Scans `output_dir` size using `self.hitung_ukuran_folder()` and formats with `self.format_size()`.
   - `log_size_formatted`: Scans log folder (`log_dir` derived from `self.log_path`) using `self.hitung_ukuran_folder()` and formats with `self.format_size()`.

## Verification & Testing
- Unit test created: `scratch/test_analytics_task2.py`
- Executed unit test with mock disk usage and mocked folder sizes.
- Verified initial test failure against hardcoded 0 placeholders.
- Verified test pass after implementation.
- Ran existing `test_analytics_task1.py` to ensure no regressions.

## Commits
- `648674a`: feat: add real storage metrics to analytics data

## Verification Logs
```
.
----------------------------------------------------------------------
Ran 1 test in 0.075s

OK
```

---

# Task 2 Fix Report: Storage Metrics (Resumed)

## Executive Summary
Addressed reviewer findings regarding `hitung_ukuran_folder()` path safety and `None` value handling across storage metric calculations.

## Fix Details
1. **Unprotected `hitung_ukuran_folder()` and `baca_log_terbaru()`**:
   - Updated `hitung_ukuran_folder(direktori)` to return `0` immediately if `direktori` is `None` or falsy, and wrapped directory traversal in a `try...except Exception` block.
   - Updated `baca_log_terbaru(batas=20)` to verify `self.log_path and os.path.exists(self.log_path)` before calling `os.path.exists`.

2. **Unsafe `None` Path Check & Exception Protection in `ambil_data_analitik()`**:
   - Replaced `self.output_dir if os.path.exists(self.output_dir) else '.'` with `self.output_dir if (self.output_dir and os.path.exists(self.output_dir)) else '.'`.
   - Updated `log_dir` calculation to `(os.path.dirname(self.log_path) or ".") if self.log_path else None` so `self.log_path = None` safely evaluates to `None` (yielding `0.00 B`) rather than defaulting to scanning the entire current working directory (`"."`).
   - Wrapped individual calls to `hitung_ukuran_folder` for `output_dir` and `log_dir` in separate `try...except` blocks, defaulting to `"0 B"` if any exception occurs.

## Verification & Testing
- Updated `scratch/test_analytics_task2.py` with 2 new unit test cases:
  1. `test_storage_metrics_none_paths`: Verifies `self.output_dir = None` and `self.log_path = None` do not raise `TypeError` and return `"0.00 B"`.
  2. `test_storage_metrics_hitung_ukuran_folder_exception`: Verifies `hitung_ukuran_folder` raising an `Exception` is safely caught without dropping analytics data.
- Ran tests prior to fix to verify failure (reproduced `TypeError` and unhandled exception).
- Re-ran tests after fix to verify all 3 test cases pass cleanly.
- Re-ran `test_analytics_task1.py` to confirm zero regressions.

## Verification Logs
```
...
----------------------------------------------------------------------
Ran 3 tests in 0.344s

OK
```
