# Python TDD Patterns

> **Note:** `lang-python.md` is the agent-facing sidecar — terse by design. This file explains the same patterns for humans.

## pytest-describe

BDD-style test grouping using nested functions: `describe_Thing`, `context_when_something`, `it_does_behavior`. Provides natural test organization without class inheritance.

### `behaves_like`

A `pytest-describe` feature for sharing test cases across different fixture contexts. Define a set of tests once, then reuse them in multiple `describe` blocks with different fixtures. Useful when multiple implementations should satisfy the same behavioral contract.

```python
def behaves_like_a_sequence():
    def it_has_length(subject):
        assert len(subject) >= 0

    def it_is_iterable(subject):
        for _ in subject:
            break

def describe_list():
    @pytest.fixture
    def subject():
        return [1, 2, 3]

    behaves_like_a_sequence()

def describe_tuple():
    @pytest.fixture
    def subject():
        return (1, 2, 3)

    behaves_like_a_sequence()
```

## conftest.py

Pytest auto-discovers `conftest.py` files at each directory level — no imports needed in test files. Inner conftest files can override or extend fixtures from outer ones. Use one per test directory, split by concern. Avoid a single monolithic conftest at the repo root.

## Fixtures over setUp/tearDown

Fixtures are explicit dependency injection. Tests declare what they need as function parameters; pytest wires it up. This replaces `setUp`/`tearDown` with composable, reusable setup that doesn't couple to a class hierarchy.

Factory fixtures (fixtures that return callables) are useful when tests need multiple similar objects with different configurations.

## Parametrize

`@pytest.mark.parametrize` is pytest's data-driven test mechanism. Each parameter set should include both **inputs and expected outputs** — the test body is pure exercise-and-assert, not decision logic.

```python
@pytest.mark.parametrize("input_val, expected", [
    ("hello", "HELLO"),
    ("", ""),
    ("already UPPER", "ALREADY UPPER"),
])
def test_upcase(input_val, expected):
    assert upcase(input_val) == expected
```

Combine with `pytest-describe` for organized, readable test suites. Parametrize helpers can live in `conftest.py` when shared across files.

## Scope: function only

The skill recommends `function` scope exclusively. `module`/`session` scoped fixtures introduce shared mutable state between tests, which makes test isolation harder to reason about and can cause ordering-dependent failures.
