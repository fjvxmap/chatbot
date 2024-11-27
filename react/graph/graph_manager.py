from neo4j import GraphDatabase


class GraphManager:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_or_update_task(self, task_name, action_code, observation, feedback=None):
        with self.driver.session() as session:
            session.write_transaction(
                self._create_or_update_task_tx,
                task_name,
                action_code,
                observation,
                feedback,
            )

    @staticmethod
    def _create_or_update_task_tx(tx, task_name, action_code, observation, feedback):
        # Task 노드 생성 또는 매칭
        tx.run("MERGE (t:Task {name: $task_name})", task_name=task_name)

        # Action 노드 생성 또는 매칭
        tx.run(
            """
            MERGE (a:Action {code: $action_code})
            ON CREATE SET a.success_count = 1
            ON MATCH SET a.success_count = a.success_count + 1
            """,
            action_code=action_code,
        )

        # 관계 생성 또는 업데이트
        tx.run(
            """
            MATCH (t:Task {name: $task_name}), (a:Action {code: $action_code})
            MERGE (t)-[r:HAS_ACTION]->(a)
            ON CREATE SET r.update_count = 1
            ON MATCH SET r.update_count = r.update_count + 1
            """,
            task_name=task_name,
            action_code=action_code,
        )

        # 옵저베이션 및 피드백 업데이트
        if feedback:
            tx.run(
                """
                MATCH (a:Action {code: $action_code})
                SET a.feedback = $feedback
                """,
                action_code=action_code,
                feedback=feedback,
            )

        if observation:
            tx.run(
                """
                MATCH (a:Action {code: $action_code})
                SET a.observation = $observation
                """,
                action_code=action_code,
                observation=observation,
            )

    def get_task_actions(self, task_name):
        with self.driver.session() as session:
            result = session.read_transaction(self._get_task_actions_tx, task_name)
            return result

    @staticmethod
    def _get_task_actions_tx(tx, task_name):
        result = tx.run(
            """
            MATCH (t:Task {name: $task_name})-[:HAS_ACTION]->(a:Action)
            RETURN a.code AS action_code, a.success_count AS success_count, a.observation AS observation
            """,
            task_name=task_name,
        )
        return [record for record in result]
