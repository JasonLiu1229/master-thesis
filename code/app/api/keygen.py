import json

from fastapi import APIRouter
from schemas.keygen_schema import KeyGenRequest, KeyGenResponse
from services.security import generate_api_key, hash_api_key

router = APIRouter()


@router.get("/keygen", response_model=KeyGenResponse)
async def keygen_endpoint(body: KeyGenRequest):
    """
    Endpoint to generate and return a new API key.
    """
    new_api_key = generate_api_key()
    hashed_key = hash_api_key(new_api_key)

    with open("../json_db.json", "r") as f:
        db = json.load(f)

    db.setdefault("api_keys", []).append(hashed_key)

    with open("../json_db.json", "w") as f:
        json.dump(db, f, indent=4)

    return KeyGenResponse(api_key=new_api_key)
