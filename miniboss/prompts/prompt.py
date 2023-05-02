from colorama import Fore

from miniboss.config.boss_config import BossConfig
from miniboss.config.buddy_config import BuddyConfig
from miniboss.config.config import Config
from miniboss.llm import ApiManager
from miniboss.logs import logger
from miniboss.prompts.generator import PromptGenerator

from miniboss.setup import prompt_user, prompt_buddy
from miniboss.utils import clean_input

CFG = Config()

DEFAULT_TRIGGERING_PROMPT = (
    "Determine which next command to use, and respond using the format specified above:"
)
DEFAULT_BUDDY_TRIGGERING_PROMPT = (
    "Determine which next command to use to solve your given job, and respond using the format specified above:"
)


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
        logger.typewriter_log("Name :", Fore.GREEN, config.ai_name)
        # logger.typewriter_log("Role :", Fore.GREEN, config.ai_role)
        logger.typewriter_log("Job:", Fore.GREEN, f"{config.ai_job}")
        logger.typewriter_log("Tasks:", Fore.GREEN, f"{config.ai_tasks}")
        logger.typewriter_log(
            "API Budget:",
            Fore.GREEN,
            "infinite" if config.api_budget <= 0 else f"${config.api_budget}",
        )
        logger.typewriter_log("Target Percentage:", Fore.GREEN,
                              "infinite" if config.target_percentage <= 0 else f"{config.target_percentage}")
        logger.typewriter_log("Tasks Complete:", Fore.GREEN,
                              "infinite" if config.complete_percentage <= 0 else f"{config.complete_percentage}")
    elif config.ai_name:
        logger.typewriter_log(
            "Welcome back! ",
            Fore.GREEN,
            f"Would you like me to return to being {config.ai_name}?",
            speak_text=True,
        )
        # Role:  {config.ai_role}
        should_continue = clean_input(
            f"""Continue with the last settings?
Name:  {config.ai_name}
Job: {config.ai_job}
Tasks: {config.ai_tasks}
Target Percentage: {"infinite" if config.target_percentage <= 0 else f"{config.target_percentage}"}
Tasks Complete: {"infinite" if config.complete_percentage <= 0 else f"{config.complete_percentage}"}
API Budget: {"infinite" if config.api_budget <= 0 else f"${config.api_budget}"}
Continue ({CFG.authorise_key}/{CFG.exit_key}): """
        )
        if should_continue.lower() == CFG.exit_key:
            config = BossConfig()

    if not config.ai_name:
        config = prompt_user()
        config.save(CFG.boss_settings_file)

    # set the total api budget
    api_manager = ApiManager()
    api_manager.set_total_budget(config.api_budget)

    # Agent Created, print message
    logger.typewriter_log(
        config.ai_name,
        Fore.LIGHTBLUE_EX,
        "has been created with the following details:",
        speak_text=True,
    )
    # Print the ai config details
    # Name
    logger.typewriter_log("Name:", Fore.GREEN, config.ai_name, speak_text=False)
    # Role
    # logger.typewriter_log("Role:", Fore.GREEN, config.ai_role, speak_text=False)
    # Job
    logger.typewriter_log("Job:", Fore.GREEN, config.ai_job, speak_text=False)
    # Tasks
    logger.typewriter_log("Tasks:", Fore.GREEN, "", speak_text=False)
    for task in config.ai_tasks:
        logger.typewriter_log("-", Fore.GREEN, task, speak_text=False)
    # todo: numbers break here
    # logger.typewriter_log("Target Percentage:", Fore.GREEN, config.target_percentage, speak_text=False)
    # logger.typewriter_log("Tasks Complete:", Fore.GREEN, config.complete_percentage, speak_text=False)

    return config


# todo: this should never prompt the user
def construct_main_buddy_config(task) -> BuddyConfig:
    """Construct the prompt for the AI to respond to

    Returns:
        str: The prompt string
    """
    config = BuddyConfig.load(CFG.buddy_settings_file)

    #     if CFG.skip_reprompt and config.ai_name:
    #
    #         logger.typewriter_log("Name :", Fore.GREEN, config.ai_name)
    #         # logger.typewriter_log("Role :", Fore.GREEN, config.ai_role)
    #         logger.typewriter_log("Job:", Fore.GREEN, f"{config.ai_job}")
    #         logger.typewriter_log("Tasks:", Fore.GREEN, f"{config.ai_tasks}")
    #         logger.typewriter_log(
    #             "API Budget:",
    #             Fore.GREEN,
    #             "infinite" if config.api_budget <= 0 else f"${config.api_budget}",
    #         )
    #     elif config.ai_name:
    #         logger.typewriter_log(
    #             "Welcome back! ",
    #             Fore.GREEN,
    #             f"Would you like me to return to being {config.ai_name}?",
    #             speak_text=True,
    #         )
    #         # Role:  {config.ai_role}
    #         should_continue = clean_input(
    #             f"""Continue with the last settings?
    # Name:  {config.ai_name}
    # Job: {config.ai_job}
    # API Budget: {"infinite" if config.api_budget <= 0 else f"${config.api_budget}"}
    # Continue ({CFG.authorise_key}/{CFG.exit_key}): """
    #         )
    #         if should_continue.lower() == CFG.exit_key:
    #             config = BuddyConfig()

    config = prompt_buddy(task)
    config.save(CFG.buddy_settings_file)
    # set the total api budget
    api_manager = ApiManager()
    api_manager.set_total_budget(config.api_budget)

    # # Agent Created, print message
    # logger.typewriter_log(
    #     config.ai_name,
    #     Fore.LIGHTBLUE_EX,
    #     "has been created with the following details:",
    #     speak_text=True,
    # )
    # Print the ai config details
    # Name
    # logger.typewriter_log("Buddy:", Fore.GREEN, config.ai_name, speak_text=False)
    # # Role
    # logger.typewriter_log("Role:", Fore.GREEN, config.ai_role, speak_text=False)
    # # Job
    # logger.typewriter_log("Job:", Fore.GREEN, config.ai_job, speak_text=False)
    # logger.typewriter_log("Target Percentage:", Fore.GREEN, config.target_percentage, speak_text=False)
    # logger.typewriter_log("Tasks Complete:", Fore.GREEN, config.complete_percentage, speak_text=False)

    return config
