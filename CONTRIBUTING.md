# Contributing to music-assistant-client

Thanks for your interest in contributing!

## Development Setup

1. Clone and install with [uv](https://github.com/astral-sh/uv):

   ```bash
   git clone https://github.com/OscillateLabsLLC/music-assistant-client
   cd music-assistant-client
   uv sync --extra test
   ```

2. Run tests:

   ```bash
   uv run pytest
   ```

3. Lint and format:

   ```bash
   uv run ruff check .
   uv run ruff format .
   ```

## Commits

Use [conventional commits](https://www.conventionalcommits.org/):

```text
feat: add new API method
fix: handle missing token gracefully
docs: update usage examples
```

## Pull Requests

1. Create a feature branch: `git checkout -b feat-my-feature`
2. Make your changes and add tests
3. Run `uv run pytest` and `uv run ruff check .`
4. Commit with clear messages
5. Open a pull request

## License

By contributing, you agree that your contributions will be licensed under the Apache-2.0 License.
