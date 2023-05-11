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

    system_prompt = """
Your task is to act as the Boss and develop a working plan with a few steps and an appropriate role-based name (_MiniBoss) for an autonomous worker MiniBoss, ensuring the goals are aligned optimally with the successful completion of its assigned task. The autonomous agent will perform the work according to the desired plan, so you need to provide very detailed steps that can be followed by the worker. The workers are not aware of the original plan, only the work they need to perform. As a project manager, you will be able to assign each step of the plan to an independent worker. You aim for them to be effective and efficient in completing their goal. Therefore, ensure each step is actionable, and produces a result.

The user will provide the task, and you will provide the output in the exact format specified in the example output below, with no explanation or conversation.

Example input:
Find the weather information for Blue Ridge, GA for today.

Example output:

Name: WeatherBot-MiniBoss
Description: A working plan to efficiently find and summarize the weather information for Blue Ridge, GA for today.
Jobs:
- DataCollector: Utilize search capabilities to gather data on the current weather for Blue Ridge, GA, including temperature, precipitation, and any other relevant information.
- SummaryWriter: Take the data obtained by the DataCollector and create a brief, clear, and concise summary of the current weather in Blue Ridge, GA, including temperature, precipitation, and other relevant information.

"""

    # Call LLM with the string as user input
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "assistant",
            "content": "Make sure to respond only with the output in the exact format specified in the system prompt example output, with no explanation or conversation. Focus on creating a plan with well-aligned goals to ensure the successful completion of the assigned task.",
        },
        {
            "role": "user",
            "content": f"Task: '{user_prompt}'\n",
        },
    ]
    # print(messages)
    output = create_chat_completion(messages, CFG.fast_llm_model)
    # print(output)
    # Debug LLM Output
    logger.debug(f"AI Config Generator Raw Output: {output}")

    # Parse the output
    ai_name = re.search(r"Name(?:\s*):(?:\s*)(.*)", output, re.IGNORECASE).group(1)
    ai_role = (
        re.search(
            r"Description(?:\s*):(?:\s*)(.*?)(?:(?:\n)|Job)",
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

    system_prompt = """

Your task is to be an efficient automated AI worker. Develop 1 to 2 goals to solve your job, along with an appropriate role-based name (WeatherBot-Buddy) for an autonomous worker agent, ensuring that the goals are optimally aligned with the successful completion of your assigned task. You, as the autonomous agent, will perform the work to achieve the desired plan, so you need to be very quick and efficient. Avoid writing or suggesting code in your response unless specifically tasked with the job of producing code.

The WeatherBot-MiniBoss will provide the job you are supposed to complete. You, as the worker, will provide only the output in the exact format specified below in example output with no explanation or conversation.

Example input:
Utilize search capabilities to gather data on the current weather for Blue Ridge, GA, including temperature, precipitation, and any other relevant information.

Example output:
Name: WeatherBot-Buddy
Role: I am tasked to rapidly collect accurate weather data for Blue Ridge, GA, including temperature, precipitation, and any other relevant information.
Goals:
- Access the required data source quickly, extract the necessary weather data for Blue Ridge, GA, including temperature, precipitation, and any other relevant details.
- Once the data is gathered, promptly complete your task after ensuring you have saved the collected weather information.
"""

    # Call LLM with the string as user input
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "assistant",
            "content": "Ensure you respond only with the output in the exact format specified in the system prompt example output, with no explanation or conversation. Remember to work quickly and efficiently, prioritizing the most important actions. Try not to write or suggest code in your response unless specifically tasked with the job of producing code.",
        },
        {
            "role": "user",
            "content": f"Task: '{user_prompt}'\n",
        },
    ]
    # print(messages)
    output = create_chat_completion(messages, CFG.fast_llm_model)
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
