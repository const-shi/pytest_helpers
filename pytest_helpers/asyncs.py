import asyncio
import functools
import inspect

import pytest


def sync_function(async_function):
    """ decorator making sync function from async function """
    @functools.wraps(async_function)
    def wrapper(*args, **kwargs):
        task = asyncio.ensure_future(async_function(*args, **kwargs))
        return asyncio.get_event_loop().run_until_complete(task)
    return wrapper


def sync_iterator_class(async_iterator_class_or_function):
    """ decorator making sync iterator from async iterator class or function """
    class SyncIterator:
        def __init__(self,  *args, **kwargs):
            self.async_gen = async_iterator_class_or_function(*args, **kwargs)

        def __iter__(self):
            return self

        def __next__(self):
            try:
                return asyncio.get_event_loop().run_until_complete(
                    self.async_gen.__anext__())
            except StopAsyncIteration:
                raise StopIteration

    return SyncIterator


def sync_generator_function(async_generator_function):
    """ decorator making sync generator function from async generator function """
    def wrapper(*args, **kwargs):
        sync_gen = sync_iterator_class(async_generator_function)
        for x in sync_gen(*args, **kwargs):
            yield x

    return wrapper


def pytest_pyfunc_call(pyfuncitem):
    if asyncio.iscoroutinefunction(pyfuncitem.obj):
        pyfuncitem.obj = sync_function(pyfuncitem.obj)


def pytest_fixture_setup(fixturedef, request):

    if asyncio.iscoroutinefunction(fixturedef.func):
        fixturedef.func = sync_function(fixturedef.func)
    if inspect.isasyncgenfunction(fixturedef.func):
        fixturedef.func = sync_generator_function(fixturedef.func)


@pytest.fixture(scope='session')
def event_loop():
    return asyncio.get_event_loop()
