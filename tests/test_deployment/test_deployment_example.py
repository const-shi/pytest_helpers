import pytest


class ProductionApp:
    attr = 0

    def inc(self):
        self.attr += 1


@pytest.mark.deployment_test
async def test_example():
    p = ProductionApp()
    p.inc()
    assert p.attr == 1
    yield
    p.inc()
    assert p.attr == 2
    yield
    p.inc()
    assert p.attr == 3


@pytest.mark.deployment_test
async def test_with_fixture(simple_fixture):
    assert simple_fixture == "simple_fixture"
    yield
    assert simple_fixture == "simple_fixture"
