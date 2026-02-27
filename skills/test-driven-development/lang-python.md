## Python TDD

Framework: **pytest** + **pytest-describe**

### Structure

### Preferred patterns

- `conftest.py` at each test directory level for shared fixtures
  - One per test directory, importing conftest from parent directory. Not imported from test files.
  - Shared fixtures, custom markers, hooks, parametrize helpers
  - Nest conftest.py files: inner overrides/extends outer
- `pytest-describe` for nested `describe_`/`context_`/`it_` BDD-style grouping
- Fixture scope: `function` (default). Don't use `class`, `module`, `session`
- Fixtures over `setUp` — composable, explicit dependency injection
- Factory fixtures return callables for parameterized object creation
- `tmp_path` / `tmp_path_factory` for filesystem tests
- `monkeypatch` for env vars, attributes, dict items
- `@pytest.mark.parametrize` for data-driven tests — parameters include both inputs AND expected outputs
- `autouse=True` sparingly — only for universal setup (logging, DB cleanup, time/randomness mocks)
- `behaves_like` to share tests across different fixture contexts

### Anti-patterns

- `unittest.TestCase` subclasses — lose fixture injection, parametrize, describe
- `setUp` — couples setup to class hierarchy, no dependency graph
- Broad `conftest.py` at repo root with everything — split by concern
- `mock.patch` decorators stacking 5+ deep — use dependency injection or fixture-based fakes
