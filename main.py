from model.controller import Controller

if __name__ == "__main__":
    with open("data/gpt_prompt.txt", "r", encoding="utf-8") as f:
        gpt_prompt = f.read()
    with open("data/task_data_set_prompt.txt", "r", encoding="utf-8") as f:
        image_prompt = f.read()
    controller = Controller("data/task_data_set.json")
    controller.initialize_chatbot(
        "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",
        gpt_prompt,
        image_prompt,
    )
    controller.activate_chatbot()
    # controller.process_image("data/test_image.jpg", "data/task_data_set.json")
    controller.wait_for_user("사진 인식", "Ws")
    controller.process_image("data/eggs.jpg", "data/task_data_set.json")

    controller.run(1)
