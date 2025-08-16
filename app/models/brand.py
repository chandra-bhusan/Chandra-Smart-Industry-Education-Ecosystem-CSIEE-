from typing import List, Optional, Dict
from pydantic import BaseModel

class FAQ(BaseModel):
    question: str
    answer: str

class SocialHandles(BaseModel):
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    tiktok: Optional[str] = None
    twitter: Optional[str] = None

class ContactDetails(BaseModel):
    emails: List[str] = []
    phones: List[str] = []

class ImportantLinks(BaseModel):
    order_tracking: Optional[str] = None
    contact_us: Optional[str] = None
    blog: Optional[str] = None

class BrandInsights(BaseModel):
    brand_name: Optional[str]
    products: list
    hero_products: list
    privacy_policy: Optional[str]
    refund_policy: Optional[str]
    return_policy: Optional[str]
    faqs: List[FAQ] = []
    social_handles: Optional[SocialHandles]
    contact_details: ContactDetails
    about: Optional[str]
    important_links: Optional[ImportantLinks]