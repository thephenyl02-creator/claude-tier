"""Legacy import support."""

import base64
import pickle


def decode_import_token(value: str):
    payload = base64.urlsafe_b64decode(value.encode("ascii"))
    return pickle.loads(payload)
