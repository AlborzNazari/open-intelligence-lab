from fastapi import FastAPI
from api.intelligence.router import router as intelligence_router

app = FastAPI()
app.include_router(intelligence_router)

