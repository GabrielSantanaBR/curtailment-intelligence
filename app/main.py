from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.core.config import settings
from app.core.db import Base, engine
from app.models import entities  # noqa: F401

Base.metadata.create_all(bind=engine)
app=FastAPI(title="Curtailment Intelligence API",version="0.9.0",description="Risk prediction, explainability and mitigation scenario optimization for renewable curtailment.")
app.add_middleware(CORSMiddleware,allow_origins=[settings.frontend_origin,"http://localhost:8000","http://127.0.0.1:8000"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(router)
web_dir=settings.project_root/'web'
app.mount('/static',StaticFiles(directory=web_dir),name='static')

@app.get('/health',tags=['system'])
def health(): return {"status":"ok","environment":settings.app_env}

@app.get('/',include_in_schema=False)
def dashboard(): return FileResponse(web_dir/'index.html')
