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

# Play media on a player
client.play_media(queue_id=players[0].player_id, media="library://artist/204")

# Queue controls
client.queue_command_pause(players[0].player_id)
client.queue_command_next(players[0].player_id)

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
