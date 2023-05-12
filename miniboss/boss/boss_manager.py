"""Agent manager for managing GPT boss"""
from __future__ import annotations

from typing import List

from miniboss.config.config import Config
from miniboss.llm import Message, create_chat_completion
from miniboss.singleton import Singleton


class BossManager(metaclass=Singleton):
    """Agent manager for managing GPT boss"""

    def __init__(self):
        """Initialize the BossManager object.

        The BossManager class is responsible for managing GPT bosses.
        It initializes the internal variables to keep track of the bosses.

        Args:
            None

        Returns:
            None
        """
        self.next_key = 0
        self.boss = {}  # key, (task, full_message_history, model)
        self.cfg = Config()

    def create_boss(self, task: str, prompt: str, model: str) -> tuple[int, str]:
        """Create a new boss and return its key.

        This method creates a new GPT boss using the provided task, prompt, and model.
        It generates a conversation history with the user's prompt and interacts with the boss model
        using the `create_chat_completion` function. The generated response from the boss is stored
        in the conversation history. The method also allows plugins to modify the conversation history
        before and after interacting with the boss.

        Args:
            task (str): The task to perform.
            prompt (str): The prompt to use.
            model (str): The model to use.

        Returns:
            tuple[int, str]: The key of the new boss and the boss's response.
        """
        messages: List[Message] = [
            {"role": "user", "content": prompt},
        ]
        for plugin in self.cfg.plugins:
            if not plugin.can_handle_pre_instruction():
                continue
            if plugin_messages := plugin.pre_instruction(messages):
                messages.extend(iter(plugin_messages))
        # Start GPT instance
        boss_reply = create_chat_completion(
            model=model,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": boss_reply})

        plugins_reply = ""
        for i, plugin in enumerate(self.cfg.plugins):
            if not plugin.can_handle_on_instruction():
                continue
            if plugin_result := plugin.on_instruction(messages):
                sep = "\n" if i else ""
                plugins_reply = f"{plugins_reply}{sep}{plugin_result}"

        if plugins_reply and plugins_reply != "":
            messages.append({"role": "assistant", "content": plugins_reply})
        key = self.next_key
        # This is done instead of len(boss) to make keys unique even if boss
        # are deleted
        self.next_key += 1

        self.boss[key] = (task, messages, model)

        for plugin in self.cfg.plugins:
            if not plugin.can_handle_post_instruction():
                continue
            boss_reply = plugin.post_instruction(boss_reply)

        return key, boss_reply

    def message_boss(self, key: str | int, message: str) -> str:
        """Send a message to a boss and return its response.

        This method sends a message to an existing boss identified by the provided key.
        It retrieves the boss's task, full message history, and model. The user message is
        added to the message history, and plugins have the opportunity to modify the history.
        The message history is then used to interact with the boss model and generate a response.
        Plugins are applied to the response before and after interacting with the boss.

        Args:
            key (str | int): The key of the boss to message.
            message (str): The message to send to the boss.

        Returns:
            str: The response from the boss.
        """
        task, messages, model = self.boss[int(key)]

        # Add user message to message history before sending to boss
        messages.append({"role": "user", "content": message})

        for plugin in self.cfg.plugins:
            if not plugin.can_handle_pre_instruction():
                continue
            if plugin_messages := plugin.pre_instruction(messages):
                for plugin_message in plugin_messages:
                    messages.append(plugin_message)

        # Start GPT instance
        boss_reply = create_chat_completion(
            model=model,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": boss_reply})

        plugins_reply = boss_reply
        for i, plugin in enumerate(self.cfg.plugins):
            if not plugin.can_handle_on_instruction():
                continue
            if plugin_result := plugin.on_instruction(messages):
                sep = "\n" if i else ""
                plugins_reply = f"{plugins_reply}{sep}{plugin_result}"
        # Update full message history
        if plugins_reply and plugins_reply != "":
            messages.append({"role": "assistant", "content": plugins_reply})

        for plugin in self.cfg.plugins:
            if not plugin.can_handle_post_instruction():
                continue
            boss_reply = plugin.post_instruction(boss_reply)

        return boss_reply

    def list_bosss(self) -> list[tuple[str | int, str]]:
        """Return a list of all bosses.

        This method returns a list of tuples representing all the bosses
        managed by the BossManager. Each tuple contains the boss's key and task.

        Returns:
            list[tuple[str | int, str]]: A list of tuples of the form (key, task).
        """

        return [(key, task) for key, (task, _, _) in self.boss.items()]

    def delete_boss(self, key: str | int) -> bool:
        """Delete a boss from the boss manager.

        This method deletes a boss from the BossManager based on the provided key.
        If the boss exists, it is removed from the boss manager. Otherwise, if the key
        does not exist, nothing happens.

        Args:
            key (str | int): The key of the boss to delete.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """

        try:
            del self.boss[int(key)]
            return True
        except KeyError:
            return False
