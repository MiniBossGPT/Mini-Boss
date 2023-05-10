import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from colorama import Fore, Style

from miniboss.app import execute_boss_command, get_boss_command
from miniboss.buddy.buddy import Buddy
from miniboss.config import Config
from miniboss.config.config import Config
from miniboss.json_utils.json_fix_llm import fix_json_using_multiple_techniques
from miniboss.json_utils.utilities import LLM_DEFAULT_RESPONSE_FORMAT, validate_json
from miniboss.llm import chat_with_ai, create_chat_completion, create_chat_message
from miniboss.llm.token_counter import count_string_tokens
from miniboss.logs import logger, print_assistant_thoughts
from miniboss.prompts.prompt import (
    DEFAULT_BUDDY_TRIGGERING_PROMPT,
    construct_main_buddy_config,
    create_main_buddy_config,
)

CFG = Config()
# from miniboss import say_text
from miniboss.spinner import Spinner
from miniboss.utils import clean_input, send_chat_message_to_user
from miniboss.workspace import Jobspace

cfg = Config()
import ast
import os
import re


class Boss:
    """Boss class for interacting with Mini-Boss.

    Attributes:
        ai_name: The name of the boss.
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
        workspace_directory,
        max_workers,
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
        self.workspace = Jobspace(workspace_directory, cfg.restrict_to_workspace)
        self.max_workers = max_workers

    def evaluate_worker_performance(self, feedback: str) -> float:
        if "perfect" in feedback.lower():
            return 1.0
        elif "effective" in feedback.lower():
            return 0.95
        elif "great" in feedback.lower():
            return 0.90
        elif "successfully" in feedback.lower():
            return 0.90
        elif "successful" in feedback.lower():
            return 0.90
        elif "good" in feedback.lower():
            return 0.80
        elif "average" in feedback.lower():
            return 0.70
        elif "poor" in feedback.lower():
            return 0.60
        else:
            return 0.20

    def set_results_for_tasks(self):
        if len(self.config.ai_task_results) == 0:
            for i, task in enumerate(self.config.ai_tasks):
                self.config.ai_task_results.append(
                    {
                        "task": task,
                        "results": [],
                        "worker_count": 0,
                        "status": "",
                        "score": 0,
                    }
                )

        self.config.save(CFG.boss_settings_file)

    def start_interaction_loop(self):
        # Interaction Loop
        cfg = Config()
        loop_count = 0
        command_name = None
        arguments = None
        user_input = ""
        buddy_workspace_directory = None
        assistant_reply_json = {}
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

            send_chat_message_to_user("Thinking... \n")
            # logger.typewriter_log(
            #     "Thinking... ", Fore.YELLOW, ""
            # )

            for i, task in enumerate(self.config.ai_tasks):
                # todo: we need to check the existing tasks here so when we start
                buddy_name = "Buddy-{}".format(i)
                BUDDY_JOB_COMPLETE = False

                if len(self.config.ai_task_results):
                    if self.config.ai_task_results[i]["status"] == "complete":
                        complete_precent = (i + 1) / len(self.config.ai_tasks)
                        self.config.complete_percentage = complete_precent
                        self.config.save(CFG.boss_settings_file)
                        # todo: add the check here to put the results in the file
                        if len(self.config.ai_task_results[i]["results"]) == 0:
                            file_name, text = self.parse_auto_gpt_logs()
                            # print("FILE NAME: ", file_name)
                            # print("TEXT: ", text)
                            self.config.ai_task_results[i]["results"].append(
                                {"file_name": file_name, "text": text}
                            )
                            self.config.save(CFG.boss_settings_file)
                        continue
                    elif self.config.ai_task_results[i]["status"] == "started":
                        buddy_config = construct_main_buddy_config(
                            task, self.config.target_percentage, buddy_name
                        )
                    else:
                        buddy_config = create_main_buddy_config(
                            task, self.config.target_percentage, buddy_name
                        )

                assistant_reply_json = {}
                buddy_config.command_registry = self.command_registry
                buddy_message_history = []
                buddy_action_count = 0

                while not BUDDY_JOB_COMPLETE:
                    if buddy_workspace_directory is None:
                        workspace_name = "miniboss_workspace/buddy-{}-workspace".format(
                            i
                        )
                        buddy_workspace_directory = (
                            Path(__file__).parent.parent.parent / workspace_name
                        )
                    else:
                        buddy_workspace_directory = Path(buddy_workspace_directory)
                    workspace_directory = Jobspace.make_workspace(
                        buddy_workspace_directory
                    )

                    current_job = task

                    if i != 0:
                        previous_results = self.config.ai_task_results[i - 1]
                        updated_results = json.dumps(previous_results)
                        print("UPDATED RESULTS: ", updated_results)
                        prep_results = (
                            updated_results.replace("{", "")
                            .replace("}", "")
                            .replace("[", "")
                            .replace("]", "")
                            .replace("\\", "")
                        )
                        previous_job = (
                            f"Please consider the previous job: {prep_results} "
                        )
                        current_job = (
                            f"{previous_job} while completing your new job: {task}"
                        )

                    buddy = Buddy(
                        ai_name=buddy_name,
                        memory=self.memory,
                        full_message_history=buddy_message_history,
                        next_action_count=buddy_action_count,
                        command_registry=self.command_registry,
                        config=buddy_config,
                        system_prompt=buddy_config.construct_full_prompt(),
                        triggering_prompt=DEFAULT_BUDDY_TRIGGERING_PROMPT,
                        current_job=current_job,
                        workspace_directory=workspace_directory,
                    )
                    # print(self.config.ai_task_results[i]["worker_count"])
                    self.config.ai_task_results[i]["worker_count"] += 1
                    self.config.ai_task_results[i]["status"] = "started"
                    # print(self.config.ai_task_results[i]["worker_count"])
                    self.config.save(CFG.boss_settings_file)
                    buddy.start_interaction_loop()

                    # print(buddy.final_result)
                    # Extract relevant information from final_result
                    # command = buddy.final_result['command']
                    task = buddy.final_result["task"]
                    feedback = buddy.final_result["feedback"]
                    arguments = buddy.final_result["arguments"]
                    # Create a new dictionary with all values from final_result
                    new_final_result = buddy.final_result.copy()
                    # Display the summary

                    # Use the evaluation function to grade the worker's performance
                    performance_grade = self.evaluate_worker_performance(feedback)

                    # Display the performance grade
                    # print(f"{buddy_name} Performance Grade: {performance_grade}")
                    # Add performance_grade to the new dictionary
                    new_final_result["performance_grade"] = performance_grade
                    # print("self.config.target_percentage", self.config.target_percentage)
                    # if performance_grade >= self.config.target_percentage:
                    #     logger.typewriter_log(f"\n{buddy_name} : SUCCESS ", Fore.GREEN,
                    #                           f"GRADE = {performance_grade} "
                    #                           f"TARGET = {self.config.target_percentage}\n")
                    #     BUDDY_JOB_COMPLETE = True
                    #     self.config.ai_task_results.append(new_final_result)
                    self.config.ai_task_results[i]["score"] = performance_grade
                    complete_precent = (i + 1) / len(self.config.ai_tasks)
                    self.config.complete_percentage = complete_precent
                    # print(self.config.ai_task_results[i]["score"])
                    file_name, text = self.parse_auto_gpt_logs()
                    self.config.ai_task_results[i]["results"].append(
                        {"file_name": file_name, "text": text}
                    )
                    self.config.save(CFG.boss_settings_file)
                    if performance_grade >= self.config.target_percentage:
                        logger.typewriter_log(
                            f"\n{buddy_name}",
                            Fore.GREEN,
                            f"GRADE = {performance_grade} "
                            f"TARGET = {self.config.target_percentage}\n",
                        )
                        self.config.ai_task_results[i]["status"] = "completed"
                        # print(self.config.ai_task_results[i]["status"])
                        self.config.save(CFG.boss_settings_file)

                        assistant_reply_json = {
                            "thoughts": {
                                "text": f"Task {i} : {task} has been completed by {buddy_name}.",
                                "reasoning": f"The worker completed the assigned task : {task} : with a performance grade of {performance_grade}.",
                                "plan": f"- We need to complete our remaining tasks.",
                                "criticism": f"We need to complete our remaining tasks in a timely manner",
                                "speak": f"I will report that Task {i} : {task} has been completed by {buddy_name}.",
                            },
                            "command": {
                                "name": "task_complete",
                                "args": {
                                    "reason": f"The worker completed the assigned task : {task} : with a performance grade of {performance_grade}."
                                },
                            },
                        }
                        thoughts = assistant_reply_json.get("thoughts", {})
                        print(assistant_reply_json)
                        self_feedback_resp = self.get_self_feedback_on_buddy(
                            thoughts, cfg.fast_llm_model
                        )
                        # logger.typewriter_log(
                        #     f"BUDDY FEEDBACK: {self_feedback_resp}",
                        #     Fore.GREEN,
                        #     "",
                        # )
                        display_feedback = self_feedback_resp.replace(
                            "Y ",
                            "",
                        )
                        markdown_text = f"``` {display_feedback}```"
                        logger.log_markdown(markdown_text)
                        if self_feedback_resp[0].lower().strip() == cfg.authorise_key:
                            user_input = "GENERATE NEXT COMMAND JSON"
                        else:
                            user_input = self_feedback_resp
                    else:
                        logger.typewriter_log(
                            f"\n{buddy_name} : FAILED ",
                            Fore.RED,
                            f"GRADE = {performance_grade} "
                            f"TARGET = {self.config.target_percentage}\n",
                        )
                        self.config.ai_task_results[i]["status"] = "failed"
                        # print(self.config.ai_task_results[i]["status"])
                        self.config.save(CFG.boss_settings_file)
                        assistant_reply_json = {
                            "thoughts": {
                                "text": f"Task {i} : {task} has failed to be completed by {buddy_name}.",
                                "reasoning": f"The worker failed to complete the assigned task : {task} : with a performance grade of {performance_grade}.",
                                "plan": f"- We need to launch a new worker to complete this task before proceeding to the next task.",
                                "criticism": f"Because the worker failed to meet the performance grade of {self.config.target_percentage} we need to launch a new worker to complete this task before proceeding to the next task.",
                                "speak": f"Task {i} : {task} has failed to be completed by {buddy_name}.",
                            },
                            "command": {
                                "name": "task_failed",
                                "args": {
                                    "reason": f"The worker failed to complete the assigned task : {task} : with a performance grade of {performance_grade}."
                                },
                            },
                        }
                        thoughts = assistant_reply_json.get("thoughts", {})
                        # print(assistant_reply_json)

                        # todo expand this to evaluate the respons and then return the grade who it is needed
                        self_feedback_resp = self.get_self_feedback_on_buddy(
                            thoughts, cfg.fast_llm_model
                        )
                        # logger.typewriter_log(
                        #     f"BUDDY FEEDBACK: {self_feedback_resp}",
                        #     Fore.RED,
                        #     "",
                        # )
                        display_feedback = self_feedback_resp.replace(
                            "Y ",
                            "",
                        )
                        markdown_text = f"``` {display_feedback}```"
                        logger.log_markdown(markdown_text)
                        if self_feedback_resp[0].lower().strip() == cfg.authorise_key:
                            user_input = "GENERATE NEXT COMMAND JSON"
                        else:
                            user_input = self_feedback_resp

                        BUDDY_JOB_COMPLETE = True

            if assistant_reply_json != {}:
                validate_json(assistant_reply_json, LLM_DEFAULT_RESPONSE_FORMAT)
                # Get command name and arguments
                try:
                    print_assistant_thoughts(
                        self.ai_name, assistant_reply_json, cfg.speak_mode
                    )

                    command_name, arguments = get_boss_command(assistant_reply_json)
                    # if cfg.speak_mode:
                    #     say_text(f"I want to execute {command_name}")

                    send_chat_message_to_user("Thinking... \n")
                    arguments = self._resolve_pathlike_command_args(arguments)

                except Exception as e:
                    logger.error("Error: \n", str(e))

            # MiniBoss is complete
            if self.config.complete_percentage == 1.0:
                markdown_text = f"# 🚀 MiniBoss is complete 🚀"
                logger.log_markdown(markdown_text)
                last_task = len(self.config.ai_tasks) - 1
                final_results = self.config.ai_task_results[last_task]["results"][0]
                file_name = final_results["file_name"]
                text = final_results["text"]
                markdown_text = f"``` Location of Results : {file_name}```"
                logger.log_markdown(markdown_text)
                markdown_text = f"```{text}```"
                logger.log_markdown(markdown_text)
                exit()

            # todo: code below may never be used
            print("CHECK CODE BELOW IN boss.py")
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
                    "Enter 'y' to authorise command, 'y -N' to run N continuous commands, 's' to run self-feedback commands"
                    "'n' to exit program, or enter feedback for "
                    f"{self.ai_name}...",
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
                command_result = execute_boss_command(
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

    def parse_auto_gpt_logs(self):
        # Define the log file path
        target_directory = f"{os.getcwd()}/auto-gpt"
        log_file_path = os.path.join(target_directory, "logs/activity.log")
        # Read the log file in reverse
        with open(log_file_path, "r", encoding="utf-8") as log_file:
            lines = log_file.readlines()
            lines.reverse()
        # Define a regular expression pattern to match the "task_complete" command and its arguments
        pattern = r"COMMAND = write_to_file\s+ARGUMENTS = ({.*})"
        # Search for the pattern in the reversed log content
        text = ""
        file_name = ""
        for line in lines:
            match = re.search(pattern, line)
            if match:
                arguments_str = match.group(1)
                # Parse the string to a Python dictionary
                arguments = ast.literal_eval(arguments_str)
                # Access the 'reason' value
                file_name = arguments["filename"]
                text = arguments["text"]
                # Print the 'reason' value
                print(f"Task complete File: {file_name}")
                print(f"Task complete Text: {text}")
                return file_name, text
        else:
            print("Task complete command not found in the log file.")
            return file_name, text

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
        ai_role = self.config.ai_role

        feedback_prompt = f"Below is a message from an AI boss with the role of {ai_role}. Please review the provided Thought, Reasoning, Plan, and Criticism. If these elements accurately contribute to the successful execution of the assumed role, respond with the letter 'Y' followed by a space, and then explain why it is effective. If the provided information is not suitable for achieving the role's objectives, please provide one or more sentences addressing the issue and suggesting a resolution."
        reasoning = thoughts.get("reasoning", "")
        plan = thoughts.get("plan", "")
        thought = thoughts.get("thoughts", "")
        criticism = thoughts.get("criticism", "")
        feedback_thoughts = thought + reasoning + plan + criticism
        return create_chat_completion(
            [{"role": "user", "content": feedback_prompt + feedback_thoughts}],
            llm_model,
        )

    def get_self_feedback_on_buddy(self, thoughts: dict, llm_model: str) -> str:
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
        ai_role = self.config.ai_role

        # todo: this needs to have a better input example
        # todo: and then I can ensure I have all the pieces
        system_prompt = """
        Your task was to act as the Project Manager and develop a working plan of up to few steps and an appropriate
role-based name (_GPT) for an autonomous worker agent, ensuring that the goals are optimally aligned with the
successful completion of its assigned task. You then gave each goal to a work or autonomous agent to perform the work in order to achieve
the desired plan. The workers were not aware of the original plan, only the work they need to perform.
The user is going to provide you with the response from the worker, and you will provide only the output in the exact format specified below in example output with no explanation or conversation.

Example input:
{'thoughts': {'text': 'Task 0 : Research Assistant: Find a reliable weather API that provides weather information for Blue Ridge, GA and obtain an API key. Provide the API key to the Webpage Developer. has been completed by Buddy-0.', 'reasoning': 'The worker completed the assigned task : Research Assistant: Find a reliable weather API that provides weather information for Blue Ridge, GA and obtain an API key. Provide the API key to the Webpage Developer. : with a performance grade of 0.95.', 'plan': '- We need to complete our remaining tasks.', 'criticism': 'We need to complete our remaining tasks in a timely manner', 'speak': 'I will report that Task 0 : Research Assistant: Find a reliable weather API that provides weather information for Blue Ridge, GA and obtain an API key. Provide the API key to the Webpage Developer. has been completed by Buddy-0.'}, 'command': {'name': 'task_complete', 'args': {'reason': 'The worker completed the assigned task : Research Assistant: Find a reliable weather API that provides weather information for Blue Ridge, GA and obtain an API key. Provide the API key to the Webpage Developer. : with a performance grade of 0.95.'}}}

Example output:
Name: Buddy-0 - Research Assistant - Assessment
Job: Find a reliable weather API that provides weather information for Blue Ridge, GA and obtain an API key. Provide the API key to the Webpage Developer
Feedback:
Grade: 0.95
"""
        feedback_prompt = f"Below is a message from an AI boss with the role of {ai_role}. Please review the provided Thought, Reasoning, Plan, and Criticism. If these elements accurately contribute to the successful execution of the assumed role, respond with the letter 'Y' followed by a space, and then explain why it is effective. If the provided information is not suitable for achieving the role's objectives, please provide one or more sentences addressing the issue and suggesting a resolution."
        reasoning = thoughts.get("reasoning", "")
        plan = thoughts.get("plan", "")
        thought = thoughts.get("thoughts", "")
        criticism = thoughts.get("criticism", "")
        feedback_thoughts = thought + reasoning + plan + criticism
        # print("feedback_thoughts", feedback_thoughts)
        return create_chat_completion(
            [
                {"role": "system", "content": feedback_prompt + feedback_thoughts},
                {"role": "user", "content": feedback_prompt + feedback_thoughts},
            ],
            llm_model,
        )
