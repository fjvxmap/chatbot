import serial

from model.model import Model
from model.view import View
from model.command import Command
from util.vision import Vision
from util.voice_control import VoiceControl
from chatbot.chatbot import Chatbot
from graph.graph_manager import GraphManager


class Controller:
    def __init__(self, json_file_path, neo4j_uri, neo4j_user, neo4j_password):
        self.model = Model(json_file_path)
        self.view = View()
        self.vision = Vision()
        self.voice_control = VoiceControl()
        self.current_task_id = None
        self.current_block_id = None
        self.current_command = None
        self.previous_command = None
        # GraphManager 초기화
        self.graph_manager = GraphManager(neo4j_uri, neo4j_user, neo4j_password)
        # Chatbot 초기화 (수정된 클래스 사용)
        self.chatbot = None

    def initialize_chatbot(
        self,
        api_key,
        gpt_prompt,
        image_prompt,
        pause_prompt,
        react_prompt,
        model="gpt-4o-mini",
    ):
        self.chatbot = Chatbot(
            api_key, gpt_prompt, image_prompt, pause_prompt, react_prompt, model
        )

    def activate_chatbot(self):
        if self.chatbot:
            self.chatbot.activate_chatbot()

    def deactivate_chatbot(self):
        if self.chatbot:
            self.chatbot.deactivate_chatbot()

    def run(self):
        """Run the controller using ReAct framework."""
        # 이미지 인식 및 작업 이름 추론
        image_path = self.get_image_from_vision_glass()
        object_list = self.chatbot.process_image(image_path)
        if not object_list:
            self.print_message("이미지를 인식하지 못했습니다.")
            return
        self.chatbot.update_history(object_list)

        previous_task_id = None

        while True:
            task_dependencies = self.model.get_dependencies()
            task_info = self.chatbot.generate_action(task_dependencies)
            if not task_info:
                self.print_message("작업을 인식하지 못했습니다.")
                break
            task_name = task_info["task_name"]
            if task_name == "None":
                self.print_message("모든 작업이 완료되었습니다.")
                break
            self.print_message(f"인식된 작업: {task_name}")
            task_id = self.model.get_task_id(
                task_info["object"], task_info["instruction"]
            )
            if task_id:
                action_code = self.model.get_task_action(task_id)
            else:
                action_code = task_info["action_code"]
            hand = action_code[action_code.index("H") + 1]
            is_task_completed = False
            need_to_ask = True
            while not is_task_completed:
                if need_to_ask:
                    while True:
                        self.print_message(f"{task_name} 시작할까요?")
                        # user_input = self.voice_control.listen_to_user()
                        # user_input = input()
                        # if user_input:
                        #     response = self.chatbot.interpret_command(user_input)
                        #     if response == "Ws":
                        #         break
                        break
                need_to_ask = False
                self.send_command_to_mcu(action_code)
                if task_id:
                    self.print_message(
                        f"이미 저장된 {task_name} 작업 정보를 사용합니다."
                    )
                else:
                    self.print_message(
                        f"{task_name} 수행 중입니다. 일시 중지를 원하시면 말씀해주세요."
                    )
                    # user_input = self.voice_control.listen_to_user()
                    # user_input = input()
                    # if user_input:
                    #     response = self.chatbot.interpret_command(user_input)
                    #     if response == "Wp":
                    #         self.send_command_to_mcu(f"H{hand}M0V0")
                    #         self.print_message("일시 중지합니다.")
                    #     elif response == "Wc":
                    #         self.print_message("작업을 취소합니다.")
                    #         self.send_command_to_mcu(f"H{hand}M1V5T0")
                    #         need_to_ask = True
                if not need_to_ask:
                    if task_id:
                        self.print_message(
                            f"저장된 정보를 사용하여 구동을 완료했습니다. 추가적인 피드백이 있으신가요?"
                        )
                    else:
                        self.print_message(f"{task_name} 중지되었습니다. 계속할까요?")
                    # user_input = self.voice_control.listen_to_user()
                    # user_input = input()
                    # if user_input:
                    #     response = self.chatbot.interpret_command(
                    #         user_input, True, action_code
                    #     )
                    #     if response == "Ws":
                    #         is_task_completed = True
                    #     elif response == "Wc":
                    #         self.print_message("작업을 취소합니다.")
                    #         self.send_command_to_mcu(f"H{hand}M1V5T0")
                    #         need_to_ask = True
                    #     elif response == "Wr":
                    #         self.print_message("작업을 재개합니다.")
                    #     else:
                    #         self.print_message("피드백을 반영하였습니다.")
                    #         action_code = response
                    is_task_completed = True
            self.print_message(f"{task_name} 작업이 완료되었습니다.")
            observation_data = self.get_observation()
            standardized_action_code = self.standardize_observation(observation_data)
            self.chatbot.update_history(
                [task_name, action_code, standardized_action_code]
            )
            task_id = self.model.put_task_block(
                task_name,
                standardized_action_code,
                task_info["object"],
                task_info["instruction"],
            )
            if previous_task_id:
                self.model.add_dependency(task_id, previous_task_id)
            previous_task_id = task_id

    def execute_action(self, action_code, task_name):
        # MCU에 명령 전송
        self.send_command_to_mcu(action_code)
        # MCU로부터 관찰 결과 수신
        observation_data = self.get_observation()
        # 수신된 데이터를 표준화된 action_code로 변환
        standardized_action_code = self.standardize_observation(observation_data)
        return standardized_action_code

    def get_image_from_vision_glass(self):
        # 비전 글래스에서 이미지를 가져오는 로직 (예시 구현)
        # 실제 구현 시 카메라 모듈과 연동
        return "data/test_image.jpg"

    def send_command_to_mcu(self, command: str):
        """Send command to MCU."""
        # self.serial_port.write(command.encode())
        self.view.display_command_sent(command)

    def get_observation(self):
        # Get observation data from MCU
        observation_data = {
            "encoder_value": 1500,
            "tension_value": 5,
            "H": 1,
            "M": 0,
            "P": 3,
            "V": 5,
            "T": 5,
        }
        return observation_data

    def standardize_observation(self, observation_data):
        # 수신된 데이터를 action_code 형식으로 변환
        action_code = f"H{observation_data['H']}M{observation_data['M']}P{observation_data['P']}T{observation_data['T']}"
        return action_code

    def print_message(self, message):
        self.view.display_chatbot_message(message)
        # self.voice_control.speak(message)
