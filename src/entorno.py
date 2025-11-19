# scraper/__init__.py
from .scraper import WebScraper

# scraper/scraper.py
import logging
from typing import List, Dict
import aiohttp
from bs4 import BeautifulSoup

class WebScraper:
    """
    A class to handle web scraping tasks.
    """

    def __init__(self, base_url: str):
        """
        Initialize the WebScraper with a base URL.

        :param base_url: The base URL of the website to scrape.
        """
        self.base_url = base_url
        self.session = None

    async def fetch(self, url: str) -> str:
        """
        Fetches the content of a given URL using aiohttp.

        :param url: The URL to fetch.
        :return: The HTML content of the page.
        :raises Exception: If an error occurs during fetching.
        """
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except aiohttp.ClientError as e:
            logging.error(f"Error fetching {url}: {e}")
            raise

    async def parse(self, html: str) -> List[Dict[str, str]]:
        """
        Parses the HTML content to extract relevant data.

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
        Orchestrates the scraping process by fetching and parsing the content.

        :return: A list of dictionaries containing scraped data.
        :raises Exception: If an error occurs during scraping.
        """
        try:
            self.session = aiohttp.ClientSession()
            html_content = await self.fetch(self.base_url)
            data = await self.parse(html_content)
            return data
        finally:
            await self.session.close()

# scraper/utils.py
import logging

def setup_logging():
    """
    Sets up basic configuration for logging.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# main.py
from fastapi import FastAPI
from scraper.scraper import WebScraper
from scraper.utils import setup_logging

setup_logging()
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """
    Event handler to initialize the web scraper on application startup.
    """
    global scraper
    scraper = WebScraper(base_url="https://example.com")

@app.get("/scrape", response_model=list)
async def scrape_data():
    """
    Endpoint to trigger the web scraping process.

    :return: A list of dictionaries containing scraped data.
    """
    try:
        data = await scraper.scrape()
        return data
    except Exception as e:
        logging.error(f"Error during scraping: {e}")
        raise

# tests/test_scraper.py
import pytest
from unittest.mock import AsyncMock, patch
from scraper.scraper import WebScraper

@pytest.fixture
async def scraper():
    """
    Fixture to create a WebScraper instance for testing.
    """
    return WebScraper(base_url="https://example.com")

@patch('aiohttp.ClientSession.get')
@pytest.mark.asyncio
async def test_fetch(mock_get, scraper):
    """
    Test the fetch method of WebScraper.
    """
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = "<html><body></body></html>"
    mock_get.return_value.__aenter__.return_value = mock_response

    content = await scraper.fetch("https://example.com")
    assert content == "<html><body></body></html>"

@patch('scraper.scraper.WebScraper.fetch')
@pytest.mark.asyncio
async def test_parse(mock_fetch, scraper):
    """
    Test the parse method of WebScraper.
    """
    mock_fetch.return_value = "<html><body><div class='item'><h2>Title</h2><a href='/link'>Link</a></div></body></html>"
    data = await scraper.scrape()
    assert data == [{'title': 'Title', 'link': '/link'}]