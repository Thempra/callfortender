# scraper/__init__.py
from .scraper import WebScraper

# scraper/scraper.py
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    """
    A class to handle web scraping operations.
    """

    def __init__(self, base_url: str):
        """
        Initialize the WebScraper with a base URL.

        :param base_url: The base URL of the website to scrape.
        """
        self.base_url = base_url

    async def fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from a given URL.

        :param url: The URL to fetch HTML from.
        :return: The HTML content as a string.
        :raises Exception: If the request fails.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            raise

    async def parse_html(self, html: str) -> List[Dict[str, str]]:
        """
        Parse HTML content to extract relevant data.

        :param html: The HTML content to parse.
        :return: A list of dictionaries containing extracted data.
        """
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        for item in soup.find_all('div', class_='item'):
            title = item.find('h2').get_text(strip=True)
            link = item.find('a')['href']
            items.append({'title': title, 'link': link})
        return items

    async def scrape(self) -> List[Dict[str, str]]:
        """
        Scrape the website and extract data.

        :return: A list of dictionaries containing extracted data.
        """
        try:
            html = await self.fetch_html(self.base_url)
            data = await self.parse_html(html)
            return data
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            raise

# scraper/tests/test_scraper.py
import pytest
from unittest.mock import patch, MagicMock
from ..scraper import WebScraper

@pytest.fixture
def mock_response():
    """
    Create a mock response for testing.
    """
    mock = MagicMock()
    mock.status_code = 200
    mock.text = '<html><body><div class="item"><h2>Title</h2><a href="/link">Link</a></div></body></html>'
    return mock

@pytest.fixture
def scraper():
    """
    Create a WebScraper instance for testing.
    """
    return WebScraper('http://example.com')

@patch('requests.get')
async def test_fetch_html(mock_get, mock_response, scraper):
    """
    Test the fetch_html method of WebScraper.
    """
    mock_get.return_value = mock_response
    html = await scraper.fetch_html('http://example.com')
    assert html == mock_response.text

@patch.object(WebScraper, 'fetch_html', return_value='<html><body><div class="item"><h2>Title</h2><a href="/link">Link</a></div></body></html>')
async def test_parse_html(mock_fetch_html, scraper):
    """
    Test the parse_html method of WebScraper.
    """
    data = await scraper.parse_html('<html><body><div class="item"><h2>Title</h2><a href="/link">Link</a></div></body></html>')
    assert data == [{'title': 'Title', 'link': '/link'}]

@patch.object(WebScraper, 'fetch_html', return_value='<html><body><div class="item"><h2>Title</h2><a href="/link">Link</a></div></body></html>')
async def test_scrape(mock_fetch_html, scraper):
    """
    Test the scrape method of WebScraper.
    """
    data = await scraper.scrape()
    assert data == [{'title': 'Title', 'link': '/link'}]