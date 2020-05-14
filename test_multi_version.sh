pip install pytest==3.10.1
echo '>> pytest tests/'
pytest tests/
echo '>> pytest tests/ --deployment_test="echo 1"'
pytest tests/ --deployment_test="echo 1"

pip install pytest==4.6.10
echo '>> pytest tests/'
pytest tests/
echo '>> pytest tests/ --deployment_test="echo 1"'
pytest tests/ --deployment_test="echo 1"

pip install pytest==5.4.2
echo '>> pytest tests/'
pytest tests/
echo '>> pytest tests/ --deployment_test="echo 1"'
pytest tests/ --deployment_test="echo 1"