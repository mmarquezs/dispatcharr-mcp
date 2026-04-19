"""Dispatcharr MCP server — exposes Dispatcharr IPTV management to AI agents.

Tools are grouped by domain:
  • Channels       — list, get, create, update, delete channels & groups
  • Channels ext.  — bulk ops, EPG matching, stream assignment, summaries
  • Streams        — list/get raw M3U streams by source
  • Proxy          — live stream status and control (change, stop, failover)
  • EPG            — EPG sources and programme data
  • M3U Accounts   — manage M3U provider accounts
  • VOD            — movies, series, episodes
  • Backups        — create, list, download, restore, schedule backups
  • System         — settings, stream profiles, system events
"""

from mcp.server.fastmcp import FastMCP

from dispatcharr_mcp.client import DispatcharrClient

mcp = FastMCP("Dispatcharr")


def _client() -> DispatcharrClient:
    """Instantiate per-call so the MCP server process doesn't hold a login
    session open indefinitely — the client re-uses its JWT until it expires."""
    return DispatcharrClient()


def _clean(params: dict) -> dict:
    """Omit unset parameters so the API applies its own defaults rather than
    receiving explicit nulls that could override or invalidate fields."""
    return {k: v for k, v in params.items() if v is not None}


# ---------------------------------------------------------------------------
# CHANNELS
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_channels(
    search: str | None = None,
    channel_group: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """List channels with optional filtering.

    Returns a paginated list of channels. Use `search` to filter by name,
    `channel_group` to filter by group name, and `page`/`page_size` for pagination.
    """
    return await _client().get(
        "/api/channels/channels/",
        params=_clean(
            {
                "search": search,
                "channel_group": channel_group,
                "page": page,
                "page_size": page_size,
            }
        ),
    )


@mcp.tool()
async def get_channel(channel_id: int) -> dict:
    """Get a single channel by its integer ID."""
    return await _client().get(f"/api/channels/channels/{channel_id}/")


@mcp.tool()
async def create_channel(
    name: str,
    channel_number: float | None = None,
    channel_group_id: int | None = None,
) -> dict:
    """Create a new channel.

    Provide at minimum a `name`. Optionally assign a channel number and group.
    """
    data: dict = {"name": name}
    if channel_number is not None:
        data["channel_number"] = channel_number
    if channel_group_id is not None:
        data["channel_group"] = channel_group_id
    return await _client().post("/api/channels/channels/", data=data)


@mcp.tool()
async def update_channel(channel_id: int, fields: dict) -> dict:
    """Partially update a channel.

    Pass any subset of channel fields as `fields` (e.g. {"name": "BBC One",
    "channel_number": 1.0}).  Only provided fields are changed.
    """
    return await _client().patch(f"/api/channels/channels/{channel_id}/", data=fields)


@mcp.tool()
async def delete_channel(channel_id: int) -> dict:
    """Delete a channel by ID."""
    return await _client().delete(f"/api/channels/channels/{channel_id}/")


@mcp.tool()
async def get_channel_streams(channel_id: int) -> dict:
    """Get all streams (M3U sources) assigned to a specific channel."""
    return await _client().get(f"/api/channels/channels/{channel_id}/streams/")


# ---------------------------------------------------------------------------
# CHANNELS (extended — bulk operations, EPG matching, ordering, summaries)
# ---------------------------------------------------------------------------


@mcp.tool()
async def bulk_delete_channels(channel_ids: list[int]) -> dict:
    """Bulk delete multiple channels by their IDs.

    Pass a list of channel integer IDs. Use cases include removing
    duplicate channels identified via ``list_channels``.
    """
    return await _client().delete(
        "/api/channels/channels/bulk-delete/",
        params={"ids": ",".join(str(i) for i in channel_ids)},
    )


@mcp.tool()
async def bulk_edit_channels(updates: list[dict]) -> dict:
    """Bulk edit multiple channels in a single request.

    Pass a list of update objects, each must include ``id`` (channel primary key).
    All other fields are optional and support partial updates. Accepted fields
    per object: ``name``, ``channel_number``, ``channel_group_id``, ``streams``
    (list of stream IDs — replaces existing), ``logo_id``, ``tvg_id``,
    ``epg_data_id``, ``user_level``, ``is_adult``.

    All updates are validated before any changes are applied and executed in
    a single database transaction.

    Example::

        [{"id": 1, "name": "BBC One HD"}, {"id": 2, "channel_group_id": 5}]
    """
    return await _client().patch(
        "/api/channels/channels/edit/bulk/",
        data=updates,
    )


@mcp.tool()
async def bulk_rename_channels_regex(
    channel_ids: list[int],
    find: str,
    replace: str,
    flags: str | None = None,
) -> dict:
    """Bulk rename channel names using a server-side regex find/replace.

    Accepts JavaScript-style named groups (e.g. ``(?<name>...)``) and converts
    them to Python syntax. Supports flags: ``i`` (IGNORECASE). Replacement
    tokens like ``$1``, ``$&`` and ``$<name>`` are translated to Python.

    Example: find ``"HD$"`` replace ``""`` flags ``"i"`` to strip trailing "HD".
    """
    return await _client().post(
        "/api/channels/channels/edit/bulk-regex/",
        data=_clean({
            "channel_ids": channel_ids,
            "find": find,
            "replace": replace,
            "flags": flags,
        }),
    )


@mcp.tool()
async def bulk_create_channels_from_streams(
    stream_ids: list[int],
    channel_profile_ids: list[int] | None = None,
    starting_channel_number: int | None = None,
) -> dict:
    """Asynchronously bulk create channels from stream IDs.

    Returns a task ID to track progress via WebSocket. This is the recommended
    approach for large bulk operations.

    ``channel_profile_ids`` behaviour: omitted = add to ALL profiles (default);
    empty list ``[]`` = add to NO profiles; specific IDs = add to those only.
    ``starting_channel_number``: null = use provider numbers; 0 = lowest
    available; other = start from that number.
    """
    return await _client().post(
        "/api/channels/channels/from-stream/bulk/",
        data=_clean({
            "stream_ids": stream_ids,
            "channel_profile_ids": channel_profile_ids,
            "starting_channel_number": starting_channel_number,
        }),
    )


@mcp.tool()
async def batch_set_channel_epg(
    associations: list[dict],
) -> dict:
    """Associate multiple channels with EPG data without triggering a full refresh.

    Pass an ``associations`` list where each item has ``channel_id`` (int) and
    ``epg_data_id`` (int or null to remove linkage).

    Example::

        [{"channel_id": 1, "epg_data_id": 42}, {"channel_id": 2, "epg_data_id": null}]
    """
    return await _client().post(
        "/api/channels/channels/batch-set-epg/",
        data={"associations": associations},
    )


@mcp.tool()
async def set_channel_epg(channel_id: int, epg_data_id: int) -> dict:
    """Set EPG data for a single channel and refresh program data."""
    return await _client().post(
        f"/api/channels/channels/{channel_id}/set-epg/",
        data={"epg_data_id": epg_data_id},
    )


@mcp.tool()
async def match_channel_epg(
    channel_ids: list[int] | None = None,
) -> dict:
    """Auto-match channels to EPG programmes based on name/TVG-ID.

    Kicks off a Celery task that fuzzy-matches channels with EPG data.
    If ``channel_ids`` is provided, only those channels are processed;
    otherwise all channels without EPG are processed.
    """
    return await _client().post(
        "/api/channels/channels/match-epg/",
        data=_clean({"channel_ids": channel_ids}),
    )


@mcp.tool()
async def match_channel_epg_single(channel_id: int) -> dict:
    """Try to auto-match a specific channel with EPG data."""
    return await _client().post(
        f"/api/channels/channels/{channel_id}/match-epg/",
        data={},
    )


@mcp.tool()
async def set_channel_logos_from_epg() -> dict:
    """Trigger a Celery task to update channel logos from matched EPG data."""
    return await _client().post("/api/channels/channels/set-logos-from-epg/", data={})


@mcp.tool()
async def set_channel_names_from_epg() -> dict:
    """Trigger a Celery task to update channel names from matched EPG data."""
    return await _client().post("/api/channels/channels/set-names-from-epg/", data={})


@mcp.tool()
async def set_channel_tvg_ids_from_epg() -> dict:
    """Trigger a Celery task to update channel TVG-IDs from matched EPG data."""
    return await _client().post("/api/channels/channels/set-tvg-ids-from-epg/", data={})


@mcp.tool()
async def assign_channel_numbers(
    channel_ids: list[int],
    starting_number: float | None = None,
) -> dict:
    """Auto-assign channel numbers in bulk by an ordered list of channel IDs.

    Pass an ordered list of ``channel_ids``. Optionally set
    ``starting_number`` for the first channel (can be decimal).
    Channels receive sequential numbers from that starting point.
    """
    return await _client().post(
        "/api/channels/channels/assign/",
        data=_clean({"channel_ids": channel_ids, "starting_number": starting_number}),
    )


@mcp.tool()
async def get_channels_by_uuids(uuids: list[str]) -> dict:
    """Look up channels by a list of UUID strings."""
    return await _client().post(
        "/api/channels/channels/by-uuids/",
        data={"uuids": uuids},
    )


@mcp.tool()
async def get_channel_summary() -> dict:
    """Get a lightweight channel list for the TV Guide (summary view)."""
    return await _client().get("/api/channels/channels/summary/")


@mcp.tool()
async def list_channel_ids() -> dict:
    """List all channel IDs (lightweight endpoint for bulk operations)."""
    return await _client().get("/api/channels/channels/ids/")


@mcp.tool()
async def reorder_channel(
    channel_id: int,
    insert_after_id: int | None = None,
) -> dict:
    """Reorder a channel's position in the channel list.

    Move ``channel_id`` to appear after ``insert_after_id`` (or to the
    start if null). The channel receives the next whole number after the
    target, and all subsequent channels are renumbered accordingly.
    """
    return await _client().post(
        f"/api/channels/channels/{channel_id}/reorder/",
        data={"insert_after_id": insert_after_id},
    )


@mcp.tool()
async def cleanup_channel_groups() -> dict:
    """Delete all channel groups that have no associations (no channels or M3U accounts)."""
    return await _client().post("/api/channels/groups/cleanup/", data={})


# ---------------------------------------------------------------------------
# CHANNEL GROUPS
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_channel_groups() -> list:
    """List all channel groups."""
    return await _client().get("/api/channels/groups/")


@mcp.tool()
async def create_channel_group(name: str) -> dict:
    """Create a new channel group."""
    return await _client().post("/api/channels/groups/", data={"name": name})


@mcp.tool()
async def delete_channel_group(group_id: int) -> dict:
    """Delete a channel group by ID."""
    return await _client().delete(f"/api/channels/groups/{group_id}/")


# ---------------------------------------------------------------------------
# STREAMS (raw M3U streams from provider accounts)
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_streams(
    search: str | None = None,
    m3u_account: int | None = None,
    channel_group_name: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """List raw M3U streams from provider accounts.

    These are the source streams imported from M3U playlists, not the
    channel output. Filter by `m3u_account` (account ID), group name,
    or free-text `search`.
    """
    return await _client().get(
        "/api/channels/streams/",
        params=_clean(
            {
                "search": search,
                "m3u_account": m3u_account,
                "channel_group_name": channel_group_name,
                "page": page,
                "page_size": page_size,
            }
        ),
    )


@mcp.tool()
async def get_stream(stream_id: int) -> dict:
    """Get a single M3U stream by its integer ID."""
    return await _client().get(f"/api/channels/streams/{stream_id}/")


@mcp.tool()
async def create_channel_from_stream(
    stream_id: int,
    name: str | None = None,
    channel_number: float | None = None,
    channel_profile_ids: list[int] | None = None,
) -> dict:
    """Create a channel directly from an existing stream.

    This is the quick way to add a channel: provide the `stream_id` and
    Dispatcharr will create a matching channel and link the stream.
    Optionally supply a custom `name`, `channel_number`, and which
    `channel_profile_ids` the new channel should belong to (omit for all profiles).
    """
    data: dict = {"stream_id": stream_id}
    if name is not None:
        data["name"] = name
    if channel_number is not None:
        data["channel_number"] = channel_number
    if channel_profile_ids is not None:
        data["channel_profile_ids"] = channel_profile_ids
    return await _client().post("/api/channels/channels/from-stream/", data=data)


# ---------------------------------------------------------------------------
# PROXY — live stream status and control
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_proxy_status() -> dict:
    """Get live status of all currently active proxy streams.

    Returns client counts, current stream URLs, buffer stats, and more for
    every channel that is actively streaming right now.
    """
    return await _client().get("/proxy/ts/status")


@mcp.tool()
async def get_channel_proxy_status(channel_id: str) -> dict:
    """Get the live proxy status for a specific channel.

    `channel_id` is the channel's string identifier used by the proxy
    (typically the channel number or UUID).
    """
    return await _client().get(f"/proxy/ts/status/{channel_id}")


@mcp.tool()
async def change_channel_stream(channel_id: str) -> dict:
    """Force a channel to switch to its next available stream source.

    Use this when a stream is buffering badly or has failed—Dispatcharr
    will immediately try the next source in the failover list.
    """
    return await _client().post(f"/proxy/ts/change_stream/{channel_id}")


@mcp.tool()
async def next_channel_stream(channel_id: str) -> dict:
    """Advance a channel to the next stream in its rotation.

    Similar to `change_channel_stream` but explicitly moves forward one
    position in the stream list rather than picking the best available.
    """
    return await _client().post(f"/proxy/ts/next_stream/{channel_id}")


@mcp.tool()
async def stop_channel_stream(channel_id: str) -> dict:
    """Stop all active streams for a channel, disconnecting all clients."""
    return await _client().post(f"/proxy/ts/stop/{channel_id}")


@mcp.tool()
async def stop_channel_client(channel_id: str) -> dict:
    """Stop a specific client connection on a channel without stopping others."""
    return await _client().post(f"/proxy/ts/stop_client/{channel_id}")


# ---------------------------------------------------------------------------
# EPG
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_epg_sources() -> list:
    """List all configured EPG (Electronic Programme Guide) sources."""
    return await _client().get("/api/epg/sources/")


@mcp.tool()
async def get_epg_source(source_id: int) -> dict:
    """Get a single EPG source by ID."""
    return await _client().get(f"/api/epg/sources/{source_id}/")


@mcp.tool()
async def create_epg_source(
    name: str,
    source_type: str = "xmltv",
    url: str | None = None,
    is_active: bool = True,
    refresh_interval: int | None = None,
    priority: int | None = None,
) -> dict:
    """Create a new EPG source.

    `source_type` must be one of: ``xmltv`` (default), ``schedules_direct``,
    or ``dummy``.  For XMLTV sources supply the `url` pointing to an .xml or
    .xml.gz EPG feed.
    """
    data: dict = {"name": name, "source_type": source_type, "is_active": is_active}
    if url is not None:
        data["url"] = url
    if refresh_interval is not None:
        data["refresh_interval"] = refresh_interval
    if priority is not None:
        data["priority"] = priority
    return await _client().post("/api/epg/sources/", data=data)


@mcp.tool()
async def update_epg_source(source_id: int, fields: dict) -> dict:
    """Partially update an EPG source.

    Pass any subset of EPG source fields as `fields`
    (e.g. ``{"url": "https://...", "is_active": True}``).
    """
    return await _client().patch(f"/api/epg/sources/{source_id}/", data=fields)


@mcp.tool()
async def delete_epg_source(source_id: int) -> dict:
    """Delete an EPG source by ID."""
    return await _client().delete(f"/api/epg/sources/{source_id}/")


@mcp.tool()
async def list_epg_data(page: int | None = None, page_size: int | None = None) -> dict:
    """List EPG data entries (programme metadata from EPG sources)."""
    return await _client().get(
        "/api/epg/epgdata/",
        params=_clean({"page": page, "page_size": page_size}),
    )


@mcp.tool()
async def list_epg_programs(
    page: int | None = None, page_size: int | None = None
) -> dict:
    """List EPG program schedule entries (start/stop times, titles, descriptions)."""
    return await _client().get(
        "/api/epg/programs/",
        params=_clean({"page": page, "page_size": page_size}),
    )


# ---------------------------------------------------------------------------
# M3U ACCOUNTS
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_m3u_accounts() -> list:
    """List all configured M3U provider accounts."""
    return await _client().get("/api/m3u/accounts/")


@mcp.tool()
async def get_m3u_account(account_id: int) -> dict:
    """Get details for a specific M3U account by ID."""
    return await _client().get(f"/api/m3u/accounts/{account_id}/")


@mcp.tool()
async def create_m3u_account(
    name: str,
    server_url: str | None = None,
    max_streams: int = 0,
    is_active: bool = True,
    account_type: str = "STD",
    username: str | None = None,
    password: str | None = None,
    refresh_interval: int | None = None,
) -> dict:
    """Create a new M3U provider account.

    `account_type` is ``STD`` (standard M3U URL, the default) or ``XC``
    (Xtream Codes).  For a standard M3U simply pass `server_url`.  Set
    `max_streams` to ``0`` for unlimited concurrent streams.
    """
    data: dict = {
        "name": name,
        "is_active": is_active,
        "account_type": account_type,
        "max_streams": max_streams,
    }
    if server_url is not None:
        data["server_url"] = server_url
    if username is not None:
        data["username"] = username
    if password is not None:
        data["password"] = password
    if refresh_interval is not None:
        data["refresh_interval"] = refresh_interval
    return await _client().post("/api/m3u/accounts/", data=data)


@mcp.tool()
async def update_m3u_account(account_id: int, fields: dict) -> dict:
    """Partially update an M3U account.

    Pass any subset of M3U account fields as `fields`
    (e.g. ``{"name": "New Name", "is_active": False}``).
    """
    return await _client().patch(f"/api/m3u/accounts/{account_id}/", data=fields)


@mcp.tool()
async def delete_m3u_account(account_id: int) -> dict:
    """Delete an M3U account by ID."""
    return await _client().delete(f"/api/m3u/accounts/{account_id}/")


@mcp.tool()
async def refresh_m3u_account(account_id: int) -> dict:
    """Trigger an immediate refresh/re-import of an M3U account's streams."""
    return await _client().post(f"/api/m3u/refresh/{account_id}/")


@mcp.tool()
async def list_m3u_filters(account_id: int) -> list:
    """List stream filters configured for a specific M3U account."""
    return await _client().get(f"/api/m3u/accounts/{account_id}/filters/")


# ---------------------------------------------------------------------------
# CHANNEL PROFILES
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_channel_profiles() -> list:
    """List all channel profiles (output profiles used for different clients)."""
    return await _client().get("/api/channels/profiles/")


# ---------------------------------------------------------------------------
# VOD — Video on Demand
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_movies(
    search: str | None = None,
    category: str | None = None,
    year: int | None = None,
    m3u_account: int | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """List VOD movies with optional filtering.

    Filter by title `search`, `category`, release `year`, or `m3u_account` ID.
    """
    return await _client().get(
        "/api/vod/movies/",
        params=_clean(
            {
                "search": search,
                "category": category,
                "year": year,
                "m3u_account": m3u_account,
                "page": page,
                "page_size": page_size,
            }
        ),
    )


@mcp.tool()
async def get_movie(movie_id: int) -> dict:
    """Get details for a specific movie by ID."""
    return await _client().get(f"/api/vod/movies/{movie_id}/")


@mcp.tool()
async def list_series(
    search: str | None = None,
    category: str | None = None,
    year: int | None = None,
    m3u_account: int | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """List VOD TV series with optional filtering."""
    return await _client().get(
        "/api/vod/series/",
        params=_clean(
            {
                "search": search,
                "category": category,
                "year": year,
                "m3u_account": m3u_account,
                "page": page,
                "page_size": page_size,
            }
        ),
    )


@mcp.tool()
async def get_series(series_id: int) -> dict:
    """Get details for a specific TV series by ID."""
    return await _client().get(f"/api/vod/series/{series_id}/")


@mcp.tool()
async def list_episodes(
    series_id: int | None = None,
    season_number: int | None = None,
    search: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """List VOD episodes, optionally filtered by series and/or season."""
    return await _client().get(
        "/api/vod/episodes/",
        params=_clean(
            {
                "series": series_id,
                "season_number": season_number,
                "search": search,
                "page": page,
                "page_size": page_size,
            }
        ),
    )


@mcp.tool()
async def list_vod_categories(
    category_type: str | None = None,
    m3u_account: int | None = None,
) -> list:
    """List VOD categories.

    Use `category_type` to filter: "movie" or "series".
    """
    return await _client().get(
        "/api/vod/categories/",
        params=_clean({"category_type": category_type, "m3u_account": m3u_account}),
    )


# ---------------------------------------------------------------------------
# SYSTEM
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_core_settings() -> list:
    """Get Dispatcharr core settings (server configuration, defaults, etc.)."""
    return await _client().get("/api/core/settings/")


@mcp.tool()
async def list_stream_profiles() -> list:
    """List stream profiles (FFmpeg/Streamlink/VLC output configurations)."""
    return await _client().get("/api/core/streamprofiles/")


@mcp.tool()
async def get_system_events(
    limit: int | None = None,
    offset: int | None = None,
    event_type: str | None = None,
) -> dict:
    """Get recent system events (channel starts, stops, buffering, client connections).

    Use `limit` (default 100, max 1000), `offset` for pagination, and
    `event_type` to filter by a specific event kind.
    """
    return await _client().get(
        "/api/core/system-events/",
        params=_clean({"limit": limit, "offset": offset, "event_type": event_type}),
    )


@mcp.tool()
async def list_stream_delivery_logs(
    page: int | None = None, page_size: int | None = None
) -> dict:
    """List stream delivery/webhook logs from the Connect integrations system."""
    return await _client().get(
        "/api/connect/logs/",
        params=_clean({"page": page, "page_size": page_size}),
    )


@mcp.tool()
async def list_integrations() -> list:
    """List all configured Connect integrations (webhooks, API callbacks, scripts)."""
    return await _client().get("/api/connect/integrations/")


@mcp.tool()
async def list_recordings() -> list:
    """List all DVR recordings."""
    return await _client().get("/api/channels/recordings/")


@mcp.tool()
async def get_recording(recording_id: int) -> dict:
    """Get details for a specific DVR recording by ID."""
    return await _client().get(f"/api/channels/recordings/{recording_id}/")


# ---------------------------------------------------------------------------
# HDHR (HDHomeRun emulation)
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_hdhr_devices() -> list:
    """List all configured HDHomeRun virtual tuner devices."""
    return await _client().get("/api/hdhr/devices/")


# ---------------------------------------------------------------------------
# BACKUPS
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_backup() -> dict:
    """Trigger a new backup of the Dispatcharr database and configuration.

    Returns a task object with a `task_id` that can be polled with
    `get_backup_status` to track progress.
    """
    return await _client().post("/api/backups/create/")


@mcp.tool()
async def list_backups() -> list:
    """List all available backups.

    Returns filename, size, creation date, and other metadata for each backup.
    """
    return await _client().get("/api/backups/")


@mcp.tool()
async def get_backup_status(
    task_id: str,
    wait: bool = True,
    timeout: int = 120,
) -> dict:
    """Check the progress of a backup or restore task.

    Pass the `task_id` returned by `create_backup` or `restore_backup`.

    By default, polls every 2 seconds until the task reaches a terminal state
    (completed/failed) or the timeout is reached. Set `wait=False` for a
    single instant status check.
    Returns status, progress details, and result when complete.
    """
    import asyncio

    terminal = {"completed", "failed", "cancelled", "success", "error"}
    elapsed = 0
    interval = 2

    while True:
        result = await _client().get(f"/api/backups/status/{task_id}/")
        if not wait:
            return result
        status = result.get("status", "") if isinstance(result, dict) else ""
        if status.lower() in terminal:
            return result
        if elapsed >= timeout:
            result["_timed_out"] = True
            result["_message"] = (
                f"Timeout after {timeout}s. Call again with the same task_id to continue waiting."
            )
            return result
        await asyncio.sleep(interval)
        elapsed += interval


@mcp.tool()
async def download_backup(filename: str) -> dict:
    """Get a download URL for a backup file.

    Since MCP tools cannot return binary files, this returns a dict containing
    the download URL with an authenticated token. Open the URL in a browser
    or use curl/wget to download the backup archive.
    """
    token_data = await _client().get(
        f"/api/backups/{filename}/download-token/"
    )
    token = token_data.get("token", "") if isinstance(token_data, dict) else ""
    base = _client()._base
    return {
        "url": f"{base}/api/backups/{filename}/download/?token={token}",
        "filename": filename,
    }


@mcp.tool()
async def restore_backup(filename: str) -> dict:
    """Restore Dispatcharr from a specific backup file.

    WARNING: This overwrites the current database and configuration.
    Returns a task object — use `get_backup_status` to track progress.
    """
    return await _client().post(f"/api/backups/{filename}/restore/")


@mcp.tool()
async def delete_backup(filename: str) -> dict:
    """Delete a backup file by its filename."""
    return await _client().delete(f"/api/backups/{filename}/delete/")


@mcp.tool()
async def get_backup_schedule() -> dict:
    """Get the current backup schedule configuration.

    Returns: enabled (bool), frequency (str: "daily"/"weekly"), time (str: "HH:MM"),
    day_of_week (int: 0-6), retention_count (int), cron_expression (str).
    """
    return await _client().get("/api/backups/schedule/")


@mcp.tool()
async def update_backup_schedule(fields: dict) -> dict:
    """Update the backup schedule configuration.

    Pass any subset of schedule fields as `fields`. Only provided fields are changed.

    Accepted fields:
        enabled (bool): Enable or disable scheduled backups.
        frequency (str): How often to run. Must be ``"daily"`` or ``"weekly"``.
        time (str): Time of day in ``"HH:MM"`` format, 24-hour (e.g. ``"03:00"``).
        day_of_week (int): Day of week for weekly frequency. 0=Sunday through 6=Saturday.
            Ignored when frequency is ``"daily"``.
        retention_count (int): Number of backups to keep. Older ones are auto-deleted.
            Set to 0 to keep all.
        cron_expression (str): Custom cron expression (e.g. ``"0 3 * * *"``).
            Overrides frequency/time/day_of_week when set. Set to ``""`` to go
            back to simple frequency mode.

    Example: ``{"enabled": true, "frequency": "daily", "time": "03:00", "retention_count": 5}``
    """
    return await _client().put("/api/backups/schedule/update/", data=fields)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
