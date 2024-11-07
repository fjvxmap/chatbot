from openai import OpenAI


class Chatbot:
    def __init__(self, api_key, gpt_prompt):
        self.chat_activation = False
        self.client = OpenAI(api_key=api_key)
        self.gpt_prompt = gpt_prompt

    def activate_chatbot(self):
        self.chat_activation = True

    def deactivate_chatbot(self):
        self.chat_activation = False

    def interpret_command(self, command_text):
        if self.chat_activation:
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
