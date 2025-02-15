import pytest
from src.ocr import TradeParser
from datetime import datetime

def test_trade_parser_initialization():
    parser = TradeParser(api_key="test_key")
    assert parser is not None

def test_parse_screenshot_with_invalid_path():
    parser = TradeParser(api_key="test_key")
    result = parser.parse_screenshot("invalid_path.jpg")
    assert result["success"] is False
    assert "error" in result

# TODO: Add more tests with actual screenshot samples
# def test_parse_screenshot_with_valid_image():
#     parser = TradeParser()
#     result = parser.parse_screenshot("tests/fixtures/sample_trade.jpg")
#     assert result["success"] is True
#     assert "ticker" in result
#     assert "quantity" in result
#     assert "price" in result
#     assert "trade_type" in result
#     assert isinstance(result["date"], datetime)
