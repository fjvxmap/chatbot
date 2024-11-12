from openai import OpenAI


class Chatbot:
    def __init__(self, api_key, gpt_prompt, image_prompt):
        self.is_active = False
        self.client = OpenAI(api_key=api_key)
        self.gpt_prompt = gpt_prompt
        self.image_prompt = image_prompt

    def activate_chatbot(self):
        self.is_active = True

    def deactivate_chatbot(self):
        self.is_active = False

    def process_image(self, image_path):
        if self.is_active:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.image_prompt},
                    {"role": "user", "content": f"image: {image_path}"},
                ],
            )
            return response.choices[0].message.content
        else:
            return None

    def interpret_command(self, command_text):
        if self.is_active:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.gpt_prompt},
                    {"role": "user", "content": command_text},
                ],
            )
            interpreted_command = response.choices[0].message.content
            return interpreted_command
        else:
            return None
