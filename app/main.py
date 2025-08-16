from fastapi import FastAPI
from app.api.endpoints import router

app = FastAPI(
    title="ChandraGenAI Shopify Insights-Fetcher",
    description="Fetches and structures brand insights from Shopify stores.",
    version="0.1.0"
)

app.include_router(router)