# Setting up Mini-Boss

## 📋 Requirements

Choose an environment to run Mini-Boss in (pick one):

  - [Docker](https://docs.docker.com/get-docker/) (*recommended*)
  - Python 3.10 or later (instructions: [for Windows](https://www.tutorialspoint.com/how-to-install-python-in-windows))
  - [VSCode + devcontainer](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)


## 🗝️ Getting an API key

Get your OpenAI API key from: [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys).

!!! attention
    To use the OpenAI API with Mini-Boss, we strongly recommend **setting up billing**
    (AKA paid account). Free accounts are [limited][openai/api limits] to 3 API calls per
    minute, which can cause the application to crash.

    You can set up a paid account at [Manage account > Billing > Overview](https://platform.openai.com/account/billing/overview).

[openai/api limits]: https://platform.openai.com/docs/guides/rate-limits/overview#:~:text=Free%20trial%20users,RPM%0A40%2C000%20TPM

!!! important
    It's highly recommended that you keep keep track of your API costs on [the Usage page](https://platform.openai.com/account/usage).
    You can also set limits on how much you spend on [the Usage limits page](https://platform.openai.com/account/billing/limits).

![For OpenAI API key to work, set up paid account at OpenAI API > Billing](./imgs/openai-api-key-billing-paid-account.png)


## Setting up Mini-Boss

### Set up with Docker

1. Make sure you have Docker installed, see [requirements](#requirements)
2. Pull the latest image from [Docker Hub]

        :::shell
        docker pull minibossgpt/mini-boss

3. Create a folder for Mini-Boss
4. In the folder, create a file called `docker-compose.yml` with the following contents:

        :::yaml
        version: "3.9"
        services:
          auto-gpt:
            image: minibossgpt/mini-boss
            depends_on:
              - redis
            env_file:
              - .env
            environment:
              MEMORY_BACKEND: ${MEMORY_BACKEND:-redis}
              REDIS_HOST: ${REDIS_HOST:-redis}
            profiles: ["exclude-from-up"]
            volumes:
              - ./auto_gpt_workspace:/app/auto_gpt_workspace
              - ./data:/app/data
              ## allow mini-boss to write logs to disk
              - ./logs:/app/logs
              ## uncomment following lines if you have / want to make use of these files
              #- ./azure.yaml:/app/azure.yaml
              #- ./ai_settings.yaml:/app/ai_settings.yaml
          redis:
            image: "redis/redis-stack-server:latest"

5. Create the necessary [configuration](#configuration) files. If needed, you can find
    templates in the [repository].
6. Continue to [Run with Docker](#run-with-docker)

!!! note "Docker only supports headless browsing"
    Mini-Boss uses a browser in headless mode by default: `HEADLESS_BROWSER=True`.
    Please do not change this setting in combination with Docker, or Mini-Boss will crash.

[Docker Hub]: https://hub.docker.com/r/minibossgpt/mini-boss
[repository]: https://github.com/MiniBossGPT/Mini-Boss


### Set up with Git

!!! important
    Make sure you have [Git](https://git-scm.com/downloads) installed for your OS.

!!! info "Executing commands"
    To execute the given commands, open a CMD, Bash, or Powershell window.  
    On Windows: press ++win+x++ and pick *Terminal*, or ++win+r++ and enter `cmd`

1. Clone the repository

        :::shell
        git clone -b stable https://github.com/MiniBossGPT/Mini-Boss.git

2. Navigate to the directory where you downloaded the repository

        :::shell
        cd Mini-Boss


### Set up without Git/Docker

!!! warning
    We recommend to use Git or Docker, to make updating easier.

1. Download `Source code (zip)` from the [latest stable release](https://github.com/MiniBossGPT/Mini-Boss/releases/latest)
2. Extract the zip-file into a folder


### Configuration (follow guide for Auto-GPT)

1. Find the file named `auto-gpt/.env.template` in the main `Auto-GPT` folder. This file may
    be hidden by default in some operating systems due to the dot prefix. To reveal
    hidden files, follow the instructions for your specific operating system:
    [Windows][show hidden files/Windows], [macOS][show hidden files/macOS].
2. Either run `./setup.sh` or create a copy of `.env.template` and call it `.env`;
    if you're already in a command prompt/terminal window: `cp auto-gpt/.env.template auto-gpt/.env`.
3. Open the `.env` file in both the top level directoy and the sub directory in a text editor.
4. Find the line that says `OPENAI_API_KEY=`.
5. After the `=`, enter your unique OpenAI API Key *without any quotes or spaces*.
6. Enter any other API keys or tokens for services you would like to use.

    !!! note
        To activate and adjust a setting, remove the `# ` prefix.

7. Save and close the `.env` file.
8. Now copy the file to the top level. `cp auto-gpt/.env .env`


## Running Mini-Boss

### Run with Docker

Easiest is to use `docker-compose`. Run the commands below in your Mini-Boss folder.

1. Build the image. If you have pulled the image from Docker Hub, skip this step.

        :::shell
        docker-compose build mini-boss

2. Run Mini-Boss

        :::shell
        docker-compose run --rm mini-boss

    By default, this will also start and attach a Redis memory backend. If you do not
    want this, comment or remove the `depends: - redis` and `redis:` sections from
    `docker-compose.yml`.

    For related settings, see [Memory > Redis setup](./configuration/memory.md#redis-setup).

You can pass extra arguments, e.g. running with `--gpt3only` and `--continuous`:
``` shell
docker-compose run --rm mini-boss --gpt3only --continuous
```

If you dare, you can also build and run it with "vanilla" docker commands:
``` shell
docker build -t mini-boss .
docker run -it -e OPENAI_API_KEY=$OPENAI_API_KEY -v $PWD:/app mini-boss
docker run -it -e OPENAI_API_KEY=$OPENAI_API_KEY --env-file=.env -v $PWD:/app mini-boss
docker run -it --env-file=.env -v $PWD:/app --rm mini-boss --gpt3only --continuous
```

[docker-compose file]: https://github.com/MiniBossGPT/Mini-Boss/blob/master/docker-compose.yml


### Run with Dev Container

1. Install the [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension in VS Code.

2. Open command palette with ++f1++ and type `Dev Containers: Open Folder in Container`.

3. Run `./run.sh`.


### Run without Docker

Simply run the startup script in your terminal. This will install any necessary Python
packages and launch Mini-Boss.

- On Linux/MacOS:

        :::shell
        ./run.sh

- On Windows:

        :::shell
        .\run.bat

If this gives errors, make sure you have a compatible Python version installed. See also
the [requirements](./installation.md#requirements).
