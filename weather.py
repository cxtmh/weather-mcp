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

def main():
    # Initialize and run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()