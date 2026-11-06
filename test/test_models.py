"""Tests for the vendored Music Assistant models."""

import json

import pytest

from ma_http_client import MediaType, MusicAssistantError, Player, QueueOption, RepeatMode


SERVER_PLAYER = {
    "player_id": "RINCON_1",
    "name": "Office",
    "available": True,
    "playback_state": "playing",
    "current_media": {"title": "Just For Now", "artist": "Imogen Heap", "media_type": "track"},
    "group_members": [{"player_id": "a"}, {"player_id": "b"}],
}


class TestPlayer:
    def test_top_level_fields_are_attributes(self):
        player = Player.from_dict(SERVER_PLAYER)
        assert player.player_id == "RINCON_1"
        assert player.name == "Office"
        assert player.available is True

    def test_nested_dicts_become_attributes(self):
        player = Player.from_dict(SERVER_PLAYER)
        assert player.current_media.title == "Just For Now"
        assert player.current_media.artist == "Imogen Heap"

    def test_lists_of_dicts_become_attribute_lists(self):
        player = Player.from_dict(SERVER_PLAYER)
        assert [member.player_id for member in player.group_members] == ["a", "b"]

    def test_missing_field_raises_attribute_error_so_getattr_defaults_work(self):
        player = Player.from_dict({"player_id": "x", "name": "X"})
        assert not hasattr(player, "current_media")
        assert getattr(player, "available", True) is True

    def test_is_a_player_instance(self):
        assert isinstance(Player.from_dict(SERVER_PLAYER), Player)


class TestEnums:
    def test_members_compare_and_serialize_as_wire_strings(self):
        assert MediaType.TRACK == "track"
        assert str(QueueOption.REPLACE) == "replace"
        assert json.dumps({"repeat": RepeatMode.ALL}) == '{"repeat": "all"}'

    def test_media_type_parses_server_values(self):
        assert MediaType("playlist") is MediaType.PLAYLIST
        assert MediaType("genre") is MediaType.GENRE

    def test_unknown_media_type_maps_to_unknown(self):
        assert MediaType("something_new") is MediaType.UNKNOWN


def test_music_assistant_error_is_an_exception():
    with pytest.raises(MusicAssistantError):
        raise MusicAssistantError("boom")
