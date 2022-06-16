"""Runs unit testings."""
import requests
import pytest
import os

requests_list = [
    dict(uri=f'{os.environ["SELF_ENDPOINT"]}', method="post", data={"email_address": "test@gmail.com", "display_name": "Libby Lebyane", "password": "password2"})
]

def test_account_creation():
    data = dict(
        email_address="test@email.com",
        display_name="Test Name",
        password="password2"
    )

    r = requests.post(os.environ["SELF_ENDPOINT"], data)
    assert r.status_code == 200 or r.json()["data"]


test_account_creation()