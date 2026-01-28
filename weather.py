from typing import Any
from datetime import datetime, timedelta

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get("event", "Unknown")}
Area: {props.get("areaDesc", "Unknown")}
Severity: {props.get("severity", "Unknown")}
Description: {props.get("description", "No description available")}
Instructions: {props.get("instruction", "No specific instructions provided")}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period["name"]}:
Temperature: {period["temperature"]}°{period["temperatureUnit"]}
Wind: {period["windSpeed"]} {period["windDirection"]}
Forecast: {period["detailedForecast"]}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


@mcp.tool()
async def get_singapore_air_temperature(date: str | None = None) -> str:
    """Get air temperature readings from various weather stations across Singapore.
    If no date is provided, this will fetch the latest readings.

    Args:
        date: The date to fetch data for, in YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss format.
              Can also accept relative dates like 'today', 'yesterday', or 'last week'.
    """
    url = "https://api-open.data.gov.sg/v2/real-time/api/air-temperature"
    headers = {"User-Agent": USER_AGENT}
    params = {}
    if date:
        api_date = date
        if date.lower() == 'last week':
            api_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        elif date.lower() == 'yesterday':
            api_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif date.lower() == 'today':
            api_date = datetime.now().strftime('%Y-%m-%d')
        params["date"] = api_date

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except httpx.RequestError as e:
            return f"Error fetching Singapore weather data: {e}"
        except Exception:
            return "An unexpected error occurred while fetching Singapore weather data."

    if not data or "data" not in data:
        return "Unable to parse temperature data or no data found."

    api_data = data["data"]
    stations = {s["id"]: s["name"] for s in api_data.get("stations", [])}
    readings = api_data.get("readings", [])

    if not readings or not stations:
        return "No temperature readings available from the API."

    # The first item in 'readings' contains the latest data
    latest_reading_set = readings[0]
    latest_readings_data = latest_reading_set.get("data", [])

    if not latest_readings_data:
        return "No temperature measurement values found."

    timestamp = latest_reading_set.get("timestamp", "latest available time")
    reading_unit = api_data.get("readingUnit", "°C")

    if date:
        output_lines = [f"Air temperature readings for {date} (as of {timestamp}):"]
    else:
        output_lines = [f"Latest air temperature readings from Singapore (as of {timestamp}):"]

    for reading in latest_readings_data:
        station_id = reading.get("stationId")
        temperature = reading.get("value")
        if station_id and temperature is not None:
            station_name = stations.get(station_id, f"Unknown Station ({station_id})")
            output_lines.append(f"- {station_name}: {temperature} {reading_unit}")

    if len(output_lines) == 1:
        return "Could not format any temperature readings."

    return "\n".join(output_lines)


@mcp.tool()
async def get_singapore_rainfall(date: str | None = None) -> str:
    """Get rainfall readings from various weather stations across Singapore.
    If no date is provided, this will fetch the latest readings.

    Args:
        date: The date to fetch data for, in YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss format.
              Can also accept relative dates like 'today', 'yesterday', or 'last week'.
    """
    url = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
    headers = {"User-Agent": USER_AGENT}
    params = {}
    if date:
        api_date = date
        if date.lower() == 'last week':
            api_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        elif date.lower() == 'yesterday':
            api_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif date.lower() == 'today':
            api_date = datetime.now().strftime('%Y-%m-%d')
        params["date"] = api_date

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except httpx.RequestError as e:
            return f"Error fetching Singapore rainfall data: {e}"
        except Exception:
            return "An unexpected error occurred while fetching Singapore rainfall data."

    if not data or "data" not in data:
        return "Unable to parse rainfall data or no data found."

    api_data = data["data"]
    stations = {s["id"]: s["name"] for s in api_data.get("stations", [])}
    readings = api_data.get("readings", [])

    if not readings or not stations:
        return "No rainfall readings available from the API."

    latest_reading_set = readings[0]
    latest_readings_data = latest_reading_set.get("data", [])

    if not latest_readings_data:
        return "No rainfall measurement values found."

    timestamp = latest_reading_set.get("timestamp", "latest available time")
    reading_unit = api_data.get("readingUnit", "mm")

    if date:
        output_lines = [f"Rainfall readings for {date} (as of {timestamp}):"]
    else:
        output_lines = [f"Latest rainfall readings from Singapore (as of {timestamp}):"]

    for reading in latest_readings_data:
        station_id = reading.get("stationId")
        rainfall = reading.get("value")
        if station_id and rainfall is not None and rainfall > 0:
            station_name = stations.get(station_id, f"Unknown Station ({station_id})")
            output_lines.append(f"- {station_name}: {rainfall} {reading_unit}")

    if len(output_lines) == 1:
        return f"No rainfall recorded in Singapore as of {timestamp}."

    return "\n".join(output_lines)


@mcp.tool()
async def get_singapore_relative_humidity(date: str | None = None) -> str:
    """Get relative humidity readings from various weather stations across Singapore.
    If no date is provided, this will fetch the latest readings.

    Args:
        date: The date to fetch data for, in YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss format.
              Can also accept relative dates like 'today', 'yesterday', or 'last week'.
    """
    url = "https://api-open.data.gov.sg/v2/real-time/api/relative-humidity"
    headers = {"User-Agent": USER_AGENT}
    params = {}
    if date:
        api_date = date
        if date.lower() == 'last week':
            api_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        elif date.lower() == 'yesterday':
            api_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif date.lower() == 'today':
            api_date = datetime.now().strftime('%Y-%m-%d')
        params["date"] = api_date

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except httpx.RequestError as e:
            return f"Error fetching Singapore relative humidity data: {e}"
        except Exception:
            return "An unexpected error occurred while fetching Singapore relative humidity data."

    if not data or "data" not in data:
        return "Unable to parse relative humidity data or no data found."

    api_data = data["data"]
    stations = {s["id"]: s["name"] for s in api_data.get("stations", [])}
    readings = api_data.get("readings", [])

    if not readings or not stations:
        return "No relative humidity readings available from the API."

    latest_reading_set = readings[0]
    latest_readings_data = latest_reading_set.get("data", [])

    if not latest_readings_data:
        return "No relative humidity measurement values found."

    timestamp = latest_reading_set.get("timestamp", "latest available time")
    reading_unit = api_data.get("readingUnit", "%")

    if date:
        output_lines = [f"Relative humidity readings for {date} (as of {timestamp}):"]
    else:
        output_lines = [f"Latest relative humidity readings from Singapore (as of {timestamp}):"]

    for reading in latest_readings_data:
        station_id = reading.get("stationId")
        humidity = reading.get("value")
        if station_id and humidity is not None:
            station_name = stations.get(station_id, f"Unknown Station ({station_id})")
            output_lines.append(f"- {station_name}: {humidity}{reading_unit}")

    if len(output_lines) == 1:
        return "Could not format any relative humidity readings."

    return "\n".join(output_lines)


def degrees_to_cardinal(d: float) -> str:
    """Converts degrees to a cardinal direction."""
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]


@mcp.tool()
async def get_singapore_wind_direction(date: str | None = None) -> str:
    """Get wind direction readings from various weather stations across Singapore.
    If no date is provided, this will fetch the latest readings.

    Args:
        date: The date to fetch data for, in YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss format.
              Can also accept relative dates like 'today', 'yesterday', or 'last week'.
    """
    url = "https://api-open.data.gov.sg/v2/real-time/api/wind-direction"
    headers = {"User-Agent": USER_AGENT}
    params = {}
    if date:
        api_date = date
        if date.lower() == 'last week':
            api_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        elif date.lower() == 'yesterday':
            api_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif date.lower() == 'today':
            api_date = datetime.now().strftime('%Y-%m-%d')
        params["date"] = api_date

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except httpx.RequestError as e:
            return f"Error fetching Singapore wind direction data: {e}"
        except Exception:
            return "An unexpected error occurred while fetching Singapore wind direction data."

    if not data or "data" not in data:
        return "Unable to parse wind direction data or no data found."

    api_data = data["data"]
    stations = {s["id"]: s["name"] for s in api_data.get("stations", [])}
    readings = api_data.get("readings", [])

    if not readings or not stations:
        return "No wind direction readings available from the API."

    latest_reading_set = readings[0]
    latest_readings_data = latest_reading_set.get("data", [])

    if not latest_readings_data:
        return "No wind direction measurement values found."

    timestamp = latest_reading_set.get("timestamp", "latest available time")

    if date:
        output_lines = [f"Wind direction readings for {date} (as of {timestamp}):"]
    else:
        output_lines = [f"Latest wind direction readings from Singapore (as of {timestamp}):"]

    for reading in latest_readings_data:
        station_id = reading.get("stationId")
        direction = reading.get("value")
        if station_id and direction is not None:
            station_name = stations.get(station_id, f"Unknown Station ({station_id})")
            cardinal_direction = degrees_to_cardinal(direction)
            output_lines.append(f"- {station_name}: {direction}° ({cardinal_direction})")

    if len(output_lines) == 1:
        return "Could not format any wind direction readings."

    return "\n".join(output_lines)


@mcp.tool()
async def get_singapore_wind_speed(date: str | None = None) -> str:
    """Get wind speed readings from various weather stations across Singapore.
    If no date is provided, this will fetch the latest readings.

    Args:
        date: The date to fetch data for, in YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss format.
              Can also accept relative dates like 'today', 'yesterday', or 'last week'.
    """
    url = "https://api-open.data.gov.sg/v2/real-time/api/wind-speed"
    headers = {"User-Agent": USER_AGENT}
    params = {}
    if date:
        api_date = date
        if date.lower() == 'last week':
            api_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        elif date.lower() == 'yesterday':
            api_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif date.lower() == 'today':
            api_date = datetime.now().strftime('%Y-%m-%d')
        params["date"] = api_date

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except httpx.RequestError as e:
            return f"Error fetching Singapore wind speed data: {e}"
        except Exception:
            return "An unexpected error occurred while fetching Singapore wind speed data."

    if not data or "data" not in data:
        return "Unable to parse wind speed data or no data found."

    api_data = data["data"]
    stations = {s["id"]: s["name"] for s in api_data.get("stations", [])}
    readings = api_data.get("readings", [])

    if not readings or not stations:
        return "No wind speed readings available from the API."

    latest_reading_set = readings[0]
    latest_readings_data = latest_reading_set.get("data", [])

    if not latest_readings_data:
        return "No wind speed measurement values found."

    timestamp = latest_reading_set.get("timestamp", "latest available time")
    reading_unit = api_data.get("readingUnit", "knots")

    if date:
        output_lines = [f"Wind speed readings for {date} (as of {timestamp}):"]
    else:
        output_lines = [f"Latest wind speed readings from Singapore (as of {timestamp}):"]

    for reading in latest_readings_data:
        station_id = reading.get("stationId")
        speed = reading.get("value")
        if station_id and speed is not None:
            station_name = stations.get(station_id, f"Unknown Station ({station_id})")
            output_lines.append(f"- {station_name}: {speed} {reading_unit}")

    if len(output_lines) == 1:
        return "Could not format any wind speed readings."

    return "\n".join(output_lines)


def main():
    # Initialize and run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()