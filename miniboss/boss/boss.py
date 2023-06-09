import json
from pathlib import Path

from colorama import Fore, Style

from miniboss.agent.buddy import Buddy
from miniboss.app import execute_command, get_command
from miniboss.config.config import Config
from miniboss.json_utils.utilities import LLM_DEFAULT_RESPONSE_FORMAT, validate_json
from miniboss.llm import create_chat_completion, create_chat_message
from miniboss.logs import logger
from miniboss.prompts.prompt import (
    DEFAULT_BUDDY_TRIGGERING_PROMPT,
    construct_main_buddy_config,
    create_main_buddy_config,
)

CFG = Config()
# from miniboss import say_text
# from miniboss.spinner import Spinner
from miniboss.utils import clean_input, send_chat_message_to_user
from miniboss.workspace import Jobspace

cfg = Config()
import ast
import os
import re

from transformers import pipeline


class Boss:
    """Boss class for interacting with Mini-Boss.

    Attributes:
        ai_name (str): The name of the boss.
        memory (object): The memory object to use.
        full_message_history (list): The full message history.
        next_action_count (int): The number of actions to execute.
        command_registry (object): The command registry object.
        config (object): The configuration object.
        system_prompt (str): The system prompt is the initial prompt that defines everything
            the AI needs to know to achieve its task successfully.
            Currently, the dynamic and customizable information in the system prompt are
            ai_name, description, and goals.
        triggering_prompt (str): The last sentence the AI will see before answering.
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
        workspace (object): The workspace object.
        max_workers (int): The maximum number of workers.

    Methods:
        start_interaction_loop(): Starts the interaction loop.
        evaluate_worker_performance(feedback): Evaluates the worker's performance based on the feedback.
        set_results_for_tasks(): Sets the results for the tasks.
        _resolve_pathlike_command_args(command_args): Resolves path-like command arguments.
        parse_auto_gpt_logs(): Parses the auto-gpt logs.
        get_self_feedback(thoughts, llm_model): Generates self-feedback based on the thoughts.
        get_self_feedback_on_buddy(thoughts, llm_model, results): Generates self-feedback on the agent based on the thoughts and results.
        log_and_save_results(logger, buddy_name, status, markdown_text, config, i, performance_grade, target_percentage, CFG): Logs and saves the results.
        build_assistant_reply(status, i, task, buddy_name, performance_grade, target_percentage): Builds the assistant's reply based on the status and other parameters.
        handle_command_error(command_name, arguments): Handles the command error.
        handle_human_feedback(user_input): Handles the human feedback.
        execute_command(command_name, arguments, cfg, command_registry, config, prompt_generator): Executes the command.
        handle_command_execution(command_name, arguments, user_input, cfg, command_registry, config, prompt_generator): Handles the command execution.
        print_next_action(command_name, arguments): Prints the next action.
        handle_console_input(console_input, assistant_reply_json, cfg): Handles the console input.

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
        """Initialize the Boss class for interacting with Mini-Boss.

        Args:
            ai_name (str): The name of the boss.
            memory (object): The memory object to use.
            full_message_history (list): The full message history.
            next_action_count (int): The number of actions to execute.
            command_registry (object): The command registry object.
            config (object): The configuration object.
            system_prompt (str): The system prompt is the initial prompt that defines everything
                the AI needs to know to achieve its task successfully.
                Currently, the dynamic and customizable information in the system prompt are
                ai_name, description, and goals.
            triggering_prompt (str): The last sentence the AI will see before answering.
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
            workspace_directory (str): The directory path for the workspace.
            max_workers (int): The maximum number of workers.
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
        self.workspace = Jobspace(workspace_directory, cfg.restrict_to_workspace)
        self.max_workers = max_workers

    def start_interaction_loop(self):
        """Start the interaction loop for the Boss class.

        This method initiates the interaction loop where the Boss communicates with Mini-Boss.
        It performs tasks such as thinking, processing commands, evaluating performance, and
        generating the next command.

        Note:
            This method assumes that the necessary configurations and parameters are already set
            in the Boss instance.

        Returns:
            None
        """

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

            # for i, task in enumerate(self.config.ai_tasks, start=1):
            for i, task in enumerate(self.config.ai_tasks):
                buddy_name = "Buddy-{}".format(i)
                BUDDY_JOB_COMPLETE = False

                if len(self.config.ai_task_results):
                    if self.config.ai_task_results[i]["status"] == "complete":
                        complete_precent = (i + 1) / len(self.config.ai_tasks)
                        self.config.complete_percentage = complete_precent
                        self.config.save(CFG.boss_settings_file)
                        if len(self.config.ai_task_results[i]["results"]) == 0:
                            file_name, text = self.parse_auto_gpt_logs()
                            # print("FILE NAME: ", file_name)
                            # print("TEXT: ", text)
                            self.config.ai_task_results[i]["results"] = []
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
                        workspace_name = "miniboss_workspace/agent-{}-workspace".format(
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
                        # print("UPDATED RESULTS: ", updated_results)
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

                    # Extract relevant information from final_result
                    task = buddy.final_result["task"]
                    feedback = buddy.final_result["feedback"]
                    arguments = buddy.final_result["arguments"]
                    # Create a new dictionary with all values from final_result
                    new_final_result = buddy.final_result.copy()
                    # Use the evaluation function to grade the worker's performance
                    # todo: this is invalid - because a worker can fail
                    performance_grade = self.evaluate_worker_performance_hf(feedback)
                    new_final_result["performance_grade"] = performance_grade
                    self.config.ai_task_results[i]["score"] = performance_grade
                    complete_precent = (i + 1) / len(self.config.ai_tasks)
                    self.config.complete_percentage = complete_precent

                    file_name, text = self.parse_auto_gpt_logs()
                    self.config.ai_task_results[i]["results"] = []
                    self.config.ai_task_results[i]["results"].append(
                        {"file_name": file_name, "text": text}
                    )
                    self.config.ai_task_results[i]["status"] = "complete"
                    self.config.save(CFG.boss_settings_file)

                    # In your main function/method:
                    markdown_text = f"# 🚀 {buddy_name} : "
                    if performance_grade >= self.config.target_percentage:
                        markdown_text += f"Success : {performance_grade}/ {self.config.target_percentage} 🚀"
                        status = "complete"
                        complete_precent = (i + 1) / len(self.config.ai_tasks)
                        self.config.complete_percentage = complete_precent
                    else:
                        markdown_text += f"Failed : {performance_grade}/ {self.config.target_percentage} 🚀"
                        status = "fail"

                    self.log_and_save_results(
                        logger,
                        buddy_name,
                        status,
                        markdown_text,
                        self.config,
                        i,
                        performance_grade,
                        self.config.target_percentage,
                        CFG,
                    )
                    assistant_reply_json = self.build_assistant_reply(
                        status,
                        i,
                        task,
                        buddy_name,
                        performance_grade,
                        self.config.target_percentage,
                    )
                    BUDDY_JOB_COMPLETE = True

            if assistant_reply_json != {}:
                validate_json(assistant_reply_json, LLM_DEFAULT_RESPONSE_FORMAT)
                # Get command name and arguments
                try:
                    # print_assistant_thoughts(
                    #     self.ai_name, assistant_reply_json, cfg.speak_mode
                    # )
                    thoughts = assistant_reply_json.get("thoughts", {})
                    # print(assistant_reply_json)
                    self_feedback_resp = self.get_self_feedback_on_buddy(
                        thoughts,
                        cfg.fast_llm_model,
                        self.config.ai_task_results[i]["results"][0],
                    )

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

                    command_name, arguments = get_command(assistant_reply_json)
                    # if cfg.speak_mode:
                    #     say_text(f"I want to execute {command_name}")
                    # print(f"Command Name : {command_name}")
                    # print(f"Arguments : {arguments}")

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
                command_name = "boss_complete"
                arguments = {
                    "reason": f"MiniBoss has completed its job to - {self.config.ai_job} - by - {self.config.ai_role}"
                }

            # In your main function/method:
            if not cfg.continuous_mode and self.next_action_count == 0:
                print("if not cfg.continuous_mode and self.next_action_count == 0")
                self.user_input = ""
                self.print_next_action(command_name, arguments)
                print(
                    "Enter 'y' to authorise command, 'y -N' to run N continuous commands, 's' to run self-feedback commands"
                    "'n' to exit program, or enter feedback for "
                    f"{self.ai_name}...",
                    flush=True,
                )
                while True:
                    console_input = (
                        clean_input(Fore.MAGENTA + "Input:" + Style.RESET_ALL)
                        if not cfg.chat_messages_enabled
                        else clean_input("Waiting for your response...")
                    )
                    user_input = self.handle_console_input(
                        console_input, assistant_reply_json, cfg
                    )
                    if user_input in ["GENERATE NEXT COMMAND JSON", "EXIT"]:
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
            else:
                self.print_next_action(command_name, arguments)

            # In your main function/method:
            result = self.handle_command_execution(
                command_name,
                arguments,
                user_input,
                cfg,
                self.command_registry,
                self.config,
                self.config.prompt_generator,
            )

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

    def evaluate_worker_performance(self, feedback: str) -> float:
        """Evaluate the performance of a worker based on the provided feedback.

        This method calculates a performance score for a worker based on the feedback received.
        The score is normalized to a scale of 0-1, with 1 being the highest performance.

        Args:
            feedback (str): The feedback received for the worker's performance.

        Returns:
            float: The performance score, normalized to a scale of 0-1.
        """
        score_search = re.search(r"\b\d{1,2}\b", feedback)
        if score_search:
            score = float(score_search.group())
            # normalize to a scale of 0-1
            return score / 10
        else:
            # if no score was found in the feedback, handle accordingly
            return 0.20

    def evaluate_worker_performance_hf(self, feedback: str) -> float:
        """Evaluate the performance of a worker based on the provided feedback using the Hugging Face sentiment analysis model.

        This method calculates a performance score for a worker based on the sentiment analysis of the feedback received.
        The score is normalized to a scale of 0-1, with 1 being the highest performance.

        Args:
            feedback (str): The feedback received for the worker's performance.

        Returns:
            float: The performance score, normalized to a scale of 0-1.
        """
        hf_analysis = pipeline("sentiment-analysis")(feedback)

        if len(hf_analysis) > 0:
            return hf_analysis[0]["score"]
        else:
            # If no score was found in the feedback, handle accordingly
            return self.evaluate_worker_performance(feedback)

    def set_results_for_tasks(self):
        """Set the initial results structure for each task.

        This method initializes the results structure for each task in the `ai_task_results` list.
        If the `ai_task_results` list is empty, it creates a results dictionary for each task
        and appends it to the list. The initial values for `worker_count`, `status`, and `score`
        are set to 0.

        Note:
            This method assumes that the necessary configurations are already set in the Boss instance.

        Returns:
            None
        """
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

    def _resolve_pathlike_command_args(self, command_args):
        """Resolve path-like command arguments.

        This method resolves path-like command arguments by converting them to absolute paths.
        It checks for specific keys in the `command_args` dictionary, such as 'filename', 'directory',
        and 'clone_path', and converts their values to absolute paths using the workspace's `get_path` method.

        Args:
            command_args (dict): The command arguments dictionary.

        Returns:
            dict: The modified command arguments dictionary with resolved path-like values.
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

    def parse_auto_gpt_logs(self):
        """Parse the auto-gpt logs to extract task complete information.

        This method reads the auto-gpt log file in reverse and searches for the "task_complete"
        command and its arguments. It returns the file name and text obtained from the command.

        Returns:
            tuple: A tuple containing the file name and text obtained from the task complete command.
                   If the task complete command is not found, empty strings are returned.
        """
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
                return file_name, text
        else:
            print("Task complete command not found in the log file.")
            return file_name, text

    def get_self_feedback(self, thoughts: dict, llm_model: str) -> str:
        """Generate feedback based on thoughts dictionary.

        This method takes in a dictionary of thoughts containing keys such as 'reasoning',
        'plan', 'thoughts', and 'criticism'. It combines these elements into a single
        feedback message and uses the `create_chat_completion()` function to generate a
        response based on the input message.

        Args:
            thoughts (dict): A dictionary containing thought elements like reasoning,
                plan, thoughts, and criticism.
            llm_model (str): The language model used to generate the feedback.

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

    def get_self_feedback_on_buddy(
        self, thoughts: dict, llm_model: str, results: object
    ) -> str:
        """Generate feedback on worker's performance.

        This method generates feedback on the worker's performance based on the provided
        thoughts dictionary, the language model used, and the results obtained from the worker.
        It combines elements such as 'reasoning', 'plan', 'thoughts', 'criticism', 'text',
        and 'file_name' into a single feedback message and uses the `create_chat_completion()`
        function to generate a response based on the input message.

        Args:
            thoughts (dict): A dictionary containing thought elements like reasoning,
                plan, thoughts, and criticism.
            llm_model (str): The language model used to generate the feedback.
            results (object): The results obtained from the worker.

        Returns:
            str: A feedback response generated using the provided thoughts dictionary,
                worker's results, and the language model.
        """
        ai_role = self.config.ai_role
        system_prompt = """
        Your task was to act as the Project Manager and develop a working plan of up to few steps and an appropriate
role-based name (_GPT) for an autonomous worker agent, ensuring that the goals are optimally aligned with the
successful completion of its assigned task. You then gave each goal to a work or autonomous agent to perform the work in order to achieve
the desired plan. The workers were not aware of the original plan, only the work they need to perform.
The user is going to provide you with the response from the worker, and you will provide only the output in the exact format specified below in the output description with no explanation or conversation.
"""

        feedback_prompt = f"""As a supervisor AI with the role of {ai_role}, please provide a detailed review of the worker's performance.
Consider the worker's Thought, Reasoning, Plan, and Criticism in your analysis.
Rate the performance on a scale of 1-10, with 1 being 'extremely ineffective' and 10 being 'extremely effective'.
Please also provide a detailed explanation for your rating and, if applicable, suggestions for improvement. If the worker failed to complete the task, please provide an explanation of why the worker failed to complete the task."""

        reasoning = thoughts.get("reasoning", "")
        plan = thoughts.get("plan", "")
        thought = thoughts.get("thoughts", "")
        criticism = thoughts.get("criticism", "")
        feedback_thoughts = (
            thought
            + reasoning
            + " "
            + results["text"]
            + " "
            + results["file_name"]
            + plan
            + criticism
        )
        # print("feedback_thoughts", feedback_thoughts)
        return create_chat_completion(
            [
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": feedback_prompt},
                {"role": "user", "content": feedback_thoughts},
            ],
            llm_model,
        )

    def log_and_save_results(
        self,
        logger,
        buddy_name,
        status,
        markdown_text,
        config,
        i,
        performance_grade,
        target_percentage,
        CFG,
    ):
        """Log and save the results of a task.

        This method logs the provided `markdown_text`, updates the status of the task in the
        `ai_task_results` configuration, and saves the configuration to a file. It also logs the
        agent's name, the status in uppercase, the performance grade, and the target percentage.

        Args:
            logger: The logger instance used for logging.
            buddy_name (str): The name of the agent.
            status (str): The status of the task ('complete' or 'failed').
            markdown_text (str): The markdown text to be logged.
            config: The configuration instance.
            i (int): The index of the task.
            performance_grade (float): The performance grade of the agent.
            target_percentage (float): The target percentage for the task.
            CFG: The configuration constant.

        Returns:
            None
        """
        logger.log_markdown(markdown_text)
        config.ai_task_results[i]["status"] = status
        config.save(CFG.boss_settings_file)
        logger.typewriter_log(
            f"\n{buddy_name} : {status.upper()} ",
            Fore.GREEN if status == "complete" else Fore.RED,
            f"GRADE = {performance_grade} " f"TARGET = {target_percentage}\n",
        )

    def build_assistant_reply(
        self, status, i, task, buddy_name, performance_grade, target_percentage
    ):
        """Build the assistant's reply based on task completion status.

        This method builds the assistant's reply based on the provided status, task details,
        agent's name, performance grade, and target percentage. It constructs the 'thoughts'
        and 'command' sections of the assistant's reply JSON.

        Args:
            status (str): The status of the task ('complete' or 'failed').
            i (int): The index of the task.
            task (str): The task description.
            buddy_name (str): The name of the agent.
            performance_grade (float): The performance grade of the agent.
            target_percentage (float): The target percentage for the task.

        Returns:
            dict: The assistant's reply JSON containing the 'thoughts' and 'command' sections.
        """
        base_text = f"Task {i} {task} has "
        base_reason = f"The worker "
        if status == "complete":
            base_text += f"been completed by {buddy_name}."
            base_reason += f"completed the assigned task {task} with a performance grade of {performance_grade}."
            plan = "- We need to complete our remaining tasks."
            criticism = "We need to complete our remaining tasks in a timely manner"
            command_name = "task_complete"
        else:
            base_text += f"failed to be completed by {buddy_name}."
            base_reason += f"failed to complete the assigned task {task} with a performance grade of {performance_grade}."
            plan = "- We need to launch a new worker to complete this task before proceeding to the next task."
            criticism = f"Because the worker failed to meet the performance grade of {target_percentage} we need to launch a new worker to complete this task before proceeding to the next task."
            command_name = "task_failed"

        return {
            "thoughts": {
                "text": base_text,
                "reasoning": base_reason,
                "plan": plan,
                "criticism": criticism,
                "speak": base_text,
            },
            "command": {
                "name": command_name,
                "args": {
                    "reason": base_reason,
                },
            },
        }

    def handle_command_error(self, command_name, arguments):
        """Handle an error thrown by a command.

        This method is called when a command throws an error. It returns a formatted error message
        containing the name of the command and the error arguments.

        Args:
            command_name (str): The name of the command that threw the error.
            arguments (str): The error arguments.

        Returns:
            str: The formatted error message.
        """
        return f"Command {command_name} threw the following error: {arguments}"

    def handle_human_feedback(self, user_input):
        """Handle human feedback.

        This method is called when the user provides feedback. It returns a formatted message
        containing the user's feedback.

        Args:
            user_input (str): The user's feedback.

        Returns:
            str: The formatted message containing the user's feedback.
        """
        return f"Human feedback: {user_input}"

    def execute_command(
        self, command_name, arguments, cfg, command_registry, config, prompt_generator
    ):
        """Execute a command.

        This method executes a command by calling the `execute_command` function with the
        provided command name, arguments, command registry, configuration, and prompt generator.
        It also calls the pre and post command methods of the registered plugins, if applicable.

        Args:
            command_name (str): The name of the command to execute.
            arguments (dict): The arguments of the command.
            cfg: The configuration constant.
            command_registry: The command registry instance.
            config: The configuration instance.
            prompt_generator: The prompt generator instance.

        Returns:
            str: The result of the command execution.
        """
        for plugin in cfg.plugins:
            if not plugin.can_handle_pre_command():
                continue
            command_name, arguments = plugin.pre_command(command_name, arguments)

        command_result = execute_command(
            command_registry,
            command_name,
            arguments,
            config.prompt_generator,
        )
        result = f"Command {command_name} returned: " f"{command_result}"

        for plugin in cfg.plugins:
            if not plugin.can_handle_post_command():
                continue
            result = plugin.post_command(command_name, result)
        return result

    def handle_command_execution(
        self,
        command_name,
        arguments,
        user_input,
        cfg,
        command_registry,
        config,
        prompt_generator,
    ):
        """Handle the execution of a command.

        This method handles the execution of a command based on the provided command name, arguments,
        user input, configuration, command registry, and prompt generator. It calls the appropriate
        methods based on the command name to handle errors, human feedback, or execute a command.
        It also checks if the `next_action_count` in the configuration is greater than 0 and decrements
        it if applicable.

        Args:
            command_name (str): The name of the command to execute.
            arguments (dict): The arguments of the command.
            user_input (str): The user's input.
            cfg: The configuration constant.
            command_registry: The command registry instance.
            config: The configuration instance.
            prompt_generator: The prompt generator instance.

        Returns:
            str: The result of the command execution.
        """
        if command_name is not None and command_name.lower().startswith("error"):
            result = self.handle_command_error(command_name, arguments)
        elif command_name == "human_feedback":
            result = self.handle_human_feedback(user_input)
        else:
            result = self.execute_command(
                command_name, arguments, cfg, command_registry, config, prompt_generator
            )
            if cfg.next_action_count > 0:
                cfg.next_action_count -= 1
        return result

    def print_next_action(self, command_name, arguments):
        """Print the next action to be performed.

        This method prints the next action to be performed, which includes the command name and arguments.
        It sends a chat message to the user and logs the next action using the logger.

        Args:
            command_name (str): The name of the next command.
            arguments (dict): The arguments of the next command.

        Returns:
            None
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

    def handle_console_input(self, console_input, assistant_reply_json, cfg):
        """Handle input from the console.

        This method handles the input from the console based on the provided console input,
        assistant reply JSON, and configuration. It checks for specific console inputs such as
        authorization key, self-feedback request, empty input, next action count modification,
        exit key, or other user input. It performs the corresponding actions based on the console
        input and returns the appropriate response.

        Args:
            console_input (str): The input from the console.
            assistant_reply_json (dict): The JSON response from the assistant.
            cfg: The configuration constant.

        Returns:
            str: The response based on the console input.
        """
        if console_input.lower().strip() == cfg.authorise_key:
            return "GENERATE NEXT COMMAND JSON"
        elif console_input.lower().strip() == "s":
            logger.typewriter_log(
                "-=-=-=-=-=-=-= THOUGHTS, REASONING, PLAN AND CRITICISM WILL NOW BE VERIFIED BY AGENT -=-=-=-=-=-=-=",
                Fore.GREEN,
                "",
            )
            thoughts = assistant_reply_json.get("thoughts", {})
            self_feedback_resp = self.get_self_feedback(thoughts, cfg.fast_llm_model)
            logger.typewriter_log(
                f"SELF FEEDBACK: {self_feedback_resp}",
                Fore.YELLOW,
                "",
            )
            return self_feedback_resp
        elif console_input.lower().strip() == "":
            print("Invalid input format.")
        elif console_input.lower().startswith(f"{cfg.authorise_key} -"):
            try:
                self.next_action_count = abs(int(console_input.split(" ")[1]))
                return "GENERATE NEXT COMMAND JSON"
            except ValueError:
                print(
                    f"Invalid input format. Please enter '{cfg.authorise_key} -N' where N is"
                    " the number of continuous tasks."
                )
        elif console_input.lower() == cfg.exit_key:
            return "EXIT"
        else:
            return console_input
