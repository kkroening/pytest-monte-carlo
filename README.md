# `pytest-monte-carlo`: pytest plugin for stochastic test selection

## Overview

The `pytest-monte-carlo` pytest plugin makes large scale matrix-testing feasible by selecting a (pseudo-)random subset of any tests marked with `@pytest.mark.monte_carlo(rate)`.

Now you can use `@pytest.mark.parametrize` to cover more permutations without worrying about excessive test runtime through combinatorial explosion.

In spite of its stochastic nature, being pseudo-random means that it integrates nicely with `pytest-randomly`, so that pinning the `--randomly-seed` gives the same, deterministic test selection.

## Example Usage

The prototypical use case for `@pytest.mark.monte_carlo` is to reduce the number of test permutations for test cases decorated with one or more `@pytest.mark.parametrize`, while still retaining a large enough subset to get an adequate sample:

```python
@pytest.mark.monte_carlo(0.1)
@pytest.mark.parametrize('animal', [Animal.CAT, Animal.DOG, Animal.RABBIT])
@pytest.mark.parametrize('biome', [Biome.BEACH, Biome.FOREST, Biome.HILLS, Biome.SPACE])
@pytest.mark.parametrize('with_leash', [False, True])
@pytest.mark.parametrize('with_treat', [False, True])
@pytest.mark.parametrize('with_water', [False, True])
def test_example(animal, biome, with_leash, with_treat, with_water):
    ...
```

In this case, there are `3 * 4 * 2 * 2 * 2 = 96` permutations, which would normally all be tested exhaustively.  However, many of the scenarios end up being redundant, so decorating the test with `@pytest.mark.monte_carlo(0.1)` selects only 10% of the permutations, and skips the rest, giving a decently representative sample but taking much less time to execute:

```
$ pytest test.py
======================================= test session starts =======================================
platform darwin -- Python 3.11.4, pytest-8.2.1, pluggy-1.5.0
Using --randomly-seed=3174870756
rootdir: /Users/me/sample
configfile: pyproject.toml
plugins: randomly-3.15.0, monte-carlo-0.1.0
collected 96 items

test.py ......... [100%]

================================== 9 passed in 0.03s ==============================================
```

Despite having 96 potential permutations in this case, only ~10% were selected, since the default behavior is to exclude any deselected tests, in order to keep the pytest output tidy.

### Skipping tests rather than excluding

By default, `pytest-monte-carlo` _excludes_ any test scenarios that are deselected via Monte Carlo, but it can instead be configured to _skip_ such tests by passing `skip=True`:

```python
@pytest.mark.monte_carlo(0.1, skip=True)
...  # same as before
```

New output:

```
$ pytest test.py
============================================= test session starts ==============================================
platform darwin -- Python 3.11.4, pytest-8.2.1, pluggy-1.5.0
Using --randomly-seed=3174870756
rootdir: /Users/me/sample
configfile: pyproject.toml
plugins: randomly-3.15.0, monte-carlo-0.1.0
collected 96 items

test.py ssssssss..sss.ss.ssssssssssssssssssssssssss.sssssssssss.ssssssssss..ssssssssssssssssssssssss.sss [100%]

======================================== 9 passed, 87 skipped in 0.03s =========================================
```

The same percentage of tests run either way, but the difference is whether the skipped permutations show up in the pytest output or not.

### `pytest-randomly` integration

When using `pytest-randomly` with `pytest-monte-carlo`, the pseudo-random test selection is tied to the randomly seed, which can be pinned by passing `--randomly-seed=xxxxx` to the `pytest` command as needed.  In other words, to reproduce a particular test failure, inspect the pytest output to see the seed that was used and then re-run with the same seed.

### Bypassing `pytest-monte-carlo`

To run all test permutations, simply run pytest with `--no-monte-carlo`, and then it's as though every `@pytest.mark.monte_carlo(...)` line is commented/removed.

## Installation

```bash
pip install pytest-monte-carlo
```
