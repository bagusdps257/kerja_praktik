# Independent Folder Update

## Problem

When the user selects a folder via the "Browse" button, the JavaScript in `folder.js` sends both `input_dir` and `output_dir` to the `/update_folder` endpoint. If one of them is empty in the DOM (e.g., `output_dir` hasn't been set yet), the server-side validation `if input_dir and output_dir:` fails silently — the folder is not saved, but the page reloads as if it succeeded.

**Root cause**: The frontend couples both fields together, requiring both to be non-empty for either to be saved.

## Solution

Make each folder field (`input_dir`, `output_dir`) update independently. When the user selects a folder for one field, only that field is sent to the server and updated.

## Changes

### Frontend: `static/js/folder.js`

The `pilihFolder(idInput)` function currently sends both `input_dir` and `output_dir` via FormData. Change it to send only the field that was just selected:

- Send `field` parameter (the name of the field: `"input_dir"` or `"output_dir"`)
- Send `value` parameter (the selected folder path)
- Continue sending `csrf_token`
- Keep existing success behavior (`window.location.reload()`)
- Keep existing error handling (alert on failure)

### Backend: `routes/folder.py`

The `/update_folder` endpoint currently requires both `input_dir` and `output_dir` to be non-empty. Change it to accept a partial update:

- Accept `field` parameter (`"input_dir"` or `"output_dir"`) and `value` parameter (the folder path)
- Validate that `field` is one of the two allowed values and `value` is non-empty
- Read existing settings to preserve the other field's value
- Update `db_model` with the new value for the changed field and the existing value for the other
- Save to `user_settings.json`
- Return `redirect(url_for("dashboard.index"))` as before

### Files not changed

- `templates/partials/engine_control_section.html` — no changes needed, the `onclick="pilihFolder('input_dir')"` and `onclick="pilihFolder('output_dir')"` calls already pass the correct field identifier
- `routes/dashboard.py` — no changes
- `app.py` — no changes

## Error Handling

- If `field` is not `"input_dir"` or `"output_dir"`, return HTTP 400
- If `value` is empty, return HTTP 400
- Frontend shows alert on non-ok response (existing behavior)
