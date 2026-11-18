import app as server


def test_server_admin_panel_is_served():
    response = server.app.test_client().get("/admin/")
    assert response.status_code == 200
    assert b"Infrastructure overview" in response.data


def test_server_admin_assets_are_served():
    response = server.app.test_client().get("/admin/assets/admin.js")
    assert response.status_code == 200
    assert b"/health/ready" in response.data
