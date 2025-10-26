import json
import os

from fastapi import APIRouter
from schemas.keygen_schema import KeygenRequest, KeygenResponse
from services.security import generate_api_key, hash_api_key

router = APIRouter()


@router.get("/keygen", response_model=KeygenResponse)
async def keygen_endpoint(body: KeygenRequest):
    """
    Endpoint to generate and return a new API key.
    """
    new_api_key = generate_api_key()
    hashed_key = hash_api_key(new_api_key)

    if os.path.exists("json_db.json"):
        with open("json_db.json", "r") as f:
            db = json.load(f)
    else:
        db = {}

    db.setdefault("api_keys", []).append(hashed_key)

    with open("json_db.json", "w") as f:
        json.dump(db, f, indent=4)

    return KeygenResponse(api_key=new_api_key)
