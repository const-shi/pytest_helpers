import pytest

pytest_plugins = ["asyncs", "deployment_test", "pytester"]


@pytest.fixture
async def simple_fixture():
    return "simple_fixture"
