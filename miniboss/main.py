"""The application entry point.  Can be invoked by a CLI or any other front end application."""
import logging
import sys
from pathlib import Path

from colorama import Fore
from rich import print
from rich.markdown import Markdown

from miniboss.boss.boss import Boss
from miniboss.commands.command import CommandRegistry
from miniboss.config import Config, check_openai_api_key
from miniboss.configurator import create_config
from miniboss.logs import logger
from miniboss.memory import get_memory
from miniboss.plugins import scan_plugins
from miniboss.prompts.prompt import (
    DEFAULT_TRIGGERING_PROMPT,
    construct_main_boss_config,
)
from miniboss.utils import (
    get_current_git_branch,
    get_latest_bulletin,
    get_latest_markdown,
)
from miniboss.workspace import Jobspace


def run_miniboss(
    continuous: bool,
    continuous_limit: int,
    boss_settings: str,
    buddy_settings: str,
    skip_reprompt: bool,
    speak: bool,
    debug: bool,
    gpt3only: bool,
    gpt4only: bool,
    memory_type: str,
    browser_name: str,
    allow_downloads: bool,
    skip_news: bool,
    workspace_directory: str,
    install_plugin_deps: bool,
):
    # Configure logging before we do anything else.
    logger.set_level(logging.DEBUG if debug else logging.INFO)
    logger.speak_mode = speak

    cfg = Config()
    # TODO: fill in llm values here
    check_openai_api_key()
    create_config(
        continuous,
        continuous_limit,
        boss_settings,
        buddy_settings,
        skip_reprompt,
        speak,
        debug,
        gpt3only,
        gpt4only,
        memory_type,
        browser_name,
        allow_downloads,
        skip_news,
    )

    if not cfg.skip_news:
        # motd = get_latest_bulletin()
        motd = get_latest_markdown()
        if motd:
            markdown_file = Path("CURRENT_BULLETIN.md")
            content = markdown_file.read_text()
            markdown_content = Markdown(content)
            # logger.typewriter_log("", Fore.GREEN, markdown_content)
            print(markdown_content)

        # git_branch = get_current_git_branch()
        # if git_branch and git_branch != "stable":
        #     logger.typewriter_log(
        #         "WARNING: ",
        #         Fore.RED,
        #         f"You are running on `{git_branch}` branch "
        #         "- this is not a supported branch.",
        #     )
        if sys.version_info < (3, 10):
            logger.typewriter_log(
                "WARNING: ",
                Fore.RED,
                "You are running on an older version of Python. "
                "Some people have observed problems with certain "
                "parts of Mini-Boss with this version. "
                "Please consider upgrading to Python 3.10 or higher.",
            )

    # TODO: have this directory live outside the repository (e.g. in a user's
    #   home directory) and have it come in as a command line argument or part of
    #   the env file.
    if workspace_directory is None:
        workspace_directory = Path(__file__).parent.parent / "miniboss_workspace"
    else:
        workspace_directory = Path(workspace_directory)
    # TODO: pass in the boss_settings file and the env file and have them cloned into
    #   the workspace directory so we can bind them to the agent.
    workspace_directory = Jobspace.make_workspace(workspace_directory)
    cfg.workspace_path = str(workspace_directory)

    # HACK: doing this here to collect some globals that depend on the workspace.
    file_logger_path = workspace_directory / "file_logger.txt"
    if not file_logger_path.exists():
        with file_logger_path.open(mode="w", encoding="utf-8") as f:
            f.write("File Operation Logger ")

    cfg.file_logger_path = str(file_logger_path)

    cfg.set_plugins(scan_plugins(cfg, cfg.debug_mode))
    # Create a CommandRegistry instance and scan default folder
    command_registry = CommandRegistry()
    command_registry.import_commands("miniboss.app")
    command_registry.import_commands("miniboss.buddy_app")

    ai_name = ""
    boss_config = construct_main_boss_config()
    boss_config.command_registry = command_registry

    # print(prompt)
    # Initialize variables
    full_message_history = []
    next_action_count = 0

    # Initialize memory and make sure it is empty.
    # this is particularly important for indexing and referencing pinecone memory
    memory = get_memory(cfg, init=True)
    logger.typewriter_log(
        "Using memory of type:", Fore.GREEN, f"{memory.__class__.__name__}"
    )
    logger.typewriter_log("Using Browser:", Fore.GREEN, cfg.selenium_web_browser)
    system_prompt = boss_config.construct_full_prompt()

    if cfg.debug_mode:
        logger.typewriter_log("Prompt:", Fore.GREEN, system_prompt)

    boss = Boss(
        ai_name=ai_name,
        memory=memory,
        full_message_history=full_message_history,
        next_action_count=next_action_count,
        command_registry=command_registry,
        config=boss_config,
        system_prompt=system_prompt,
        triggering_prompt=DEFAULT_TRIGGERING_PROMPT,
        workspace_directory=workspace_directory,
        max_workers=1,
    )
    boss.set_results_for_tasks()
    boss.start_interaction_loop()
