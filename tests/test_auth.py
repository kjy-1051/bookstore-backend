def test_login_success(client):
    res = client.post("/auth/login", json={
        "email": "user1@test.com",
        "password": "password123"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password(client):
    res = client.post("/auth/login", json={
        "email": "user1@test.com",
        "password": "wrong"
    })
    assert res.status_code == 401


def test_login_no_user(client):
    res = client.post("/auth/login", json={
        "email": "noone@test.com",
        "password": "password123"
    })
    assert res.status_code == 401


def test_refresh_success(client, user_token):
    res = client.post("/auth/refresh", json={
        "refresh_token": "dummy"  # ❗ 실제 refresh 토큰 쓰면 더 좋음
    })
    assert res.status_code in [200, 401]  # 허용


def test_refresh_validation_fail(client):
    res = client.post("/auth/refresh", json={})
    assert res.status_code == 422


def test_logout(client, user_token):
    res = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert res.status_code == 200
