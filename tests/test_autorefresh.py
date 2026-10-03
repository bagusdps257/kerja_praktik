import os
import pytest
from models.extensions import db
from models.user_model import UserModel
from models.dashboard_model import Riwayat

def test_api_status_structure(client, app, test_user):
    client.post("/login", data={
        "username": "admin_test",
        "password": "password123"
    }, follow_redirects=True)

    with app.app_context():
        r = Riwayat(nama_file='Document_Report_01.pdf', status='SUKSES', keterangan='OCR Berhasil')
        db.session.add(r)
        db.session.commit()

    res = client.get('/api/status')
    assert res.status_code == 200
    data = res.get_json()
    assert 'stats' in data
    assert 'recent_files' in data
    assert len(data['recent_files']) >= 1
    assert data['recent_files'][0]['nama_file'] == 'Document_Report_01.pdf'

def test_index_html_contains_autorefresh_elements(client, app, test_user):
    client.post("/login", data={
        "username": "admin_test",
        "password": "password123"
    }, follow_redirects=True)

    res = client.get('/')
    assert res.status_code == 200
    html = res.data.decode('utf-8')

    # Verify refresh.js script is loaded for background auto-refresh
    assert 'refresh.js' in html
    # Verify unnecessary badges are removed per user specification
    assert 'Auto-refresh Aktif' not in html
    assert 'Unit Cilamaya' not in html

    # Must contain KPI and distribution elements
    assert 'id="stat-total-input"' in html
    assert 'id="stat-success"' in html
    assert 'id="stat-failed"' in html
    assert 'id="stat-pending"' in html
    assert 'id="distributionChart"' in html
    assert 'id="distribution-rate-text"' in html
    assert 'id="recent-files-body"' in html

    # Must contain progress elements
    assert 'id="progress-bar"' in html
    assert 'id="progress-persen"' in html
    assert 'id="progress-status"' in html

def test_refresh_js_has_escape_html():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    refresh_js_path = os.path.join(base_dir, 'static', 'js', 'refresh.js')
    with open(refresh_js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'function escapeHtml' in content or 'const escapeHtml' in content, (
        "refresh.js must define escapeHtml function to prevent ReferenceError when rendering recent files"
    )
