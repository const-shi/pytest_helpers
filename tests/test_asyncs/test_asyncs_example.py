
async def test_async_example(async_fixture, sync_fixture, async_gen_fixture):
    print(f"async ({async_fixture}, {sync_fixture}, {async_gen_fixture})")
    assert 1 == 1


def test_example(async_fixture, sync_fixture, async_gen_fixture):
    print(f"sync ({async_fixture}, {sync_fixture}, {async_gen_fixture})")
    assert 1 == 1


