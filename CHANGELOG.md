# Changelog

All notable changes to dispatcharr-mcp are documented here.

---

## [0.2.0] - 2026-04-22

### Added

**EPG**
- `get_current_programs` — now-playing programme for all channels or a filtered list of channel UUIDs
- `get_epg_grid` — full TV guide grid covering the past hour, now, and the next 24 hours

**DVR Recordings**
- `schedule_recording` — schedule a new recording by channel ID with start/end datetimes
- `delete_recording` — delete a recording and remove the file from disk
- `stop_recording` — stop an in-progress recording early while keeping the partial file
- `extend_recording` — extend an active recording's end time without interrupting the stream

**DVR Series Rules**
- `list_series_rules` — list all configured series recording rules
- `create_series_rule` — create or update a series rule (record all or only new episodes)
- `delete_series_rule` — delete a series rule and remove its future scheduled recordings
- `evaluate_series_rules` — trigger evaluation of rules to schedule matching episodes

**DVR Recurring Rules**
- `list_recurring_rules` — list all time-based recurring recording rules
- `create_recurring_rule` — create a recurring rule (day-of-week, time window, date bounds)
- `update_recurring_rule` — partially update a recurring rule
- `delete_recurring_rule` — delete a recurring rule

**M3U Filters**
- `create_m3u_filter` — add a regex-based stream filter to an M3U account
- `update_m3u_filter` — partially update an existing M3U filter
- `delete_m3u_filter` — delete an M3U filter

**Channel Groups**
- `update_channel_group` — rename a channel group

**Channel Profiles**
- `create_channel_profile` — create a new output channel profile
- `delete_channel_profile` — delete a channel profile

**System**
- `get_version` — get the running Dispatcharr application version

---

## [0.1.1] - initial release

### Added
- Full channel CRUD: `list_channels`, `get_channel`, `create_channel`, `update_channel`, `delete_channel`, `get_channel_streams`
- Channel group management: `list_channel_groups`, `create_channel_group`, `delete_channel_group`
- Stream listing: `list_streams`, `get_stream`, `create_channel_from_stream`
- Live proxy control: `get_proxy_status`, `get_channel_proxy_status`, `change_channel_stream`, `next_channel_stream`, `stop_channel_stream`, `stop_channel_client`
- EPG source management: `list_epg_sources`, `get_epg_source`, `create_epg_source`, `update_epg_source`, `delete_epg_source`, `list_epg_data`, `list_epg_programs`
- M3U account management: `list_m3u_accounts`, `get_m3u_account`, `create_m3u_account`, `update_m3u_account`, `delete_m3u_account`, `refresh_m3u_account`, `list_m3u_filters`
- Channel profiles: `list_channel_profiles`
- VOD: `list_movies`, `get_movie`, `list_series`, `get_series`, `list_episodes`, `list_vod_categories`
- System: `get_core_settings`, `list_stream_profiles`, `get_system_events`, `list_integrations`, `list_stream_delivery_logs`
- DVR: `list_recordings`, `get_recording`
- HDHomeRun: `list_hdhr_devices`
- Auth: API key (stateless) and JWT (username/password) modes
