import pytest


@pytest.mark.parametrize("_async", ["async ", ""])
def test_simple(_async, testdir):
    testdir.makepyfile(f"""
        import pytest
        @pytest.mark.parametrize("failed", [True, False])  # one time failed and one time passed
        {_async}def test(failed):  # no matter sync or async
            assert not failed

    """)
    result = testdir.runpytest()
    result.assert_outcomes(failed=1, error=0, passed=1, skipped=0)


@pytest.mark.parametrize("_async", ["async ", ""])
def test_fixtures(_async, testdir):
    testdir.makeconftest("""
        import pytest
        @pytest.fixture
        async def async_fixture():
            return "async_fixture works"
        
        @pytest.fixture
        async def async_gen_fixture():
            yield "async_gen_fixture works"
        
        @pytest.fixture
        def sync_fixture():
            return "sync_fixture works"
        
        @pytest.fixture
        def sync_gen_fixture():
            yield "sync_gen_fixture works"

    """)
    testdir.makepyfile(f"""
        {_async}def test(async_fixture, async_gen_fixture, sync_fixture, sync_gen_fixture):
            assert async_fixture == "async_fixture works"
            assert async_gen_fixture == "async_gen_fixture works"
            assert sync_fixture == "sync_fixture works"
            assert sync_gen_fixture == "sync_gen_fixture works"

    """)
    result = testdir.runpytest()
    result.assert_outcomes(failed=0, error=0, passed=1, skipped=0)
