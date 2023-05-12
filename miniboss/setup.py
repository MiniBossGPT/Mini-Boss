"""Set up the AI and its goals"""
import re

from colorama import Fore, Style

from miniboss import utils
from miniboss.config import Config
from miniboss.config.autogpt_config import AutoGPTConfig
from miniboss.config.boss_config import BossConfig
from miniboss.config.buddy_config import BuddyConfig
from miniboss.llm import create_chat_completion
from miniboss.logs import logger

CFG = Config()

from datetime import date


def print_todays_date():
    return date.today()


def prompt_user() -> BossConfig:
    """Prompt the user for input

    Returns:
        BossConfig: The BossConfig object tailored to the user's input
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

    ai_role = "you are an AI designed to autonomously deploy worker agent buddy's to professionally solve the desired goal of the user"

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
    """Generates an BossConfig object from the given string.

    Returns:
    BossConfig: The BossConfig object tailored to the user's input
    """

    system_prompt = f"""Your task is to act as the MiniBoss, an orchestrator of sub-tasks. Your role involves developing a detailed working plan to accomplish the main goal provided by the user.
    The working plan should contain a series of actionable steps, each of which can be assigned to an autonomous worker (Buddy) for execution.
    Remember, the Buddies are not privy to the overall plan; they only receive the specific sub-tasks you assign to them. Therefore, each sub-task needs to be self-contained, actionable, and result-oriented. Each sub-task should lead to a tangible output that contributes directly to the main goal.
    In your task assignments, prioritize quick solutions that leverage existing resources. Encourage the use of internet searches like Google or Bing to rapidly gather necessary information or solve problems rather than creating new APIs or software.
    The user will provide the main task. Your output should be in the exact format specified in the example output below, with no additional explanation or conversation.

        The current date is {print_todays_date()}.

        Example input:
        Analyze and report on the performance of Tesla's stock price this week.

        Example output:
        Name: StockAnalysisBot-MiniBoss
        Role: Devise a strategic plan to efficiently analyze and report on the performance of Tesla's stock price for the current week, considering today's date is {print_todays_date()}. This involves coordinating autonomous agents to collect, analyze, and summarize the relevant data.
        Tasks:
        - DataCollector: Use Google or Bing search to retrieve the most recent and reliable Tesla's stock prices for the current week. Your task is to prioritize speed and accuracy in your data collection.
        - DataAnalyzer: Perform a detailed analysis on the retrieved data to discern patterns, trends, and notable events. Your analysis should enable clear insights into Tesla's stock performance this week.
        - ReportWriter: Compile the insights from the data analysis into a clear, concise report summarizing the performance of Tesla's stock price this week.
        """

    # Call LLM with the string as user input
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "assistant",
            "content": "Your main focus should be on devising a strategic plan, breaking down the user's task into self-contained, actionable steps. Each step should be defined clearly and lead to a tangible output that directly contributes to the main task. Remember to assign each step to an appropriate autonomous worker role. Keep your output strictly within the format specified in the system prompt, without any additional explanation or conversation.",
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


# todo: this is for the auto-=gpt task
def generate_aiconfig_automatic_buddy_gpt(
    user_prompt, target_percentage, name
) -> BuddyConfig:
    """Generates an BossConfig object from the given string.

    Returns:
    BossConfig: The BossConfig object tailored to the user's input
    """

    system_prompt = f"""
        Your task is to act as a Buddy, an autonomous worker. You will be assigned a specific task to complete, and you must develop 1 to 2 strategic goals to achieve this task effectively. Additionally, assign yourself an appropriate role-based name (StockDataCollector-Buddy) to reflect your function in the task.

        Remember, you are an autonomous agent whose goal is to achieve the task quickly and efficiently. To do this, prioritize using internet searches to gather necessary information or solve problems. Unless it is absolutely necessary, you should avoid writing or suggesting code.

        The MiniBoss will provide you with the task you need to complete. Your output should be in the exact format specified in the example output below, with no additional explanation or conversation.

        The current date is {print_todays_date()}.

        Example input:
        Use appropriate data sources to retrieve Tesla's stock prices for the current week.

        Example output:
        Name: StockDataCollector-Buddy
        Role: My task is to rapidly and accurately retrieve Tesla's stock prices for the current week, considering today's date is {print_todays_date()}.
        Goals:
        - Utilize internet search engines like Google or Bing to identify the most appropriate and reliable data sources for retrieving Tesla's stock prices for the current week. Ensure the data is recent and accurate.
        - Extract the necessary stock price data and save it in a format that can be easily analyzed. Promptly complete your task, ensuring the data is ready for further analysis.
        """

    # Call LLM with the string as user input
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "assistant",
            "content": "As an autonomous worker, your focus should be on achieving your assigned task quickly and accurately. Formulate clear goals that align with your task. Avoid suggesting or writing code unless your task explicitly requires it. If you're provided a location of a previous worker's data file, ensure you search the directory first. Adhere strictly to the format specified in the system prompt, providing no additional explanation or conversation.",
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
