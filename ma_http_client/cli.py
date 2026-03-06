"""CLI for Music Assistant operations. Used by the Claude Code skill."""

import argparse
import json
import os
import sys

from ma_http_client import SimpleHTTPMusicAssistantClient


def get_client() -> SimpleHTTPMusicAssistantClient:
    url = os.environ.get("MA_URL")
    if not url:
        print("Error: MA_URL environment variable is not set", file=sys.stderr)
        raise SystemExit(1)
    return SimpleHTTPMusicAssistantClient(
        server_url=url,
        token=os.environ.get("MA_TOKEN"),
    )


def cmd_players(args):
    client = get_client()
    players = client.get_players()
    print(json.dumps([
        {"player_id": p.player_id, "name": p.name, "available": getattr(p, "available", False)}
        for p in players
    ], indent=2))


def cmd_search(args):
    from music_assistant_models.enums import MediaType

    type_map = {
        "artist": MediaType.ARTIST,
        "track": MediaType.TRACK,
        "album": MediaType.ALBUM,
        "playlist": MediaType.PLAYLIST,
        "radio": MediaType.RADIO,
    }
    client = get_client()
    mt = type_map.get(args.type)
    results = client.search_media(args.query, media_types=[mt] if mt else None, limit=args.limit)
    print(json.dumps(results, indent=2, default=str))


def cmd_play(args):
    from music_assistant_models.enums import QueueOption

    client = get_client()
    client.play_media(
        queue_id=args.player_id,
        media=args.uri,
        option=QueueOption.PLAY,
        radio_mode=args.radio,
    )
    print(json.dumps({"success": True, "player_id": args.player_id, "uri": args.uri}))


def cmd_pause(args):
    client = get_client()
    client.queue_command_pause(args.player_id)
    print(json.dumps({"success": True, "action": "pause", "player_id": args.player_id}))


def cmd_next(args):
    client = get_client()
    client.queue_command_next(args.player_id)
    print(json.dumps({"success": True, "action": "next", "player_id": args.player_id}))


def cmd_previous(args):
    client = get_client()
    client.queue_command_previous(args.player_id)
    print(json.dumps({"success": True, "action": "previous", "player_id": args.player_id}))


def cmd_volume(args):
    client = get_client()
    level = max(0, min(100, args.level))
    client.player_command_volume_set(args.player_id, level)
    print(json.dumps({"success": True, "player_id": args.player_id, "volume": level}))


def cmd_state(args):
    client = get_client()
    state = client.get_player_state(args.player_id)
    if state is None:
        print(json.dumps({"found": False, "player_id": args.player_id}))
        raise SystemExit(1)
    print(json.dumps(state, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(prog="ma-client", description="Music Assistant CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("players", help="List all players")

    p_search = sub.add_parser("search", help="Search for media")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--type", default="artist", choices=["artist", "track", "album", "playlist", "radio"])
    p_search.add_argument("--limit", type=int, default=5)

    p_play = sub.add_parser("play", help="Play media on a player")
    p_play.add_argument("player_id", help="Player ID")
    p_play.add_argument("uri", help="Media URI from search results")
    p_play.add_argument("--radio", action="store_true", help="Enable radio mode")

    p_pause = sub.add_parser("pause", help="Pause playback")
    p_pause.add_argument("player_id", help="Player ID")

    p_next = sub.add_parser("next", help="Skip to next track")
    p_next.add_argument("player_id", help="Player ID")

    p_previous = sub.add_parser("previous", help="Go to previous track")
    p_previous.add_argument("player_id", help="Player ID")

    p_volume = sub.add_parser("volume", help="Set volume (0-100)")
    p_volume.add_argument("player_id", help="Player ID")
    p_volume.add_argument("level", type=int, help="Volume level 0-100")

    p_state = sub.add_parser("state", help="Get player state")
    p_state.add_argument("player_id", help="Player ID")

    args = parser.parse_args()

    commands = {
        "players": cmd_players,
        "search": cmd_search,
        "play": cmd_play,
        "pause": cmd_pause,
        "next": cmd_next,
        "previous": cmd_previous,
        "volume": cmd_volume,
        "state": cmd_state,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
