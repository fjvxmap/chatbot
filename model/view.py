class View:
    def display_chatbot_message(self, message):
        print(f"Chatbot: {message}")

    def display_instruction(self, instruction):
        print(f"Instruction: {instruction}")

    def display_command_sent(self, command):
        print(f"Command Sent to MCU: {command}")

    def get_user_feedback(self):
        return input("User Feedback: ")
