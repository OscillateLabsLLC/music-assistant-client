"""
Debug Music Assistant client with fixture capture capabilities.

This client extends the SimpleHTTPMusicAssistantClient with debugging features:
- Captures all API responses as JSON fixtures
- Logs detailed request/response data
- Handles circular references in Music Assistant models
- Perfect for troubleshooting new MA versions or regressions

Usage:
    from music_assistant_client.debug import DebugMusicAssistantClient

    # Enable fixture capture
    client = DebugMusicAssistantClient("http://localhost:8095",
                                       fixture_capture=True,
                                       fixture_dir="./debug_fixtures")

    # Use exactly like the normal client
    players = client.get_players()
    # Fixtures are automatically saved to debug_fixtures/
"""

import json
import os
import uuid
from typing import Any, Dict, List, Optional

import requests
from music_assistant_models.enums import MediaType
from music_assistant_models.errors import MusicAssistantError
from music_assistant_models.player import Player

from .client import SimpleHTTPMusicAssistantClient


class DebugMusicAssistantClient(SimpleHTTPMusicAssistantClient):
    """Music Assistant client with advanced debugging and fixture capture."""

    def __init__(
        self,
        server_url: str,
        session: requests.Session | None = None,
        fixture_capture: bool = True,
        fixture_dir: str | None = None,
    ):
        super().__init__(server_url, session=session)

        # Debug configuration
        self.fixture_capture_enabled = fixture_capture
        self.fixture_dir = fixture_dir or os.path.join(os.path.dirname(__file__), "..", "debug_fixtures")
        self.fixture_counter = 1

    def send_command(self, command: str, **args) -> Any:
        """Send command with optional fixture capture."""
        payload = {"command": command, "message_id": uuid.uuid4().hex, "args": args}

        response = self.session.post(self.api_url, json=payload)
        if response.status_code == 200:
            result = response.json()

            # Capture fixture if enabled
            if self.fixture_capture_enabled:
                self._save_fixture(
                    f"send_command_{command.replace('/', '_')}", {"command": command, "args": args, "response": result}
                )

            return result
        raise MusicAssistantError(f"HTTP {response.status_code}: {response.text}")

    def get_players(self) -> List[Player]:
        """Get players with optional fixture capture."""
        result = self.send_command("players/all")
        players = [Player.from_dict(player_data) for player_data in result]

        # Capture processed players fixture
        if self.fixture_capture_enabled:
            self._save_fixture(
                "get_players",
                {
                    "raw_response": result,
                    "player_count": len(players),
                    "players": [self._serialize_for_json(player) for player in players],
                },
            )

        return players

    def search_media(
        self, query: str, media_types: Optional[List[MediaType]] = None, limit: int = 5
    ) -> Dict[str, Any]:
        """Search media with optional fixture capture."""
        args = {"search_query": query, "limit": limit}
        if media_types:
            args["media_types"] = [mt.value for mt in media_types]

        result = self.send_command("music/search", **args)

        # Capture search results fixture
        if self.fixture_capture_enabled:
            self._save_fixture(
                "search_media",
                {
                    "query": query,
                    "media_types": [mt.value for mt in media_types] if media_types else None,
                    "limit": limit,
                    "result": result,
                },
            )

        return result

    def get_player_state(self, player_id: str):
        """Get player state with optional fixture capture."""
        player = self._find_player_by_id(player_id)
        if not player:
            if self.fixture_capture_enabled:
                self._save_fixture("get_player_state_not_found", {"player_id": player_id, "result": None})
            return None

        state = {
            "state": self._extract_playback_state(player),
            "powered": getattr(player, "powered", True),
            "volume_level": getattr(player, "volume_level", None),
            "volume_muted": getattr(player, "volume_muted", False),
            "current_track": self._extract_current_track(player),
            "player_name": getattr(player, "name", "Unknown"),
        }

        # Capture player state fixture
        if self.fixture_capture_enabled:
            self._save_fixture(
                "get_player_state",
                {"player_id": player_id, "raw_player": self._serialize_for_json(player), "processed_state": state},
            )

        return state

    def _save_fixture(self, name: str, data: Any):
        """Save fixture data to JSON file."""
        if not self.fixture_capture_enabled:
            return

        try:
            os.makedirs(self.fixture_dir, exist_ok=True)
            filename = f"{self.fixture_counter:03d}_{name}.json"
            filepath = os.path.join(self.fixture_dir, filename)

            # Convert data to JSON-serializable format
            json_data = self._serialize_for_json(data)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2)

            self.log.info(f"Saved debug fixture: {filename}")
            self.fixture_counter += 1
        except Exception as e:
            self.log.warning(f"Failed to save debug fixture {name}: {e}")

    def _serialize_for_json(self, data: Any, visited: Optional[set] = None) -> Any:
        """Convert data to JSON-serializable format with circular reference protection."""
        if visited is None:
            visited = set()

        # Check for circular references
        obj_id = id(data)
        if obj_id in visited:
            return f"<circular_ref:{type(data).__name__}>"

        if isinstance(data, list):
            return [self._serialize_for_json(item, visited) for item in data]
        elif isinstance(data, dict):
            return {k: self._serialize_for_json(v, visited) for k, v in data.items()}
        elif hasattr(data, "value") and type(data).__name__ not in ("type", "function"):
            # Handle enums before generic __dict__ serialization
            return data.value
        elif hasattr(data, "__dict__"):
            visited.add(obj_id)
            try:
                # Handle dataclass/model objects
                result = {k: self._serialize_for_json(v, visited) for k, v in data.__dict__.items()}
                visited.remove(obj_id)
                return result
            except:
                visited.remove(obj_id)
                return f"<object:{type(data).__name__}>"
        else:
            # Basic types or convert to string
            try:
                json.dumps(data)
                return data
            except (TypeError, ValueError):
                return str(data)

    def enable_fixture_capture(self, fixture_dir: str | None = None):
        """Enable fixture capture for debugging."""
        self.fixture_capture_enabled = True
        if fixture_dir:
            self.fixture_dir = fixture_dir
        self.log.info(f"Debug fixture capture enabled: {self.fixture_dir}")

    def disable_fixture_capture(self):
        """Disable fixture capture for normal operation."""
        self.fixture_capture_enabled = False
        self.log.info("Debug fixture capture disabled")

    def get_fixture_stats(self) -> Dict[str, Any]:
        """Get statistics about captured fixtures."""
        if not os.path.exists(self.fixture_dir):
            return {"fixture_count": 0, "fixture_dir": self.fixture_dir, "exists": False}

        fixture_files = [f for f in os.listdir(self.fixture_dir) if f.endswith(".json")]
        return {
            "fixture_count": len(fixture_files),
            "fixture_dir": self.fixture_dir,
            "exists": True,
            "latest_counter": self.fixture_counter - 1,
            "files": sorted(fixture_files),
        }
