import inspect
import subprocess
from collections import defaultdict
from functools import wraps

import pytest

# deploy statuses
STATUS_BEFORE, STATUS_AFTER, STATUS_CRUSHED = "before", "after", "crushed"


class State:
    """ class for common vars """
    terminal = None  # terminal for printing
    deploy_cmd = None  # deploy command
    status = None  # deploy status text

state = State()


def pytest_addoption(parser):
    parser.addoption(
        "--deployment_test", action="store", help="Run deployment tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "deployment_test: mark test as deployment test"
        "parametrize deploys when test yields")
    state.deploy_cmd = config.option.deployment_test
    state.status = STATUS_BEFORE  # it is here because of plugin testing


def pytest_generate_tests(metafunc):
    if state.deploy_cmd and get_marker(metafunc.function, "deployment_test"):
        runs_cnt = get_runs_count(metafunc.function)
        assert runs_cnt > 2, f"Need 'yield' in deployment test {metafunc.function}"
        metafunc.fixturenames.append("_yield_cnt")
        metafunc.parametrize("_yield_cnt", range(runs_cnt))


def pytest_collection_modifyitems(session, config, items):
    """
    if deploy mode then ignore normal(not deploy) tests
    if deploy mode then ordering: deploy tests, deploy command, deploy tests
    decorating function here because it doesn't work in pytest_pycollect_makeitem or pytest_generate_tests
    """
    if state.deploy_cmd:
        deploy_tests = [i for i in items if get_marker(i.obj, 'deployment_test')]
        if not deploy_tests:
            items[:] = []
            return
        for i in items:
            i.obj = deployment_test(i.obj)

        state.terminal = config.pluginmanager.get_plugin('terminalreporter')
        state.terminal.write_sep("=", "DEPLOYMENT TESTING !")
        items[:] = (
            deploy_tests +  # this tests will iterate till yield
            [create_test(deploy_tests[0].parent, do_deploy)] +
            deploy_tests  # this tests will iterate after yield
        )
    else:
        for i in items:
            if get_marker(i.obj, 'deployment_test'):
                i.obj = deployment_test(i.obj)


def deployment_test(test_func):

    depl_test_runner = DeploymentTestRunner(test_func)

    @wraps(test_func)
    async def wrapper(*args, **kwargs):
        if not state.deploy_cmd:
            await depl_test_runner.start_and_finish_one_test(*args, **kwargs)
        elif state.status == STATUS_CRUSHED:
            return pytest.skip("Skip tests after deploy crush")
        elif state.status == STATUS_BEFORE:
            await depl_test_runner.start_test(*args, **kwargs)
        elif state.status == STATUS_AFTER:
            await depl_test_runner.finish_test()

    return wrapper


class DeploymentTestRunner:
    """
    There are ('yield' count)+2 parametrized tests for one test function.
    Every next run of test function must be with different deploy moment
    This class manage executing of tests for that.
    """
    __instances_by_test_func__ = {}  # one DeploymentTestRunner instance for one test func
    iterated_cnt = defaultdict(int)  # iterated count of every generator
    count = 0  # count of parametrized test func (deploy parameter and others)

    def __new__(cls, test_func):
        obj = cls.__instances_by_test_func__.get(test_func)
        if not obj:
            obj = cls.__instances_by_test_func__[test_func] = super().__new__(cls)
        obj.count += 1
        return obj

    def __init__(self, test_func):
        self.test_func = test_func
        self.generators = []
        self.max_runs_cnt = get_runs_count(test_func)

    async def start_test(self, *args, **kwargs):
        need_iterate_cnt = len(self.generators) // (self.count / self.max_runs_cnt)
        generator = self.test_func(*args, **kwargs)
        self.generators.append(generator)
        if need_iterate_cnt == 0:
            return
        try:
            async for _ in generator:
                self.iterated_cnt[generator] += 1
                if self.iterated_cnt[generator] == need_iterate_cnt:
                    return
        except Exception:
            self.iterated_cnt[generator] = None
            raise

    async def finish_test(self):
        generator, *self.generators = self.generators
        if self.iterated_cnt[generator] is None:
            return pytest.skip("Skip test finish past deploy because of test fail before deploy")
        async for _ in generator:
            self.iterated_cnt[generator] += 1
        assert self.iterated_cnt[generator] == self.max_runs_cnt - 2, "'yield' must only be non conditional keyword"

    async def start_and_finish_one_test(self, *args, **kwargs):
        async for _ in self.test_func(*args, **kwargs):
            pass


@pytest.mark.deployment_test
def do_deploy():
    """ Execute deploy command """
    state.status = STATUS_AFTER
    state.terminal.write_sep("=", "DEPLOY STARTED")
    state.terminal.write_sep("=", f">> {state.deploy_cmd}")
    pr = subprocess.Popen(state.deploy_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret_code = pr.wait()
    out, err = pr.stdout.read().decode(), pr.stderr.read().decode()
    if ret_code:
        state.status = STATUS_CRUSHED
        raise Exception(f"""Deploy returned {ret_code}.\n\nstdout: {out}\n\nstderr: {err}""")
    state.terminal.write_sep("=", "DEPLOY FINISHED")


@pytest.fixture(scope="session")
def deploy_status():
    class DeployStatus:
        @property
        def status(self):
            return state.status
    return DeployStatus()


def get_marker(func_item, mark):
    """ Getting mark which works in various pytest versions """
    pytetstmark = [m for m in (getattr(func_item, 'pytestmark', None) or []) if m.name == mark]
    if pytetstmark:
        return pytetstmark[0]


def create_test(metafunc, func):
    if pytest.__version__ >= "5.":
        return pytest.Function.from_parent(metafunc, name=func.__name__, callobj=func)
    return pytest.Function(do_deploy.__name__, metafunc, callobj=do_deploy)


def get_runs_count(func):
    # TODO it can work wrong, fix that later!
    #      for example "def yield_that(_yield): a = 'yield_yield'; yield a # yield"
    #      but we check that real iterates count == calculated yield count, so ok now
    return inspect.getsource(func).count('yield') + 2
