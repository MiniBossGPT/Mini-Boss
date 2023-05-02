"""Agent manager for managing GPT boss"""
from __future__ import annotations

from typing import List

from miniboss.config.config import Config
from miniboss.llm import create_chat_completion
from miniboss.singleton import Singleton
from miniboss.types.openai import Message


class BossManager(metaclass=Singleton):
    """Agent manager for managing GPT boss"""

    def __init__(self):
        self.next_key = 0
        self.boss = {}  # key, (task, full_message_history, model)
        self.cfg = Config()

    # Create new GPT boss
    # TODO: Centralise use of create_chat_completion() to globally enforce token limit

    def create_boss(self, task: str, prompt: str, model: str) -> tuple[int, str]:
        """Create a new boss and return its key

        Args:
            task: The task to perform
            prompt: The prompt to use
            model: The model to use

        Returns:
            The key of the new boss
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
        """Send a message to an boss and return its response

        Args:
            key: The key of the boss to message
            message: The message to send to the boss

        Returns:
            The boss's response
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
        """Return a list of all boss

        Returns:
            A list of tuples of the form (key, task)
        """

        # Return a list of boss keys and their tasks
        return [(key, task) for key, (task, _, _) in self.boss.items()]

    def delete_boss(self, key: str | int) -> bool:
        """Delete an boss from the boss manager

        Args:
            key: The key of the boss to delete

        Returns:
            True if successful, False otherwise
        """

        try:
            del self.boss[int(key)]
            return True
        except KeyError:
            return False
