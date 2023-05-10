from colorama import Fore

from miniboss.config.boss_config import BossConfig
from miniboss.config.buddy_config import BuddyConfig
from miniboss.config.config import Config
from miniboss.llm import ApiManager
from miniboss.logs import logger
from miniboss.prompts.generator import PromptGenerator
from miniboss.setup import prompt_buddy, prompt_user
from miniboss.utils import clean_input

CFG = Config()

DEFAULT_TRIGGERING_PROMPT = (
    "Determine which next command to use, and respond using the format specified above:"
)
DEFAULT_BUDDY_TRIGGERING_PROMPT = "Determine which next command to use to solve your given job, and respond using the format specified above:"


def build_default_prompt_generator() -> PromptGenerator:
    """
    This function generates a prompt string that includes various constraints,
        commands, resources, and performance evaluations.

    Returns:
        str: The generated prompt string.
    """

    # Initialize the PromptGenerator object
    prompt_generator = PromptGenerator()

    # Add constraints to the PromptGenerator object
    prompt_generator.add_constraint(
        "~4000 word limit for short term memory. Your short term memory is short, so"
        " immediately save important information to files."
    )
    prompt_generator.add_constraint(
        "If you are unsure how you previously did something or want to recall past"
        " events, thinking about similar events will help you remember."
    )
    prompt_generator.add_constraint("No user assistance")
    prompt_generator.add_constraint(
        'Exclusively use the commands listed in double quotes e.g. "command name"'
    )

    # Define the command list
    commands = [
        ("Task Complete (Shutdown)", "task_complete", {"reason": "<reason>"}),
    ]

    # Add commands to the PromptGenerator object
    for command_label, command_name, args in commands:
        prompt_generator.add_command(command_label, command_name, args)

    # Add resources to the PromptGenerator object
    prompt_generator.add_resource(
        "Internet access for searches and information gathering. Always use command: Google Search."
    )
    prompt_generator.add_resource("Long Term memory management.")
    prompt_generator.add_resource(
        "GPT-3.5 powered Agents for delegation of simple tasks."
    )
    prompt_generator.add_resource("File output.")

    # Add performance evaluations to the PromptGenerator object
    prompt_generator.add_performance_evaluation(
        "Continuously review and analyze your actions to ensure you are performing to"
        " the best of your abilities."
    )
    prompt_generator.add_performance_evaluation(
        "Constructively self-criticize your big-picture behavior constantly."
    )
    prompt_generator.add_performance_evaluation(
        "Reflect on past decisions and strategies to refine your approach."
    )
    prompt_generator.add_performance_evaluation(
        "Every command has a cost, so be smart and efficient. Aim to complete tasks in"
        " the least number of steps."
    )
    prompt_generator.add_performance_evaluation("Write all code to a file.")
    return prompt_generator


def construct_main_boss_config() -> BossConfig:
    """Construct the prompt for the AI to respond to

    Returns:
        str: The prompt string
    """

    config = BossConfig.load(CFG.boss_settings_file)
    if CFG.skip_reprompt and config.ai_name:
        logger.log_mini_boss_setup(config)
    elif config.ai_name:
        logger.typewriter_log("", Fore.GREEN, "\n")
        logger.typewriter_log("Welcome back! \n", Fore.GREEN, "")
        logger.typewriter_log("", Fore.GREEN, "\n")
        logger.typewriter_log(
            "",
            Fore.GREEN,
            f"Would you like me to return to being {config.ai_name}? \n\n",
        )
        logger.log_mini_boss_setup(config)

        should_continue = clean_input(
            f"""Continue with the last settings?
Continue ({CFG.authorise_key}/{CFG.exit_key}): """
        )

        # reset the config if the user did not want to continue last settings
        if should_continue.lower() == CFG.exit_key:
            config = BossConfig()

    # set the total api budget
    api_manager = ApiManager()
    api_manager.set_total_budget(config.api_budget)

    # if no existing config
    if not config.ai_name:
        config = prompt_user()
        config.save(CFG.boss_settings_file)
        # Agent Created, print message
        logger.typewriter_log(
            config.ai_name,
            Fore.LIGHTBLUE_EX,
            "has been created with the following details:",
            speak_text=False,
        )
        logger.log_mini_boss_setup(config)

    return config


def construct_main_buddy_config(task, target_percentage, name) -> BuddyConfig:
    """Construct the prompt for the AI to respond to

    Returns:
        str: The prompt string
    """
    config = BuddyConfig.load(CFG.buddy_settings_file)
    if CFG.skip_reprompt and config.ai_name:
        logger.log_buddy_setup(config)
    elif config.ai_name:
        logger.typewriter_log("", Fore.GREEN, "\n")
        logger.typewriter_log(
            "",
            Fore.GREEN,
            f"Would you like me to return to being {config.ai_name}? \n\n",
        )
        logger.log_buddy_setup(config)

        should_continue = clean_input(
            f"""Continue with the last settings?
Continue ({CFG.authorise_key}/{CFG.exit_key}): """
        )

        # reset the config if the user did not want to continue last settings
        if should_continue.lower() == CFG.exit_key:
            config = BuddyConfig()

    # if no existing config
    if not config.ai_name:
        config = prompt_buddy(task, target_percentage, name)
        config.save(CFG.buddy_settings_file)
        logger.log_buddy_setup(config)

    return config


def create_main_buddy_config(task, target_percentage, name) -> BuddyConfig:
    """Construct the prompt for the AI to respond to

    Returns:
        str: The prompt string
    """
    config = prompt_buddy(task, target_percentage, name)
    config.save(CFG.buddy_settings_file)
    logger.log_buddy_setup(config)

    return config
