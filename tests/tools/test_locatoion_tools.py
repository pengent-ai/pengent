import pytest
from pengent.tools.tools.location.locatoion_tools import LocationTools
from pengent.tools.api.services.open_weather import ApiOpenWeatherMap
from pengent.tools import FunctionTool


@pytest.fixture(autouse=True)
def clear_cache():
    """各テスト前にキャッシュをクリアするFixture"""
    ApiOpenWeatherMap._API_CACHE = {
        "geocoding": {"Tokyo": {"lat": 35.6828387, "lon": 139.7594549, "country": "JP"}}
    }


def test_geocoding_success():
    location = "Tokyo"
    result = LocationTools.geocoding(location)
    assert isinstance(result, dict)
    assert "lat" in result
    assert "lon" in result
    assert "country" in result
    print(f"Result for {location}: {result}")


def test_tools_location_registry_success():
    tool = FunctionTool(LocationTools.geocoding)
    # OpenAI形式の場合、function内にnameがある
    assert tool.name == "geocoding"
    assert "都市名" in tool.description
    dump_tool = tool.dump()
    assert dump_tool.get("function", {}).get("name") == "geocoding"


def test_geocoding_tools_mcp_exec_success():
    tool = FunctionTool(LocationTools.geocoding)
    result = tool.run(location="Tokyo")
    assert "lat" in result
    assert "lon" in result
    assert "country" in result
