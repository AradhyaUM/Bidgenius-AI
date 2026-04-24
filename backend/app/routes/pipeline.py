from fastapi import APIRouter
from pydantic import BaseModel
from app.services.pipeline import run_pipeline

router = APIRouter()


class RequestModel(BaseModel):
    keyword: str
    region: str


@router.post("/run")
def run(req: RequestModel):
    return run_pipeline(req.keyword, req.region)