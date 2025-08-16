import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_invalid_url():
    response = client.post("/brand-insights/", json={"website_url": "https://notarealshopifystore12345.com"})
    assert response.status_code in (401, 500)

def test_valid_shopify():
    response = client.post("/brand-insights/", json={"website_url": "https://memy.co.in"})
    assert response.status_code == 200
    data = response.json()
    assert "brand_name" in data
    assert "products" in data