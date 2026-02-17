import subprocess

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="codereader raw API", version="1.0")

DEFAULT_CFG = "codereader.yml"

class GradeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    config_file: str | None = None  
    

class GradeResponse(BaseModel):
    output: str
    
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/grade", response_model=GradeResponse)
def grade(req: GradeRequest):
    cfg = req.config_file or DEFAULT_CFG
    if not cfg:
        raise HTTPException(
            status_code=400,
            detail="No config file provided. Set CODEREADER_CONFIG_FILE or pass config_file.",
        )

    cmd = ["codereader", "grade", "-c", cfg, "--text", req.text, "--simple"]

    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="codereader binary not found in container.")

    raw = p.stdout or ""
    if p.returncode != 0:
        raise HTTPException(status_code=500, detail=raw)

    return GradeResponse(output=raw)
