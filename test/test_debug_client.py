import json
import os
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
import requests
from music_assistant_models.enums import MediaType
from music_assistant_models.player import Player

from ma_http_client.debug import DebugMusicAssistantClient


class TestDebugMusicAssistantClient:
    """Tests for DebugMusicAssistantClient."""

    @pytest.fixture
    def fixtures_dir(self):
        return Path(__file__).parent / "fixtures"

    @pytest.fixture
    def load_fixture(self, fixtures_dir):
        def _load(filename: str) -> Dict[str, Any]:
            with open(fixtures_dir / filename, "r", encoding="utf-8") as f:
                return json.load(f)

        return _load

    @pytest.fixture
    def mock_session(self):
        return Mock(spec=requests.Session)

    @pytest.fixture
    def client(self, mock_session, tmp_path):
        return DebugMusicAssistantClient(
            server_url="http://test-server:8095",
            session=mock_session,
            fixture_capture=True,
            fixture_dir=str(tmp_path / "fixtures"),
        )

    @pytest.fixture
    def client_no_capture(self, mock_session, tmp_path):
        return DebugMusicAssistantClient(
            server_url="http://test-server:8095",
            session=mock_session,
            fixture_capture=False,
            fixture_dir=str(tmp_path / "fixtures"),
        )

    # --- Initialization ---

    def test_init_defaults(self, mock_session):
        client = DebugMusicAssistantClient("http://localhost:8095", session=mock_session)
        assert client.fixture_capture_enabled is True
        assert client.fixture_counter == 1
        assert "debug_fixtures" in client.fixture_dir

    def test_init_custom_fixture_dir(self, mock_session, tmp_path):
        client = DebugMusicAssistantClient(
            "http://localhost:8095", session=mock_session, fixture_dir=str(tmp_path)
        )
        assert client.fixture_dir == str(tmp_path)

    def test_init_capture_disabled(self, mock_session):
        client = DebugMusicAssistantClient(
            "http://localhost:8095", session=mock_session, fixture_capture=False
        )
        assert client.fixture_capture_enabled is False

    # --- send_command ---

    def test_send_command_saves_fixture(self, client, mock_session):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "ok"}
        mock_session.post.return_value = mock_response

        result = client.send_command("players/all")

        assert result == {"result": "ok"}
        fixture_files = os.listdir(client.fixture_dir)
        assert len(fixture_files) == 1
        assert "send_command_players_all" in fixture_files[0]

    def test_send_command_fixture_content(self, client, mock_session):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"player_id": "abc"}]
        mock_session.post.return_value = mock_response

        client.send_command("players/all")

        fixture_path = os.path.join(client.fixture_dir, os.listdir(client.fixture_dir)[0])
        with open(fixture_path) as f:
            data = json.load(f)
        assert data["command"] == "players/all"
        assert data["response"] == [{"player_id": "abc"}]

    def test_send_command_no_capture(self, client_no_capture, mock_session):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_session.post.return_value = mock_response

        client_no_capture.send_command("players/all")

        assert not os.path.exists(client_no_capture.fixture_dir)

    def test_send_command_increments_counter(self, client, mock_session):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session.post.return_value = mock_response

        client.send_command("cmd/one")
        client.send_command("cmd/two")

        assert client.fixture_counter == 3
        files = sorted(os.listdir(client.fixture_dir))
        assert files[0].startswith("001_")
        assert files[1].startswith("002_")

    def test_send_command_http_error(self, client, mock_session):
        from music_assistant_models.errors import MusicAssistantError

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_session.post.return_value = mock_response

        with pytest.raises(MusicAssistantError):
            client.send_command("players/all")

    # --- get_players ---

    def test_get_players_saves_fixture(self, client, mock_session, load_fixture):
        fixture = load_fixture("001_send_command_players_all.json")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = fixture["response"]
        mock_session.post.return_value = mock_response

        players = client.get_players()

        assert len(players) > 0
        # send_command fixture + get_players fixture
        assert client.fixture_counter == 3

    def test_get_players_no_capture(self, client_no_capture, mock_session, load_fixture):
        fixture = load_fixture("001_send_command_players_all.json")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = fixture["response"]
        mock_session.post.return_value = mock_response

        players = client_no_capture.get_players()

        assert len(players) > 0
        assert not os.path.exists(client_no_capture.fixture_dir)

    # --- search_media ---

    def test_search_media_saves_fixture(self, client, mock_session, load_fixture):
        fixture = load_fixture("006_search_media.json")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = fixture["result"]
        mock_session.post.return_value = mock_response

        result = client.search_media("Radiohead")

        assert result == fixture["result"]
        files = os.listdir(client.fixture_dir)
        assert any("search_media" in f for f in files)

    def test_search_media_with_media_types(self, client, mock_session):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tracks": []}
        mock_session.post.return_value = mock_response

        client.search_media("test", media_types=[MediaType.TRACK])

        files = os.listdir(client.fixture_dir)
        fixture_path = os.path.join(client.fixture_dir, sorted(files)[-1])
        with open(fixture_path) as f:
            data = json.load(f)
        assert data["media_types"] == ["track"]

    def test_search_media_no_capture(self, client_no_capture, mock_session):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session.post.return_value = mock_response

        client_no_capture.search_media("test")

        assert not os.path.exists(client_no_capture.fixture_dir)

    # --- get_player_state ---

    def test_get_player_state_found(self, client, mock_session, load_fixture):
        fixture = load_fixture("002_get_players.json")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = fixture["raw_response"]
        mock_session.post.return_value = mock_response

        player_id = fixture["raw_response"][0]["player_id"]
        state = client.get_player_state(player_id)

        assert state is not None
        assert "state" in state
        files = os.listdir(client.fixture_dir)
        assert any("get_player_state" in f for f in files)

    def test_get_player_state_not_found(self, client, mock_session, load_fixture):
        fixture = load_fixture("002_get_players.json")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = fixture["raw_response"]
        mock_session.post.return_value = mock_response

        state = client.get_player_state("nonexistent-id")

        assert state is None
        files = os.listdir(client.fixture_dir)
        assert any("get_player_state_not_found" in f for f in files)

    def test_get_player_state_found_no_capture(self, client_no_capture, mock_session, load_fixture):
        fixture = load_fixture("002_get_players.json")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = fixture["raw_response"]
        mock_session.post.return_value = mock_response

        player_id = fixture["raw_response"][0]["player_id"]
        state = client_no_capture.get_player_state(player_id)

        assert state is not None
        assert not os.path.exists(client_no_capture.fixture_dir)

    def test_get_player_state_not_found_no_capture(self, client_no_capture, mock_session, load_fixture):
        fixture = load_fixture("002_get_players.json")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = fixture["raw_response"]
        mock_session.post.return_value = mock_response

        state = client_no_capture.get_player_state("nonexistent-id")

        assert state is None
        assert not os.path.exists(client_no_capture.fixture_dir)

    # --- _save_fixture ---

    def test_save_fixture_disabled(self, client, tmp_path):
        client.fixture_capture_enabled = False
        client._save_fixture("test", {"data": 1})
        assert not os.path.exists(os.path.join(client.fixture_dir, "001_test.json"))

    def test_save_fixture_write_error(self, client):
        client.fixture_dir = "/nonexistent/readonly/path"
        # Should not raise — logs warning instead
        client._save_fixture("test", {"data": 1})

    # --- _serialize_for_json ---

    def test_serialize_primitives(self, client):
        assert client._serialize_for_json(42) == 42
        assert client._serialize_for_json("hello") == "hello"
        assert client._serialize_for_json(True) is True
        assert client._serialize_for_json(None) is None

    def test_serialize_list(self, client):
        assert client._serialize_for_json([1, 2, 3]) == [1, 2, 3]

    def test_serialize_dict(self, client):
        assert client._serialize_for_json({"a": 1}) == {"a": 1}

    def test_serialize_enum(self, client):
        result = client._serialize_for_json(MediaType.TRACK)
        assert result == "track"

    def test_serialize_object_with_dict(self, client):
        class Obj:
            def __init__(self):
                self.x = 1
                self.y = "hello"

        result = client._serialize_for_json(Obj())
        assert result == {"x": 1, "y": "hello"}

    def test_serialize_circular_reference(self, client):
        class Node:
            def __init__(self):
                self.self_ref = None

        node = Node()
        node.self_ref = node
        result = client._serialize_for_json(node)
        assert result["self_ref"].startswith("<circular_ref:")

    def test_serialize_non_json_type(self, client):
        import datetime

        dt = datetime.datetime(2024, 1, 1, 12, 0, 0)
        result = client._serialize_for_json(dt)
        assert result == str(dt)

    # --- enable/disable fixture capture ---

    def test_enable_fixture_capture(self, client_no_capture, tmp_path):
        new_dir = str(tmp_path / "new_fixtures")
        client_no_capture.enable_fixture_capture(fixture_dir=new_dir)
        assert client_no_capture.fixture_capture_enabled is True
        assert client_no_capture.fixture_dir == new_dir

    def test_enable_fixture_capture_no_dir(self, client_no_capture):
        original_dir = client_no_capture.fixture_dir
        client_no_capture.enable_fixture_capture()
        assert client_no_capture.fixture_capture_enabled is True
        assert client_no_capture.fixture_dir == original_dir

    def test_disable_fixture_capture(self, client):
        client.disable_fixture_capture()
        assert client.fixture_capture_enabled is False

    # --- get_fixture_stats ---

    def test_get_fixture_stats_dir_missing(self, client):
        stats = client.get_fixture_stats()
        assert stats["exists"] is False
        assert stats["fixture_count"] == 0

    def test_get_fixture_stats_with_fixtures(self, client, mock_session):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session.post.return_value = mock_response

        client.send_command("cmd/one")
        client.send_command("cmd/two")

        stats = client.get_fixture_stats()
        assert stats["exists"] is True
        assert stats["fixture_count"] == 2
        assert stats["latest_counter"] == 2
        assert len(stats["files"]) == 2
