from pydantic import BaseModel


class KeygenResponse(BaseModel):
    api_key: str


class KeygenRequest(BaseModel):
    email: str
    name: str
