# music-assistant-client

[![Status: Active](https://img.shields.io/badge/status-active-brightgreen)](https://github.com/OscillateLabsLLC/.github/blob/main/SUPPORT_STATUS.md)

A simple synchronous HTTP client for the [Music Assistant](https://music-assistant.io/) API.

## Installation

```bash
pip install ma-http-client
```

## Usage

```python
from ma_http_client import SimpleHTTPMusicAssistantClient

client = SimpleHTTPMusicAssistantClient(
    server_url="http://localhost:8095",
    token="YOUR_TOKEN",  # required for MA >= 2.7.2
)

# Get all players
players = client.get_players()

# Search for media
results = client.search_media("Radiohead", limit=5)

# Resolve one item by name; the server matches across types, or narrow it
album = client.get_item_by_name("Abbey Road", artist="The Beatles")
track = client.get_track_by_name("Come Together", artist_name="The Beatles")

# Play media on a player (a uri or a list of uris; shuffle is optional)
client.play_media(queue_id=players[0].player_id, media="library://artist/204")
client.play_media(queue_id=players[0].player_id, media=album["uri"], shuffle=True)

# Queue controls and modes
client.queue_command_pause(players[0].player_id)
client.queue_command_next(players[0].player_id)
client.queue_set_shuffle(players[0].player_id, True)
client.queue_set_repeat(players[0].player_id, RepeatMode.ALL)  # from music_assistant_models.enums

# Favorites
client.add_favorite(track["uri"])

# Library listings and genres ("play some jazz", "play some music")
from ma_http_client import SORT_RANDOM
jazz = client.search_genres("jazz")[0]
tracks = client.genre_tracks(jazz["item_id"], limit=30, sort_field=SORT_RANDOM)
random_tracks = client.library_items(MediaType.TRACK, limit=20, sort_field=SORT_RANDOM)
client.play_media(players[0].player_id, [t["uri"] for t in tracks], shuffle=True)

# Volume
client.player_command_volume_set(players[0].player_id, 50)
```

## Claude Code Skill

Control Music Assistant with natural language from [Claude Code](https://docs.anthropic.com/en/docs/claude-code). See [CLAUDE.md](CLAUDE.md) for full setup.

```bash
pip install ma-http-client
ma-install-skill
```

Then in any Claude Code session:

```
/music-assistant play some Radiohead
```

Or just ask naturally — Claude auto-invokes the skill when it matches.

### Standalone Agent

For use outside Claude Code (scripts, OVOS, etc.), install the `claude` extra:

```bash
pip install "ma-http-client[claude]"
```

```python
from ma_http_client.claude_tools import MusicAssistantAgent

agent = MusicAssistantAgent(
    ma_url="http://homeassistant.local:8095",
    ma_token="YOUR_MA_TOKEN",
    default_player="Living Room",
)
print(agent.run("Play some Radiohead"))
```

## Debug Client

The `DebugMusicAssistantClient` extends the base client with fixture capture for troubleshooting:

```python
from ma_http_client.debug import DebugMusicAssistantClient

client = DebugMusicAssistantClient(
    "http://localhost:8095",
    fixture_capture=True,
    fixture_dir="./debug_fixtures",
)

players = client.get_players()
# API responses are automatically saved to ./debug_fixtures/
```
