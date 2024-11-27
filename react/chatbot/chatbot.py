import os
import base64
from openai import OpenAI


class Chatbot:
    def __init__(
        self,
        api_key,
        gpt_prompt,
        image_prompt,
        pause_prompt,
        react_prompt,
        model="gpt-4o-mini",
    ):
        self.is_active = False
        self.client = OpenAI(api_key=api_key)
        self.gpt_prompt = gpt_prompt
        self.image_prompt = image_prompt
        self.pause_prompt = pause_prompt
        self.react_prompt = react_prompt
        self.model = model
        self.history = []
        self.data_folder = "data"

    def activate_chatbot(self):
        self.is_active = True

    def deactivate_chatbot(self):
        self.is_active = False

    def _get_next_file_number(self, prefix):
        files = [
            f
            for f in os.listdir(self.data_folder)
            if f.startswith(prefix) and f.endswith(".txt")
        ]
        numbers = [
            int(f[len(prefix) : -4]) for f in files if f[len(prefix) : -4].isdigit()
        ]
        next_number = max(numbers) + 1 if numbers else 1
        return next_number

    def _save_generated_content(self, content, prefix):
        next_number = self._get_next_file_number(prefix)
        filename = f"{prefix}{next_number}.txt"
        filepath = os.path.join(self.data_folder, filename)
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(content)

    def generate_react_prompt(self, user_input=None):
        if user_input:
            prompt = f"{self.gpt_prompt}\n사용자: {user_input}\nAI 어시스턴트:"
        else:
            # 작업 이름 추론을 위한 초기 프롬프트
            prompt = (
                f"{self.image_prompt}\n사용자: 이미지를 제공합니다.\nAI 어시스턴트:"
            )
        return prompt

    def convert_image_to_base64(self, image_path):
        """Convert the image to base64 encoding."""
        with open(image_path, "rb") as img_file:
            img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
        return img_b64

    def process_image(self, image_path):
        """Process the image and return the list of detected objects."""
        if self.is_active:
            img_b64_str = self.convert_image_to_base64(image_path)
            img_type = f"image/{image_path.split('.')[-1]}"
            response = (
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.image_prompt},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{img_type};base64,{img_b64_str}"
                                    },
                                },
                            ],
                        },
                    ],
                    max_tokens=500,
                    temperature=0.7,
                )
                .choices[0]
                .message.content
            )
            object_list = response.strip().split(",")
        else:
            object_list = None
        return object_list

    def update_history(self, object_list):
        self.history.append(object_list)

    def generate_action(self, task_dependencies: list):
        if self.is_active:
            history_text = ""
            for i, item in enumerate(self.history):
                history_text += f"H{i}: {item}\n"
            prompt = (
                f"{self.react_prompt}"
                + f"\n작업 순서 기록: {task_dependencies}"
                + f"\n\n주어진 히스토리:{history_text}"
            )
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                ],
                max_tokens=150,
                temperature=0.7,
            )
            task_info = response.choices[0].message.content.strip().split(",")
            task_info = {
                "task_name": task_info[0],
                "action_code": task_info[1],
                "object": task_info[2],
                "instruction": task_info[3],
            }
        else:
            task_info = None
        return task_info

    def _parse_task_name(self, response):
        # Task Name 추출 로직 (예시: "Task: 샌드위치 만들기")
        for line in response.split("\n"):
            if line.startswith("Task:"):
                return line[len("Task:") :].strip()
        return "Unknown Task"

    def _parse_response(self, response):
        lines = response.strip().split("\n")
        thought = ""
        action_description = ""
        action_code = ""
        for line in lines:
            if line.startswith("Thought:"):
                thought = line[len("Thought:") :].strip()
            elif line.startswith("Action:"):
                action_description = line[len("Action:") :].strip()
            elif line.startswith("- action_code:"):
                action_code = line[len("- action_code:") :].strip()
        return action_description, action_code, thought

    def interpret_command(self, command_text, is_paused=False, given_command=None):
        if self.is_active:
            if is_paused:
                prompt = self.pause_prompt
            else:
                prompt = self.gpt_prompt
            command_text += f"\n{given_command}" if given_command else ""
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": command_text},
                ],
                max_tokens=150,
                temperature=0.7,
            )
            interpreted_command = response.choices[0].message.content
            return interpreted_command
        else:
            return None
