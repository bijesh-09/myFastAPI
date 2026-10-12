from app import pydantic_schemas
import pytest

# -------------------------------------------------------get all posts----------------------------------------------------------------

#happy path
def test_get_all_posts(set_of_users_fixture, client, auth_headers, create_posts_fixture):
    res = client.get('/posts/', headers=auth_headers(set_of_users_fixture[0]['id'])) # trying only for 1st user
    for p in res.json(): 
        pydantic_schemas.PostWithVotes(**p)
    print(res.json())
    assert res.status_code == 200

@pytest.mark.parametrize("case, detail",[
    ("garbage",     "Could not validate credentials"),
    ("empty",       "Not authenticated"),
    ("none",        "Not authenticated"),
    ("ghost_user",  "Could not validate credentials"),
])

#auth
def test_unauthenticated_get_all_posts(create_posts_fixture, client, case, detail, auth_headers):
    lookup = {
        "garbage":    {"Authorization": "Bearer garbage"},
        "empty":      {"Authorization": ""},
        "none":       {},
        "ghost_user": auth_headers(100000000), #user with id 1billion 
    }
    headers_case = lookup[case] #its like dict_name['key_name'] but here parametrize fills up these vars in each test
    res = client.get('/posts/', headers=headers_case)
    print(res.json())
    assert res.status_code == 401
    assert res.json()['detail'] == detail

# -------------------------------------------------------------------------------------------------------------------------------------

# ------------------------------------------------------------get one post-----------------------------------------------------------

#happy path
def test_get_one_post(authenticated_client, create_posts_fixture):
    res = authenticated_client.get(f'/posts/{create_posts_fixture[0]['id']}')
    print(res.json())
    post = pydantic_schemas.PostWithVotes(**res.json())
    assert res.status_code == 200
    
    assert post.Post.id == create_posts_fixture[0]['id']
    assert post.Post.title == create_posts_fixture[0]['title']
    assert post.Post.content == create_posts_fixture[0]['content']

#auth
@pytest.mark.parametrize("case, detail",[
    ("garbage",     "Could not validate credentials"),
    ("empty",       "Not authenticated"),
    ("none",        "Not authenticated"),
    ("ghost_user",  "Could not validate credentials"),
])
def test_unauthenticated_get_one_post(create_posts_fixture, client, case, detail, auth_headers):
    lookup = {
        "garbage":    {"Authorization": "Bearer garbage"},
        "empty":      {"Authorization": ""},
        "none":       {},
        "ghost_user": auth_headers(100000000), #user with id 1billion 
    }
    headers_case = lookup[case] #its like dict_name['key_name'] but here parametrize fills up these vars in each test
    res = client.get(f'/posts/{create_posts_fixture[0]['id']}', headers=headers_case)
    print(res.json())
    assert res.status_code == 401
    assert res.json()['detail'] == detail

#not found
def test_get_one_post_not_exist(authenticated_client, create_posts_fixture):
    res = authenticated_client.get('/posts/1000000')
    print(res.json())
    assert res.status_code == 404
    assert res.json()['detail'] == f"Post with id: 1000000 was not found"

# ----------------------------------------------------------------------------------------------------------------------------------------

# --------------------------------------------------------------------create posts---------------------------------------------------------

#happy path
@pytest.mark.parametrize("title, content, published", [
    ("new title", "new content", True),
    ("another", "more content", False),
])
def test_create_post(authenticated_client, single_user_fixture, title, content, published):
    res = authenticated_client.post(
        "/posts/",
        json={"title": title, "content": content, "published": published}
    )
    assert res.status_code == 201
    post = pydantic_schemas.PostRespond(**res.json())
    assert post.title == title
    assert post.content == content
    assert post.published == published
    assert post.owner_id == single_user_fixture['id']

def test_create_post_default_published(authenticated_client):
    res = authenticated_client.post("/posts/", json={"title": "t", "content": "c"})
    assert res.status_code == 201
    assert res.json()["published"] is True

#auth
@pytest.mark.parametrize("case, detail",[
    ("garbage",     "Could not validate credentials"),
    ("empty",       "Not authenticated"),
    ("none",        "Not authenticated"),
    ("ghost_user",  "Could not validate credentials"),
])
def test_unauthenticated_create_posts(client, case, detail, auth_headers):
    lookup = {
        "garbage":    {"Authorization": "Bearer garbage"},
        "empty":      {"Authorization": ""},
        "none":       {},
        "ghost_user": auth_headers(100000000), #user with id 1billion 
    }
    headers_case = lookup[case]
    res = client.post('/posts/', json={"title": "random title", "content": "random content"}, headers=headers_case)
    print(res.json())
    assert res.status_code == 401
    assert res.json()['detail'] == detail

#validation
@pytest.mark.parametrize("payload", [
    {"content": "c"},                  # missing title
    {"title": "t"},                    # missing content
    {"title": "", "content": "c"},     # empty title (only if you add min_length)
    {"title": None, "content": "c"},   # null
    {},                                # empty body
])
def test_create_post_invalid_payload(authenticated_client, payload):
    res = authenticated_client.post("/posts/", json=payload)
    assert res.status_code == 422

# ----------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------delete posts---------------------------------------------------------

#happy path
def test_delete_post(set_of_users_fixture, create_posts_fixture, client, auth_headers):
    res = client.delete(f'/posts/{create_posts_fixture[0]['id']}', headers=auth_headers(set_of_users_fixture[0]['id']))
    assert res.status_code == 204
    assert res.content == b""  # res has no body if 204 status code, b"" means empty bytes

    #checking if post is actually deleted
    res_after = client.get(f"/posts/{create_posts_fixture[0]['id']}", headers=auth_headers(set_of_users_fixture[0]['id']))
    print(res_after.json())
    assert res_after.status_code == 404
    assert res_after.json()['detail'] == f"Post with id: {create_posts_fixture[0]['id']} was not found" 

#not found
def test_delete_post_not_exist(create_posts_fixture, authenticated_client):
    res = authenticated_client.delete(f'/posts/10000000000')
    print(res.json())
    assert res.status_code == 404
    assert res.json()['detail'] == "Post with id: 10000000000 could not be deleted since its not found"

#auth
def test_delete_post_not_owner(create_posts_fixture, authenticated_client):
    res = authenticated_client.delete(f'/posts/{create_posts_fixture[0]['id']}')
    print(res.json())
    assert res.status_code == 403
    assert res.json()['detail'] == "Not authorized to perform requested action"

@pytest.mark.parametrize("case, detail",[
    ("garbage",     "Could not validate credentials"),
    ("empty",       "Not authenticated"),
    ("none",        "Not authenticated"),
    ("ghost_user",  "Could not validate credentials"),
])
def test_unauthenticated_delete_post(client, case, detail, auth_headers):
    lookup = {
        "garbage":    {"Authorization": "Bearer garbage"},
        "empty":      {"Authorization": ""},
        "none":       {},
        "ghost_user": auth_headers(100000000), #user with id 1billion 
    }
    headers_case = lookup[case]
    res = client.delete('/posts/1', headers=headers_case)
    print(res.json())
    assert res.status_code == 401
    assert res.json()['detail'] == detail

# ----------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------update posts---------------------------------------------------------

#happy path
@pytest.mark.parametrize("title, content, published", [
    ("updated hi post 1 published true", "updated high post content 2", True),
    ("updated hi post 1 published False", "updated high post content 2", False),
])
def test_update_post(set_of_users_fixture, create_posts_fixture, client, auth_headers, title, content, published):
    res = client.put(f'/posts/{create_posts_fixture[0]['id']}', 
                     json={"title": title, "content": content, "published": published},
                     headers=auth_headers(set_of_users_fixture[0]['id']))
    pydantic_schemas.PostRespond(**res.json())
    assert res.status_code == 200
    assert res.json()['id'] == create_posts_fixture[0]['id']
    assert res.json()['title'] == title
    assert res.json()['content'] == content
    assert res.json()['published'] == published

#not found
def test_update_post_not_exist(create_posts_fixture, authenticated_client):
    res = authenticated_client.put(f'/posts/10000000000', json={"title": "non exist", "content": "non exist"})
    print(res.json())
    assert res.status_code == 404
    assert res.json()['detail'] == f"post with id: 10000000000 could not be updated since its not found"

#auth
def test_update_post_not_owner(create_posts_fixture, authenticated_client):
    res = authenticated_client.put(f'/posts/{create_posts_fixture[0]['id']}',
                                   json={"title": "updated by non owner", "content": "content updated by non owner"})
    print(res.json())
    assert res.status_code == 403
    assert res.json()['detail'] == "Not authorized to perform requested action"

@pytest.mark.parametrize("case, detail",[
    ("garbage",     "Could not validate credentials"),
    ("empty",       "Not authenticated"),
    ("none",        "Not authenticated"),
    ("ghost_user",  "Could not validate credentials"),
])
def test_unauthenticated_update_post(client, case, detail, auth_headers):
    lookup = {
        "garbage":    {"Authorization": "Bearer garbage"},
        "empty":      {"Authorization": ""},
        "none":       {},
        "ghost_user": auth_headers(100000000), #user with id 1billion 
    }
    headers_case = lookup[case]
    res = client.put('/posts/1', headers=headers_case)
    print(res.json())
    assert res.status_code == 401
    assert res.json()['detail'] == detail

# ----------------------------------------------------------------------------------------------------------------------------------------