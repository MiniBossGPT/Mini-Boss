"""The application entry point. Can be invoked by a CLI or any other front-end application.

Functions:
    run_miniboss(continuous, continuous_limit, boss_settings, buddy_settings, skip_reprompt, speak, debug, gpt3only,
                 gpt4only, memory_type, browser_name, allow_downloads, skip_news, workspace_directory, install_plugin_deps):
        The main function to run Mini-Boss.

"""
import logging

from miniboss.boss.boss import Boss
from miniboss.config import check_openai_api_key
from miniboss.configurator import create_config
from miniboss.memory import get_memory
from miniboss.prompts.prompt import (
    DEFAULT_TRIGGERING_PROMPT,
    construct_main_boss_config,
)
from miniboss.utils import *


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
    """The main function to run Mini-Boss.

    Args:
        continuous (bool): Whether to run Mini-Boss in continuous mode.
        continuous_limit (int): The limit of continuous actions to execute.
        boss_settings (str): The path to the boss settings file.
        buddy_settings (str): The path to the agent settings file.
        skip_reprompt (bool): Whether to skip the reprompt when the user input is empty.
        speak (bool): Whether to enable the speak mode.
        debug (bool): Whether to enable debug mode.
        gpt3only (bool): Whether to use GPT-3 only.
        gpt4only (bool): Whether to use GPT-4 only.
        memory_type (str): The type of memory to use.
        browser_name (str): The name of the browser to use for web scraping.
        allow_downloads (bool): Whether to allow file downloads in the browser.
        skip_news (bool): Whether to skip checking for news updates.
        workspace_directory (str): The directory to use for the workspace.
        install_plugin_deps (bool): Whether to install plugin dependencies.

    """
    print("hi")
    # Configure logging before we do anything else.
    logger.set_level(logging.DEBUG if debug else logging.INFO)
    logger.speak_mode = speak
    cfg = Config()
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
        install_plugin_deps,
    )

    check_news_updates(cfg)
    log_warnings()
    workspace_directory = setup_workspace(cfg, workspace_directory)
    setup_file_logger(cfg, workspace_directory)
    command_registry = setup_plugins_and_commands(cfg)

    def construct_boss_config(command_registry):
        """Constructs the boss configuration.

        Args:
            command_registry (object): The command registry object.

        Returns:
            Tuple[str, object]: A tuple containing the AI name and the boss configuration object.
        """
        ai_name = ""
        boss_config = construct_main_boss_config()
        boss_config.command_registry = command_registry
        return ai_name, boss_config

    def initialize_variables():
        """Initializes the variables.

        Returns:
            Tuple[list, int]: A tuple containing the full message history (an empty list) and the next action count (0).
        """
        full_message_history = []
        next_action_count = 0
        return full_message_history, next_action_count

    def initialize_memory(cfg):
        """Initializes the memory.

        Args:
            cfg (object): The configuration object.

        Returns:
            object: The initialized memory object.
        """
        memory = get_memory(cfg, init=True)
        logger.typewriter_log(
            "Using memory of type:", Fore.GREEN, f"{memory.__class__.__name__}"
        )
        logger.typewriter_log("Using Browser:", Fore.GREEN, cfg.selenium_web_browser)
        return memory

    def start_boss(
        cfg,
        ai_name,
        memory,
        full_message_history,
        next_action_count,
        command_registry,
        boss_config,
        workspace_directory,
    ):
        """Starts the boss.

        Args:
            cfg (object): The configuration object.
            ai_name (str): The AI name.
            memory (object): The memory object.
            full_message_history (list): The full message history.
            next_action_count (int): The number of next actions to execute.
            command_registry (object): The command registry object.
            boss_config (object): The boss configuration object.
            workspace_directory (str): The directory for the workspace.
        """
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

    ai_name, boss_config = construct_boss_config(command_registry)
    full_message_history, next_action_count = initialize_variables()
    memory = initialize_memory(cfg)
    start_boss(
        cfg,
        ai_name,
        memory,
        full_message_history,
        next_action_count,
        command_registry,
        boss_config,
        workspace_directory,
    )
