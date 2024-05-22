from pytest_monte_carlo import plugin


def test_should_keep_node(faker):
    node_id = faker.md5()
    assert plugin._should_keep_node(node_id, 0.0) is False
    assert plugin._should_keep_node(node_id, 1.0) is True

    expected_rate = faker.pyfloat(min_value=0.2, max_value=0.6)
    results = [plugin._should_keep_node(node_id, expected_rate) for _ in range(10000)]
    actual_rate = sum(results) / len(results)
    assert abs(actual_rate - expected_rate) < 0.01


class Test__integration:
    def test_simple(self, pytester):
        pytester.makepyfile(
            '''
            import pytest

            @pytest.mark.monte_carlo(0.0)
            def test_0():
                pass

            @pytest.mark.monte_carlo(1.0)
            def test_100():
                pass

            def test_unmarked():
                pass
            '''
        )
        result = pytester.runpytest('-v')
        result.assert_outcomes(passed=2, skipped=1)

    def test_disabled(self, pytester):
        pytester.makepyfile(
            '''
            import pytest

            @pytest.mark.monte_carlo(0.0)
            def test_0():
                pass
            '''
        )
        result = pytester.runpytest('-v', '--no-monte-carlo')
        result.assert_outcomes(passed=1)

    def test_matrix(self, pytester):
        pytester.makepyfile(
            '''
            import pytest

            # Parametrized test with 2**5 = 32 permutations
            @pytest.mark.monte_carlo(0.3)
            @pytest.mark.parametrize('arg1', [False, True])
            @pytest.mark.parametrize('arg2', [False, True])
            @pytest.mark.parametrize('arg3', [False, True])
            @pytest.mark.parametrize('arg4', [False, True])
            @pytest.mark.parametrize('arg5', [False, True])
            def test_30(arg1, arg2, arg3, arg4, arg5):
                pass
            '''
        )

        # Run the matrix test 10 times and compute the average skip rate.
        num_permutations = 2**5  # five levels of binary parametrizing above
        num_trials = 10

        expected_rate = 0.3
        expected_skipped = num_permutations * num_trials * (1 - expected_rate)
        expected_passed = num_permutations * num_trials * expected_rate
        expected_total = num_permutations * num_trials

        actual_skipped = 0
        actual_passed = 0
        for _ in range(num_trials):
            result = pytester.runpytest()
            outcomes = result.parseoutcomes()
            actual_skipped += outcomes.get('skipped', 0)
            actual_passed += outcomes.get('passed', 0)

        actual_total = actual_skipped + actual_passed
        assert actual_total == expected_total

        delta_skipped = actual_skipped - expected_skipped
        delta_passed = actual_passed - expected_passed
        tolerance = 0.2  # within 20% (season to taste)
        assert abs(delta_skipped / expected_skipped) < tolerance
        assert abs(delta_passed / expected_passed) < tolerance
