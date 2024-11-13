import serial

from model.model import Model
from model.view import View
from vision.vision import Vision
from chatbot.chatbot import Chatbot


class Controller:
    def __init__(self, json_file_path):
        self.model = Model(json_file_path)
        self.view = View()
        self.vision = Vision()
        self.current_task_id = None
        self.current_block_id = None
        self.current_command = None
        self.previous_command = None
        # self.serial_port = serial.Serial("COM10", 115200, timeout=1)

    def initialize_chatbot(self, api_key, gpt_prompt, image_prompt):
        self.chatbot = Chatbot(api_key, gpt_prompt, image_prompt)

    def activate_chatbot(self):
        self.chatbot.activate_chatbot()

    def deactivate_chatbot(self):
        self.chatbot.deactivate_chatbot()

    def get_action_code(self, instruction):
        """Execute a specific instruction."""
        action_type = instruction["action_type"]
        if action_type == "chatbot_message":
            self.view.display_chatbot_message(instruction["tts_text"])
            return None
        else:
            action_code = instruction["action_code"]
            self.view.display_instruction(instruction["tts_text"])
            return action_code

    def wait_for_user(self, task_name, accepting_command):
        while True:
            self.view.display_chatbot_message(f"{task_name} 시작할까요?")
            user_feedback = self.view.get_user_feedback()
            command = self.chatbot.interpret_command(user_feedback)
            if command:
                if command == accepting_command:
                    break
            else:
                self.view.display_chatbot_message(
                    "I'm sorry, I didn't understand that."
                )

    def run(self, task_id):
        """Run the task with the given task ID."""
        self.current_task_id = task_id
        task_blocks = self.model.get_task_blocks(task_id)
        task_block_index = 0
        while task_block_index < len(task_blocks):
            self.current_block_id = task_block_index
            current_block = task_blocks[task_block_index]
            instructions = current_block["instructions"]
            instruction_index = 0
            self.wait_for_user(current_block["block_name"], "Ws")
            need_to_wait = False
            while instruction_index < len(instructions):
                if need_to_wait:
                    self.wait_for_user(instructions[instruction_index]["action"], "Ws")
                    need_to_wait = False
                action_code = self.get_action_code(instructions[instruction_index])
                if not action_code:
                    instruction_index += 1
                    continue
                self.send_command_to_mcu(action_code)
                self.previous_command = self.current_command
                self.current_command = action_code
                user_feedback = self.view.get_user_feedback()
                command = self.chatbot.interpret_command(user_feedback)
                if command:
                    if command == "Wa":
                        self.activate_chatbot()
                    elif command == "Wx":
                        self.deactivate_chatbot()
                    elif command == "Wc":
                        self.view.display_chatbot_message("Command cancelled.")
                        self.send_command_to_mcu(f"H2M1P9V9T3")
                        need_to_wait = True
                    elif command == "Ws":
                        instruction_index += 1
                    else:
                        variable = command[0]
                        variable_index = self.current_command.index(variable)
                        modified_value = int(self.current_command[variable_index + 1])
                        if command[1] == "+":
                            modified_value += int(command[2])
                            if modified_value > 9:
                                modified_value = 9
                        else:
                            modified_value -= int(command[2])
                            if modified_value < 0:
                                modified_value = 0
                        self.previous_command = self.current_command
                        self.current_command = f"{self.current_command[:variable_index]}{variable}{modified_value}{self.current_command[variable_index + 2:]}"
                        self.view.display_chatbot_message(
                            f"Command updated: {self.current_command}"
                        )
                        instructions[instruction_index][
                            "action_code"
                        ] = self.current_command
                else:
                    self.view.display_chatbot_message(
                        "I'm sorry, I didn't understand that."
                    )
            task_block_index += 1

    def send_command_to_mcu(self, command: str):
        """Send interpreted command to MCU."""
        # self.serial_port.write(command.encode())
        self.view.display_command_sent(command)

    def process_image(self, image_path, json_file_path):
        """Send image to chatbot for processing."""
        response = self.chatbot.process_image(image_path)
        if response:
            with open(json_file_path, "w") as file:
                file.write(response)
            self.view.display_chatbot_message(f"Image has been processed successfully.")
            self.model = Model(json_file_path)
        else:
            self.view.display_chatbot_message(
                f"An error occurred while processing the image."
            )
