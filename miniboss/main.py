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
from miniboss.prompts.prompt import (
    DEFAULT_TRIGGERING_PROMPT,
    construct_main_boss_config,
)
from miniboss.utils import *
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

    check_news_updates(cfg)
    log_warnings()
    workspace_directory = setup_workspace(cfg, workspace_directory)
    setup_file_logger(cfg, workspace_directory)
    command_registry = setup_plugins_and_commands(cfg)

    def construct_boss_config(command_registry):
        ai_name = ""
        boss_config = construct_main_boss_config()
        boss_config.command_registry = command_registry
        return ai_name, boss_config

    def initialize_variables():
        full_message_history = []
        next_action_count = 0
        return full_message_history, next_action_count

    def initialize_memory(cfg):
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
