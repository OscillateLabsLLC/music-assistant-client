import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from ma_http_client.claude_tools import MusicAssistantAgent, create_ma_tools


@pytest.fixture
def mock_ma_client():
    return Mock()


@pytest.fixture
def tools(mock_ma_client):
    return create_ma_tools(mock_ma_client)


@pytest.fixture
def tool_map(tools):
    return {t.name: t for t in tools}


class TestCreateMATools:
    def test_returns_eight_tools(self, tools):
        assert len(tools) == 8

    def test_tool_names(self, tool_map):
        expected = {
            "get_players",
            "search_media",
            "play_media",
            "pause_playback",
            "next_track",
            "previous_track",
            "set_volume",
            "get_player_state",
        }
        assert set(tool_map.keys()) == expected

    def test_get_players_returns_json_list(self, tool_map, mock_ma_client):
        mock_player = Mock()
        mock_player.player_id = "player-1"
        mock_player.name = "Living Room"
        mock_player.available = True
        mock_ma_client.get_players.return_value = [mock_player]

        result = json.loads(tool_map["get_players"]())
        assert result == [{"player_id": "player-1", "name": "Living Room", "available": True}]

    def test_get_players_missing_available_attr(self, tool_map, mock_ma_client):
        mock_player = Mock(spec=["player_id", "name"])
        mock_player.player_id = "p1"
        mock_player.name = "Kitchen"
        mock_ma_client.get_players.return_value = [mock_player]

        result = json.loads(tool_map["get_players"]())
        assert result[0]["available"] is False

    def test_search_media_found(self, tool_map, mock_ma_client):
        mock_ma_client.search_media.return_value = {
            "artists": [{"name": "Radiohead", "uri": "library://artist/1"}]
        }

        result = json.loads(tool_map["search_media"]("Radiohead", "artist"))
        assert result["found"] is True
        assert result["name"] == "Radiohead"
        assert result["uri"] == "library://artist/1"
        assert result["media_type"] == "artist"

    def test_search_media_not_found(self, tool_map, mock_ma_client):
        mock_ma_client.search_media.return_value = {"artists": []}

        result = json.loads(tool_map["search_media"]("Unknown Artist", "artist"))
        assert result["found"] is False
        assert result["query"] == "Unknown Artist"

    def test_search_media_default_type(self, tool_map, mock_ma_client):
        mock_ma_client.search_media.return_value = {
            "artists": [{"name": "Radiohead", "uri": "library://artist/1"}]
        }

        result = json.loads(tool_map["search_media"]("Radiohead"))
        assert result["found"] is True

    def test_search_media_track_type(self, tool_map, mock_ma_client):
        mock_ma_client.search_media.return_value = {
            "tracks": [{"name": "Creep", "uri": "library://track/42"}]
        }

        result = json.loads(tool_map["search_media"]("Creep", "track"))
        assert result["found"] is True
        assert result["uri"] == "library://track/42"

    def test_search_media_playlist_type(self, tool_map, mock_ma_client):
        mock_ma_client.search_media.return_value = {
            "playlists": [{"name": "My Playlist", "uri": "library://playlist/5"}]
        }

        result = json.loads(tool_map["search_media"]("My Playlist", "playlist"))
        assert result["found"] is True

    def test_search_media_unknown_type_falls_back(self, tool_map, mock_ma_client):
        mock_ma_client.search_media.return_value = {"artists": []}

        result = json.loads(tool_map["search_media"]("something", "bogus"))
        assert result["found"] is False

    def test_play_media_success(self, tool_map, mock_ma_client):
        result = json.loads(tool_map["play_media"]("player-1", "library://artist/1"))
        mock_ma_client.play_media.assert_called_once()
        assert result["success"] is True
        assert result["player_id"] == "player-1"
        assert result["uri"] == "library://artist/1"
        assert result["radio_mode"] is False

    def test_play_media_radio_mode(self, tool_map, mock_ma_client):
        result = json.loads(tool_map["play_media"]("player-1", "library://artist/1", True))
        assert result["radio_mode"] is True

    def test_pause_playback(self, tool_map, mock_ma_client):
        result = json.loads(tool_map["pause_playback"]("player-1"))
        mock_ma_client.queue_command_pause.assert_called_once_with("player-1")
        assert result["success"] is True
        assert result["player_id"] == "player-1"

    def test_next_track(self, tool_map, mock_ma_client):
        result = json.loads(tool_map["next_track"]("player-1"))
        mock_ma_client.queue_command_next.assert_called_once_with("player-1")
        assert result["success"] is True

    def test_previous_track(self, tool_map, mock_ma_client):
        result = json.loads(tool_map["previous_track"]("player-1"))
        mock_ma_client.queue_command_previous.assert_called_once_with("player-1")
        assert result["success"] is True

    def test_set_volume_clamps_to_range(self, tool_map, mock_ma_client):
        tool_map["set_volume"]("player-1", 150)
        mock_ma_client.player_command_volume_set.assert_called_with("player-1", 100)

        tool_map["set_volume"]("player-1", -10)
        mock_ma_client.player_command_volume_set.assert_called_with("player-1", 0)

    def test_set_volume_valid(self, tool_map, mock_ma_client):
        result = json.loads(tool_map["set_volume"]("player-1", 50))
        mock_ma_client.player_command_volume_set.assert_called_with("player-1", 50)
        assert result["success"] is True
        assert result["volume"] == 50

    def test_get_player_state_found(self, tool_map, mock_ma_client):
        mock_ma_client.get_player_state.return_value = {
            "state": "playing",
            "player_name": "Living Room",
        }

        result = json.loads(tool_map["get_player_state"]("player-1"))
        assert result["state"] == "playing"

    def test_get_player_state_not_found(self, tool_map, mock_ma_client):
        mock_ma_client.get_player_state.return_value = None

        result = json.loads(tool_map["get_player_state"]("player-1"))
        assert result["found"] is False
        assert result["player_id"] == "player-1"


class TestMusicAssistantAgent:
    @pytest.fixture
    def mock_anthropic_cls(self):
        with patch("ma_http_client.claude_tools.anthropic.Anthropic") as mock_cls:
            yield mock_cls

    @pytest.fixture
    def agent(self, mock_anthropic_cls):
        return MusicAssistantAgent(
            ma_url="http://localhost:8095",
            ma_token="test-token",
            anthropic_api_key="test-api-key",
        )

    def test_init_creates_ma_client(self, agent):
        assert agent.ma_client is not None
        assert agent.ma_client.server_url == "http://localhost:8095"

    def test_init_stores_default_player(self, mock_anthropic_cls):
        a = MusicAssistantAgent(
            ma_url="http://localhost:8095",
            anthropic_api_key="key",
            default_player="Living Room",
        )
        assert a.default_player == "Living Room"

    def test_init_default_model(self, agent):
        assert agent.model == "claude-sonnet-4-6"

    def test_init_custom_model(self, mock_anthropic_cls):
        a = MusicAssistantAgent(
            ma_url="http://localhost:8095",
            anthropic_api_key="key",
            model="claude-sonnet-4-6",
        )
        assert a.model == "claude-sonnet-4-6"

    def test_init_creates_tools(self, agent):
        assert len(agent._tools) == 8

    def test_run_returns_text_from_last_message(self, agent, mock_anthropic_cls):
        mock_text_block = Mock()
        mock_text_block.text = "Playing Radiohead in the living room."

        mock_last_message = Mock()
        mock_last_message.content = [mock_text_block]

        mock_runner = iter([Mock(), mock_last_message])
        mock_anthropic_cls.return_value.beta.messages.tool_runner.return_value = mock_runner

        result = agent.run("Play some Radiohead")
        assert result == "Playing Radiohead in the living room."

    def test_run_returns_empty_string_when_no_messages(self, agent, mock_anthropic_cls):
        mock_anthropic_cls.return_value.beta.messages.tool_runner.return_value = iter([])

        result = agent.run("Play something")
        assert result == ""

    def test_run_skips_non_text_blocks(self, agent, mock_anthropic_cls):
        mock_thinking_block = Mock(spec=[])  # no .text attr
        mock_text_block = Mock()
        mock_text_block.text = "Done."

        mock_last_message = Mock()
        mock_last_message.content = [mock_thinking_block, mock_text_block]

        mock_anthropic_cls.return_value.beta.messages.tool_runner.return_value = iter([mock_last_message])

        result = agent.run("Pause")
        assert result == "Done."

    def test_run_includes_default_player_in_system(self, mock_anthropic_cls):
        captured = {}

        def capture_kwargs(**kwargs):
            captured.update(kwargs)
            return iter([])

        mock_anthropic_cls.return_value.beta.messages.tool_runner.side_effect = capture_kwargs

        agent = MusicAssistantAgent(
            ma_url="http://localhost:8095",
            anthropic_api_key="key",
            default_player="Kitchen",
        )
        agent.run("Play jazz")

        assert "Kitchen" in captured["system"]

    def test_run_passes_correct_model(self, mock_anthropic_cls):
        captured = {}

        def capture_kwargs(**kwargs):
            captured.update(kwargs)
            return iter([])

        mock_anthropic_cls.return_value.beta.messages.tool_runner.side_effect = capture_kwargs

        agent = MusicAssistantAgent(
            ma_url="http://localhost:8095",
            anthropic_api_key="key",
        )
        agent.run("Test")

        assert captured["model"] == "claude-sonnet-4-6"

    def test_run_passes_adaptive_thinking(self, mock_anthropic_cls):
        captured = {}

        def capture_kwargs(**kwargs):
            captured.update(kwargs)
            return iter([])

        mock_anthropic_cls.return_value.beta.messages.tool_runner.side_effect = capture_kwargs

        agent = MusicAssistantAgent(
            ma_url="http://localhost:8095",
            anthropic_api_key="key",
        )
        agent.run("Test")

        assert captured["thinking"] == {"type": "adaptive"}

    def test_run_passes_user_prompt(self, mock_anthropic_cls):
        captured = {}

        def capture_kwargs(**kwargs):
            captured.update(kwargs)
            return iter([])

        mock_anthropic_cls.return_value.beta.messages.tool_runner.side_effect = capture_kwargs

        agent = MusicAssistantAgent(
            ma_url="http://localhost:8095",
            anthropic_api_key="key",
        )
        agent.run("Play some jazz")

        assert captured["messages"] == [{"role": "user", "content": "Play some jazz"}]

    def test_init_uses_env_var_for_api_key(self, mock_anthropic_cls):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"}):
            MusicAssistantAgent(ma_url="http://localhost:8095")
        mock_anthropic_cls.assert_called_with(api_key="env-key")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
