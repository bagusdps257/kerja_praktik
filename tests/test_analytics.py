import pytest
from services.system_service import format_size, hitung_ukuran_folder, get_hardware_metrics
from services.analytics_service import _safe_float

def test_system_service_metrics():
    # Format size tests
    assert format_size(0) == "0.00 B"
    assert format_size(1024) == "1.00 KB"
    assert format_size(1024 * 1024) == "1.00 MB"
    assert format_size(1024 * 1024 * 1024) == "1.00 GB"

    # Hardware metrics
    hw = get_hardware_metrics('.')
    assert "cpu_usage" in hw
    assert "memory_usage" in hw
    assert "disk_used_percent" in hw
    assert isinstance(hw["cpu_usage"], int)

def test_safe_float_helper():
    assert _safe_float("12.34") == 12.34
    assert _safe_float(5) == 5.0
    assert _safe_float(None) == 0.0
    assert _safe_float("invalid") == 0.0
