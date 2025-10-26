import hashlib
import hmac
import os
import secrets

from dotenv import load_dotenv


def generate_api_key():
    return "api_" + secrets.token_hex(32)


def hash_api_key(api_key: str) -> str:
    load_dotenv()
    SERVER_SECRET = os.getenv("SERVER_SECRET").encode("utf-8")
    return hmac.new(SERVER_SECRET, api_key.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    provided_hash = hash_api_key(provided_key)
    return hmac.compare_digest(provided_hash, stored_hash)


if __name__ == "__main__":
    new_key = generate_api_key()
    print("Generated API Key:", new_key)
    hashed_key = hash_api_key(new_key)
    print("Hashed API Key:", hashed_key)
    assert verify_api_key(new_key, hashed_key)
    print("API Key verification successful.")
