
def test_get_all_posts(set_of_users_fixture, client, auth_headers, create_posts_fixture):
    res = client.get('/posts/', headers=auth_headers(set_of_users_fixture[0]['id'])) # trying only for 1st user
    print(res.json())
    assert res.status_code == 200