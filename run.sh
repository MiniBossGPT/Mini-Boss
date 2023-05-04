#!/bin/bash

python scripts/check_requirements.py auto-gpt/requirements.txt
if [ $? -eq 1 ]
then
    echo Installing missing packages...
    pip install -r auto-gpt/requirements.txt
fi
python -m miniboss $@
read -p "Press any key to continue..."
