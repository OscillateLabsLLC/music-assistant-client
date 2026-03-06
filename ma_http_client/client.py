import functools
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

import requests
from music_assistant_models.enums import MediaType, QueueOption
from music_assistant_models.errors import MusicAssistantError
from music_assistant_models.player import Player


def debug_method(func):
    """Decorator to log method inputs and outputs for debugging purposes."""

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Format arguments for logging
        args_str = ", ".join([repr(arg) for arg in args])
        kwargs_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])

        # Combine args and kwargs for display
        all_args = []
        if args_str:
            all_args.append(args_str)
        if kwargs_str:
            all_args.append(kwargs_str)
        args_display = ", ".join(all_args)

        # Log the method call
        method_name = f"{self.__class__.__name__}.{func.__name__}"
        self.log.debug(f"CALL {method_name}({args_display})")

        try:
            # Execute the function
            result = func(self, *args, **kwargs)

            # Format result for logging (truncate if too long)
            if result is None:
                result_str = "None"
            elif isinstance(result, (str, int, float, bool)):
                result_str = repr(result)
            elif isinstance(result, (list, dict)):
                result_str = json.dumps(result, default=str, indent=None)
                if len(result_str) > 200:
                    result_str = result_str[:200] + "..."
            else:
                result_str = f"<{type(result).__name__} object>"

            self.log.debug(f"RETURN {method_name} -> {result_str}")
            return result

        except Exception as e:
            self.log.debug(f"ERROR {method_name} -> {type(e).__name__}: {e}")
            raise

    return wrapper


class SimpleHTTPMusicAssistantClient:
    """Simple HTTP-based Music Assistant client that avoids WebSocket issues."""

    def __init__(
        self,
        server_url: str,
        token: str | None = None,
        session: requests.Session | None = None,
    ):
        self.server_url = server_url.rstrip("/")
        self.api_url = f"{self.server_url}/api"
        self.token = token
        self.session = session or requests.Session()
        self.log = logging.getLogger(__name__)

    @debug_method
    def send_command(self, command: str, **args) -> Any:
        """Send a command to Music Assistant via HTTP API."""
        payload = {"command": command, "message_id": uuid.uuid4().hex, "args": args}

        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        response = self.session.post(self.api_url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        raise MusicAssistantError(f"HTTP {response.status_code}: {response.text}")

    @debug_method
    def get_players(self) -> List[Player]:
        """Get all available players."""
        result = self.send_command("players/all")
        return [Player.from_dict(player_data) for player_data in result]

    def search_media(
        self, query: str, media_types: Optional[List[MediaType]] = None, limit: int = 5
    ) -> Dict[str, Any]:
        """Search for media."""
        args = {"search_query": query, "limit": limit}
        if media_types:
            args["media_types"] = [mt.value for mt in media_types]
        return self.send_command("music/search", **args)

    def track_info(self, uri: str) -> Dict[str, Any]:
        """Search for media."""
        args = {"uri": uri}
        return self.send_command("music/item_by_uri", **args)

    def recommendations(self) -> Dict[str, Any]:
        """Search for media."""
        return self.send_command("music/recommendations")

    def recently_played(self) -> Dict[str, Any]:
        """Search for media."""
        return self.send_command("music/recently_played_items")

    def play_media(
        self,
        queue_id: str,
        media: str,
        option: QueueOption = QueueOption.PLAY,  # type: ignore
        radio_mode: bool = False,
    ):
        """Play media on a player queue."""
        self.log.info(
            f"Sending play_media: queue_id={queue_id}, media={media}, option={option.value}, "
            f"radio_mode={radio_mode}"
        )
        return self.send_command(
            command="player_queues/play_media",
            queue_id=queue_id,
            media=media,
            option=option.value,
            radio_mode=radio_mode,
        )

    def queue_command_play(self, queue_id: str):
        """Send PLAY command to given queue."""
        return self.send_command("player_queues/play", queue_id=queue_id)

    def queue_command_pause(self, queue_id: str):
        """Pause playback."""
        return self.send_command("player_queues/play_pause", queue_id=queue_id)

    def queue_command_next(self, queue_id: str):
        """Skip to next track."""
        return self.send_command("player_queues/next", queue_id=queue_id)

    def queue_command_previous(self, queue_id: str):
        """Go to previous track."""
        return self.send_command("player_queues/previous", queue_id=queue_id)

    def player_command_power_on(self, player_id: str):
        """Power on a player."""
        return self.send_command("players/player_command_power_on", player_id=player_id)

    def player_command_power_off(self, player_id: str):
        """Power off a player."""
        return self.send_command("players/player_command_power_off", player_id=player_id)

    # Volume control commands
    def player_command_volume_set(self, player_id: str, volume: int):
        """Set player volume (0-100)."""
        return self.send_command("players/cmd/volume_set", player_id=player_id, volume_level=volume)

    def player_command_volume_up(self, player_id: str):
        """Increase player volume."""
        return self.send_command("players/cmd/volume_up", player_id=player_id)

    def player_command_volume_down(self, player_id: str):
        """Decrease player volume."""
        return self.send_command("players/cmd/volume_down", player_id=player_id)

    def player_command_volume_mute(self, player_id: str, muted: bool = True):
        """Mute/unmute player."""
        return self.send_command("players/cmd/volume_mute", player_id=player_id, muted=muted)

    # player controls
    def player_command_seek(self, player_id: str, position: int) -> None:
        """Handle SEEK command for given player.

        - player_id: player_id of the player to handle the command.
        - position: position in seconds to seek to in the current playing item.
        """
        return self.send_command("players/cmd/seek", player_id=player_id, position=position)

    def player_command_stop(self, player_id: str) -> None:
        """Handle STOP command for given player.

        - player_id: player_id of the player to handle the command.
        """
        return self.send_command("players/cmd/stop", player_id=player_id)

    # State checking methods
    def get_player_queue_items(self, queue_id: str, limit: int = 10, offset: int = 0):
        """Get current queue items for a player."""
        return self.send_command("player_queues/items", queue_id=queue_id, limit=limit, offset=offset)

    def get_active_queue(self, player_id: str):
        """Get the current active queue for a player."""
        return self.send_command("player_queues/get_active_queue", player_id=player_id)

    def _find_player_by_id(self, player_id: str) -> Optional[Player]:
        """Find a player by ID."""
        players = self.get_players()
        for player in players:
            if player.player_id == player_id:
                return player
        return None

    def _extract_playback_state(self, player: Player) -> str:
        """Extract playback state from player object."""
        if not hasattr(player, "playback_state"):
            return "unknown"

        state = player.playback_state
        return state.value if hasattr(state, "value") else str(state)

    def _extract_track_from_media(self, player: Player) -> Optional[str]:
        """Extract track name from player's current_media."""
        if not (hasattr(player, "current_media") and player.current_media):
            return None

        media = player.current_media
        if not (hasattr(media, "title") and media.title):
            return None

        track_name = media.title
        if hasattr(media, "artist") and media.artist:
            return f"{media.artist} - {track_name}"
        return track_name

    def _extract_track_from_queue(self, player: Player) -> Optional[str]:
        """Extract track name from player's queue items."""
        if not (hasattr(player, "current_item_id") and player.current_item_id):
            return None

        try:
            queue_items = self.get_player_queue_items(player.player_id, limit=1)
            if not (queue_items and len(queue_items) > 0):
                return None

            item = queue_items[0]
            if hasattr(item, "name") and item.name:
                return item.name
            if hasattr(item, "media_item") and item.media_item:
                return getattr(item.media_item, "name", None)
        except:
            self.log.exception("Error extracting track from queue, returning None")
        return None

    def _extract_current_track(self, player: Player) -> str:
        """Extract current track name with artist info."""
        track_name = self._extract_track_from_media(player)
        if track_name:
            return track_name

        track_name = self._extract_track_from_queue(player)
        if track_name:
            return track_name

        return "No track"

    def get_player_state(self, player_id: str):
        """Get current player state (playing, paused, etc.)."""
        player = self._find_player_by_id(player_id)
        if not player:
            return None

        return {
            "state": self._extract_playback_state(player),
            "powered": getattr(player, "powered", True),
            "volume_level": getattr(player, "volume_level", None),
            "volume_muted": getattr(player, "volume_muted", False),
            "current_track": self._extract_current_track(player),
            "player_name": getattr(player, "name", "Unknown"),
            "player_type": getattr(player, "provider", "Unknown"),
            "available": getattr(player, "available", False),
        }

    @debug_method
    def _format_status_emoji(self, state: str) -> str:
        """Map player state to appropriate emoji."""
        emoji_map = {"playing": "▶️", "paused": "⏸️", "stopped": "⏹️", "idle": "💤"}
        return emoji_map.get(state.lower(), "❓")

    @debug_method
    def _format_power_display(self, powered: bool) -> str:
        """Format power status display."""
        return "🔌" if powered else "🔌❌"

    @debug_method
    def _format_volume_display(self, volume_level: Optional[int], volume_muted: bool) -> str:
        """Format volume display with mute status."""
        volume_emoji = "🔇" if volume_muted else "🔊"
        if volume_level is not None:
            return f"{volume_emoji} {volume_level}%"
        return f"{volume_emoji} ?"

    @debug_method
    def show_current_state(self, player_id: str, action: str = ""):
        """Display current player state and track info."""
        try:
            state = self.get_player_state(player_id)
            if not state:
                self.log.warning(f"   {action} - Could not get player state")
                return

            status_emoji = self._format_status_emoji(state["state"])
            power_display = self._format_power_display(state["powered"])
            volume_display = self._format_volume_display(state["volume_level"], state.get("volume_muted", False))

            self.log.info(
                f"   {action} - {status_emoji} {state['state'].title()} | {power_display} | {volume_display}"
            )
            self.log.info(f"   Current: {state.get('current_track', 'No track')}")

        except Exception as e:
            self.log.exception(f"   {action} - Error getting state: {e}")
