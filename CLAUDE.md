# Setting Up the Music Assistant Claude Code Skill

Control Music Assistant with natural language from [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## 1. Install the package

```bash
pip install ma-http-client
```

## 2. Install the skill

```bash
ma-install-skill
```

This copies the bundled skill to `~/.claude/skills/music-assistant/SKILL.md`.

## 3. Set environment variables

Add to `~/.claude/settings.json` (create it if it doesn't exist):

```json
{
  "env": {
    "MA_URL": "http://homeassistant.local:8095",
    "MA_TOKEN": "your-token-here",
    "MA_DEFAULT_PLAYER": "Living Room"
  }
}
```

Tokens are stored in Claude Code's config and never appear in your chat.

## 4. Use it

Invoke the skill explicitly:

```
/music-assistant play some Radiohead
```

Or just ask naturally — Claude auto-invokes the skill when it matches:

```
Play some Radiohead in the living room
```

## Finding Your MA Token

In Music Assistant: **Settings → Advanced → Authentication Tokens** → create a new token.

## Finding Your Server URL

Default port is `8095`. If running via Home Assistant add-on: `http://<ha-ip>:8095`. mDNS works too: `http://homeassistant.local:8095`.

## Standalone Agent

For use outside Claude Code (scripts, OVOS, etc.), install the `claude` extra and use `MusicAssistantAgent` directly. This runs its own Claude instance — see the [README](README.md) for details.

```bash
pip install "ma-http-client[claude]"
```
