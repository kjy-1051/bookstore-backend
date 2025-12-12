def test_admin_dashboard_success(client, admin_token):
    res = client.get(
        "/admin/dashboard/stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200


def test_admin_dashboard_forbidden(client, user_token):
    res = client.get(
        "/admin/dashboard/stats",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert res.status_code == 403


def test_admin_users_list(client, admin_token):
    res = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
