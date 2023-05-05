@echo off
python scripts/check_requirements.py auto-gpt/requirements.txt
if errorlevel 1 (
    echo Installing missing packages...
    pip install -r auto-gpt/requirements.txt
    pip install rich
)
python -m miniboss %*
pause
