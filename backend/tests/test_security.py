from app.core.security import hash_password, sign_session, verify_password, verify_session


def test_password_hash_and_verify():
    h = hash_password("s3cret")
    assert h != "s3cret"
    assert verify_password("s3cret", h)
    assert not verify_password("wrong", h)


def test_session_sign_and_verify():
    token = sign_session({"account_id": 1, "role": "seller"})
    data = verify_session(token)
    assert data["account_id"] == 1
    assert data["role"] == "seller"


def test_session_rejects_tampered_token():
    token = sign_session({"account_id": 1, "role": "seller"})
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
    assert verify_session(tampered) is None
