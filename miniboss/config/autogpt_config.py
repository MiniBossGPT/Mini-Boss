# sourcery skip: do-not-use-staticmethod
"""
A module that contains the AutoGPTConfig class object that contains the configuration
"""
from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Optional, Type

import distro
import yaml

from miniboss.prompts.generator import PromptGenerator

# Soon this will go in a folder where it remembers more stuff about the run(s)
SAVE_FILE = str(Path(os.getcwd()) / "auto_gpt_settings.yaml")


class AutoGPTConfig:
    """
    A class object that contains the configuration information for the AI

    Attributes:
        name (str): The name of the AI.
        role (str): The description of the AI's role.
        ai_job (str): The objective the AI is supposed to complete.
        goals (list): The list of objectives the AI is supposed to complete.
        api_budget (float): The maximum dollar value for API calls (0.0 means infinite)
    """

    def __init__(
        self,
        name: str = "",
        role: str = "",
        goals: list | None = None,
        api_budget: float = 0.0,
    ) -> None:
        """
        Initialize a class instance

        Parameters:
            name (str): The name of the AI.
            role (str): The description of the AI's role.
            ai_job (list): The list of objectives the AI is supposed to complete.
            goals (list): The list of objectives the AI is supposed to complete.
            api_budget (float): The maximum dollar value for API calls (0.0 means infinite)
        Returns:
            None
        """
        if goals is None:
            goals = []
        self.name = name
        self.role = role
        self.goals = goals
        self.api_budget = api_budget

    @staticmethod
    def load(config_file: str = SAVE_FILE) -> "AutoGPTConfig":
        """
        Returns class object with parameters (name, role, ai_job, goals, api_budget) loaded from
          yaml file if yaml file exists,
        else returns class with no parameters.

        Parameters:
           config_file (int): The path to the config yaml file.
             DEFAULT: "../boss_settings.yaml"

        Returns:
            cls (object): An instance of given cls object
        """

        try:
            with open(config_file, encoding="utf-8") as file:
                config_params = yaml.load(file, Loader=yaml.FullLoader)
        except FileNotFoundError:
            config_params = {}

        name = config_params.get("ai_name", "")
        role = config_params.get("ai_role", "")
        goals = config_params.get("ai_goals", [])
        # ai_job = config_params.get("ai_job", "")
        api_budget = config_params.get("api_budget", 0.0)
        # type: Type[AutoGPTConfig]
        return AutoGPTConfig(name, role, goals)

    def save(self, config_file: str = SAVE_FILE) -> None:
        """
        Saves the class parameters to the specified file yaml file path as a yaml file.

        Parameters:
            config_file(str): The path to the config yaml file.
              DEFAULT: "../boss_settings.yaml"

        Returns:
            None
        """

        config = {"ai_name": self.name, "ai_role": self.role, "ai_goals": self.goals}
        with open(config_file, "w", encoding="utf-8") as file:
            yaml.dump(config, file, allow_unicode=True)

    def construct_full_prompt(
        self, prompt_generator: Optional[PromptGenerator] = None
    ) -> str:
        """
        Returns a prompt to the user with the class information in an organized fashion.

        Parameters:
            None

        Returns:
            full_prompt (str): A string containing the initial prompt for the user
              including the name, role, ai_job, goals, and api_budget.
        """

        prompt_start = (
            "Your decisions must always be made independently without"
            " seeking user assistance. Play to your strengths as an LLM."
            ""
        )

        from miniboss.config import Config
        from miniboss.prompts.prompt import build_default_prompt_generator

        cfg = Config()
        if prompt_generator is None:
            prompt_generator = build_default_prompt_generator()
        prompt_generator.goals = self.goals
        prompt_generator.name = self.name
        prompt_generator.role = self.role

        # Construct full prompt
        full_prompt = f"You are {prompt_generator.name}, {prompt_generator.role}\n{prompt_start}\n\nJob:\n\n"
        # full_prompt += f"{self.ai_job}\n"
        for i, task in enumerate(self.goals):
            full_prompt += f"{i+1}. {task}\n"
        if self.api_budget > 0.0:
            full_prompt += f"\nIt takes money to let you run. Your API budget is ${self.api_budget:.3f}"
        self.prompt_generator = prompt_generator
        full_prompt += f"\n\n{prompt_generator.generate_prompt_string()}"
        return full_prompt
