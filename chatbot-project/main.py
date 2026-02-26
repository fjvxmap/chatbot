import os
from pathlib import Path

from dotenv import load_dotenv

from model.controller import Controller


def load_env():
    base_dir = Path(__file__).resolve().parent
    for env_path in (base_dir / ".env", base_dir.parent / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)


if __name__ == "__main__":
    load_env()

    with open("data/gpt_prompt.txt", "r", encoding="utf-8") as f:
        gpt_prompt = f.read()
    with open("data/task_data_set_prompt.txt", "r", encoding="utf-8") as f:
        image_prompt = f.read()
    with open("data/pause_prompt.txt", "r", encoding="utf-8") as f:
        pause_prompt = f.read()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("Missing OPENAI_API_KEY. Set it in your .env file.")

    controller = Controller("data/task_data_set.json")
    controller.initialize_chatbot(
        openai_api_key,
        gpt_prompt,
        image_prompt,
        pause_prompt,
    )
    controller.activate_chatbot()
    # controller.process_image("data/test_image.jpg", "data/task_data_set.json")
    # controller.wait_for_user("사진 인식", "Ws")
    # controller.process_image("data/eggs.jpg", "data/task_data_set.json")

    controller.run(1)
