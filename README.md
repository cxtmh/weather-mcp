# Weather MCP Server

A Model Context Protocol (MCP) server that provides weather data using the National Weather Service (NWS) API.

## Features

- **Get Alerts**: Fetch active weather alerts for a specific US state.
- **Get Forecast**: Get the weather forecast for a specific latitude and longitude.

## Prerequisites

- Python 3.10 or higher

## Setup

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

This server runs over standard input/output (stdio). You can run it directly with Python:

```bash
uv run weather.py
```

### Using with Claude Desktop

To connect this server to Claude Desktop, add the following configuration to your `claude_desktop_config.json` (typically located in `~/Library/Application Support/Claude/` on macOS or `%APPDATA%\Claude\` on Windows):

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/PARENT/FOLDER/weather",
        "run",
        "weather.py"
      ]
    }
  }
}
```