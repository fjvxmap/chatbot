import json
import os


class Model:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self.load_data()

    def load_data(self):
        if not os.path.exists(self.file_path):
            return self.initialize_data()
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if not data:
                    return self.initialize_data()
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            return self.initialize_data()

    def initialize_data(self):
        initial_data = {"task_blocks": []}
        self.save_data(initial_data)
        return initial_data

    def save_data(self, data=None):
        if data is None:
            data = self.data
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def get_task_id(self, object, instruction):
        for task_block in self.data["task_blocks"]:
            if (
                task_block["object"] == object
                and task_block["instruction"] == instruction
            ):
                return task_block["id"]
        return None

    def get_task_action(self, id):
        for task_block in self.data["task_blocks"]:
            if task_block["id"] == id:
                return task_block["action_code"]
        return None

    def put_task_block(self, task_name, action_code, object, instruction):
        for task_block in self.data["task_blocks"]:
            if (
                task_block["object"] == object
                and task_block["instruction"] == instruction
            ):
                task_block["task_name"] = task_name
                task_block["action_code"] = action_code
                self.save_data()
                return task_block["id"]
        new_id = len(self.data["task_blocks"]) + 1
        new_task_block = {
            "id": new_id,
            "task_name": task_name,
            "action_code": action_code,
            "object": object,
            "instruction": instruction,
        }
        self.data["task_blocks"].append(new_task_block)
        self.save_data()
        return new_id

    def add_dependency(self, task_id, dependency_id):
        for task_block in self.data["task_blocks"]:
            if task_block["id"] == task_id:
                if "dependencies" not in task_block:
                    task_block["dependencies"] = []
                if dependency_id not in task_block["dependencies"]:
                    task_block["dependencies"].append(dependency_id)
                self.save_data()
                return
        return None

    def get_dependencies(self):
        id_to_name = {
            task["id"]: task["task_name"] for task in self.data["task_blocks"]
        }

        result = []
        for task in self.data["task_blocks"]:
            task_name = task["task_name"]
            dependencies = task.get("dependencies", [])
            if dependencies:
                for dep_id in dependencies:
                    dep_name = id_to_name.get(dep_id, "Unknown")
                    result.append(f"{dep_name} → {task_name}")

        return result
