import pytest


def test_no_yield(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.mark.deployment_test
        def test():
            assert True
    """)
    result = testdir.runpytest('--deployment_test=echo 1')

    assert "Need 'yield' in deployment test" in result.stdout.str()
    result.assert_outcomes(failed=0, error=1, passed=0, skipped=0)


def test_too_much_yields(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.mark.deployment_test
        async def test():
            assert True # yield
            yield
            assert True
    """)
    result = testdir.runpytest('--deployment_test=echo 1')
    assert "'yield' must only be non conditional keyword" in result.stdout.str()
    result.assert_outcomes(failed=4, error=0, passed=5, skipped=0)


def test_normal_tests(testdir):
    """ In deployment mode pytest doesn't see normal tests at all """
    testdir.makepyfile("""
        def test():
            assert True
    """)
    result = testdir.runpytest('--deployment_test="echo 1"')
    result.assert_outcomes(failed=0, error=0, passed=0, skipped=0)


@pytest.mark.parametrize("failed", [True, False])
def test_ok_or_failed(failed, testdir):
    testdir.makepyfile(f"""
        import pytest
        class Production:
            attr = 0
            def inc(self):
                self.attr += 1
    
        @pytest.mark.deployment_test
        async def test():
            p = Production()
            p.inc()
            assert p.attr == 1
            yield
            p.inc()
            assert p.attr == {2 if not failed else 555}
            yield
            p.inc()
            assert p.attr == 3
    """)
    result = testdir.runpytest('--deployment_test=echo 1')
    if failed:
        result.assert_outcomes(failed=4, error=0, passed=3, skipped=2)
    else:
        result.assert_outcomes(failed=0, error=0, passed=9, skipped=0)


def test_failed_and_marked_which(testdir):
    testdir.makepyfile(f"""
        import pytest
        @pytest.mark.deployment_test
        async def test_failed_and_marked_which(deploy_status):
            yield
            assert deploy_status.status == 'after'  #  after deploy here will be third(2) run of test
    """)
    result = testdir.runpytest('--deployment_test=echo 1')
    assert "test_failed_and_marked_which[2]" in result.stdout.str()
    result.assert_outcomes(failed=1, error=0, passed=5, skipped=1)


@pytest.mark.parametrize("deploy_mode", [True, False])
def test_work_in_deploy_and_not_deploy_mode(deploy_mode, testdir):
    """ It must fail in deploy and in normal mode """
    testdir.makepyfile("""
        import pytest
        @pytest.mark.deployment_test
        async def test_one_failed_and_marked_which():
            yield
            assert False
    """)
    if deploy_mode:
        result = testdir.runpytest('--deployment_test=echo 1')
        result.assert_outcomes(failed=3, error=0, passed=3, skipped=1)
    else:
        result = testdir.runpytest('')
        result.assert_outcomes(failed=1, error=0, passed=0, skipped=0)


def test_skipped_after_crush(testdir):
    testdir.makepyfile(f"""
        import pytest
        @pytest.mark.deployment_test
        async def test_skipped_after_crush():
            yield
    """)
    result = testdir.runpytest('--deployment_test=no_that_command')
    result.assert_outcomes(failed=1, error=0, passed=3, skipped=3)


def test_fixture(testdir):
    testdir.makepyfile(f"""
        import pytest
        data = [0, 0, 0]
        a = -1
        @pytest.fixture
        async def fixture():
            global a
            a += 1
            return a

        def teardown_module():
            assert data == [2, 2, 2]

        @pytest.mark.deployment_test
        async def test_fixture(fixture):
            data[fixture] += 1
            yield
            data[fixture] += 1
    """)
    result = testdir.runpytest('--deployment_test=echo 1')
    result.assert_outcomes(failed=0, error=0, passed=7, skipped=0)


def test_before_after(testdir):
    """ every codeplace tested (yield_cnt + 2) times in before-deploy state and in after-deploy state """
    testdir.makepyfile("""
        import pytest
        data = {"before": [0]*3, "after": [0]*3}
        def teardown_module():
            assert data["before"] == [3, 2, 1]
            assert data["after"] == [1, 2, 3]

        @pytest.mark.deployment_test 
        async def test_parametrize(deploy_status):
            data[deploy_status.status][0] += 1
            yield
            data[deploy_status.status][1] += 1
            yield
            data[deploy_status.status][2] += 1
    """)
    result = testdir.runpytest('-s', '--deployment_test=echo 1')
    result.assert_outcomes(failed=0, error=0, passed=9, skipped=0)


def test__before_after__parametrize__many_functions(testdir):
    """ every codeplace tested (yield_cnt + 2) times in before-deploy state and in after-deploy state """
    testdir.makepyfile("""
        import pytest
        data = {p1: {p2: {"before": [0]*3, "after": [0]*3} for p2 in [7, 8]} for p1 in [1, 2]}
        data2 = {p1: {p2: {"before": [0]*3, "after": [0]*3} for p2 in [7, 8]} for p1 in [1, 2]}
        
        def teardown_module():
            assert data  == {p1: {p2: {"before": [3, 2, 1], "after": [1, 2, 3]} for p2 in [7, 8]} for p1 in [1, 2]}
            assert data2 == {p1: {p2: {"before": [3, 2, 1], "after": [1, 2, 3]} for p2 in [7, 8]} for p1 in [1, 2]}

        @pytest.mark.parametrize("param1", [1, 2])
        @pytest.mark.deployment_test
        @pytest.mark.parametrize("param2", [7, 8])
        async def test_parametrize(param1, param2, deploy_status):
            data[param1][param2][deploy_status.status][0] += 1
            yield
            data[param1][param2][deploy_status.status][1] += 1
            yield
            data[param1][param2][deploy_status.status][2] += 1
        
        @pytest.mark.parametrize("param1", [1, 2])
        @pytest.mark.deployment_test
        @pytest.mark.parametrize("param2", [7, 8])
        async def test_parametrize2(param1, param2, deploy_status):
            data2[param1][param2][deploy_status.status][0] += 1
            yield
            data2[param1][param2][deploy_status.status][1] += 1
            yield
            data2[param1][param2][deploy_status.status][2] += 1
    """)
    result = testdir.runpytest('--deployment_test=echo 1')
    result.assert_outcomes(failed=0, error=0, passed=65, skipped=0)


@pytest.mark.parametrize("deco_order", [True, False])
def test_parametrize(deco_order, testdir):
    testdir.makepyfile(f"""
        import pytest
        data = []
        def teardown_module():
            print(data)
            assert data == [
                [1, 1, 2, 'before'],
                [1, 3, 4, 'before'],
                [1, 1, 2, 'before'],
                [2, 1, 2, 'before'],
                [1, 3, 4, 'before'],
                [2, 3, 4, 'before'],
                [1, 1, 2, 'before'],
                [2, 1, 2, 'before'],
                [3, 1, 2, 'before'],
                [1, 3, 4, 'before'],
                [2, 3, 4, 'before'],
                [3, 3, 4, 'before'],
                [1, 1, 2, 'after'],
                [2, 1, 2, 'after'],
                [3, 1, 2, 'after'],
                [1, 3, 4, 'after'],
                [2, 3, 4, 'after'],
                [3, 3, 4, 'after'],
                [2, 1, 2, 'after'],
                [3, 1, 2, 'after'],
                [2, 3, 4, 'after'],
                [3, 3, 4, 'after'],
                [3, 1, 2, 'after'],
                [3, 3, 4, 'after'],
            ]

        {"".join(sorted(['''
        @pytest.mark.parametrize("param1, param2", [[1, 2], [3, 4]]) ''', '''
        @pytest.mark.deployment_test 
        '''], reverse=deco_order))}
        async def test_parametrize(param1, param2, deploy_status):
            data.append([1, param1, param2, deploy_status.status])
            yield
            data.append([2, param1, param2, deploy_status.status])
            yield
            data.append([3, param1, param2, deploy_status.status])
    """)
    result = testdir.runpytest('-s', '--deployment_test=echo 1')
    result.assert_outcomes(failed=0, error=0, passed=17, skipped=0)
