import json
import os

import yaml


class GameEngine:
    def __init__(self):
        self.stories = {}
        self.sessions = {}

    def load_story(self, file_path: str, story_id: str = "default"):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Story file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                if file_path.endswith(".yaml") or file_path.endswith(".yml"):
                    data = yaml.safe_load(f)
                elif file_path.endswith(".json"):
                    data = json.load(f)
                else:
                    raise ValueError("Unsupported file format. Use JSON or YAML.")
            except Exception as e:
                raise ValueError(f"Failed to parse story file: {e}")

        if not data or not isinstance(data, dict):
            raise ValueError("Invalid story structure. Must be a dictionary.")

        if "start" not in data:
            first_node = next(iter(data), None)
            if first_node:
                data["start"] = data[first_node]
            else:
                raise ValueError("Story file must contain at least one node or a 'start' node.")

        self.stories[story_id] = data
        return True

    def start_session(self, user_id: int, story_id: str = "default"):
        if story_id not in self.stories:
            raise ValueError(f"Story ID '{story_id}' not loaded.")

        story_data = self.stories[story_id]
        start_node = "start"

        if start_node not in story_data:
            raise ValueError("Critical Error: 'start' node missing from loaded story.")

        self.sessions[user_id] = {"story_id": story_id, "current_node": start_node, "history": []}
        return self.get_node_data(user_id)

    def get_node_data(self, user_id: int):
        session = self.sessions.get(user_id)
        if not session:
            return None

        story_id = session["story_id"]
        node_id = session["current_node"]
        story = self.stories.get(story_id)

        if not story:
            return None

        node = story.get(node_id)
        if not node:
            return {"text": "End of story or Error: Node not found.", "options": []}

        return {"text": node.get("text", ""), "image": node.get("image", None), "options": node.get("options", [])}

    def make_choice(self, user_id: int, option_index: int):
        session = self.sessions.get(user_id)
        if not session:
            raise ValueError("Session not found.")

        story_id = session["story_id"]
        node_id = session["current_node"]
        story = self.stories.get(story_id)

        if not story:
            raise ValueError("Story data missing.")

        node = story.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found.")

        options = node.get("options", [])
        if option_index < 0 or option_index >= len(options):
            raise ValueError("Invalid option index.")

        selected_option = options[option_index]
        next_node = selected_option.get("next")

        if not next_node:
            return None

        session["history"].append(node_id)
        session["current_node"] = next_node

        return self.get_node_data(user_id)

    def end_session(self, user_id: int):
        if user_id in self.sessions:
            del self.sessions[user_id]
