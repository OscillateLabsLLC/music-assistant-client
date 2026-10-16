"""Tests for library listing and genre methods."""

from unittest.mock import Mock

import pytest
import requests
from music_assistant_models.enums import MediaType

from ma_http_client import SORT_RANDOM, SimpleHTTPMusicAssistantClient


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


class TestLibraryItems:
    def test_random_tracks(self, client, mock_session):
        _respond(mock_session, [])

        client.library_items(MediaType.TRACK, limit=20, sort_field=SORT_RANDOM)

        sent = _sent(mock_session)
        assert sent["command"] == "music/tracks/library_items"
        assert sent["args"] == {"limit": 20, "order_by": "random"}

    def test_named_sort_uses_sort_field(self, client, mock_session):
        _respond(mock_session, [])

        client.library_items(MediaType.TRACK, sort_field="sort_name")

        assert _sent(mock_session)["args"] == {"limit": 25, "sort_field": "sort_name"}

    def test_favorite_albums_with_search(self, client, mock_session):
        _respond(mock_session, [])

        client.library_items(MediaType.ALBUM, search="abbey", favorite=True, genre_ids=[3, 4])

        sent = _sent(mock_session)
        assert sent["command"] == "music/albums/library_items"
        assert sent["args"] == {"limit": 25, "search": "abbey", "favorite": True, "genre": [3, 4]}

    def test_favorite_false_is_sent(self, client, mock_session):
        _respond(mock_session, [])

        client.library_items(MediaType.TRACK, favorite=False)

        assert _sent(mock_session)["args"]["favorite"] is False


class TestGenres:
    def test_search_genres(self, client, mock_session):
        _respond(mock_session, [{"name": "Jazz", "item_id": "7"}])

        result = client.search_genres("jazz")

        sent = _sent(mock_session)
        assert sent["command"] == "music/genres/library_items"
        assert sent["args"] == {"search": "jazz", "limit": 5}
        assert result[0]["name"] == "Jazz"

    def test_genre_tracks_random(self, client, mock_session):
        _respond(mock_session, [])

        client.genre_tracks("7", limit=30, sort_field=SORT_RANDOM)

        sent = _sent(mock_session)
        assert sent["command"] == "music/genres/tracks"
        assert sent["args"] == {"item_id": "7", "limit": 30, "sort_field": "random"}

    def test_genre_albums_default(self, client, mock_session):
        _respond(mock_session, [])

        client.genre_albums(7)

        sent = _sent(mock_session)
        assert sent["command"] == "music/genres/albums"
        assert sent["args"] == {"item_id": 7, "limit": 50}
