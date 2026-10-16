"""Tests for the browse method."""

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


def test_browse_root_omits_path(client, mock_session):
    _respond(mock_session, [{"media_type": "folder", "path": "radiobrowser://"}])

    result = client.browse()

    sent = _sent(mock_session)
    assert sent["command"] == "music/browse"
    assert sent["args"] == {"limit": 100, "offset": 0}
    assert result[0]["media_type"] == "folder"


def test_browse_radio_country(client, mock_session):
    _respond(mock_session, [])

    client.browse("radiobrowser://category/country/ES", limit=20, offset=40)

    assert _sent(mock_session)["args"] == {
        "limit": 20,
        "offset": 40,
        "path": "radiobrowser://category/country/ES",
    }
