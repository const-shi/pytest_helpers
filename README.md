# Pytest helpers

This is pytest plugins which adds features:
* Async tests
* Deployment tests

Tested in pytest versions 3.10.1 and 4.6.10 and 5.4.2

## Async tests

Add "asyncs" to pytest_plugins, and you can use async test functions and async fixtures.
It is conveniently when you test async project.

## Deployment tests
Deployment test is test which starts before deployment and finishes after deployment.
So you can test influence of deployment process to your project.
Mark deployment_test will slice test function into 2 parts by "yield" keyword.
First part(before yield) will run before deploy.
Then deploy command will be executed.
Then second part(after yield) will be executed.
If test function has more than one 'yield', then test will be parametrized by deploy moment.
Also whole test will be run one time before deploy, and one time after deploy.
See example for clarity.
You need:
* add "deployment_test" and "asyncs" to pytest_plugins
* mark test function with @pytest.mark.deployment_test
* add 'yield' keyword to the function(to the top layer, 'yield' must not be conditional)
* provide deploy command, for example:
  ```pytest tests/ --deployment_test="sh deploy.sh"```

Normal(not deployment) tests will not be executed if deploy command provided.
If no deploy command provided then deploy tests executed like normal tests without yields.
Test function must be async - just add async keyword if it is not.

**Example**
```
@pytest.mark.deployment_test
async def test():
    print(1)
    yield
    print(2)
    yield
    print(3)
```
There will be 4 runs in this example.
In the first run, whole test will be executed after deploy.
In the last run, whole test will be executed before deploy.
In second and third runs, part of the test will be executed before deploy and part - after deploy.
See table:

Run name |  |  |  |  |
--- | --- | --- | --- | --- |
test[0] | **deploy** | print(1)   | print(2)   | print(3)   |
test[1] | print(1)   | **deploy** | print(2)   | print(3)   |
test[2] | print(1)   | print(2)   | **deploy** | print(3)   |
test[3] | print(1)   | print(2)   | print(3)   | **deploy** |

If test failed, run name will be printed, so you can see which deploy moment broke tested function.
Every test run shown in log as 2 tests: one test before deploy, and one test after deploy.
If before deploy test passed and after deploy test failed, so it will be shown as "1 passed, 1 failed".
If before deploy test failed then test after deploy will be skipped, "1 failed, 1 skipped".
Deploy shown as test also - passed or failed.
