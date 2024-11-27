from model.controller import Controller

if __name__ == "__main__":
    # 프롬프트 로드
    with open("data/gpt_prompt.txt", "r", encoding="utf-8") as f:
        gpt_prompt = f.read()
    with open("data/image_prompt.txt", "r", encoding="utf-8") as f:
        image_prompt = f.read()
    with open("data/pause_prompt.txt", "r", encoding="utf-8") as f:
        pause_prompt = f.read()
    with open("data/react_prompt.txt", "r", encoding="utf-8") as f:
        react_prompt = f.read()

    # Neo4j 연결 정보
    neo4j_uri = "bolt://localhost:7687"
    neo4j_user = "neo4j"
    neo4j_password = "neo4j"  # 실제 비밀번호로 대체

    # Controller 초기화
    controller = Controller(
        "data/task_blocks.json", neo4j_uri, neo4j_user, neo4j_password
    )
    controller.initialize_chatbot(
        "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",
        gpt_prompt,
        image_prompt,
        pause_prompt,
        react_prompt,
        model="gpt-4o",
    )
    controller.activate_chatbot()
    controller.run()
