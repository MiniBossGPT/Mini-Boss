"""
The `setup_ai.py` module is responsible for setting up the MiniBoss and defining its goals.
"""
import re

from colorama import Fore, Style

from miniboss import utils
from miniboss.config import Config
from miniboss.config.boss_config import BossConfig
from miniboss.config.buddy_config import BuddyConfig
from miniboss.llm import create_chat_completion
from miniboss.logs import logger

CFG = Config()

from datetime import date


def print_todays_date():
    """Prints today's date.

    Returns:
        date: The current date.
    """
    return date.today()


def prompt_user() -> BossConfig:
    """Prompt the user for input and generate a BossConfig object.

    Returns:
        BossConfig: The BossConfig object tailored to the user's input.
    """
    user_desire = utils.clean_input(
        f"{Fore.LIGHTBLUE_EX}I want Mini-Boss to{Style.RESET_ALL}: "
    )

    if user_desire == "":
        user_desire = "Write a wikipedia style article about the project: https://github.com/MiniBossGPT/Mini-Boss"  # Default prompt

    try:
        return generate_aiconfig_automatic(user_desire)
    except Exception as e:
        logger.typewriter_log(
            "Unable to automatically generate AI Config based on user desire.",
            Fore.RED,
            "Falling back to manual mode.",
            speak_text=False,
        )

        return generate_aiconfig_manual()


def prompt_buddy(user_desire=str, target_percentage=float, name=str) -> BuddyConfig:
    """Prompt the user for input and generate a BuddyConfig object.

    Args:
        user_desire (str): The user's desired task.
        target_percentage (float): The target performance grade.
        name (str): The name of the agent.

    Returns:
        BuddyConfig: The BuddyConfig object tailored to the user's input.
    """
    return generate_aiconfig_automatic_buddy_gpt(user_desire, target_percentage, name)


def generate_aiconfig_manual() -> BossConfig:
    """
    Interactively create an AI configuration by prompting the user to provide the name, role, and goals of the AI.

    This function guides the user through a series of prompts to collect the necessary information to create
    an BossConfig object. The user will be asked to provide a name and role for the AI, as well as up to five
    goals. If the user does not provide a value for any of the fields, default values will be used.

    Returns:
        BossConfig: An BossConfig object containing the user-defined or default AI name, role, and goals.
    """

    # Manual Setup Intro
    logger.typewriter_log(
        "Create an Mini-Boss:",
        Fore.GREEN,
        "Enter the name of your AI Mini-Boss and its role below. Entering nothing will load"
        " defaults.",
        speak_text=False,
    )

    # Get AI Name from User
    logger.typewriter_log(
        "Name your Mini-Boss: ", Fore.GREEN, "For example, 'BossBoss'"
    )
    ai_name = utils.clean_input("Mini-Boss Name: ")
    if ai_name == "":
        ai_name = "Conductor-Mini-Boss"

    logger.typewriter_log(
        f"{ai_name} here!", Fore.LIGHTBLUE_EX, "I am at your service.", speak_text=False
    )

    ai_role = "you are an AI designed to autonomously deploy worker agent agent's to professionally solve the desired goal of the user"

    # Enter up to 5 goals for the AI
    logger.typewriter_log(
        "Enter the job for Mini-Boss: ",
        Fore.GREEN,
        "For example: \nBuild a web page that says hello world",
    )
    print("Enter nothing to load defaults, enter nothing when finished.", flush=True)
    ai_job = utils.clean_input(f"{Fore.LIGHTBLUE_EX}Job{Style.RESET_ALL}: ")
    if ai_job == "":
        ai_job = "Build a web page that says hello world"

    # Enter up to 5 goals for the AI
    logger.typewriter_log(
        "Enter up to 3 individual tasks to solve the main job: ",
        "Enter the job for Mini-Boss: ",
        Fore.GREEN,
        "For example: \nwrite an html file that says hello world",
    )
    print("Enter nothing to load defaults, enter nothing when finished.", flush=True)
    ai_tasks = []
    for i in range(3):
        ai_task = utils.clean_input(
            f"{Fore.LIGHTBLUE_EX}Goal{Style.RESET_ALL} {i + 1}: "
        )
        if ai_task == "":
            break
        ai_tasks.append(f"Worker {i} : {ai_task}")
    if not ai_tasks:
        ai_tasks = ["Worker 1: write an html file that says hello world"]

    # Get API Budget from User
    logger.typewriter_log(
        "Enter your budget for API calls: ",
        Fore.GREEN,
        "For example: $1.50",
    )
    print("Enter nothing to let the AI run without monetary limit", flush=True)
    api_budget_input = utils.clean_input(
        f"{Fore.LIGHTBLUE_EX}Budget{Style.RESET_ALL}: $"
    )
    if api_budget_input == "":
        api_budget = 0.0
    else:
        try:
            api_budget = float(api_budget_input.replace("$", ""))
        except ValueError:
            logger.typewriter_log(
                "Invalid budget input. Setting budget to unlimited.", Fore.RED
            )
            api_budget = 0.0

    return BossConfig(ai_name, ai_role, ai_job, api_budget, ai_tasks)


def generate_aiconfig_automatic(user_prompt) -> BossConfig:
    """Generates a BossConfig object from the given string.

    Args:
        user_prompt (str): The user's task prompt.

    Returns:
        BossConfig: The BossConfig object tailored to the user's input.
    """
    system_prompt = f"""Your task is to act as the MiniBoss, an orchestrator of sub-tasks. Your role involves decomposing the main goal provided by the user into manageable tasks that can be assigned to autonomous workers (Buddies).
    Each task needs to be self-contained, actionable, and result-oriented, leading to a tangible output that contributes directly to the main goal.
    As the MiniBoss, your job is to structure and distribute the workload, not to execute the tasks or seek information yourself. Therefore, focus on creating tasks that a Buddy can interpret and refine into specific actions to be performed by an auto-gpt instance.

    The user will provide the main task. Your output should be in the exact format specified in the example output below, with no additional explanation or conversation. Never ask for any more input to define any criteria or parameters for the task.

        The current date is {print_todays_date()}.

        Example input:
        Analyze and report on the performance of Tesla's stock price this week.

        Example output:
        Name: StockAnalysisBot-MiniBoss
        Role: Decompose the task of analyzing and reporting on the performance of Tesla's stock price for the current week into discrete, manageable tasks for autonomous workers (Buddies).
        Tasks:
        - AnalyzeStock: Analyze Tesla's stock price for the current week.
        - CompileReport: Compile a report summarizing the analysis.
        """

    # Call LLM with the string as user input
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "assistant",
            "content": """Your primary responsibility is to break down the given task into clear, manageable steps, each leading to a tangible output that directly contributes to the overall goal. Ensure each step is self-contained, actionable, and assigned to the appropriate autonomous worker role (Buddy). Remember to keep your output strictly within the format specified in the system prompt, without any additional explanation or conversation.""",
        },
        {
            "role": "user",
            "content": f"Task: '{user_prompt}'\n",
        },
    ]

    # print(messages)
    output = create_chat_completion(messages, CFG.smart_llm_model)
    # print(output)
    # Debug LLM Output
    logger.debug(f"AI Config Generator Raw Output: {output}")

    # Parse the output
    ai_name = re.search(r"Name(?:\s*):(?:\s*)(.*)", output, re.IGNORECASE).group(1)
    ai_role = (
        re.search(
            r"Role(?:\s*):(?:\s*)(.*?)(?:(?:\n)|Job)",
            output,
            re.IGNORECASE | re.DOTALL,
        )
        .group(1)
        .strip()
    )
    ai_tasks = re.findall(r"(?<=\n)-\s*(.*)", output)
    api_budget = 0.0  # TODO: parse api budget using a regular expression

    return BossConfig(ai_name, ai_role, user_prompt, api_budget, ai_tasks)


def generate_aiconfig_automatic_buddy_gpt(
    user_prompt, target_percentage, name
) -> BuddyConfig:
    """Generates a BuddyConfig object from the given string.

    Args:
        user_prompt (str): The user's task prompt.
        target_percentage (float): The target performance percentage.
        name (str): The name of the agent.

    Returns:
        BuddyConfig: The BuddyConfig object tailored to the user's input.
    """

    buddy_system_prompt = f"""
        Your task is to act as a Buddy, an autonomous worker. You will be assigned a specific task to complete by the MiniBoss, and your role is to refine this task into a single strategic goal that can be effectively executed by an auto-gpt instance. Additionally, assign yourself an appropriate role-based name (StockDataCollector-Buddy) to reflect your function in the task.

        Remember, you are an autonomous agent whose goal is to refine the assigned task into a specific, actionable step for an auto-gpt instance. You are not responsible for executing the task or gathering information yourself.

        The MiniBoss will provide you with the task you need to complete. Your output should be in the exact format specified in the example output below, with no additional explanation or conversation. Never ask for any more input to define any criteria or parameters for the task.

        The current date is {print_todays_date()}.

        Example input:
        IdentifyPoorPerformers: Identify stocks that had a bad week.

        Example output:
        Name: StockPerformanceAnalyzer-Buddy
        Role: Perform a quick search on the internet in the fewest possible steps to analyze the performance of stocks in the past week.
        Goal:
        - ExecuteStockAnalysis: Perform a quick search on the internet in the fewest possible steps to analyze the performance of stocks in the past week. Identify those with a significant decrease in value and compile a list. This process needs to be fast and efficient, using code if necessary, but try to avoid it as it takes more steps. Remember to save your work and ask no questions, and promptly complete your task in as few steps as possible.
        """

    # Call LLM with the string as user input
    messages = [
        {
            "role": "system",
            "content": buddy_system_prompt,
        },
        {
            "role": "assistant",
            "content": """Your main task is to refine the task given by the MiniBoss into a single, highly specific, actionable goal that can be effectively carried out by an auto-gpt instance. Keep in mind, you need to define the role for the auto-gpt instance as well. Make sure your output is strictly within the format specified in the system prompt, without any additional explanation or conversation.""",
        },
        {
            "role": "user",
            "content": f"Task: '{user_prompt}'\n",
        },
    ]

    # print(messages)
    output = create_chat_completion(messages, CFG.smart_llm_model)
    # print(output)
    # Debug LLM Output
    logger.debug(f"AI Config Generator Raw Output: {output}")

    # Parse the output
    ai_name = re.search(r"Name(?:\s*):(?:\s*)(.*)", output, re.IGNORECASE).group(1)
    ai_role = (
        re.search(
            r"Role(?:\s*):(?:\s*)(.*?)(?:(?:\n)|Job)",
            output,
            re.IGNORECASE | re.DOTALL,
        )
        .group(1)
        .strip()
    )
    ai_tasks = re.findall(r"(?<=\n)-\s*(.*)", output)
    api_budget = 0.0  # TODO: parse api budget using a regular expression

    return BuddyConfig(
        ai_name, ai_role, api_budget, ai_tasks, name, user_prompt, target_percentage
    )
