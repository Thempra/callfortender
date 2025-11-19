# scraper/__init__.py

from .scraper import WebScraper


# scraper/config.py

import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    BASE_URL: str = "https://example.com"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    POSTGRES_DB: str = "scraper_db"
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    class Config:
        env_file = ".env"

settings = Settings()


# scraper/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import settings

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """
    Dependency to get the database session.

    Yields:
        AsyncSession: The database session.
    """
    async with AsyncSessionLocal() as session:
        yield session


# scraper/models.py

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(255), unique=True, nullable=False)


# scraper/scraper.py

import logging
from typing import List, Dict
import aiohttp
from bs4 import BeautifulSoup
from .config import settings
from .database import get_db
from .models import Article
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, base_url: str):
        """
        Initialize the WebScraper with a base URL.

        Args:
            base_url (str): The base URL to scrape.
        """
        self.base_url = base_url

    async def fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from a given URL.

        Args:
            url (str): The URL to fetch.

        Returns:
            str: The HTML content of the page.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"Failed to fetch {url}: Status code {response.status}")
                    raise Exception(f"Failed to fetch {url}")

    def parse_html(self, html: str) -> List[Dict[str, str]]:
        """
        Parse HTML content and extract article data.

        Args:
            html (str): The HTML content to parse.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing article data.
        """
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        for item in soup.find_all('article'):
            title = item.find('h2').get_text(strip=True)
            content = item.find('p').get_text(strip=True)
            url = item.find('a')['href']
            articles.append({'title': title, 'content': content, 'url': url})
        return articles

    async def scrape_articles(self) -> List[Article]:
        """
        Scrape articles from the base URL and save them to the database.

        Returns:
            List[Article]: A list of scraped Article objects.
        """
        html = await self.fetch_html(self.base_url)
        article_data = self.parse_html(html)
        articles = [Article(**data) for data in article_data]
        async with get_db() as session:
            session.add_all(articles)
            await session.commit()
            return articles