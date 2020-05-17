from setuptools import setup

setup(
    name="pytest_helpers",
    version="0.1.0",
    description="pytest helpers",
    url="https://github.com/const-shi/pytest_helpers",
    license="MIT License",
    author="const-shi",
    packages=["pytest_helpers"],
    # the following makes a plugin available to pytest
    entry_points={"pytest11": [
        "asyncs = pytest_helpers.asyncs",
        "deployment_test = pytest_helpers.deployment_test"
    ]},
    # custom PyPI classifier for pytest plugins
    classifiers=["Framework :: Pytest"],
    install_requires=["pytest"]
)
