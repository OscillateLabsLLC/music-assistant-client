import json
from unittest.mock import Mock, patch

import pytest

from ma_http_client.cli import main


@pytest.fixture
def mock_client():
    with patch("ma_http_client.cli.SimpleHTTPMusicAssistantClient") as cls:
        yield cls.return_value


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("MA_URL", "http://test:8095")
    monkeypatch.setenv("MA_TOKEN", "test-token")


class TestCLIPlayers:
    def test_players(self, mock_client, env, capsys):
        player = Mock()
        player.player_id = "p1"
        player.name = "Office"
        player.available = True
        mock_client.get_players.return_value = [player]

        with patch("sys.argv", ["ma-client", "players"]):
            main()

        out = json.loads(capsys.readouterr().out)
        assert out == [{"player_id": "p1", "name": "Office", "available": True}]


class TestCLISearch:
    def test_search_default_type(self, mock_client, env, capsys):
        mock_client.search_media.return_value = {"artists": [{"name": "Radiohead"}]}

        with patch("sys.argv", ["ma-client", "search", "Radiohead"]):
            main()

        out = json.loads(capsys.readouterr().out)
        assert out["artists"][0]["name"] == "Radiohead"

    def test_search_with_type(self, mock_client, env, capsys):
        mock_client.search_media.return_value = {"tracks": [{"name": "Creep"}]}

        with patch("sys.argv", ["ma-client", "search", "Creep", "--type", "track"]):
            main()

        out = json.loads(capsys.readouterr().out)
        assert "tracks" in out

    def test_search_with_limit(self, mock_client, env, capsys):
        mock_client.search_media.return_value = {"artists": []}

        with patch("sys.argv", ["ma-client", "search", "test", "--limit", "3"]):
            main()

        mock_client.search_media.assert_called_once()
        call_kwargs = mock_client.search_media.call_args
        assert call_kwargs[1]["limit"] == 3 or call_kwargs[0][2] == 3


class TestCLIPlay:
    def test_play(self, mock_client, env, capsys):
        with patch("sys.argv", ["ma-client", "play", "p1", "library://artist/1"]):
            main()

        mock_client.play_media.assert_called_once()
        out = json.loads(capsys.readouterr().out)
        assert out["success"] is True
        assert out["player_id"] == "p1"

    def test_play_radio(self, mock_client, env, capsys):
        with patch("sys.argv", ["ma-client", "play", "p1", "library://artist/1", "--radio"]):
            main()

        call_kwargs = mock_client.play_media.call_args[1]
        assert call_kwargs["radio_mode"] is True


class TestCLIControls:
    def test_pause(self, mock_client, env, capsys):
        with patch("sys.argv", ["ma-client", "pause", "p1"]):
            main()
        mock_client.queue_command_pause.assert_called_once_with("p1")

    def test_next(self, mock_client, env, capsys):
        with patch("sys.argv", ["ma-client", "next", "p1"]):
            main()
        mock_client.queue_command_next.assert_called_once_with("p1")

    def test_previous(self, mock_client, env, capsys):
        with patch("sys.argv", ["ma-client", "previous", "p1"]):
            main()
        mock_client.queue_command_previous.assert_called_once_with("p1")


class TestCLIVolume:
    def test_volume(self, mock_client, env, capsys):
        with patch("sys.argv", ["ma-client", "volume", "p1", "50"]):
            main()
        mock_client.player_command_volume_set.assert_called_once_with("p1", 50)
        out = json.loads(capsys.readouterr().out)
        assert out["volume"] == 50

    def test_volume_clamps_high(self, mock_client, env, capsys):
        with patch("sys.argv", ["ma-client", "volume", "p1", "150"]):
            main()
        mock_client.player_command_volume_set.assert_called_once_with("p1", 100)

    def test_volume_clamps_low(self, mock_client, env, capsys):
        with patch("sys.argv", ["ma-client", "volume", "p1", "-10"]):
            main()
        mock_client.player_command_volume_set.assert_called_once_with("p1", 0)


class TestCLIState:
    def test_state_found(self, mock_client, env, capsys):
        mock_client.get_player_state.return_value = {"state": "playing", "player_name": "Office"}

        with patch("sys.argv", ["ma-client", "state", "p1"]):
            main()

        out = json.loads(capsys.readouterr().out)
        assert out["state"] == "playing"

    def test_state_not_found(self, mock_client, env, capsys):
        mock_client.get_player_state.return_value = None

        with patch("sys.argv", ["ma-client", "state", "p1"]):
            with pytest.raises(SystemExit):
                main()


class TestCLIMissingEnv:
    def test_no_ma_url(self, monkeypatch, capsys):
        monkeypatch.delenv("MA_URL", raising=False)

        with patch("sys.argv", ["ma-client", "players"]):
            with pytest.raises(SystemExit):
                main()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
