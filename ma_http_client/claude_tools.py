"""Claude-powered natural language interface for Music Assistant.

Requires the `claude` optional dependency:
    pip install ma-http-client[claude]

Usage:
    from ma_http_client.claude_tools import MusicAssistantAgent

    agent = MusicAssistantAgent(
        ma_url="http://localhost:8095",
        ma_token="YOUR_MA_TOKEN",       # required for MA >= 2.7.2
        default_player="Living Room",   # optional
    )
    print(agent.run("Play some Radiohead"))
    print(agent.run("Pause the kitchen speaker"))
    print(agent.run("Set volume to 40 in the bedroom"))
"""

import json
import os

import anthropic
from anthropic import beta_tool

from .client import SimpleHTTPMusicAssistantClient


_SYSTEM_PROMPT = """You are a music controller for Music Assistant, a self-hosted music server.

Workflow for playing music:
1. Call get_players() to discover available players and match the requested location
2. Call search_media() for the requested content
3. Call play_media() with the player_id and URI from the search result

For playback controls (pause, next, previous, volume), call get_players() first to resolve the player_id.

Keep responses brief — one sentence. Examples:
- "Playing Radiohead in the living room."
- "Paused."
- "Volume set to 50%."
- "Couldn't find a player named 'bathroom'."
"""


def create_ma_tools(client: SimpleHTTPMusicAssistantClient) -> list:
    """Create Claude beta_tool functions wrapping an MA client instance."""

    @beta_tool
    def get_players() -> str:
        """Get all available Music Assistant players with their IDs, names, and availability."""
        players = client.get_players()
        return json.dumps(
            [
                {
                    "player_id": p.player_id,
                    "name": p.name,
                    "available": getattr(p, "available", False),
                }
                for p in players
            ]
        )

    @beta_tool
    def search_media(query: str, media_type: str = "artist") -> str:
        """Search Music Assistant for media to play.

        Args:
            query: Artist name, track title, album name, playlist name, or radio station.
            media_type: One of: artist, track, album, playlist, radio.

        Returns the best match with its URI, which is required for play_media.
        """
        from music_assistant_models.enums import MediaType

        type_map = {
            "artist": MediaType.ARTIST,
            "track": MediaType.TRACK,
            "album": MediaType.ALBUM,
            "playlist": MediaType.PLAYLIST,
            "radio": MediaType.RADIO,
        }
        mt = type_map.get(media_type.lower())
        results = client.search_media(query, media_types=[mt] if mt else None, limit=5)

        key_map = {
            "artist": "artists",
            "track": "tracks",
            "album": "albums",
            "playlist": "playlists",
            "radio": "radio",
        }
        items = results.get(key_map.get(media_type.lower(), "artists"), [])
        if not items:
            return json.dumps({"found": False, "query": query, "media_type": media_type})

        item = items[0]
        return json.dumps(
            {
                "found": True,
                "name": item.get("name", "Unknown"),
                "uri": item.get("uri", ""),
                "media_type": media_type,
            }
        )

    @beta_tool
    def play_media(player_id: str, uri: str, radio_mode: bool = False) -> str:
        """Play media on a Music Assistant player.

        Args:
            player_id: Player ID from get_players.
            uri: Media URI from search_media.
            radio_mode: Set True for continuous radio-style playback.
        """
        from music_assistant_models.enums import QueueOption

        client.play_media(queue_id=player_id, media=uri, option=QueueOption.PLAY, radio_mode=radio_mode)
        return json.dumps({"success": True, "player_id": player_id, "uri": uri, "radio_mode": radio_mode})

    @beta_tool
    def pause_playback(player_id: str) -> str:
        """Pause or resume playback on a player.

        Args:
            player_id: Player ID from get_players.
        """
        client.queue_command_pause(player_id)
        return json.dumps({"success": True, "player_id": player_id})

    @beta_tool
    def next_track(player_id: str) -> str:
        """Skip to the next track on a player.

        Args:
            player_id: Player ID from get_players.
        """
        client.queue_command_next(player_id)
        return json.dumps({"success": True, "player_id": player_id})

    @beta_tool
    def previous_track(player_id: str) -> str:
        """Go to the previous track on a player.

        Args:
            player_id: Player ID from get_players.
        """
        client.queue_command_previous(player_id)
        return json.dumps({"success": True, "player_id": player_id})

    @beta_tool
    def set_volume(player_id: str, volume: int) -> str:
        """Set player volume.

        Args:
            player_id: Player ID from get_players.
            volume: Volume level 0-100.
        """
        client.player_command_volume_set(player_id, max(0, min(100, volume)))
        return json.dumps({"success": True, "player_id": player_id, "volume": volume})

    @beta_tool
    def get_player_state(player_id: str) -> str:
        """Get the current playback state of a player (track, volume, playing/paused).

        Args:
            player_id: Player ID from get_players.
        """
        state = client.get_player_state(player_id)
        if state is None:
            return json.dumps({"found": False, "player_id": player_id})
        return json.dumps(state)

    return [
        get_players,
        search_media,
        play_media,
        pause_playback,
        next_track,
        previous_track,
        set_volume,
        get_player_state,
    ]


class MusicAssistantAgent:
    """Claude-powered natural language interface for Music Assistant."""

    def __init__(
        self,
        ma_url: str,
        ma_token: str | None = None,
        anthropic_api_key: str | None = None,
        default_player: str | None = None,
        model: str = "claude-sonnet-4-6",
    ):
        self.ma_client = SimpleHTTPMusicAssistantClient(ma_url, token=ma_token, timeout=30)
        self._anthropic = anthropic.Anthropic(api_key=anthropic_api_key or os.environ["ANTHROPIC_API_KEY"])
        self._tools = create_ma_tools(self.ma_client)
        self.default_player = default_player
        self.model = model

    def run(self, prompt: str) -> str:
        """Process a natural language music control request and return a brief response."""
        system = _SYSTEM_PROMPT
        if self.default_player:
            system += f"\nDefault player (use if no location specified): {self.default_player}"

        runner = self._anthropic.beta.messages.tool_runner(
            model=self.model,
            max_tokens=1024,
            system=system,
            thinking={"type": "adaptive"},
            tools=self._tools,
            messages=[{"role": "user", "content": prompt}],
        )

        last_message = None
        for message in runner:
            last_message = message

        if last_message is None:
            return ""

        return next(
            (block.text for block in last_message.content if hasattr(block, "text")),
            "",
        )
