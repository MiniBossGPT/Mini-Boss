#!/usr/bin/env bash

echo "Please enter your OPENAI_API_KEY: "
read OPENAI_API_KEY
export OPENAI_API_KEY

python scripts/check_requirements.py auto-gpt/requirements.txt
if [ $? -eq 1 ]
then
    echo Installing missing packages...
    pip install -r auto-gpt/requirements.txt
    python -m pip install rich
fi
python -m miniboss $@
read -p "Press any key to continue..."
