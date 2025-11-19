# scraper/__init__.py

from .scraper import Scraper

# scraper/scraper.py

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Scraper:
    """
    A class to handle web scraping tasks.
    """

    def __init__(self, base_url: str):
        """
        Initialize the Scraper with a base URL.

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
            logger.error(f"Failed to fetch URL {url}: {e}")
            raise

    async def parse_html(self, html: str) -> List[Dict[str, str]]:
        """
        Parse HTML content and extract relevant data.

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
        :raises Exception: If fetching or parsing fails.
        """
        try:
            html = await self.fetch_html(self.base_url)
            return await self.parse_html(html)
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise

# scraper/tests/test_scraper.py

import pytest
from unittest.mock import patch, MagicMock
from ..scraper import Scraper

@pytest.fixture
def scraper():
    return Scraper("http://example.com")

@patch('requests.get')
async def test_fetch_html(mock_get, scraper):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body><h1>Test</h1></body></html>"
    mock_get.return_value = mock_response

    html = await scraper.fetch_html("http://example.com")
    assert html == "<html><body><h1>Test</h1></body></html>"

@patch('requests.get')
async def test_fetch_html_failure(mock_get, scraper):
    mock_get.side_effect = requests.RequestException("Failed to fetch")

    with pytest.raises(Exception) as e:
        await scraper.fetch_html("http://example.com")
    assert str(e.value) == "Failed to fetch"

def test_parse_html(scraper):
    html = "<html><body><div class='item'><h2>Title</h2><a href='/link'>Link</a></div></body></html>"
    items = scraper.parse_html(html)
    assert items == [{'title': 'Title', 'link': '/link'}]

@patch('scraper.scraper.Scraper.fetch_html')
@patch('scraper.scraper.Scraper.parse_html')
async def test_scrape(mock_parse, mock_fetch, scraper):
    mock_fetch.return_value = "<html><body><div class='item'><h2>Title</h2><a href='/link'>Link</a></div></body></html>"
    mock_parse.return_value = [{'title': 'Title', 'link': '/link'}]

    items = await scraper.scrape()
    assert items == [{'title': 'Title', 'link': '/link'}]

@patch('scraper.scraper.Scraper.fetch_html')
async def test_scrape_failure(mock_fetch, scraper):
    mock_fetch.side_effect = Exception("Scraping failed")

    with pytest.raises(Exception) as e:
        await scraper.scrape()
    assert str(e.value) == "Scraping failed"