# dispatcharr-mcp

An [MCP](https://modelcontextprotocol.io) server for [Dispatcharr](https://github.com/Dispatcharr/Dispatcharr) — giving AI agents full control over your IPTV streams, channels, EPG, and VOD library.

## Tools

| Domain | Tools |
|--------|-------|
| **Channels** | `list_channels`, `get_channel`, `create_channel`, `update_channel`, `delete_channel`, `get_channel_streams` |
| **Channel Groups** | `list_channel_groups`, `create_channel_group`, `delete_channel_group` |
| **Streams** | `list_streams`, `get_stream`, `create_channel_from_stream` |
| **Proxy / Live** | `get_proxy_status`, `get_channel_proxy_status`, `change_channel_stream`, `next_channel_stream`, `stop_channel_stream`, `stop_channel_client` |
| **EPG** | `list_epg_sources`, `get_epg_source`, `create_epg_source`, `update_epg_source`, `delete_epg_source`, `list_epg_data`, `list_epg_programs` |
| **M3U Accounts** | `list_m3u_accounts`, `get_m3u_account`, `create_m3u_account`, `update_m3u_account`, `delete_m3u_account`, `refresh_m3u_account`, `list_m3u_filters` |
| **Channel Profiles** | `list_channel_profiles` |
| **VOD** | `list_movies`, `get_movie`, `list_series`, `get_series`, `list_episodes`, `list_vod_categories` |
| **System** | `get_core_settings`, `list_stream_profiles`, `get_system_events`, `list_integrations`, `list_stream_delivery_logs` |
| **DVR** | `list_recordings`, `get_recording` |
| **HDHomeRun** | `list_hdhr_devices` |

## Requirements

- Python 3.10+
- A running Dispatcharr instance (v0.20+)
- A Dispatcharr user account (username + password)

## Authentication

This MCP uses **JWT authentication**. It logs in with your Dispatcharr username and password, obtains a JWT access token, and automatically refreshes it as needed. No static API key is required.

It is recommended to create a dedicated Dispatcharr user (e.g. `mcp`) rather than using your admin account.

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/dispatcharr-mcp
cd dispatcharr-mcp
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Usage

### VS Code (`mcp.json`)

```json
{
  "servers": {
    "dispatcharr": {
      "type": "stdio",
      "command": "/path/to/dispatcharr-mcp/.venv/bin/dispatcharr-mcp",
      "args": [],
      "env": {
        "DISPATCHARR_URL": "http://your-dispatcharr-host:9191",
        "DISPATCHARR_USERNAME": "mcp",
        "DISPATCHARR_PASSWORD": "your-password"
      }
    }
  }
}
```

### CLI / manual

```bash
export DISPATCHARR_URL=http://dispatcharr.local:9191
export DISPATCHARR_USERNAME=mcp
export DISPATCHARR_PASSWORD=your-password

.venv/bin/dispatcharr-mcp
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISPATCHARR_URL` | ✅ | Base URL of your Dispatcharr instance |
| `DISPATCHARR_USERNAME` | ✅ | Dispatcharr username |
| `DISPATCHARR_PASSWORD` | ✅ | Dispatcharr password |

## License

MIT