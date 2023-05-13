""" Command and Control """
import json
import os
from typing import Dict, List, NoReturn, Union

from miniboss.boss.boss_manager import BossManager
from miniboss.buddy.buddy_manager import BuddyManager
from miniboss.commands.command import CommandRegistry, command
from miniboss.commands.web_requests import scrape_links, scrape_text
from miniboss.config import Config
from miniboss.memory import get_memory
from miniboss.processing.text import summarize_text
from miniboss.prompts.generator import PromptGenerator

# from miniboss.speech import say_text
from miniboss.url_utils.validators import validate_url

CFG = Config()
BUDDY_MANAGER = BuddyManager()
BOSS_MANAGER = BossManager()
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


def is_valid_int(value: str) -> bool:
    """Check if the value is a valid integer

    Args:
        value (str): The value to check

    Returns:
        bool: True if the value is a valid integer, False otherwise
    """
    try:
        int(value)
        return True
    except ValueError:
        return False


def get_command(response_json: Dict):
    """Parse the response and return the command name and arguments

    Args:
        response_json (json): The response from the AI

    Returns:
        tuple: The command name and arguments

    Raises:
        json.decoder.JSONDecodeError: If the response is not valid JSON

        Exception: If any other error occurs
    """
    try:
        if "command" not in response_json:
            return "Error:", "Missing 'command' object in JSON"

        if not isinstance(response_json, dict):
            return "Error:", f"'response_json' object is not dictionary {response_json}"

        command = response_json["command"]
        if not isinstance(command, dict):
            return "Error:", "'command' object is not a dictionary"

        if "name" not in command:
            return "Error:", "Missing 'name' field in 'command' object"

        command_name = command["name"]

        # Use an empty dictionary if 'args' field is not present in 'command' object
        arguments = command.get("args", {})

        return command_name, arguments
    except json.decoder.JSONDecodeError:
        return "Error:", "Invalid JSON"
    # All other errors, return "Error: + error message"
    except Exception as e:
        return "Error:", str(e)


def get_boss_command(response_json: Dict):
    """Parse the response and return the command name and arguments

    Args:
        response_json (json): The response from the AI

    Returns:
        tuple: The command name and arguments

    Raises:
        json.decoder.JSONDecodeError: If the response is not valid JSON

        Exception: If any other error occurs
    """
    try:
        if "command" not in response_json:
            return "Error:", "Missing 'command' object in JSON"

        if not isinstance(response_json, dict):
            return "Error:", f"'response_json' object is not dictionary {response_json}"

        command = response_json["command"]
        if not isinstance(command, dict):
            return "Error:", "'command' object is not a dictionary"

        if "name" not in command:
            return "Error:", "Missing 'name' field in 'command' object"

        command_name = command["name"]

        # Use an empty dictionary if 'args' field is not present in 'command' object
        arguments = command.get("args", {})

        return command_name, arguments
    except json.decoder.JSONDecodeError:
        return "Error:", "Invalid JSON"
    # All other errors, return "Error: + error message"
    except Exception as e:
        return "Error:", str(e)


def map_command_synonyms(command_name: str):
    """Takes the original command name given by the AI, and checks if the
    string matches a list of common/known hallucinations
    """
    synonyms = [
        ("write_file", "write_to_file"),
        ("create_file", "write_to_file"),
        ("search", "google"),
    ]
    for seen_command, actual_command_name in synonyms:
        if command_name == seen_command:
            return actual_command_name
    return command_name


def execute_command(
    command_registry: CommandRegistry,
    command_name: str,
    arguments,
    prompt: PromptGenerator,
):
    """Execute the command and return the result

    Args:
        command_name (str): The name of the command to execute
        arguments (dict): The arguments for the command

    Returns:
        str: The result of the command
    """
    try:
        cmd = command_registry.commands.get(command_name)

        # If the command is found, call it with the provided arguments
        if cmd:
            return cmd(**arguments)

        # TODO: Remove commands below after they are moved to the command registry.
        command_name = map_command_synonyms(command_name.lower())

        if command_name == "memory_add":
            return get_memory(CFG).add(arguments["string"])

        # TODO: Change these to take in a file rather than pasted code, if
        # non-file is given, return instructions "Input should be a python
        # filepath, write your code to file and try again
        elif command_name == "task_complete":
            # print("buddy complete - proceed to next task")
            # shutdown()
            return command_name, arguments
        else:
            for command in prompt.commands:
                if (
                    command_name == command["label"].lower()
                    or command_name == command["name"].lower()
                ):
                    return command["function"](**arguments)
            return (
                f"Unknown command '{command_name}'. Please refer to the 'COMMANDS'"
                " list for available commands and only respond in the specified JSON"
                " format."
            )
    except Exception as e:
        return f"Error: {str(e)}"


def execute_boss_command(
    command_registry: CommandRegistry,
    command_name: str,
    arguments,
    prompt: PromptGenerator,
):
    """Execute the command and return the result

    Args:
        command_name (str): The name of the command to execute
        arguments (dict): The arguments for the command

    Returns:
        str: The result of the command
    """
    try:
        cmd = command_registry.commands.get(command_name)

        # If the command is found, call it with the provided arguments
        if cmd:
            return cmd(**arguments)

        # TODO: Remove commands below after they are moved to the command registry.
        command_name = map_command_synonyms(command_name.lower())

        if command_name == "memory_add":
            return get_memory(CFG).add(arguments["string"])

        # TODO: Change these to take in a file rather than pasted code, if
        # non-file is given, return instructions "Input should be a python
        # filepath, write your code to file and try again
        elif command_name == "task_complete":
            return
        elif command_name == "boss_complete":
            shutdown()
        else:
            for command in prompt.commands:
                if (
                    command_name == command["label"].lower()
                    or command_name == command["name"].lower()
                ):
                    return command["function"](**arguments)
            return (
                f"Unknown command '{command_name}'. Please refer to the 'COMMANDS'"
                " list for available commands and only respond in the specified JSON"
                " format."
            )
    except Exception as e:
        return f"Error: {str(e)}"


@command(
    "get_text_summary", "Get text summary", '"url": "<url>", "question": "<question>"'
)
@validate_url
def get_text_summary(url: str, question: str) -> str:
    """Return the results of a Google search

    Args:
        url (str): The url to scrape
        question (str): The question to summarize the text for

    Returns:
        str: The summary of the text
    """
    text = scrape_text(url)
    summary = summarize_text(url, text, question)
    return f""" "Result" : {summary}"""


@command("get_hyperlinks", "Get text summary", '"url": "<url>"')
@validate_url
def get_hyperlinks(url: str) -> Union[str, List[str]]:
    """Return the results of a Google search

    Args:
        url (str): The url to scrape

    Returns:
        str or list: The hyperlinks on the page
    """
    return scrape_links(url)


def shutdown() -> NoReturn:
    """Shut down the program"""
    print("Shutting down...")
    quit()


@command(
    "boss",
    "Start GPT Agent",
    '"name": "<name>", "task": "<short_task_desc>", "prompt": "<prompt>"',
)
def start_boss(name: str, task: str, prompt: str, model=CFG.smart_llm_model) -> str:
    """Start an buddy with a given name, task, and prompt

    Args:
        name (str): The name of the buddy
        task (str): The task of the buddy
        prompt (str): The prompt for the buddy
        model (str): The model to use for the buddy

    Returns:
        str: The response of the buddy
    """
    # Remove underscores from name
    voice_name = name.replace("_", " ")

    first_message = f"""You are {name}.  Respond with: "Acknowledged"."""
    buddy_intro = f"{voice_name} here, Reporting for duty!"

    # # Create buddy
    # if CFG.speak_mode:
    #     say_text(buddy_intro, 1)
    # key, ack = BUDDY_MANAGER.create_buddy(task, first_message, model)
    key, ack = BOSS_MANAGER.create_boss(task, first_message, model)
    #
    # if CFG.speak_mode:
    #     say_text(f"Hello {voice_name}. Your task is as follows. {task}.")

    # Assign task (prompt), get response
    # buddy_response = BUDDY_MANAGER.message_buddy(key, prompt)
    buddy_response = BOSS_MANAGER.message_boss(key, prompt)

    return f"Agent {name} created with key {key}. First response: {buddy_response}"


@command("message_buddy", "Message GPT Agent", '"key": "<key>", "message": "<message>"')
def message_boss(key: str, message: str) -> str:
    """Message an buddy with a given key and message"""
    # Check if the key is a valid integer
    if is_valid_int(key):
        # buddy_response = BUDDY_MANAGER.message_buddy(int(key), message)
        buddy_response = BOSS_MANAGER.message_boss(int(key), message)
    else:
        return "Invalid key, must be an integer."

    # # Speak response
    # if CFG.speak_mode:
    #     say_text(buddy_response, 1)
    return buddy_response


@command("list_bosss", "List GPT Agents", "")
def list_bosss() -> str:
    """List all buddys

    Returns:
        str: A list of all buddys
    """
    return "List of buddys:\n" + "\n".join(
        # [str(x[0]) + ": " + x[1] for x in BUDDY_MANAGER.list_buddys()]
        [str(x[0]) + ": " + x[1] for x in BOSS_MANAGER.list_bosss()]
    )


@command("delete_boss", "Delete GPT Agent", '"key": "<key>"')
def delete_boss(key: str) -> str:
    """Delete an buddy with a given key

    Args:
        key (str): The key of the buddy to delete

    Returns:
        str: A message indicating whether the buddy was deleted or not
    """
    # result = BUDDY_MANAGER.delete_buddy(key)
    result = BOSS_MANAGER.delete_boss(key)
    return f"Agent {key} deleted." if result else f"Agent {key} does not exist."
