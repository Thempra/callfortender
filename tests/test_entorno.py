import pytest
from unittest.mock import patch, MagicMock
from scraper.scraper import Scraper

# Fixtures
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
    mock_get.side_effect = Exception("Failed to fetch")

    try:
        await scraper.fetch_html("http://example.com")
    except Exception as e:
        assert str(e) == "Failed to fetch"

def test_parse_html_basic(scraper):
    html_content = "<html><body><div class='item'>Test Item</div></body></html>"
    with patch.object(Scraper, 'parse_html', return_value=['Test Item']) as mock_parse:
        result = scraper.parse_html(html_content)
        assert result == ['Test Item']

# Tests de funcionalidad básica
def test_scraper_initialization():
    scraper = Scraper("http://example.com")
    assert scraper.base_url == "http://example.com"

@patch('requests.get')
async def test_scrape_data_success(mock_get, scraper):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body><div class='item'>Test Item</div></body></html>"
    mock_get.return_value = mock_response

    with patch.object(Scraper, 'parse_html', return_value=['Test Item']) as mock_parse:
        result = await scraper.scrape_data()
        assert result == ['Test Item']

# Tests de edge cases
def test_scraper_with_empty_url():
    try:
        Scraper("")
    except ValueError as e:
        assert str(e) == "Base URL cannot be empty"

@patch('requests.get')
async def test_scrape_data_with_no_items(mock_get, scraper):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body></body></html>"
    mock_get.return_value = mock_response

    with patch.object(Scraper, 'parse_html', return_value=[]) as mock_parse:
        result = await scraper.scrape_data()
        assert result == []

# Tests de manejo de errores
@patch('requests.get')
async def test_scrape_data_with_http_error(mock_get, scraper):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    try:
        await scraper.scrape_data()
    except Exception as e:
        assert str(e) == "Failed to fetch data: HTTP Error 404"

@patch('requests.get')
async def test_scrape_data_with_exception(mock_get, scraper):
    mock_get.side_effect = Exception("Network error")

    try:
        await scraper.scrape_data()
    except Exception as e:
        assert str(e) == "Failed to fetch data: Network error"