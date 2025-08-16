import re
from bs4 import BeautifulSoup
from app.models.brand import SocialHandles

def extract_emails(html: str):
    # Simple regex for emails
    return list(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", html or "")))

def extract_phones(html: str):
    # Simple regex for Indian/Intl phone numbers (very basic)
    return list(set(re.findall(r"\b(?:\+?91)?[6-9][0-9]{9}\b", html or "")))

def extract_social_links(html: str):
    soup = BeautifulSoup(html, "html.parser")
    social = SocialHandles()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "instagram.com" in href:
            social.instagram = href
        elif "facebook.com" in href:
            social.facebook = href
        elif "tiktok.com" in href:
            social.tiktok = href
        elif "twitter.com" in href or "x.com" in href:
            social.twitter = href
    return social