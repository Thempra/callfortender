import pytest
from unittest.mock import AsyncMock, patch
from aiohttp import ClientResponseError
from bs4 import BeautifulSoup
from scraper.scraper import WebScraper
from scraper.config import settings
from scraper.models import Article
from sqlalchemy.ext.asyncio import AsyncSession

# Fixtures
@pytest.fixture
def mock_aiohttp_session():
    session = AsyncMock()
    response = AsyncMock()
    response.status = 200
    response.text.return_value = "<html><body><h1>Title</h1><p>Content</p></body></html>"
    session.get.return_value.__aenter__.return_value = response
    return session

@pytest.fixture
def scraper(mock_aiohttp_session):
    with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
        yield WebScraper()

@pytest.fixture
async def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    return session

# Tests de funcionalidad básica
def test_fetch_page_success(scraper, mock_aiohttp_session):
    url = "http://example.com"
    content = scraper.fetch_page(url)
    assert content == "<html><body><h1>Title</h1><p>Content</p></body></html>"
    mock_aiohttp_session.get.assert_called_once_with(url)

def test_parse_content_success(scraper):
    html_content = "<html><body><h1>Title</h1><p>Content</p></body></html>"
    soup = BeautifulSoup(html_content, 'html.parser')
    title, content = scraper.parse_content(soup)
    assert title == "Title"
    assert content == "Content"

def test_save_article_success(mock_db_session):
    article = Article(title="Test Title", content="Test Content")
    WebScraper.save_article(article, mock_db_session)
    mock_db_session.add.assert_called_once_with(article)
    mock_db_session.commit.assert_called_once()

# Tests de edge cases
def test_fetch_page_empty_url(scraper):
    url = ""
    with pytest.raises(ValueError) as excinfo:
        scraper.fetch_page(url)
    assert str(excinfo.value) == "URL cannot be empty"

def test_parse_content_no_title(scraper):
    html_content = "<html><body><p>Content</p></body></html>"
    soup = BeautifulSoup(html_content, 'html.parser')
    title, content = scraper.parse_content(soup)
    assert title is None
    assert content == "Content"

def test_parse_content_no_content(scraper):
    html_content = "<html><body><h1>Title</h1></body></html>"
    soup = BeautifulSoup(html_content, 'html.parser')
    title, content = scraper.parse_content(soup)
    assert title == "Title"
    assert content is None

# Tests de manejo de errores
def test_fetch_page_client_error(scraper, mock_aiohttp_session):
    url = "http://example.com"
    response = AsyncMock()
    response.status = 404
    response.text.return_value = "Not Found"
    mock_aiohttp_session.get.return_value.__aenter__.return_value = response
    with pytest.raises(ClientResponseError) as excinfo:
        scraper.fetch_page(url)
    assert excinfo.value.status == 404

def test_parse_content_invalid_html(scraper):
    html_content = "<html><body><h1>Title</h1></p>Content</p></body></html>"
    soup = BeautifulSoup(html_content, 'html.parser')
    title, content = scraper.parse_content(soup)
    assert title == "Title"
    assert content is None

def test_save_article_none(mock_db_session):
    article = None
    with pytest.raises(ValueError) as excinfo:
        WebScraper.save_article(article, mock_db_session)
    assert str(excinfo.value) == "Article cannot be None"