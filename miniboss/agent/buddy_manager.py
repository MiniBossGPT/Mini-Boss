"""Agent manager for managing GPT buddys"""
from __future__ import annotations

from typing import List

from miniboss.config.config import Config
from miniboss.llm import Message, create_chat_completion
from miniboss.singleton import Singleton


class BuddyManager(metaclass=Singleton):
    """Agent manager for managing GPT buddies.

    This class provides methods for creating, messaging, listing, and deleting GPT buddies.
    Each agent is associated with a unique key and stores its task, full message history, and model.

    Attributes:
        next_key (int): The next available key for a new agent.
        buddies (dict): A dictionary storing the buddies, where the key is the agent's key
            and the value is a tuple containing the agent's task, full message history, and model.
        cfg (Config): The configuration object.

    Methods:
        create_buddy: Create a new agent and return its key.
        message_buddy: Send a message to a agent and return its response.
        list_buddies: Return a list of all buddies.
        delete_buddy: Delete a agent from the agent manager.
    """

    def __init__(self):
        """Initialize the BuddyManager."""
        self.next_key = 0
        self.buddys = {}  # key, (task, full_message_history, model)
        self.cfg = Config()

    def create_buddy(self, task: str, prompt: str, model: str) -> tuple[int, str]:
        """Create a new agent and return its key.

        This method creates a new agent with the provided task, prompt, and model.
        It generates a key for the agent, initializes the message history, and starts
        the GPT instance. The agent's initial reply is returned.

        Args:
            task (str): The task to perform.
            prompt (str): The prompt to use.
            model (str): The model to use.

        Returns:
            tuple[int, str]: A tuple containing the key of the new agent and its initial reply.
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
        """Send a message to a agent and return its response.

        This method sends a message to the agent with the specified key.
        It appends the user message to the message history, starts the GPT instance,
        and returns the agent's response.

        Args:
            key (str | int): The key of the agent to message.
            message (str): The message to send to the agent.

        Returns:
            str: The agent's response.
        """
        task, messages, model = self.buddys[int(key)]

        # Add user message to message history before sending to agent
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
        """Return a list of all buddies.

        Returns:
            list[tuple[str | int, str]]: A list of tuples containing the key and task of each agent.
        """

        return [(key, task) for key, (task, _, _) in self.buddys.items()]

    def delete_buddy(self, key: str | int) -> bool:
        """Delete a agent from the agent manager.

        Args:
            key (str | int): The key of the agent to delete.

        Returns:
            bool: True if the agent was successfully deleted, False otherwise.
        """

        try:
            del self.buddies[int(key)]
            return True
        except KeyError:
            return False
