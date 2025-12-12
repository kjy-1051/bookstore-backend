def test_books_list(client):
    res = client.get("/books")
    assert res.status_code == 200


def test_books_invalid_page(client):
    res = client.get("/books?page=0")
    assert res.status_code == 400


def test_book_detail_success(client):
    res = client.get("/books/1")
    assert res.status_code in [200, 404]


def test_book_detail_invalid_id(client):
    res = client.get("/books/abc")
    assert res.status_code == 422


def test_book_search(client):
    res = client.get("/books/search?keyword=test&page=1&size=5")
    assert res.status_code == 200


def test_book_search_invalid_size(client):
    res = client.get("/books/search?size=0")
    assert res.status_code == 400
