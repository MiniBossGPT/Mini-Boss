"""Logging module for Mini-Boss."""
import logging
import os
import random
import re
import time
from logging import LogRecord

from colorama import Fore, Style
from rich.console import Console
from rich.markdown import Markdown

# from miniboss.speech import say_text
from rich.table import Table

from miniboss.singleton import Singleton


class Logger(metaclass=Singleton):
    """
    Logger that handle titles in different colors.
    Outputs logs in console, activity.log, and errors.log
    For console handler: simulates typing
    """

    def __init__(self):
        # create log directory if it doesn't exist
        this_files_dir_path = os.path.dirname(__file__)
        log_dir = os.path.join(this_files_dir_path, "../logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_file = "activity.log"
        error_file = "error.log"

        console_formatter = minibossFormatter("%(title_color)s %(message)s")

        # Create a handler for console which simulate typing
        self.typing_console_handler = TypingConsoleHandler()
        self.typing_console_handler.setLevel(logging.INFO)
        self.typing_console_handler.setFormatter(console_formatter)

        # Create a handler for console without typing simulation
        self.console_handler = ConsoleHandler()
        self.console_handler.setLevel(logging.DEBUG)
        self.console_handler.setFormatter(console_formatter)

        # Info handler in activity.log
        self.file_handler = logging.FileHandler(
            os.path.join(log_dir, log_file), "a", "utf-8"
        )
        self.file_handler.setLevel(logging.DEBUG)
        info_formatter = minibossFormatter(
            "%(asctime)s %(levelname)s %(title)s %(message_no_color)s"
        )
        self.file_handler.setFormatter(info_formatter)

        # Error handler error.log
        error_handler = logging.FileHandler(
            os.path.join(log_dir, error_file), "a", "utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = minibossFormatter(
            "%(asctime)s %(levelname)s %(module)s:%(funcName)s:%(lineno)d %(title)s"
            " %(message_no_color)s"
        )
        error_handler.setFormatter(error_formatter)

        self.typing_logger = logging.getLogger("TYPER")
        self.typing_logger.addHandler(self.typing_console_handler)
        self.typing_logger.addHandler(self.file_handler)
        self.typing_logger.addHandler(error_handler)
        self.typing_logger.setLevel(logging.DEBUG)

        self.logger = logging.getLogger("LOGGER")
        self.logger.addHandler(self.console_handler)
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(error_handler)
        self.logger.setLevel(logging.DEBUG)

        self.speak_mode = False

    def typewriter_log(
        self, title="", title_color="", content="", speak_text=False, level=logging.INFO
    ):
        # if speak_text and self.speak_mode:
        #     say_text(f"{title}. {content}")

        if content:
            if isinstance(content, list):
                content = " ".join(content)
        else:
            content = ""

        self.typing_logger.log(
            level, content, extra={"title": title, "color": title_color}
        )

    def log_mini_boss_setup(self, config):
        console = Console()
        logger.typewriter_log("", Fore.GREEN, "\n")
        # Role:  {config.ai_role}
        logger.typewriter_log("Name :", Fore.CYAN, config.ai_name)
        # logger.typewriter_log("Role :", Fore.GREEN, config.ai_role)
        logger.typewriter_log("Job:", Fore.CYAN, f"{config.ai_job}")
        logger.typewriter_log("", Fore.GREEN, "\n")
        target_percentage = str(config.target_percentage * 100) + "%"
        complete_percentage = str(config.complete_percentage * 100) + "%"
        api_budget = "unlimited" if config.api_budget <= 0 else f"${config.api_budget}"
        logger.typewriter_log("Complete:", Fore.YELLOW, f"{str(complete_percentage)}")
        logger.typewriter_log("Budget:", Fore.YELLOW, api_budget)
        logger.typewriter_log("", Fore.GREEN, "\n")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#", style="white", width=4)
        table.add_column("Task", style="white", width=12)
        table.add_column("Status", style="cyan", width=8)
        table.add_column("Score", style="cyan", width=8)
        table.add_column("Target", style="cyan", width=8)
        table.add_column("Workers", style="cyan", width=8)
        table.add_column("Description")
        # print(config.ai_task_results)
        # Add tasks to
        for i, task in enumerate(config.ai_tasks):
            task_parts = task.split(": ", 1)  # split on the first occurrence of ': '
            if len(task_parts) == 2:
                if len(config.ai_task_results):
                    task_results = config.ai_task_results[i]
                    status = task_results["status"]
                    score = task_results["score"]
                    worker_count = task_results["worker_count"]
                else:
                    status = "-"
                    score = 0
                    worker_count = 0
                # Set border style for rows
                row_style = "dim white"
                display_count = i + 1
                task_title, task_description = task_parts
                table.add_row(
                    str(display_count),
                    task_title,
                    str(status),
                    str(score),
                    target_percentage,
                    str(worker_count),
                    task_description,
                )
                table.add_row("", "", "", "", "", "", style=row_style)
            else:
                logger.typewriter_log(
                    "Error", Fore.RED, f"Could not parse task: {task}", speak_text=False
                )

        console.print(table)

    def log_buddy_setup(self, config):
        console = Console()
        logger.typewriter_log("", Fore.GREEN, "\n")
        # Role:  {config.ai_role}
        markdown_text = f"# 🚀 {config.name} : {config.ai_name} 🚀"
        logger.log_markdown(markdown_text)
        markdown_text = f"``` Job: {config.current_job} ```"
        logger.log_markdown(markdown_text)
        logger.typewriter_log("", Fore.GREEN, "\n")
        logger.typewriter_log("", Fore.GREEN, "\n")
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("#", style="white", width=4)
        table.add_column("Buddy Objectives for Auto-GPT")

        # Add tasks to
        for i, task in enumerate(config.ai_goals):
            row_style = "dim white"
            display_count = i + 1
            table.add_row(str(display_count), task)
            table.add_row("", "", style=row_style)

        console.print(table)

    def log_markdown(self, message):
        console = Console()
        md = Markdown(message)
        console.print(md)
        logger.typewriter_log("", Fore.GREEN, "\n")

    def debug(
        self,
        message,
        title="",
        title_color="",
    ):
        self._log(title, title_color, message, logging.DEBUG)

    def info(
        self,
        message,
        title="",
        title_color="",
    ):
        self._log(title, title_color, message, logging.INFO)

    def warn(
        self,
        message,
        title="",
        title_color="",
    ):
        self._log(title, title_color, message, logging.WARN)

    def error(self, title, message=""):
        self._log(title, Fore.RED, message, logging.ERROR)

    def _log(
        self,
        title: str = "",
        title_color: str = "",
        message: str = "",
        level=logging.INFO,
    ):
        if message:
            if isinstance(message, list):
                message = " ".join(message)
        self.logger.log(
            level, message, extra={"title": str(title), "color": str(title_color)}
        )

    def set_level(self, level):
        self.logger.setLevel(level)
        self.typing_logger.setLevel(level)

    def double_check(self, additionalText=None):
        if not additionalText:
            additionalText = (
                "Please ensure you've setup and configured everything"
                " correctly. Read https://github.com/MiniBossGPT/Mini-Boss#readme to "
                "double check. You can also create a github issue or join the discord"
                " and ask there!"
            )

        self.typewriter_log("DOUBLE CHECK CONFIGURATION", Fore.YELLOW, additionalText)


"""
Output stream to console using simulated typing
"""


class TypingConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        min_typing_speed = 0.05
        max_typing_speed = 0.01

        msg = self.format(record)
        try:
            words = msg.split()
            for i, word in enumerate(words):
                print(word, end="", flush=True)
                if i < len(words) - 1:
                    print(" ", end="", flush=True)
                typing_speed = random.uniform(min_typing_speed, max_typing_speed)
                time.sleep(typing_speed)
                # type faster after each word
                min_typing_speed = min_typing_speed * 0.95
                max_typing_speed = max_typing_speed * 0.95
            print()
        except Exception:
            self.handleError(record)


class ConsoleHandler(logging.StreamHandler):
    def emit(self, record) -> None:
        msg = self.format(record)
        try:
            print(msg)
        except Exception:
            self.handleError(record)


class minibossFormatter(logging.Formatter):
    """
    Allows to handle custom placeholders 'title_color' and 'message_no_color'.
    To use this formatter, make sure to pass 'color', 'title' as log extras.
    """

    def format(self, record: LogRecord) -> str:
        if hasattr(record, "color"):
            record.title_color = (
                getattr(record, "color")
                + getattr(record, "title")
                + " "
                + Style.RESET_ALL
            )
        else:
            record.title_color = getattr(record, "title")
        if hasattr(record, "msg"):
            record.message_no_color = remove_color_codes(getattr(record, "msg"))
        else:
            record.message_no_color = ""
        return super().format(record)


def remove_color_codes(s: str) -> str:
    # print(s)
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", s)


logger = Logger()


def print_assistant_thoughts(
    ai_name: object,
    assistant_reply_json_valid: object,
    speak_mode: bool = False,
) -> None:
    assistant_thoughts_reasoning = None
    assistant_thoughts_plan = None
    assistant_thoughts_speak = None
    assistant_thoughts_criticism = None

    assistant_thoughts = assistant_reply_json_valid.get("thoughts", {})
    assistant_thoughts_text = assistant_thoughts.get("text")
    if assistant_thoughts:
        assistant_thoughts_reasoning = assistant_thoughts.get("reasoning")
        assistant_thoughts_plan = assistant_thoughts.get("plan")
        assistant_thoughts_criticism = assistant_thoughts.get("criticism")
        assistant_thoughts_speak = assistant_thoughts.get("speak")
    logger.typewriter_log(
        f"{ai_name.upper()} THOUGHTS:", Fore.YELLOW, f"{assistant_thoughts_text}"
    )
    logger.typewriter_log("REASONING:", Fore.YELLOW, f"{assistant_thoughts_reasoning}")
    if assistant_thoughts_plan:
        logger.typewriter_log("PLAN:", Fore.YELLOW, "")
        # If it's a list, join it into a string
        if isinstance(assistant_thoughts_plan, list):
            assistant_thoughts_plan = "\n".join(assistant_thoughts_plan)
        elif isinstance(assistant_thoughts_plan, dict):
            assistant_thoughts_plan = str(assistant_thoughts_plan)

        # Split the input_string using the newline character and dashes
        lines = assistant_thoughts_plan.split("\n")
        for line in lines:
            line = line.lstrip("- ")
            logger.typewriter_log("- ", Fore.GREEN, line.strip())
    logger.typewriter_log("CRITICISM:", Fore.YELLOW, f"{assistant_thoughts_criticism}")
    # # Speak the assistant's thoughts
    # if speak_mode and assistant_thoughts_speak:
    #     say_text(assistant_thoughts_speak)


def print_buddy_thoughts(
    ai_name: object,
    assistant_reply_json_valid: object,
    speak_mode: bool = False,
) -> None:
    assistant_thoughts_reasoning = None
    assistant_thoughts_plan = None
    assistant_thoughts_speak = None
    assistant_thoughts_criticism = None

    assistant_thoughts = assistant_reply_json_valid.get("thoughts", {})
    assistant_thoughts_text = assistant_thoughts.get("text")
    if assistant_thoughts:
        assistant_thoughts_reasoning = assistant_thoughts.get("reasoning")
        assistant_thoughts_plan = assistant_thoughts.get("plan")
        assistant_thoughts_criticism = assistant_thoughts.get("criticism")
        assistant_thoughts_speak = assistant_thoughts.get("speak")
    logger.typewriter_log(
        f"{ai_name.upper()} THOUGHTS:", Fore.YELLOW, f"{assistant_thoughts_text}"
    )
    logger.typewriter_log("REASONING:", Fore.YELLOW, f"{assistant_thoughts_reasoning}")
    if assistant_thoughts_plan:
        logger.typewriter_log("PLAN:", Fore.YELLOW, "")
        # If it's a list, join it into a string
        if isinstance(assistant_thoughts_plan, list):
            assistant_thoughts_plan = "\n".join(assistant_thoughts_plan)
        elif isinstance(assistant_thoughts_plan, dict):
            assistant_thoughts_plan = str(assistant_thoughts_plan)

        # Split the input_string using the newline character and dashes
        lines = assistant_thoughts_plan.split("\n")
        for line in lines:
            line = line.lstrip("- ")
            logger.typewriter_log("- ", Fore.GREEN, line.strip())
    logger.typewriter_log("CRITICISM:", Fore.YELLOW, f"{assistant_thoughts_criticism}")
    # # Speak the assistant's thoughts
    # if speak_mode and assistant_thoughts_speak:
    #     say_text(assistant_thoughts_speak)
