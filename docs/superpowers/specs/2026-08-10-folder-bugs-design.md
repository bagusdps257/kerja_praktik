# Fix Folder Selection Bugs

## Purpose
Address two specific bugs related to folder selection:
1. The page doesn't refresh automatically in all scenarios after a folder is selected/changed.
2. Typing an invalid path or deleting a character in the input field inadvertently creates a new, empty folder on the system instead of rejecting the input.

## Approach

### 1. Backend Fix (`routes/folder.py`)
- Differentiate between `input_dir` and `output_dir`.
- For `input_dir`: We must **validate** that the folder actually exists using `os.path.isdir()`. If it doesn't exist, return a `400 Bad Request` error. We should never automatically create an input folder because it's supposed to contain existing documents.
- For `output_dir`: We can keep `os.makedirs()` since it's normal to create a non-existent folder to save results.

### 2. Frontend Fix (`static/js/folder.js`)
- Update the `change` event listener (which triggers when a user manually edits the text input).
- If the API returns success (`res.ok`), we must call `window.location.reload()` so the dashboard refreshes and immediately calculates the new folder size/metrics. If it fails (e.g., folder not found), we revert or show an alert.

## Constraints & Trade-offs
- Calling `window.location.reload()` forces a full page refresh, which is currently the intended behavior to update all stats cards. 
- Bad inputs will be rejected instead of blindly polluting the file system with misspelled folders.
