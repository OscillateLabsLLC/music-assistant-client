"""Tests for the playlist methods."""

from unittest.mock import Mock

import pytest
import requests

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


def test_library_playlists_search(client, mock_session):
    _respond(mock_session, [{"name": "Workout"}])

    result = client.library_playlists(search="workout")

    sent = _sent(mock_session)
    assert sent["command"] == "music/playlists/library_items"
    assert sent["args"] == {"limit": 25, "search": "workout"}
    assert result[0]["name"] == "Workout"


def test_create_playlist_default_provider(client, mock_session):
    _respond(mock_session, {"item_id": "12", "name": "Workout"})

    result = client.create_playlist("Workout")

    sent = _sent(mock_session)
    assert sent["command"] == "music/playlists/create_playlist"
    assert sent["args"] == {"name": "Workout"}
    assert result["item_id"] == "12"


def test_create_playlist_with_provider(client, mock_session):
    _respond(mock_session, {})

    client.create_playlist("Workout", provider="spotify")

    assert _sent(mock_session)["args"]["provider_instance_or_domain"] == "spotify"


def test_playlist_tracks(client, mock_session):
    _respond(mock_session, [])

    client.playlist_tracks(12, limit=10)

    sent = _sent(mock_session)
    assert sent["command"] == "music/playlists/playlist_tracks"
    assert sent["args"] == {"item_id": "12", "provider_instance_id_or_domain": "library", "limit": 10}


def test_add_and_remove_playlist_tracks(client, mock_session):
    _respond(mock_session, None)

    client.add_playlist_tracks(12, ["library://track/1"])
    sent = _sent(mock_session)
    assert sent["command"] == "music/playlists/add_playlist_tracks"
    assert sent["args"] == {"db_playlist_id": 12, "uris": ["library://track/1"]}

    client.remove_playlist_tracks(12, [0, 3])
    sent = _sent(mock_session)
    assert sent["command"] == "music/playlists/remove_playlist_tracks"
    assert sent["args"] == {"db_playlist_id": 12, "positions_to_remove": [0, 3]}


def test_save_queue_as_playlist(client, mock_session):
    _respond(mock_session, None)

    client.save_queue_as_playlist("queue-1", "Tonight")

    sent = _sent(mock_session)
    assert sent["command"] == "player_queues/save_as_playlist"
    assert sent["args"] == {"queue_id": "queue-1", "name": "Tonight"}
