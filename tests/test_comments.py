def test_comment_create_unauthorized(client):
    res = client.post("/comments", json={
        "book_id": 1,
        "content": "hello"
    })
    assert res.status_code == 401


def test_comment_create_success(client, user_token):
    res = client.post(
        "/comments",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"book_id": 1, "content": "good book"}
    )
    assert res.status_code in [200, 201]


def test_comment_list(client):
    res = client.get("/comments?book_id=1")
    assert res.status_code == 200


def test_comment_update_forbidden(client, user_token):
    res = client.patch(
        "/comments/9999",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"content": "hack"}
    )
    assert res.status_code in [403, 404]
