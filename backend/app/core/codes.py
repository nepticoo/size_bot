import secrets


def new_code() -> str:
    """An unguessable, non-sequential code for link_code / view_code."""
    return secrets.token_urlsafe(8)
