from fastapi import FastAPI
from api.intelligence.router import router as intelligence_router

app = FastAPI(title="Open Intelligence Lab API")

app.include_router(intelligence_router)
