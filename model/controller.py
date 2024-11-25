import serial

from model.model import Model
from model.view import View
from model.command import Command
from util.vision import Vision
from util.voice_control import VoiceControl
from chatbot.chatbot import Chatbot


class Controller:
    def __init__(self, json_file_path):
        self.model = Model(json_file_path)
        self.view = View()
        self.vision = Vision()
        self.voice_control = VoiceControl()
        self.current_task_id = None
        self.current_block_id = None
        self.current_command = None
        self.previous_command = None
        # self.serial_port = serial.Serial("COM10", 115200, timeout=1)

    def initialize_chatbot(self, api_key, gpt_prompt, image_prompt, pause_prompt):
        self.chatbot = Chatbot(api_key, gpt_prompt, image_prompt, pause_prompt)

    def activate_chatbot(self):
        self.chatbot.activate_chatbot()

    def deactivate_chatbot(self):
        self.chatbot.deactivate_chatbot()

    def get_action_code(self, instruction):
        """Execute a specific instruction."""
        action_type = instruction["action_type"]
        if action_type == "chatbot_message":
            self.view.display_chatbot_message(instruction["tts_text"])
            self.voice_control.speak(instruction["tts_text"])
            return None
        else:
            action_code = instruction["action_code"]
            self.view.display_instruction(instruction["tts_text"])
            self.voice_control.speak(instruction["tts_text"])
            return action_code

    def wait_for_user(self, task_name, accepting_command):
        while True:
            self.view.display_chatbot_message(f"{task_name} 시작할까요?")
            self.voice_control.speak(f"{task_name} 시작할까요?")
            user_feedback = self.voice_control.listen_to_user()  # 음성 입력
            if not user_feedback:
                self.view.display_chatbot_message("죄송합니다. 다시 말씀해주세요.")
                self.voice_control.speak("죄송합니다. 다시 말씀해주세요.")
                continue
            command = self.chatbot.interpret_command(user_feedback)
            if command and command == accepting_command:
                break

    def wait_for_process(self, task_name):
        while True:
            self.view.display_chatbot_message(f"{task_name} 계속 진행할까요?")
            self.voice_control.speak(f"{task_name} 계속 진행할까요?")
            user_feedback = self.voice_control.listen_to_user()  # 음성 입력
            if not user_feedback:
                self.view.display_chatbot_message("죄송합니다. 다시 말씀해주세요.")
                self.voice_control.speak("죄송합니다. 다시 말씀해주세요.")
                continue
            command = self.chatbot.interpret_command(user_feedback, is_paused=True)
            if command:
                if command == "Ws":
                    self.view.display_chatbot_message("작업을 건너뛰겠습니다.")
                    self.voice_control.speak("작업을 건너뛰겠습니다.")
                    return Command.SKIP, command
                elif command == "Wr":
                    self.view.display_chatbot_message("작업을 다시 시작하겠습니다.")
                    self.voice_control.speak("작업을 다시 시작하겠습니다.")
                    return Command.RESUME, command
                elif command == "Wc":
                    self.view.display_chatbot_message("작업을 취소합니다.")
                    self.voice_control.speak("작업을 취소합니다.")
                    self.send_command_to_mcu(f"H2M1P9V9T3")
                    return Command.CANCEL, command
                else:
                    return Command.FEEDBACK, command

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
            need_to_wait_user = False
            need_to_wait_process = False
            while instruction_index < len(instructions):
                if need_to_wait_user:
                    task_name = instructions[instruction_index]["action"]
                    if need_to_wait_process:
                        pause_response, feedback_command = self.wait_for_process(
                            task_name
                        )
                        if pause_response == Command.CANCEL:
                            need_to_wait_process = False
                            continue
                        elif pause_response == Command.SKIP:
                            need_to_wait_process = False
                            instruction_index += 1
                            continue
                    else:
                        self.wait_for_user(task_name, "Ws")
                    need_to_wait_user = False
                if not need_to_wait_process or (
                    need_to_wait_process and pause_response == Command.RESUME
                ):
                    action_code = self.get_action_code(instructions[instruction_index])
                    if not action_code:
                        instruction_index += 1
                        continue
                    self.send_command_to_mcu(action_code)
                    self.previous_command = self.current_command
                    self.current_command = action_code
                    # user_feedback = self.view.get_user_feedback()
                    user_feedback = self.voice_control.listen_to_user()
                    command = self.chatbot.interpret_command(
                        user_feedback,
                        given_command=instructions[instruction_index]["tts_text"],
                    )
                    if need_to_wait_process:
                        need_to_wait_process = False
                elif pause_response == Command.FEEDBACK:
                    command = feedback_command
                    need_to_wait_user = True
                if command:
                    if command == "Wa":
                        self.activate_chatbot()
                    elif command == "Wx":
                        self.deactivate_chatbot()
                    elif command == "Wp":
                        self.view.display_chatbot_message("작업이 일시 중지되었습니다.")
                        self.voice_control.speak("작업이 일시 중지되었습니다.")
                        hand_value = self.current_command[
                            self.current_command.index("H") + 1
                        ]
                        moter_value = self.current_command[
                            self.current_command.index("M") + 1
                        ]
                        pause_command = f"H{hand_value}M{moter_value}V0"
                        self.send_command_to_mcu(pause_command)
                        need_to_wait_user = True
                        need_to_wait_process = True
                    elif command == "Wc":
                        self.view.display_chatbot_message("작업이 취소되었습니다.")
                        self.voice_control.speak("작업이 취소되었습니다.")
                        self.send_command_to_mcu(f"H2M1P9V9T3")
                        need_to_wait_user = True
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
                    self.view.display_chatbot_message("죄송합니다. 다시 말씀해주세요.")
                    self.voice_control.speak("죄송합니다. 다시 말씀해주세요.")
            task_block_index += 1

    def send_command_to_mcu(self, command: str):
        """Send interpreted command to MCU."""
        # self.serial_port.write(f"{command}\n".encode())
        self.view.display_command_sent(command)
        # while self.serial_port.in_waiting > 0:
        #     line = self.serial_port.readline().decode().strip()
        #     print(f"Arduino says: {line}")

    def process_image(self, image_path, json_file_path):
        """Send image to chatbot for processing."""
        response = self.chatbot.process_image(image_path)
        if response:
            with open(json_file_path, "w", encoding="utf-8") as file:
                file.write(response)
            self.view.display_chatbot_message(f"이미지 처리가 완료되었습니다.")
            self.model = Model(json_file_path)
        else:
            self.view.display_chatbot_message(
                f"이미지 처리 중 오류가 발생했습니다. 다시 시도해주세요."
            )
