import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from scraper.scraper import WebScraper
from main import app

# Fixtures
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def mock_aiohttp_session():
    session = AsyncMock()
    session.get.return_value.__aenter__.return_value.status = 200
    session.get.return_value.__aenter__.return_value.text.return_value = "<html><body><div class='item'><h2>Title</h2><a href='/link'>Link</a></div></body></html>"
    return session

@pytest.fixture
def mock_web_scraper(mock_aiohttp_session):
    scraper = WebScraper("http://example.com")
    scraper.session = mock_aiohttp_session
    return scraper

# Tests de funcionalidad básica
def test_scrape_data_success(client, mock_web_scraper):
    with patch('scraper.scraper.WebScraper', return_value=mock_web_scraper):
        response = client.get("/scrape/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['title'] == "Title"
        assert data[0]['link'] == "/link"

# Tests de edge cases
def test_scrape_data_empty_response(client, mock_web_scraper):
    mock_web_scraper.session.get.return_value.__aenter__.return_value.text.return_value = "<html><body></body></html>"
    with patch('scraper.scraper.WebScraper', return_value=mock_web_scraper):
        response = client.get("/scrape/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

# Tests de manejo de errores
def test_scrape_data_invalid_url(client, mock_aiohttp_session):
    mock_aiohttp_session.get.return_value.__aenter__.return_value.status = 404
    scraper = WebScraper("http://invalid-url.com")
    scraper.session = mock_aiohttp_session
    with patch('scraper.scraper.WebScraper', return_value=scraper):
        response = client.get("/scrape/")
        assert response.status_code == 500

def test_scrape_data_no_title(client, mock_web_scraper):
    mock_web_scraper.session.get.return_value.__aenter__.return_value.text.return_value = "<html><body><div class='item'><a href='/link'>Link</a></div></body></html>"
    with patch('scraper.scraper.WebScraper', return_value=mock_web_scraper):
        response = client.get("/scrape/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['title'] is None
        assert data[0]['link'] == "/link"

def test_scrape_data_no_link(client, mock_web_scraper):
    mock_web_scraper.session.get.return_value.__aenter__.return_value.text.return_value = "<html><body><div class='item'><h2>Title</h2></div></body></html>"
    with patch('scraper.scraper.WebScraper', return_value=mock_web_scraper):
        response = client.get("/scrape/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['title'] == "Title"
        assert data[0]['link'] is None

def test_scrape_data_no_items(client, mock_web_scraper):
    mock_web_scraper.session.get.return_value.__aenter__.return_value.text.return_value = "<html><body></body></html>"
    with patch('scraper.scraper.WebScraper', return_value=mock_web_scraper):
        response = client.get("/scrape/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0