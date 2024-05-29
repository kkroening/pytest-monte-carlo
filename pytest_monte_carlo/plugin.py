import hashlib
import pytest
import random
from typing import Any

_DEFAULT_RATIO = 1.0

_HASH_BYTES = 2
_HASH_BITS = _HASH_BYTES * 8
_HASH_MAX = 2**_HASH_BITS - 1


def pytest_configure(
    config: pytest.Config,
) -> None:
    config.addinivalue_line(
        'markers',
        (
            'monte_carlo(rate): stochastically selects a percentage of test cases to '
            'run, and skipping the rest.'
        ),
    )


def pytest_addoption(
    parser: pytest.Parser,
) -> None:
    parser.addoption(
        '--no-monte-carlo',
        action='store_true',
        help='Ignore Monte Carlo markers and run all tests',
    )


def _should_keep_node(
    node_id: str,
    rate: float,
) -> bool:
    """Determines whether to run a test based on a pseudorandom decision.

    The decision is derived from the test's unique ID, and also influenced by the pytest
    session's random seed.  This makes test selection deterministic when using
    ``pytest-randomly`` with a pinned seed value.
    """
    hash_digest = hashlib.md5(node_id.encode()).digest()
    hash_int = int.from_bytes(hash_digest[:_HASH_BYTES])
    nonce = random.randint(0, _HASH_MAX)
    return (hash_int ^ nonce) <= int(rate * _HASH_MAX)


def _handle_node(
    node: Any,
) -> Any:
    marker = node.get_closest_marker('monte_carlo')
    if marker is not None:
        if len(marker.args) != 1:
            raise ValueError('Expected one positional argument - `rate`')

        if not isinstance(marker.args[0], (int, float)):
            raise TypeError('Rate must be an int or float')

        rate = float(marker.args[0])
        if rate < 0 or rate > 1:
            raise ValueError('Rate must be between 0.0 and 1.0')

        should_skip = marker.kwargs.get('skip', False)
        if not isinstance(should_skip, bool):
            raise TypeError(f'Expected boolean value for `skip`; got {should_skip!r}')

        if not _should_keep_node(node.nodeid, rate):
            if should_skip:
                node.add_marker(
                    pytest.mark.skip(reason='Skipped by Monte Carlo selection')
                )
            else:
                node = None  # TBD: alternatively discard the test

    return node


def pytest_collection_modifyitems(
    session: pytest.Session,  # pylint: disable=unused-argument
    config: pytest.Config,
    items: list[Any],
) -> None:
    if not config.getoption('--no-monte-carlo'):
        items[:] = list(filter(None, [_handle_node(x) for x in items]))
