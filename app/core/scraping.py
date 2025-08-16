import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from app.models.brand import BrandInsights, FAQ, SocialHandles, ContactDetails, ImportantLinks
from app.utils.helpers import extract_emails, extract_phones, extract_social_links
import re

class ShopifyScraper:
    def __init__(self, base_url: str):
        self.base_url = self._normalize_url(base_url)
        self.client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)
    
    def _normalize_url(self, url: str) -> str:
        if not url.startswith("http"):
            return "https://" + url
        return url.rstrip("/")
    
    async def fetch(self, path: str):
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        try:
            resp = await self.client.get(url)
            if resp.status_code == 200:
                return resp.text
            return None
        except Exception:
            return None
    
    async def fetch_json(self, path: str):
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        try:
            resp = await self.client.get(url)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None

    async def scrape_all(self):
        # Check if site is up
        test = await self.fetch("/")
        if not test:
            await self.client.aclose()
            return None

        # 1. Product Catalog
        products_json = await self.fetch_json("/products.json")
        products = products_json.get("products", []) if products_json else []

        # 2. Hero Products (from homepage)
        homepage_html = await self.fetch("/")
        hero_products = self._extract_hero_products(homepage_html, products)

        # 3. Policies
        privacy_policy = await self._extract_policy("privacy-policy")
        refund_policy = await self._extract_policy("refund-policy")
        return_policy = await self._extract_policy("return-policy")

        # 4. FAQs
        faqs = await self._extract_faqs()

        # 5. Social Handles and Contacts
        social_handles = extract_social_links(homepage_html)
        emails = extract_emails(homepage_html)
        phones = extract_phones(homepage_html)
        contact_details = ContactDetails(emails=emails, phones=phones)

        # 6. About/Brand Text
        about = self._extract_about(homepage_html)

        # 7. Important links
        important_links = self._extract_links(homepage_html)

        # 8. Brand Name
        brand_name = self._extract_brand_name(homepage_html)

        await self.client.aclose()
        return BrandInsights(
            brand_name=brand_name,
            products=products,
            hero_products=hero_products,
            privacy_policy=privacy_policy,
            refund_policy=refund_policy,
            return_policy=return_policy,
            faqs=faqs,
            social_handles=social_handles,
            contact_details=contact_details,
            about=about,
            important_links=important_links
        )

    def _extract_hero_products(self, homepage_html, all_products):
        soup = BeautifulSoup(homepage_html, "html.parser")
        hero_products = []
        # Heuristic: Look for products on homepage by matching product URLs or titles
        product_handles = set(p["handle"] for p in all_products)
        for a in soup.find_all("a", href=True):
            match = re.match(r"/products/([^/]+)", a["href"])
            if match and match.group(1) in product_handles:
                title = a.get_text(strip=True)
                hero_products.append({"handle": match.group(1), "title": title})
        return hero_products

    async def _extract_policy(self, policy_type):
        # Try standard Shopify policy routes
        html = await self.fetch(f"/policies/{policy_type}")
        if not html:
            html = await self.fetch(f"/pages/{policy_type.replace('-', '')}")
        if html:
            soup = BeautifulSoup(html, "html.parser")
            main = soup.find("main") or soup
            text = main.get_text(" ", strip=True)
            return text[:3000]  # Limit max length
        return None

    async def _extract_faqs(self):
        # Try FAQ page
        html = await self.fetch("/pages/faqs") or await self.fetch("/pages/faq")
        faqs = []
        if html:
            soup = BeautifulSoup(html, "html.parser")
            # Find Q/A pairs
            for q in soup.find_all(["h2", "h3", "strong"]):
                question = q.get_text(strip=True)
                next_p = q.find_next_sibling("p")
                answer = next_p.get_text(strip=True) if next_p else ""
                if len(question) > 5 and len(answer) > 2:
                    faqs.append({"question": question, "answer": answer})
            # Fallback: look for common Q/A patterns
            if not faqs:
                text = soup.get_text("\n", strip=True)
                for m in re.finditer(r'Q[:\)]\s*(.+?)\nA[:\)]\s*(.+?)(?=\nQ[:\)]|\Z)', text, re.DOTALL | re.I):
                    faqs.append({"question": m.group(1).strip(), "answer": m.group(2).strip()})
        return [FAQ(**f) for f in faqs]

    def _extract_about(self, homepage_html):
        soup = BeautifulSoup(homepage_html, "html.parser")
        about = ""
        # Try meta description
        desc = soup.find("meta", attrs={"name": "description"})
        if desc:
            about = desc.get("content", "")
        # Or look for About Us section/link
        if not about:
            for a in soup.find_all("a", href=True):
                if "about" in a["href"]:
                    about_html = self.fetch(a["href"])  # NOTE: would need to await if called
                    break
        return about

    def _extract_links(self, homepage_html):
        soup = BeautifulSoup(homepage_html, "html.parser")
        links = {}
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True).lower()
            href = urljoin(self.base_url + "/", a["href"])
            if "track" in text:
                links["order_tracking"] = href
            if "contact" in text:
                links["contact_us"] = href
            if "blog" in text:
                links["blog"] = href
        return ImportantLinks(**links)

    def _extract_brand_name(self, homepage_html):
        soup = BeautifulSoup(homepage_html, "html.parser")
        # Try <title>
        title = soup.find("title")
        if title:
            return title.get_text(strip=True)
        # Fallback: h1 in header
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        return urlparse(self.base_url).hostname.split(".")[0]