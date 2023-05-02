from colorama import Fore, Style

from miniboss.app import execute_command, get_command
from miniboss.config import Config
from miniboss.json_utils.json_fix_llm import fix_json_using_multiple_techniques
from miniboss.json_utils.utilities import LLM_DEFAULT_RESPONSE_FORMAT, validate_json
from miniboss.llm import chat_with_ai, buddy_chat_with_ai, create_chat_completion, create_chat_message
from miniboss.logs import logger, print_assistant_thoughts
# from miniboss import say_text
from miniboss.spinner import Spinner
from miniboss.utils import clean_input, send_chat_message_to_user
from miniboss.workspace import Jobspace
import subprocess
from autogpt.cli import main as autogpt_main
import os
"""Execute code in a Docker container"""
import subprocess
import sys
import re
from pathlib import Path
import ast
import docker
from docker.errors import ImageNotFound

from miniboss.config import Config

CFG = Config()

def we_are_running_in_a_docker_container() -> bool:
    """Check if we are running in a Docker container

    Returns:
        bool: True if we are running in a Docker container, False otherwise
    """
    return os.path.exists("/.dockerenv")


def execute_auto_gpt():

    # if we_are_running_in_a_docker_container():
    #     result = subprocess.run(
    #         f"python {filename}", capture_output=True, encoding="utf8", shell=True
    #     )
    #     if result.returncode == 0:
    #         return result.stdout
    #     else:
    #         return f"Error: {result.stderr}"

    try:
        client = docker.from_env()
        image_name = "significantgravitas/auto-gpt:latest"
        try:
            client.images.get(image_name)
            print(f"Image '{image_name}' found locally")
        except ImageNotFound:
            print(f"Image '{image_name}' not found locally, pulling from Docker Hub")
            low_level_client = docker.APIClient()
            for line in low_level_client.pull(image_name, stream=True, decode=True):
                status = line.get("status")
                progress = line.get("progress")
                if status and progress:
                    print(f"{status}: {progress}")
                elif status:
                    print(status)

        env_file = '.env'
        with open(env_file) as f:
            env_vars = {line.strip().split('=')[0]: line.strip().split('=')[1] for line in f if line.strip()}

        container = client.containers.run(
            image_name,
            ["auto-gpt", "--gpt3only", "--continuous"],
            volumes={
                os.path.abspath(os.getcwd()): {
                    "bind": "/workspace",
                    "mode": "rw",
                }
            },
            working_dir="/app",
            environment=env_vars,
            stderr=True,
            stdout=True,
            detach=True,
            auto_remove=True,
        )

        container.wait()
        logs = container.logs().decode("utf-8")
        container.remove()

        # print(f"Execution complete. Output: {output}")
        # print(f"Logs: {logs}")

        return logs

    except docker.errors.DockerException as e:
        print(
            "Could not run the script in a container. If you haven't already, please install Docker https://docs.docker.com/get-docker/"
        )
        return f"Error: {str(e)}"

    except Exception as e:
        return f"Error: {str(e)}"


class Buddy:
    """Buddy class for interacting with Mini-Boss.

    Attributes:
        ai_name: The name of the buddy.
        memory: The memory object to use.
        full_message_history: The full message history.
        next_action_count: The number of actions to execute.
        system_prompt: The system prompt is the initial prompt that defines everything
          the AI needs to know to achieve its task successfully.
        Currently, the dynamic and customizable information in the system prompt are
          ai_name, description and goals.

        triggering_prompt: The last sentence the AI will see before answering.
            For Mini-Boss, this prompt is:
            Determine which next command to use, and respond using the format specified
              above:
            The triggering prompt is not part of the system prompt because between the
              system prompt and the triggering
            prompt we have contextual information that can distract the AI and make it
              forget that its goal is to find the next task to achieve.
            SYSTEM PROMPT
            CONTEXTUAL INFORMATION (memory, previous conversations, anything relevant)
            TRIGGERING PROMPT

        The triggering prompt reminds the AI about its short term meta task
        (defining the next task)
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
                # logger.typewriter_log(
                #     "Continuous Limit Reached: ", Fore.YELLOW, f"{cfg.continuous_limit}"
                # )
                # send_chat_message_to_user(
                #     f"Continuous Limit Reached: \n {cfg.continuous_limit}"
                # )
                break
                # Agent Created, print message
            logger.typewriter_log(
                self.ai_name,
                Fore.LIGHTBLUE_EX,
                "currently working!",
                speak_text=True,
            )
            # Print the ai config details
            # Name
            # logger.typewriter_log(f"{self.ai_name}:", Fore.GREEN, self.ai_name, speak_text=False)
            # Role
            # logger.typewriter_log("Role:", Fore.GREEN, config.ai_role, speak_text=False)
            # Job
            arguments_str = ""
            BUDDY_COMPLETE = False
            logger.typewriter_log(f"{self.ai_name} Job:", Fore.GREEN, self.current_job, speak_text=False)
            # logger.typewriter_log("Target Percentage:", Fore.GREEN, config.target_percentage, speak_text=False)
            # logger.typewriter_log("Tasks Complete:", Fore.GREEN, config.complete_percentage, speak_text=False)
            send_chat_message_to_user(f"{self.ai_name} Thinking... \n")
            # Send message to AI, get response
            # with Spinner(f"{self.ai_name} Thinking... "):
            while not BUDDY_COMPLETE:
                # todo: if the buddy is running its own job it should work?

                # Your main program code here

                # Run another Python program in parallel and capture its output
                # # Set the target directory
                target_directory = f"{os.getcwd()}/auto-gpt"

                ##############################################
                ### Disable this block to test
                ##############################################
                buddy_settings = f"{os.getcwd()}/buddy_settings.yaml"
                # # todo: plug in all of the options here
                # # command = ["python3", "-m", "autogpt", "--gpt3only", "--continuous", "-C", buddy_settings,"-m", "local"]
                # # command = ["python3", "-m", "autogpt", "--gpt3only", "-C", buddy_settings,"-m", "local"]
                command = ["python3", "-m", "autogpt", "-C", buddy_settings, "-m", "local"]

                #
                # # working
                process = subprocess.run(command, encoding='utf8', stdout=None, stderr=None, cwd=target_directory)

                # Check the return code to see if the command was successful
                if process.returncode == 0:
                    print("Buddy completed work successfully.")
                else:
                    print("Buddy work failed.")


                ##############################################
                # Define the log file path
                log_file_path = os.path.join(target_directory, "logs/activity.log")

                # Read the log file in reverse
                with open(log_file_path, "r", encoding="utf-8") as log_file:
                    lines = log_file.readlines()
                    lines.reverse()

                # Define a regular expression pattern to match the "task_complete" command and its arguments
                pattern = r"COMMAND = task_complete\s+ARGUMENTS = ({.*})"

                # Search for the pattern in the reversed log content
                for line in lines:
                    match = re.search(pattern, line)
                    if match:
                        arguments_str = match.group(1)
                        # Parse the string to a Python dictionary
                        arguments = ast.literal_eval(arguments_str)
                        # Access the 'reason' value

                        pre_reason = arguments['reason']
                        # Remove single and double quotes
                        reason = pre_reason.strip('\'"').replace("'", "")
                        # Print the 'reason' value
                        print(f"Task complete Reason: {reason}")
                        break
                else:
                    print("Task complete command not found in the log file.")
                    break

                # Convert the arguments string to a dictionary

                assistant_reply_json = {
                    'thoughts': {'text': 'My task is complete',
                                 'reasoning': f'I completed the assigned task : {self.current_job}',
                                 'plan': f'- Report to MiniBoss that the task is complete : {self.current_job} : with results {reason}',
                                 'criticism': f'I need to make sure I report that I completed my task : {self.current_job}',
                                 'speak': f'I will report that I completed my task : {self.current_job}.'},
                    'command': {'name': 'task_complete', 'args': {'reason': reason}}}  # print("self.ai_name ", self.ai_name)
                thoughts = assistant_reply_json.get("thoughts", {})
                # print(assistant_reply_json)
                self_feedback_resp = self.get_self_feedback(
                    thoughts, cfg.fast_llm_model
                )
                logger.typewriter_log(
                    f"BUDDY FEEDBACK: {self_feedback_resp}",
                    Fore.YELLOW,
                    "",
                )
                if self_feedback_resp[0].lower().strip() == cfg.authorise_key:
                    user_input = "GENERATE NEXT COMMAND JSON"
                else:
                    user_input = self_feedback_resp
                BUDDY_COMPLETE = True
                # print(result)

                # this is a local buddy - this worked - possible different app
                # test_assistant_reply = buddy_chat_with_ai(
                #     self,
                #     self.system_prompt,
                #     f"{self.triggering_prompt} The job you need to solve as quickly as possible and in as few steps as possible is: {self.current_job}. Remember it is your job to make decisions quickly to be an efficient worker.",
                #     self.full_message_history,
                #     self.memory,
                #     cfg.fast_token_limit,
                # )  # TODO: This hardcodes the model to use GPT3.5. Make this an argument
                # test_assistant_reply_json = fix_json_using_multiple_techniques(test_assistant_reply)
                # print("\ntest_assistant_reply_json\n")
                # print(test_assistant_reply_json)


            # Print Assistant thoughts
            if assistant_reply_json != {}:
                validate_json(assistant_reply_json, LLM_DEFAULT_RESPONSE_FORMAT)
                # Get command name and arguments
                try:
                    print_assistant_thoughts(
                        self.ai_name, assistant_reply_json, cfg.speak_mode
                    )
                    command_name, arguments = get_command(assistant_reply_json)
                    # if cfg.speak_mode:
                    #     say_text(f"I want to execute {command_name}")

                    send_chat_message_to_user("Thinking... \n")
                    arguments = self._resolve_pathlike_command_args(arguments)

                except Exception as e:
                    logger.error("Error: \n", str(e))

            if not cfg.continuous_mode and self.next_action_count == 0:
                # ### GET USER AUTHORIZATION TO EXECUTE COMMAND ###
                # Get key press: Prompt the user to press enter to continue or escape
                # to exit
                self.user_input = ""
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
                print(
                    f"{self.ai_name}..."
                    "Enter 'y' to authorise command, 'y -N' to run N continuous commands, 's' to run self-feedback commands"
                    "'n' to exit program, or enter feedback.",
                    flush=True,
                )
                while True:
                    console_input = ""
                    if cfg.chat_messages_enabled:
                        console_input = clean_input("Waiting for your response...")
                    else:
                        console_input = clean_input(
                            Fore.MAGENTA + "Input:" + Style.RESET_ALL
                        )
                    if console_input.lower().strip() == cfg.authorise_key:
                        user_input = "GENERATE NEXT COMMAND JSON"
                        break
                    elif console_input.lower().strip() == "s":
                        logger.typewriter_log(
                            "-=-=-=-=-=-=-= THOUGHTS, REASONING, PLAN AND CRITICISM WILL NOW BE VERIFIED BY AGENT -=-=-=-=-=-=-=",
                            Fore.GREEN,
                            "",
                        )
                        thoughts = assistant_reply_json.get("thoughts", {})
                        self_feedback_resp = self.get_self_feedback(
                            thoughts, cfg.fast_llm_model
                        )
                        logger.typewriter_log(
                            f"SELF FEEDBACK: {self_feedback_resp}",
                            Fore.YELLOW,
                            "",
                        )
                        if self_feedback_resp[0].lower().strip() == cfg.authorise_key:
                            user_input = "GENERATE NEXT COMMAND JSON"
                        else:
                            user_input = self_feedback_resp
                        break
                    elif console_input.lower().strip() == "":
                        print("Invalid input format.")
                        continue
                    elif console_input.lower().startswith(f"{cfg.authorise_key} -"):
                        try:
                            self.next_action_count = abs(
                                int(console_input.split(" ")[1])
                            )
                            user_input = "GENERATE NEXT COMMAND JSON"
                        except ValueError:
                            print(
                                f"Invalid input format. Please enter '{cfg.authorise_key} -N' where N is"
                                " the number of continuous tasks."
                            )
                            continue
                        break
                    elif console_input.lower() == cfg.exit_key:
                        user_input = "EXIT"
                        break
                    else:
                        user_input = console_input
                        command_name = "human_feedback"
                        break

                if user_input == "GENERATE NEXT COMMAND JSON":
                    logger.typewriter_log(
                        "-=-=-=-=-=-=-= COMMAND AUTHORISED BY USER -=-=-=-=-=-=-=",
                        Fore.MAGENTA,
                        "",
                    )
                elif user_input == "EXIT":
                    send_chat_message_to_user("Exiting...")
                    print("Exiting...", flush=True)
                    break
            else:
                # Print command
                send_chat_message_to_user(
                    "NEXT ACTION: \n " + f"COMMAND = {command_name} \n "
                                         f"ARGUMENTS = {arguments}"
                )

                logger.typewriter_log(
                    "NEXT ACTION: ",
                    Fore.CYAN,
                    f"COMMAND = {Fore.CYAN}{command_name}{Style.RESET_ALL}"
                    f"  ARGUMENTS = {Fore.CYAN}{arguments}{Style.RESET_ALL}",
                )

            # Execute command
            if command_name is not None and command_name.lower().startswith("error"):
                result = (
                    f"Command {command_name} threw the following error: {arguments}"
                )
            elif command_name == "human_feedback":
                result = f"Human feedback: {user_input}"
            else:
                for plugin in cfg.plugins:
                    if not plugin.can_handle_pre_command():
                        continue
                    command_name, arguments = plugin.pre_command(
                        command_name, arguments
                    )
                print("command_name", command_name)
                print("arguments", arguments)

                #  todo: this will be key for completing the cycle here
                command_result = execute_command(
                    self.command_registry,
                    command_name,
                    arguments,
                    self.config.prompt_generator,
                )

                result = f"Command {command_name} returned: " f"{command_result}"

                for plugin in cfg.plugins:
                    if not plugin.can_handle_post_command():
                        continue
                    result = plugin.post_command(command_name, result)
                if self.next_action_count > 0:
                    self.next_action_count -= 1

            # Check if there's a result from the command append it to the message
            # history
            if result is not None:
                self.full_message_history.append(create_chat_message("system", result))
                logger.typewriter_log("SYSTEM: ", Fore.YELLOW, result)
                if command_name == "task_complete":
                    self.final_result = {
                        "command": command_name,
                        "arguments": reason,
                        "task": self.current_job,
                        "feedback": self_feedback_resp or {}
                    }
                    break
            else:
                self.full_message_history.append(
                    create_chat_message("system", "Unable to execute command")
                )
                logger.typewriter_log(
                    "SYSTEM: ", Fore.YELLOW, "Unable to execute command"
                )

    def _resolve_pathlike_command_args(self, command_args):
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
        """Generates a feedback response based on the provided thoughts dictionary.
        This method takes in a dictionary of thoughts containing keys such as 'reasoning',
        'plan', 'thoughts', and 'criticism'. It combines these elements into a single
        feedback message and uses the create_chat_completion() function to generate a
        response based on the input message.
        Args:
            thoughts (dict): A dictionary containing thought elements like reasoning,
            plan, thoughts, and criticism.
        Returns:
            str: A feedback response generated using the provided thoughts dictionary.
        """
        ai_role = self.current_job
        print("ai_role", ai_role)
        feedback_prompt = f"Below is a message from an AI buddy with the role of {ai_role}. Please review the provided Thought, Reasoning, Plan, and Criticism. If these elements accurately contribute to the successful execution of the assumed role, respond with the letter 'Y' followed by a space, and then explain why it is effective. If the provided information is not suitable for achieving the role's objectives, please provide one or more sentences addressing the issue and suggesting a resolution."
        reasoning = thoughts.get("reasoning", "")
        plan = thoughts.get("plan", "")
        thought = thoughts.get("thoughts", "")
        criticism = thoughts.get("criticism", "")
        feedback_thoughts = thought + reasoning + plan + criticism
        return create_chat_completion(
            [{"role": "user", "content": feedback_prompt + feedback_thoughts}],
            llm_model,
        )
