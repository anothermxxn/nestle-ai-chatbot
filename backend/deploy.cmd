@echo off

echo Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo Deployment completed successfully. 