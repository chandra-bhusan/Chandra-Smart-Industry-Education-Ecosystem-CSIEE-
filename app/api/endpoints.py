from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl
from app.core.scraping import ShopifyScraper
from app.models.brand import BrandInsights

router = APIRouter()

class WebsiteRequest(BaseModel):
    website_url: HttpUrl

@router.post("/brand-insights/", response_model=BrandInsights)
async def get_brand_insights(payload: WebsiteRequest):
    try:
        scraper = ShopifyScraper(str(payload.website_url))
        brand_data = await scraper.scrape_all()
        if brand_data is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Website not found")
        return brand_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))