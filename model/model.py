import json


class Model:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self._load_data()

    def _load_data(self):
        """Load JSON data from the given file path."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading JSON file: {e}")
            return None

    def get_tasks(self):
        """Retrieve all tasks."""
        if self.data and "tasks" in self.data:
            return self.data["tasks"]
        return []

    def get_task_blocks(self, task_id):
        """Retrieve task blocks for a specific task."""
        tasks = self.get_tasks()
        for task in tasks:
            if task["task_id"] == task_id:
                return task["task_flow"]["blocks"]
        return []

    def get_task_block(self, task_id, block_id):
        """Retrieve a specific task block."""
        task_blocks = self.get_task_blocks(task_id)
        for block in task_blocks:
            if block["block_id"] == block_id:
                return block
        return None

    def get_task_checklist(self, task_id):
        """Retrieve the task checklist for a specific task."""
        tasks = self.get_tasks()
        for task in tasks:
            if task["task_id"] == task_id:
                return task["task_checklist"]
        return []

    def get_power_words(self):
        """Retrieve power words."""
        if self.data and "power_words" in self.data:
            return self.data["power_words"]
        return {}

    def get_parameters(self):
        """Retrieve parameter details."""
        if self.data and "parameters" in self.data:
            return self.data["parameters"]
        return {}
