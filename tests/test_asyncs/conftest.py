import pytest

pytest_plugins = ["pytester"]


@pytest.fixture
async def async_fixture():
    return "async_fixture works"


@pytest.fixture
async def async_gen_fixture():
    yield "async_gen_fixture works"


@pytest.fixture
def sync_fixture():
    return "sync_fixture works"
