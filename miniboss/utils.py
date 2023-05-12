import os
import sys
from pathlib import Path

import requests
import yaml
from colorama import Fore
from git.repo import Repo
from rich import print
from rich.markdown import Markdown

from miniboss.commands.command import CommandRegistry
from miniboss.logs import logger
from miniboss.plugins import scan_plugins
from miniboss.workspace import Jobspace

# Use readline if available (for clean_input)
try:
    import readline
except:
    pass

import ast
import re

from miniboss.config import Config


def send_chat_message_to_user(report: str):
    """
    Sends a chat message to the user.

    Args:
        report (str): The message to send to the user.
    """
    cfg = Config()
    if not cfg.chat_messages_enabled:
        return
    for plugin in cfg.plugins:
        if not hasattr(plugin, "can_handle_report"):
            continue
        if not plugin.can_handle_report():
            continue
        plugin.report(report)


def clean_input(prompt: str = "", talk=False):
    """
    Cleans the user input and handles user interaction.

    Args:
        prompt (str): The input prompt.
        talk (bool): Flag indicating whether to enable user interaction.

    Returns:
        str: The cleaned user input.
    """
    try:
        cfg = Config()
        if cfg.chat_messages_enabled:
            for plugin in cfg.plugins:
                if not hasattr(plugin, "can_handle_user_input"):
                    continue
                if not plugin.can_handle_user_input(user_input=prompt):
                    continue
                plugin_response = plugin.user_input(user_input=prompt)
                if not plugin_response:
                    continue
                if plugin_response.lower() in [
                    "yes",
                    "yeah",
                    "y",
                    "ok",
                    "okay",
                    "sure",
                    "alright",
                ]:
                    return cfg.authorise_key
                elif plugin_response.lower() in [
                    "no",
                    "nope",
                    "n",
                    "negative",
                ]:
                    return cfg.exit_key
                return plugin_response

        # ask for input, default when just pressing Enter is y
        logger.typewriter_log("", Fore.GREEN, "\n")
        logger.typewriter_log("Asking user via keyboard...", Fore.YELLOW, "")
        logger.typewriter_log("", Fore.GREEN, "\n")
        answer = input(prompt)
        return answer
    except KeyboardInterrupt:
        logger.typewriter_log("", Fore.GREEN, "\n")
        logger.typewriter_log("You interrupted Mini-Boss...", Fore.RED, "\n")
        logger.typewriter_log("", Fore.GREEN, "\n")
        logger.typewriter_log("Quitting...", Fore.RED, "\n")
        exit(0)


def validate_yaml_file(file: str):
    """
    Validates a YAML file.

    Args:
        file (str): The path to the YAML file.

    Returns:
        tuple: A tuple containing the validation result (True/False) and the validation message.
    """
    try:
        with open(file, encoding="utf-8") as fp:
            yaml.load(fp.read(), Loader=yaml.FullLoader)
    except FileNotFoundError:
        return (False, f"The file {Fore.CYAN}`{file}`{Fore.RESET} wasn't found")
    except yaml.YAMLError as e:
        return (
            False,
            f"There was an issue while trying to read with your AI Settings file: {e}",
        )

    return (True, f"Successfully validated {Fore.CYAN}`{file}`{Fore.RESET}!")


def readable_file_size(size, decimal_places=2):
    """
    Converts the given size in bytes to a readable format.

    Args:
        size: Size in bytes.
        decimal_places (int): Number of decimal places to display.

    Returns:
        str: The readable file size.
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def get_bulletin_from_web():
    """
    Retrieves the bulletin from the web.

    Returns:
        str: The retrieved bulletin text.
    """
    try:
        response = requests.get(
            "https://raw.githubusercontent.com/MiniBossGPT/Mini-Boss/main/BULLETIN.md"
        )
        if response.status_code == 200:
            return response.text
    except requests.exceptions.RequestException:
        pass

    return ""


def get_current_git_branch() -> str:
    """
    Retrieves the current git branch.

    Returns:
        str: The name of the current git branch.
    """
    try:
        repo = Repo(search_parent_directories=True)
        branch = repo.active_branch
        return branch.name
    except:
        return ""


def get_latest_bulletin() -> str:
    """
    Retrieves the latest bulletin.

    Returns:
        str: The latest bulletin text.
    """
    exists = os.path.exists("CURRENT_BULLETIN.md")
    current_bulletin = ""
    if exists:
        current_bulletin = open("CURRENT_BULLETIN.md", "r", encoding="utf-8").read()
    new_bulletin = get_bulletin_from_web()
    is_new_news = new_bulletin != current_bulletin

    if new_bulletin and is_new_news:
        open("CURRENT_BULLETIN.md", "w", encoding="utf-8").write(new_bulletin)
        return f" {Fore.RED}::UPDATED:: {Fore.CYAN}{new_bulletin}{Fore.RESET}"
    return current_bulletin


def get_latest_markdown() -> str:
    """
    Retrieves the latest markdown content.

    Returns:
        str: The latest markdown content.
    """
    exists = os.path.exists("CURRENT_BULLETIN.md")
    current_bulletin = ""
    if exists:
        markdown_file = Path("CURRENT_BULLETIN.md")
        content = markdown_file.read_text()
        current_bulletin = Markdown(content)
        # print(current_bulletin)
        # markdown_content = Markdown(content)
        # current_bulletin = open("CURRENT_BULLETIN.md", "r", encoding="utf-8").read()
    new_bulletin = get_bulletin_from_web()
    is_new_news = new_bulletin != current_bulletin

    if new_bulletin and is_new_news:
        open("CURRENT_BULLETIN.md", "w", encoding="utf-8").write(new_bulletin)
        return f" {Fore.RED}::UPDATED:: {Fore.CYAN}{new_bulletin}{Fore.RESET}"
    return current_bulletin


def parse_auto_gpt_logs(target_directory):
    """
    Parses the logs of the AutoGPT task.

    Args:
        target_directory (str): The path to the target directory.

    Returns:
        str: The parsed reason for task completion.
    """
    # Define the log file path
    log_file_path = os.path.join(target_directory, "logs/activity.log")
    # Read the log file in reverse
    with open(log_file_path, "r", encoding="utf-8") as log_file:
        lines = log_file.readlines()
        lines.reverse()
    # Define a regular expression pattern to match the "task_complete" command and its arguments
    pattern = r"COMMAND = task_complete\s+ARGUMENTS = ({.*})"
    # Search for the pattern in the reversed log content
    reason = ""
    for line in lines:
        match = re.search(pattern, line)
        if match:
            arguments_str = match.group(1)
            # Parse the string to a Python dictionary
            arguments = ast.literal_eval(arguments_str)
            # Access the 'reason' value
            pre_reason = arguments["reason"]
            # Remove single and double quotes
            reason = pre_reason.strip("'\"").replace("'", "")
            # Print the 'reason' value
            # print(f"Task complete Reason: {reason}")
            return reason
    else:
        # make this an error
        # print("Task complete command not found in the log file.")
        return reason


def check_news_updates(cfg):
    """
    Checks for news updates and displays the latest news.

    Args:
        cfg: The configuration object.
    """
    if not cfg.skip_news:
        motd = get_latest_markdown()
        if motd:
            display_latest_news()


def display_latest_news():
    """
    Displays the latest news.
    """
    markdown_file = Path("CURRENT_BULLETIN.md")
    content = markdown_file.read_text()
    markdown_content = Markdown(content)
    print(markdown_content)


def log_warnings():
    """
    Logs warnings related to the current environment.
    """
    check_git_branch()
    check_python_version()


def check_git_branch():
    """
    Checks the current git branch and logs a warning if it is not a supported branch.
    """
    git_branch = get_current_git_branch()
    if git_branch and git_branch not in ["stable", "main"]:
        logger.typewriter_log(
            "WARNING: ",
            Fore.RED,
            f"You are running on `{git_branch}` branch - this is not a supported branch.",
        )


def check_python_version():
    """
    Checks the Python version and logs a warning if it is an older version.
    """
    if sys.version_info < (3, 10):
        logger.typewriter_log(
            "WARNING: ",
            Fore.RED,
            "You are running on an older version of Python. Some people have observed problems with certain "
            "parts of Mini-Boss with this version. Please consider upgrading to Python 3.10 or higher.",
        )


def setup_workspace(cfg, workspace_directory):
    """
    Sets up the workspace directory.

    Args:
        cfg: The configuration object.
        workspace_directory (str): The path to the workspace directory.

    Returns:
        str: The path to the created workspace directory.
    """
    if workspace_directory is None:
        workspace_directory = Path(__file__).parent.parent / "miniboss_workspace"
    else:
        workspace_directory = Path(workspace_directory)
    workspace_directory = Jobspace.make_workspace(workspace_directory)
    cfg.workspace_path = str(workspace_directory)
    return workspace_directory


def setup_file_logger(cfg, workspace_directory):
    """
    Sets up the file logger.

    Args:
        cfg: The configuration object.
        workspace_directory (str): The path to the workspace directory.
    """
    file_logger_path = workspace_directory / "file_logger.txt"
    if not file_logger_path.exists():
        with file_logger_path.open(mode="w", encoding="utf-8") as f:
            f.write("File Operation Logger ")
    cfg.file_logger_path = str(file_logger_path)


def setup_plugins_and_commands(cfg):
    """
    Sets up the plugins and commands.

    Args:
        cfg: The configuration object.

    Returns:
        CommandRegistry: The command registry.
    """
    cfg.set_plugins(scan_plugins(cfg, cfg.debug_mode))
    command_registry = CommandRegistry()
    command_registry.import_commands("miniboss.app")
    command_registry.import_commands("miniboss.buddy_app")
    return command_registry
