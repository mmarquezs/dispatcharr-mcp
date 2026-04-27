# dispatcharr-mcp

An [MCP](https://modelcontextprotocol.io) server for [Dispatcharr](https://github.com/Dispatcharr/Dispatcharr) — giving AI agents full control over your IPTV streams, channels, EPG, and VOD library.

## Authentication

Two modes are supported — `DISPATCHARR_API_KEY` takes priority if set:

| Mode | Variables needed |
|------|------------------|
| API Key (stateless, no token expiry) | `DISPATCHARR_URL` + `DISPATCHARR_API_KEY` |
| JWT (username/password) | `DISPATCHARR_URL` + `DISPATCHARR_USERNAME` + `DISPATCHARR_PASSWORD` |

To generate an API key: Dispatcharr UI → **System → Users** → edit your user → copy the API Key field.

## Tools

| Domain | Tools |
|--------|-------|
| **Channels** | `list_channels`, `get_channel`, `create_channel`, `update_channel`, `delete_channel`, `get_channel_streams` |
| **Channel Groups** | `list_channel_groups`, `create_channel_group`, `update_channel_group`, `delete_channel_group` |
| **Streams** | `list_streams`, `get_stream`, `create_channel_from_stream` |
| **Proxy / Live** | `get_proxy_status`, `get_channel_proxy_status`, `change_channel_stream`, `next_channel_stream`, `stop_channel_stream`, `stop_channel_client` |
| **EPG** | `list_epg_sources`, `get_epg_source`, `create_epg_source`, `update_epg_source`, `delete_epg_source`, `list_epg_data`, `list_epg_programs`, `get_current_programs`, `get_epg_grid` |
| **M3U Accounts** | `list_m3u_accounts`, `get_m3u_account`, `create_m3u_account`, `update_m3u_account`, `delete_m3u_account`, `refresh_m3u_account`, `list_m3u_filters`, `create_m3u_filter`, `update_m3u_filter`, `delete_m3u_filter` |
| **Channel Profiles** | `list_channel_profiles`, `create_channel_profile`, `delete_channel_profile` |
| **VOD** | `list_movies`, `get_movie`, `list_series`, `get_series`, `list_episodes`, `list_vod_categories` |
| **System** | `get_core_settings`, `get_version`, `list_stream_profiles`, `get_system_events`, `list_integrations`, `list_stream_delivery_logs` |
| **DVR Recordings** | `list_recordings`, `get_recording`, `schedule_recording`, `delete_recording`, `stop_recording`, `extend_recording` |
| **DVR Series Rules** | `list_series_rules`, `create_series_rule`, `delete_series_rule`, `evaluate_series_rules` |
| **DVR Recurring Rules** | `list_recurring_rules`, `create_recurring_rule`, `update_recurring_rule`, `delete_recurring_rule` |
| **HDHomeRun** | `list_hdhr_devices` |
| **Backups** | `create_backup`, `list_backups`, `get_backup_status`, `download_backup`, `restore_backup`, `delete_backup`, `get_backup_schedule`, `update_backup_schedule` |

## Requirements

- Python 3.10+
- A running Dispatcharr instance (v0.20+)
- A Dispatcharr API key **or** a username + password

## Installation

```bash
git clone https://github.com/mmarquezs/dispatcharr-mcp
cd dispatcharr-mcp
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Usage

### VS Code (`mcp.json`) — API Key (recommended)

```json
{
  "servers": {
    "dispatcharr": {
      "type": "stdio",
      "command": "/path/to/dispatcharr-mcp/.venv/bin/dispatcharr-mcp",
      "args": [],
      "env": {
        "DISPATCHARR_URL": "http://your-dispatcharr-host:9191",
        "DISPATCHARR_API_KEY": "your-api-key"
      }
    }
  }
}
```

### VS Code (`mcp.json`) — Username/Password (JWT)

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
export DISPATCHARR_API_KEY=your-api-key   # or use USERNAME + PASSWORD below

.venv/bin/dispatcharr-mcp
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISPATCHARR_URL` | ✅ | Base URL of your Dispatcharr instance |
| `DISPATCHARR_API_KEY` | ✅ (or user+pass) | Static API key — preferred auth method |
| `DISPATCHARR_USERNAME` | ✅ (or api key) | Dispatcharr username (JWT fallback) |
| `DISPATCHARR_PASSWORD` | ✅ (or api key) | Dispatcharr password (JWT fallback) |

## License

MIT

## Contributing

This project follows a **per-API-group** contribution pattern. Each Dispatcharr API domain (Backups, Channels, EPG, etc.) is developed as a separate unit.

### Adding a new API group

1. Check existing [issues](../../issues) for the API group you want to work on, or create one
2. Create a branch: `feat/<group-name>-tools` (e.g. `feat/backup-tools`)
3. Add tools to `dispatcharr_mcp/server.py` following the existing pattern:
   - Group tools under a comment header (e.g. `# BACKUPS`)
   - Use `@mcp.tool()` decorator
   - Use `_client()` for API calls and `_clean()` to strip None params
   - Add descriptive docstrings — they become the tool descriptions visible to AI agents
4. Update the Tools table in this README
5. Open a PR against `main`

### Tool naming convention

- `list_<resource>` — paginated list with optional filters
- `get_<resource>` — single item by ID
- `create_<resource>` — new item
- `update_<resource>` — partial update by ID (accepts `fields: dict`)
- `delete_<resource>` — delete by ID
- Action verbs for operations: `refresh_`, `restore_`, `trigger_`, etc.

### Code style

- Python 3.10+ (use `X | None` not `Optional[X]`)
- Lint with `ruff check dispatcharr_mcp/`
- No external dependencies beyond `mcp[cli]` and `httpx`