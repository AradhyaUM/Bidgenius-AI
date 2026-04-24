from dotenv import load_dotenv
load_dotenv()

import os, logging, traceback, sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("bidgenius.main")

from app.services.pipeline import run_pipeline, run_list_mode

app = FastAPI(title="BidGenius API")

@app.on_event("startup")
async def startup():
    logger.info("=" * 50)
    logger.info("BidGenius API started")
    logger.info(f"  TAVILY : {'set' if os.getenv('TAVILY_API_KEY') else 'MISSING'}")
    logger.info(f"  GROQ   : {'set' if os.getenv('GROQ_API_KEY') else 'MISSING'}")
    logger.info(f"  EXA    : {'set' if os.getenv('EXA_API_KEY') else 'not set (optional)'}")
    logger.info("=" * 50)


class PipelineRequest(BaseModel):
    keyword: str
    region:  str = "India"
    scope:   Optional[str] = "all"
    profile: Optional[Dict[str, Any]] = None   # company profile from frontend


class ListRequest(BaseModel):
    keyword: str
    region:  str = "India"


@app.post("/run")
@app.post("/api/run")
def run(req: PipelineRequest):
    if not req.keyword:
        raise HTTPException(400, "keyword required")
    logger.info(f"/run  keyword='{req.keyword}'  region='{req.region}'  scope='{req.scope}'")
    try:
        result = run_pipeline(
            req.keyword, req.region,
            scope=req.scope,
            company_profile=req.profile or {}
        )
        logger.info(f"/run  returning {len(result)} results")
        return result
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Pipeline crashed:\n{tb}")
        print(tb, flush=True)
        return JSONResponse(status_code=500, content={"error": str(e), "traceback": tb})


@app.post("/list")
@app.post("/api/list")
def list_tenders(req: ListRequest):
    if not req.keyword:
        raise HTTPException(400, "keyword required")
    try:
        return run_list_mode(req.keyword, req.region)
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"List mode crashed:\n{tb}")
        return JSONResponse(status_code=500, content={"error": str(e), "traceback": tb})


@app.get("/health")
@app.get("/api/health")
def health():
    import importlib
    errors = []
    for name, path in [
        ("search_agent",    "app.agents.search_agent"),
        ("reader_agent",    "app.agents.reader_agent"),
        ("extractor_agent", "app.agents.extractor_agent"),
        ("validator_agent", "app.agents.validator_agent"),
        ("analysis_agent",  "app.agents.analysis_agent"),
        ("bid_agent",       "app.agents.bid_agent"),
        ("llm_router",      "app.llm.llm_router"),
        ("pipeline",        "app.services.pipeline"),
    ]:
        try:
            importlib.import_module(path)
        except Exception as e:
            errors.append(f"{name}: {e}")
    return {
        "status": "ok" if not errors else "degraded",
        "errors": errors,
        "tavily": bool(os.getenv("TAVILY_API_KEY")),
        "groq":   bool(os.getenv("GROQ_API_KEY")),
        "exa":    bool(os.getenv("EXA_API_KEY")),
    }


@app.get("/")
@app.get("/api")
def root():
    return {"service": "BidGenius API", "status": "ok"}