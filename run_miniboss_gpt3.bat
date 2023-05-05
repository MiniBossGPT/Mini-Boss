@echo off
echo Pulling the Docker image...
docker pull minibossgpt/mini-boss:latest

set /p OPENAI_API_KEY="Please enter your OPENAI_API_KEY: "

echo Running the Docker container...
docker run -it -e OPENAI_API_KEY="%OPENAI_API_KEY%" minibossgpt/mini-boss:latest --gpt3only
echo Press any key to exit...
pause >nul
