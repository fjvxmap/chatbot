from rich.console import Console
from rich.prompt import Prompt


class View:
    def __init__(self):
        self.console = Console()

    def display_chatbot_message(self, message):
        self.console.print(f"[bold green]Chatbot:[/bold green] {message}")

    def display_instruction(self, instruction):
        self.console.print(f"[bold cyan]Instruction:[/bold cyan] {instruction}")

    def display_command_sent(self, command):
        self.console.print(
            f"[bold magenta]Command Sent to MCU:[/bold magenta] {command}"
        )

    def get_user_feedback(self):
        return Prompt.ask("[bold yellow]User Feedback[/bold yellow]")
