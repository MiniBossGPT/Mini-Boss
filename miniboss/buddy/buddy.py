import os
import subprocess

from colorama import Fore, Style

from miniboss.buddy_app import execute_buddy_command, get_buddy_command
from miniboss.config import Config
from miniboss.json_utils.utilities import LLM_DEFAULT_RESPONSE_FORMAT, validate_json
from miniboss.llm import create_chat_completion, create_chat_message
from miniboss.logs import logger
from miniboss.utils import clean_input, parse_auto_gpt_logs, send_chat_message_to_user
from miniboss.workspace import Jobspace

CFG = Config()


class Buddy:
    """Buddy class for interacting with Mini-Boss.

    Attributes:
        ai_name (str): The name of the buddy.
        memory (object): The memory object to use.
        full_message_history (list): The full message history.
        next_action_count (int): The number of actions to execute.
        command_registry (object): The command registry object.
        config (object): The configuration object.
        system_prompt (str): The system prompt that defines the initial information the AI needs.
        triggering_prompt (str): The prompt before the AI's response.
        current_job (str): The current job assigned to the buddy.
        workspace (object): The Jobspace object for workspace management.
        final_result (dict): The final result of the buddy's interaction.
    """

    def __init__(
        self,
        ai_name,
        memory,
        full_message_history,
        next_action_count,
        command_registry,
        config,
        system_prompt,
        triggering_prompt,
        current_job,
        workspace_directory,
    ):
        """Initialize the Buddy class.

        Args:
            ai_name (str): The name of the buddy.
            memory (object): The memory object to use.
            full_message_history (list): The full message history.
            next_action_count (int): The number of actions to execute.
            command_registry (object): The command registry object.
            config (object): The configuration object.
            system_prompt (str): The system prompt that defines the initial information the AI needs.
            triggering_prompt (str): The prompt before the AI's response.
            current_job (str): The current job assigned to the buddy.
            workspace_directory (str): The directory for the workspace.
        """
        cfg = Config()
        self.ai_name = ai_name
        self.memory = memory
        self.full_message_history = full_message_history
        self.next_action_count = next_action_count
        self.command_registry = command_registry
        self.config = config
        self.system_prompt = system_prompt
        self.triggering_prompt = triggering_prompt
        self.current_job = current_job
        self.workspace = Jobspace(workspace_directory, cfg.restrict_to_workspace)
        self.final_result = {}

    def start_interaction_loop(self):
        """Start the interaction loop of the buddy."""
        # Interaction Loop
        cfg = Config()
        loop_count = 0
        command_name = None
        arguments = None
        reason = None
        user_input = ""
        while True:
            # Discontinue if continuous limit is reached
            loop_count += 1
            if (
                cfg.continuous_mode
                and cfg.continuous_limit > 0
                and loop_count > cfg.continuous_limit
            ):
                logger.typewriter_log(
                    "Continuous Limit Reached: ", Fore.YELLOW, f"{cfg.continuous_limit}"
                )
                send_chat_message_to_user(
                    f"Continuous Limit Reached: \n {cfg.continuous_limit}"
                )
                break
                # Agent Created, print message

            arguments_str = ""
            BUDDY_COMPLETE = False
            # logger.typewriter_log(
            #     f"{self.ai_name} Job:", Fore.GREEN, self.current_job, speak_text=False
            # )

            send_chat_message_to_user(f"{self.ai_name} Thinking... \n")
            # Send message to AI, get response
            # with Spinner(f"{self.ai_name} Thinking... "):
            while not BUDDY_COMPLETE:
                # # Set the target directory

                from rich.markdown import Markdown

                markdown_text = (
                    f"# 🚀 {self.ai_name} : {self.config.ai_name} : Launching Auto-GPT 🚀"
                )
                logger.log_markdown(markdown_text)

                target_directory = f"{os.getcwd()}/auto-gpt"
                buddy_settings = f"{os.getcwd()}/buddy_settings.yaml"
                command = [
                    "python3",
                    "-m",
                    "autogpt",
                    "-C",
                    buddy_settings,
                    "-m",
                    CFG.memory_backend,
                    "-b",
                    CFG.selenium_web_browser,
                ]

                if CFG.smart_llm_model == "gpt-3.5-turbo":
                    command.append("--gpt3only")
                elif CFG.set_smart_llm_model == "gpt4":
                    command.append("--gpt4only")

                command.extend(["--skip-reprompt", "--skip-news"])

                if CFG.continuous_mode:
                    command.extend(
                        [
                            "--continuous",
                            "--continuous_limit",
                            str(CFG.continuous_limit),
                        ]
                    )

                if CFG.debug_mode:
                    command.append("--debug")

                if CFG.speak_mode:
                    command.append("--speak")

                if CFG.allow_downloads:
                    command.append("--allow-downloads")

                if CFG.install_plugin_deps:
                    command.append("--install-plugin-deps")

                ##############################################
                # to test completetion loop disable this block
                # Launch Auto-GPT
                process = subprocess.run(
                    command,
                    encoding="utf8",
                    stdout=None,
                    stderr=None,
                    cwd=target_directory,
                )
                # Check the return code to see if the command was successful
                # if process.returncode == 0:
                #     print("Buddy completed work successfully.")
                # else:
                #     print("Buddy work failed.")
                #
                reason = parse_auto_gpt_logs(target_directory)
                ##############################################
                # reason = 'Successfully retrieved Googles stock prices for yesterday and saved them in a format that can be easily analyzed.'
                ##############################################

                # Convert the arguments string to a dictionary
                # the Buddy - Auto-GPT instance only completes when task is completed
                # todo: move this to prompts
                self_feedback_resp, assistant_reply_json = self.complete_buddy_task(
                    reason, cfg
                )

                if self_feedback_resp[0].lower().strip() == cfg.authorise_key:
                    user_input = "GENERATE NEXT COMMAND JSON"
                else:
                    user_input = self_feedback_resp

                BUDDY_COMPLETE = True

            # Print Assistant thoughts
            if assistant_reply_json != {}:
                validate_json(assistant_reply_json, LLM_DEFAULT_RESPONSE_FORMAT)
                # Get command name and arguments
                try:
                    # print_buddy_thoughts(
                    #     self.ai_name, assistant_reply_json, cfg.speak_mode
                    # )
                    command_name, arguments = get_buddy_command(assistant_reply_json)
                    # if cfg.speak_mode:
                    #     say_text(f"I want to execute {command_name}")

                    send_chat_message_to_user("Thinking... \n")
                    arguments = self._resolve_pathlike_command_args(arguments)

                except Exception as e:
                    logger.error("Error: \n", str(e))

            # Your main function
            if not cfg.continuous_mode and self.next_action_count == 0:
                self.user_input = ""
                self.print_next_action(command_name, arguments)
                print(
                    f"{self.ai_name}..."
                    "Enter 'y' to authorise command, 'y -N' to run N continuous commands, 's' to run self-feedback commands"
                    "'n' to exit program, or enter feedback.",
                    flush=True,
                )
                while True:
                    console_input = self.get_console_input(cfg)
                    user_input = self.process_console_input(
                        console_input, cfg, assistant_reply_json
                    )
                    if user_input is not None:
                        break
                if user_input == "EXIT":
                    send_chat_message_to_user("Exiting...")
                    print("Exiting...", flush=True)
            else:
                self.print_next_action(command_name, arguments)

            # Execute command
            result, command_name = self.execute_buddy_command(
                command_name, arguments, user_input, cfg
            )
            if self.log_result(result, command_name, self_feedback_resp, reason):
                break

    def _resolve_pathlike_command_args(self, command_args):
        """Resolve path-like command arguments to actual paths.

        Args:
            command_args (dict): The command arguments.

        Returns:
            dict: The command arguments with resolved path-like values.
        """
        if "directory" in command_args and command_args["directory"] in {"", "/"}:
            command_args["directory"] = str(self.workspace.root)
        else:
            for pathlike in ["filename", "directory", "clone_path"]:
                if pathlike in command_args:
                    command_args[pathlike] = str(
                        self.workspace.get_path(command_args[pathlike])
                    )
        return command_args

    def get_self_feedback(self, thoughts: dict, llm_model: str) -> str:
        """Generate self-feedback response based on the provided thoughts.

        Args:
            thoughts (dict): A dictionary containing thought elements like reasoning, plan, thoughts, and criticism.
            llm_model (str): The LLM model to use for generating the response.

        Returns:
            str: The self-feedback response.
        """
        ai_role = self.current_job
        # print("ai_role", ai_role)
        feedback_prompt = f"Below is a message from an AI buddy with the role of {ai_role}. Please review the provided Thought, Reasoning, Plan, and Criticism. If these elements accurately contribute to the successful execution of the assumed role, respond with the letter 'Y' followed by a space, and then explain why it is effective. If the provided information is not suitable for achieving the role's objectives, please provide one or more sentences addressing the issue and suggesting a resolution. The final work will be graded. This AI buddy needs a target score of {self.config.target_percentage} to pass. \n"
        reasoning = thoughts.get("reasoning", "")
        plan = thoughts.get("plan", "")
        thought = thoughts.get("thoughts", "")
        criticism = thoughts.get("criticism", "")
        feedback_thoughts = thought + reasoning + plan + criticism
        return create_chat_completion(
            [{"role": "user", "content": feedback_prompt + feedback_thoughts}],
            llm_model,
        )

    def complete_buddy_task(self, reason, cfg):
        """Complete the buddy's task and generate self-feedback response.

        Args:
            reason (str): The reason for completing the task.
            cfg (object): The configuration object.

        Returns:
            Tuple[str, dict]: A tuple containing the self-feedback response and the assistant reply JSON.
        """
        assistant_reply_json = {
            "thoughts": {
                "text": "My task is complete",
                "reasoning": f"I completed the assigned task : {self.current_job}",
                "plan": f"Report to MiniBoss that I have completed the job : {self.current_job} : with the following results {reason}",
                "criticism": f"I need to make sure I report that I completed my task : {self.current_job} : and determine if ",
                "speak": f"I will report that I completed my task : {self.current_job}.",
            },
            "command": {"name": "task_complete", "args": {"reason": reason}},
        }  # print("self.ai_name ", self.ai_name)
        thoughts = assistant_reply_json.get("thoughts", {})
        # print(assistant_reply_json)
        self_feedback_resp = self.get_self_feedback(thoughts, cfg.fast_llm_model)
        # logger.typewriter_log(
        #     f"BUDDY FEEDBACK: {self_feedback_resp}",
        #     Fore.YELLOW,
        #     "",
        # )
        markdown_text = (
            f"# 🚀 {self.ai_name} : {self.config.ai_name} : Auto-GPT Task Complete 🚀"
        )
        logger.log_markdown(markdown_text)
        display_feedback = self_feedback_resp.replace(
            "Y. ",
            "",
        )
        display_feedback = display_feedback.replace(
            "Y ",
            "",
        )
        final_feedback = (
            f"{self.ai_name} has completed its task, and has concluded based it its results that:"
            + display_feedback
        )
        markdown_text = f"``` {final_feedback}"
        logger.log_markdown(markdown_text)
        return display_feedback, assistant_reply_json

    def get_console_input(self, cfg):
        """Get input from the console.

        Args:
            cfg (object): The configuration object.

        Returns:
            str: The console input.
        """
        console_input = ""
        if cfg.chat_messages_enabled:
            console_input = clean_input("Waiting for your response...")
        else:
            console_input = clean_input(Fore.MAGENTA + "Input:" + Style.RESET_ALL)
        return console_input.lower().strip()

    def process_console_input(self, console_input, cfg, assistant_reply_json):
        """Process the console input and determine the action to be taken.

        This method processes the console input and determines the appropriate action to be taken based on the input.

        Args:
            console_input (str): The input provided from the console.
            cfg (object): The configuration object.
            assistant_reply_json (dict): The assistant reply JSON.

        Returns:
            Tuple[str, None] or Tuple[str, str]: A tuple containing the action to be taken and the command name (if applicable).
            The action can be one of the following:
            - "GENERATE NEXT COMMAND JSON": The next command JSON should be generated.
            - "EXIT": The program should exit.
            - console_input (str): The console input itself, indicating a command to be processed.
            - None: If the console input is invalid or does not match any predefined action.
        """
        if console_input == cfg.authorise_key:
            return "GENERATE NEXT COMMAND JSON"
        elif console_input == "s":
            thoughts = assistant_reply_json.get("thoughts", {})
            self_feedback_resp = self.get_self_feedback(thoughts, cfg.fast_llm_model)
            if self_feedback_resp[0].lower().strip() == cfg.authorise_key:
                return "GENERATE NEXT COMMAND JSON"
            else:
                return self_feedback_resp
        elif console_input == "":
            print("Invalid input format.")
            return None
        elif console_input.startswith(f"{cfg.authorise_key} -"):
            try:
                self.next_action_count = abs(int(console_input.split(" ")[1]))
                return "GENERATE NEXT COMMAND JSON"
            except ValueError:
                print(
                    f"Invalid input format. Please enter '{cfg.authorise_key} -N' where N is"
                    " the number of continuous tasks."
                )
                return None
        elif console_input == cfg.exit_key:
            return "EXIT"
        else:
            return console_input

    def print_next_action(self, command_name, arguments):
        """Print the next action to be performed by the buddy.

        Args:
            command_name (str): The name of the command.
            arguments (dict): The arguments for the command.
        """
        send_chat_message_to_user(
            "NEXT ACTION: \n " + f"COMMAND = {command_name} \n "
            f"ARGUMENTS = {arguments}"
        )
        logger.typewriter_log(
            "NEXT ACTION: ",
            Fore.CYAN,
            f"COMMAND = {Fore.CYAN}{command_name}{Style.RESET_ALL}  "
            f"ARGUMENTS = {Fore.CYAN}{arguments}{Style.RESET_ALL}",
        )

    def process_plugins_pre_command(self, cfg, command_name, arguments):
        """Process plugins before executing a command.

        Args:
            cfg (object): The configuration object.
            command_name (str): The name of the command.
            arguments (dict): The arguments for the command.

        Returns:
            Tuple[str, dict]: A tuple containing the updated command name and arguments.
        """
        for plugin in cfg.plugins:
            if not plugin.can_handle_pre_command():
                continue
            command_name, arguments = plugin.pre_command(command_name, arguments)
        return command_name, arguments

    def process_plugins_post_command(self, cfg, command_name, result):
        """Process plugins after executing a command.

        Args:
            cfg (object): The configuration object.
            command_name (str): The name of the command.
            result (str): The result of the command execution.

        Returns:
            str: The updated result after processing plugins.
        """
        for plugin in cfg.plugins:
            if not plugin.can_handle_post_command():
                continue
            result = plugin.post_command(command_name, result)
        return result

    def execute_buddy_command(self, command_name, arguments, user_input, cfg):
        """Execute a command based on the given command name and arguments.

        Args:
            command_name (str): The name of the command.
            arguments (dict): The arguments for the command.
            user_input (str): The user input.
            cfg (object): The configuration object.

        Returns:
            Tuple[str, str]: A tuple containing the result of the command execution and the command name (if applicable).
        """
        if command_name is not None and command_name.lower().startswith("error"):
            return (
                f"Command {command_name} threw the following error: {arguments}",
                command_name,
            )
        elif command_name == "human_feedback":
            return f"Human feedback: {user_input}", command_name
        else:
            command_name, arguments = self.process_plugins_pre_command(
                cfg, command_name, arguments
            )
            command_result = execute_buddy_command(
                self.command_registry,
                command_name,
                arguments,
                self.config.prompt_generator,
            )
            result = f"Command {command_name} returned: {command_result}"
            result = self.process_plugins_post_command(cfg, command_name, result)
            if self.next_action_count > 0:
                self.next_action_count -= 1
            return result, command_name

    def log_result(self, result, command_name, self_feedback_resp, reason):
        """Log the result of the command execution.

        Args:
            result (str): The result of the command execution.
            command_name (str): The name of the command.
            self_feedback_resp (str): The self-feedback response.
            reason (str): The reason for completing the task.

        Returns:
            bool: True if the command was executed successfully, False otherwise.
        """
        if result is not None:
            self.full_message_history.append(create_chat_message("system", result))
            logger.typewriter_log("", Fore.GREEN, "\n")
            if command_name == "task_complete":
                self.final_result = {
                    "command": command_name,
                    "arguments": reason,
                    "task": self.current_job,
                    "feedback": self_feedback_resp or {},
                }
                return True
        else:
            self.full_message_history.append(
                create_chat_message("system", "Unable to execute command")
            )
            logger.typewriter_log("SYSTEM: ", Fore.YELLOW, "Unable to execute command")
        return False
