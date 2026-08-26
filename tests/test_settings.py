import pytest
from services.settings_service import load_settings, save_settings, resolve_tesseract_cmd

def test_settings_load_and_save():
    # Load default or existing settings
    current = load_settings()
    assert isinstance(current, dict)
    assert "dpi_render" in current
    assert "max_retry" in current

    # Save with out-of-bound values to verify automatic clamping
    payload = current.copy()
    payload["dpi_render"] = 9999  # Should clamp to 600
    payload["max_retry"] = -5     # Should clamp to 1
    payload["storage_warning"] = 150 # Should clamp to 95

    saved = save_settings(payload)
    assert saved["dpi_render"] == 600
    assert saved["max_retry"] == 1
    assert saved["storage_warning"] == 95

    # Restore sensible defaults
    payload["dpi_render"] = 150
    payload["max_retry"] = 5
    payload["storage_warning"] = 85
    save_settings(payload)
