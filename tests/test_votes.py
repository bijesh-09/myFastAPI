import pytest

#happy path
def test_vote_on_post(client, set_of_users_fixture, create_posts_fixture, auth_headers):
    res = client.post("/vote/", json={"post_id": create_posts_fixture[0]["id"], "dir": 1},
                      headers=auth_headers(set_of_users_fixture[0]["id"]))
    assert res.status_code == 201
    assert res.json()['message'] == "Successfully added vote"

def test_remove_vote_on_post(client, set_of_users_fixture, create_posts_fixture, auth_headers):
    res = client.post("/vote/", json={"post_id": create_posts_fixture[0]["id"], "dir": 1},
                      headers=auth_headers(set_of_users_fixture[0]["id"]))
    assert res.status_code == 201
    assert res.json()['message'] == "Successfully added vote"

    #tryna removing same vote
    res = client.post("/vote/", json={"post_id": create_posts_fixture[0]["id"], "dir": 0},
                          headers=auth_headers(set_of_users_fixture[0]["id"]))
    assert res.status_code == 200
    assert res.json()['message'] == "Successfully deleted vote"

#edge cases
def test_vote_twice(client, set_of_users_fixture, create_posts_fixture, auth_headers):
    res = client.post("/vote/", json={"post_id": create_posts_fixture[0]["id"], "dir": 1},
                          headers=auth_headers(set_of_users_fixture[0]["id"]))
    assert res.status_code == 201
    assert res.json()['message'] == "Successfully added vote"

    #trying to vote twice
    res = client.post("/vote/", json={"post_id": create_posts_fixture[0]["id"], "dir": 1},
                          headers=auth_headers(set_of_users_fixture[0]["id"]))
    assert res.status_code == 409
    assert res.json()['detail'] == f"User {set_of_users_fixture[0]["id"]} has already voted on post {create_posts_fixture[0]["id"]}"

def test_remove_vote_not_voted(client, set_of_users_fixture, create_posts_fixture, auth_headers):
    res = client.post("/vote/", json={"post_id": create_posts_fixture[0]["id"], "dir": 0},
                      headers=auth_headers(set_of_users_fixture[0]["id"]))
    assert res.status_code == 404
    assert res.json()['detail'] == f"User {set_of_users_fixture[0]["id"]} has not voted on post {create_posts_fixture[0]["id"]}"

#not found
def test_vote_post_not_exist(client, set_of_users_fixture, auth_headers):
    vote_payload = {"post_id": 99999, "dir": 1}
    res = client.post("/vote/", json=vote_payload, headers=auth_headers(set_of_users_fixture[0]["id"]))
    assert res.status_code == 404
    assert res.json()['detail'] == f"Post with id: {vote_payload['post_id']} does not exist"

#auth
@pytest.mark.parametrize("case, detail",[
    ("garbage",     "Could not validate credentials"),
    ("empty",       "Not authenticated"),
    ("none",        "Not authenticated"),
    ("ghost_user",  "Could not validate credentials"),
])
def test_unauthenticated_vote_on_post(create_posts_fixture, client, case, detail, auth_headers):
    lookup = {
        "garbage":    {"Authorization": "Bearer garbage"},
        "empty":      {"Authorization": ""},
        "none":       {},
        "ghost_user": auth_headers(100000000)
    }
    headers_case = lookup[case]
    res = client.post(f'/vote/', headers=headers_case)
    print(res.json())
    assert res.status_code == 401
    assert res.json()['detail'] == detail