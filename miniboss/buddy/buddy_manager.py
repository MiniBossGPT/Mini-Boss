"""Agent manager for managing GPT buddys"""
from __future__ import annotations

from typing import List

from miniboss.config.config import Config
from miniboss.llm import Message, create_chat_completion
from miniboss.singleton import Singleton


class BuddyManager(metaclass=Singleton):
    """Agent manager for managing GPT buddys"""

    def __init__(self):
        self.next_key = 0
        self.buddys = {}  # key, (task, full_message_history, model)
        self.cfg = Config()

    # Create new GPT buddy
    # TODO: Centralise use of create_chat_completion() to globally enforce token limit

    def create_buddy(self, task: str, prompt: str, model: str) -> tuple[int, str]:
        """Create a new buddy and return its key

        Args:
            task: The task to perform
            prompt: The prompt to use
            model: The model to use

        Returns:
            The key of the new buddy
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
        buddy_reply = create_chat_completion(
            model=model,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": buddy_reply})

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
        # This is done instead of len(buddys) to make keys unique even if buddys
        # are deleted
        self.next_key += 1

        self.buddys[key] = (task, messages, model)

        for plugin in self.cfg.plugins:
            if not plugin.can_handle_post_instruction():
                continue
            buddy_reply = plugin.post_instruction(buddy_reply)

        return key, buddy_reply

    def message_buddy(self, key: str | int, message: str) -> str:
        """Send a message to an buddy and return its response

        Args:
            key: The key of the buddy to message
            message: The message to send to the buddy

        Returns:
            The buddy's response
        """
        task, messages, model = self.buddys[int(key)]

        # Add user message to message history before sending to buddy
        messages.append({"role": "user", "content": message})

        for plugin in self.cfg.plugins:
            if not plugin.can_handle_pre_instruction():
                continue
            if plugin_messages := plugin.pre_instruction(messages):
                for plugin_message in plugin_messages:
                    messages.append(plugin_message)

        # Start GPT instance
        buddy_reply = create_chat_completion(
            model=model,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": buddy_reply})

        plugins_reply = buddy_reply
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
            buddy_reply = plugin.post_instruction(buddy_reply)

        return buddy_reply

    def list_buddys(self) -> list[tuple[str | int, str]]:
        """Return a list of all buddys

        Returns:
            A list of tuples of the form (key, task)
        """

        # Return a list of buddy keys and their tasks
        return [(key, task) for key, (task, _, _) in self.buddys.items()]

    def delete_buddy(self, key: str | int) -> bool:
        """Delete an buddy from the buddy manager

        Args:
            key: The key of the buddy to delete

        Returns:
            True if successful, False otherwise
        """

        try:
            del self.buddys[int(key)]
            return True
        except KeyError:
            return False
