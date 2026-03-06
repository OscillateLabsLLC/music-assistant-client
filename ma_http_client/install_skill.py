"""CLI entry point: install the music-assistant Claude Code skill."""

import shutil
from pathlib import Path


def main():
    dest_dir = Path.home() / ".claude" / "skills" / "music-assistant"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "SKILL.md"

    # SKILL.md ships alongside this module
    src = Path(__file__).parent / "skills" / "music-assistant" / "SKILL.md"
    if not src.exists():
        print(f"Error: bundled skill not found at {src}")
        raise SystemExit(1)

    shutil.copy(src, dest)

    print(f"Installed: {dest}")
    print()
    print("Set your Music Assistant connection in ~/.claude/settings.json:")
    print()
    print('  {')
    print('    "env": {')
    print('      "MA_URL": "http://homeassistant.local:8095",')
    print('      "MA_TOKEN": "your-token-here",')
    print('      "MA_DEFAULT_PLAYER": "Living Room"')
    print('    }')
    print('  }')


if __name__ == "__main__":
    main()
