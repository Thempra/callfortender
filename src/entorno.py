# scraper/__init__.py

from .scraper import WebScraper


# scraper/scraper.py

import logging
from typing import List, Dict
from aiohttp import ClientSession, ClientError
from bs4 import BeautifulSoup

class WebScraper:
    """
    A class to handle web scraping tasks.
    """

    def __init__(self, base_url: str):
        """
        Initialize the WebScraper with a base URL.

        :param base_url: The base URL for the website to scrape.
        """
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    async def fetch_html(self, session: ClientSession, url: str) -> str:
        """
        Fetch HTML content from a given URL using an aiohttp session.

        :param session: An aiohttp ClientSession instance.
        :param url: The URL to fetch the HTML content from.
        :return: The HTML content as a string.
        :raises ClientError: If there is an error during the HTTP request.
        """
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except ClientError as e:
            self.logger.error(f"Error fetching {url}: {e}")
            raise

    def parse_html(self, html: str) -> List[Dict[str, str]]:
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
        :raises ClientError: If there is an error during the HTTP request.
        """
        url = self.base_url
        async with ClientSession() as session:
            html = await self.fetch_html(session, url)
            return self.parse_html(html)


# scraper/utils.py

import logging

def setup_logging():
    """
    Set up basic configuration for logging.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')