"""Tests for the by-name lookup, favorites, and queue mode methods."""

from unittest.mock import Mock

import pytest
import requests
from music_assistant_models.enums import MediaType, QueueOption, RepeatMode

from ma_http_client import SimpleHTTPMusicAssistantClient


@pytest.fixture
def mock_session():
    return Mock(spec=requests.Session)


@pytest.fixture
def client(mock_session):
    return SimpleHTTPMusicAssistantClient(server_url="http://test-server:8095", session=mock_session)


def _respond(mock_session, payload):
    response = Mock()
    response.status_code = 200
    response.json.return_value = payload
    mock_session.post.return_value = response


def _sent(mock_session):
    return mock_session.post.call_args[1]["json"]


class TestItemByName:
    def test_bare_name_sends_only_name(self, client, mock_session):
        _respond(mock_session, {"name": "Abbey Road", "media_type": "album"})

        result = client.get_item_by_name("Abbey Road")

        sent = _sent(mock_session)
        assert sent["command"] == "music/item_by_name"
        assert sent["args"] == {"name": "Abbey Road"}
        assert result["name"] == "Abbey Road"

    def test_filters_are_sent_when_given(self, client, mock_session):
        _respond(mock_session, None)

        result = client.get_item_by_name(
            "Come Together", artist="The Beatles", album="Abbey Road", media_type=MediaType.TRACK
        )

        assert _sent(mock_session)["args"] == {
            "name": "Come Together",
            "artist": "The Beatles",
            "album": "Abbey Road",
            "media_type": "track",
        }
        assert result is None

    def test_track_by_name(self, client, mock_session):
        _respond(mock_session, {"name": "Come Together"})

        client.get_track_by_name("Come Together", artist_name="The Beatles")

        sent = _sent(mock_session)
        assert sent["command"] == "music/track_by_name"
        assert sent["args"] == {"track_name": "Come Together", "artist_name": "The Beatles"}


class TestFavorites:
    def test_add_favorite_sends_uri(self, client, mock_session):
        _respond(mock_session, None)

        client.add_favorite("library://track/42")

        sent = _sent(mock_session)
        assert sent["command"] == "music/favorites/add_item"
        assert sent["args"] == {"item": "library://track/42"}

    def test_remove_favorite_sends_type_and_id(self, client, mock_session):
        _respond(mock_session, None)

        client.remove_favorite(MediaType.TRACK, 42)

        sent = _sent(mock_session)
        assert sent["command"] == "music/favorites/remove_item"
        assert sent["args"] == {"media_type": "track", "library_item_id": 42}


class TestQueueModes:
    def test_set_shuffle(self, client, mock_session):
        _respond(mock_session, None)

        client.queue_set_shuffle("queue-1", True)

        sent = _sent(mock_session)
        assert sent["command"] == "player_queues/shuffle"
        assert sent["args"] == {"queue_id": "queue-1", "shuffle_enabled": True}

    def test_set_repeat(self, client, mock_session):
        _respond(mock_session, None)

        client.queue_set_repeat("queue-1", RepeatMode.ALL)

        sent = _sent(mock_session)
        assert sent["command"] == "player_queues/repeat"
        assert sent["args"] == {"queue_id": "queue-1", "repeat_mode": "all"}

    def test_play_media_omits_shuffle_by_default(self, client, mock_session):
        _respond(mock_session, None)

        client.play_media("queue-1", "library://artist/1")

        args = _sent(mock_session)["args"]
        assert "shuffle" not in args
        assert args["option"] == QueueOption.PLAY.value

    def test_play_media_sends_shuffle_and_uri_list(self, client, mock_session):
        _respond(mock_session, None)

        client.play_media("queue-1", ["library://track/1", "library://track/2"], shuffle=True)

        args = _sent(mock_session)["args"]
        assert args["media"] == ["library://track/1", "library://track/2"]
        assert args["shuffle"] is True
