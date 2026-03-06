---
name: music-assistant
description: Control Music Assistant — play music, adjust volume, skip tracks, pause, and check what's playing. Use when the user asks about music playback, speakers, or audio controls.
allowed-tools: Bash(ma-client *)
---

Control Music Assistant using the `ma-client` CLI. All commands output JSON.

## Commands

```
ma-client players                           # List all players
ma-client search "query" --type artist      # Search (artist|track|album|playlist|radio)
ma-client play <player_id> <uri>            # Play media (add --radio for radio mode)
ma-client pause <player_id>                 # Pause/resume
ma-client next <player_id>                  # Next track
ma-client previous <player_id>              # Previous track
ma-client volume <player_id> <0-100>        # Set volume
ma-client state <player_id>                 # Get playback state
```

## Workflow

1. Run `ma-client players` to discover players and match the requested location. Use `MA_DEFAULT_PLAYER` env var if no location is specified.
2. For play requests: run `ma-client search` first, then `ma-client play` with the player_id and URI from the top result.
3. For controls (pause, next, volume): run the relevant command directly.

## Response Style

One sentence confirming the action. Examples:
- "Playing Radiohead in the living room."
- "Paused."
- "Volume set to 40% in the kitchen."
- "Skipped to the next track."
- "Couldn't find a player named 'garage'."
