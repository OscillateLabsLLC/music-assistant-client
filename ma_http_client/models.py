"""The small part of the Music Assistant data model that this client uses.

This module replaces the `music-assistant-models` dependency. Upstream needs
Python 3.13 or later, and this client supports Python 3.10 and later. The enum
values must stay in sync with the server's wire format, which is defined in
https://github.com/music-assistant/models/blob/main/music_assistant_models/enums.py
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any


if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Python 3.10 stand-in for enum.StrEnum: members are their string values."""

        def __str__(self) -> str:
            return str.__str__(self)


class MediaType(StrEnum):
    """Type of a media item."""

    ARTIST = "artist"
    ALBUM = "album"
    TRACK = "track"
    PLAYLIST = "playlist"
    RADIO = "radio"
    AUDIOBOOK = "audiobook"
    PODCAST = "podcast"
    PODCAST_EPISODE = "podcast_episode"
    FOLDER = "folder"
    COLLECTION = "collection"
    ANNOUNCEMENT = "announcement"
    FLOW_STREAM = "flow_stream"
    PLUGIN_SOURCE = "plugin_source"
    AUDIO_SOURCE = "audio_source"
    SOUND_EFFECT = "sound_effect"
    GENRE = "genre"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> MediaType:
        """Map a value that this module does not know to UNKNOWN, as upstream does."""
        return cls.UNKNOWN


class QueueOption(StrEnum):
    """How new items enter a player queue."""

    PLAY = "play"
    REPLACE = "replace"
    NEXT = "next"
    REPLACE_NEXT = "replace_next"
    ADD = "add"
    UNKNOWN = "unknown"


class RepeatMode(StrEnum):
    """Repeat mode of a player queue."""

    OFF = "off"
    ONE = "one"
    ALL = "all"
    UNKNOWN = "unknown"


class MusicAssistantError(Exception):
    """Error raised for a failed Music Assistant request."""

    error_code = 0


def _to_namespace(value: Any) -> Any:
    """Recursively turn dicts into attribute namespaces; leave other values as they are."""
    if isinstance(value, dict):
        return SimpleNamespace(**{str(key): _to_namespace(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_to_namespace(item) for item in value]
    return value


class Player(SimpleNamespace):
    """A player as the server reports it, with attribute access to every field.

    There is no fixed schema: fields the server adds are available, and a field
    the server does not send raises AttributeError, so getattr defaults apply.
    """

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Player:
        """Build a Player from one entry of the `players/all` response."""
        return cls(**_to_namespace(data).__dict__)


__all__ = ["MediaType", "MusicAssistantError", "Player", "QueueOption", "RepeatMode"]
