import json
import yaml
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class GameEngine:
    def __init__(self):
        self.story_data = {}
        self.user_sessions = {}

    def load_story(self, file_path: str):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.endswith((".yaml", ".yml")):
                    self.story_data = yaml.safe_load(f)
                elif file_path.endswith(".json"):
                    self.story_data = json.load(f)
                else:
                    raise ValueError("Unsupported file format. Please use .yaml or .json")
        except Exception as e:
            raise RuntimeError(f"Failed to load story file: {e}")

    def start_session(self, user_id: int):
        start_node = self.story_data.get("start")
        if not start_node:
            raise ValueError("Story file must contain a 'start' node.")
        
        self.user_sessions[user_id] = "start"
        return self._render_node("start")

    def handle_choice(self, user_id: int, callback_data: str):
        if not callback_data.startswith("game_"):
            return None 

        next_node_id = callback_data.replace("game_", "", 1)
        
        if next_node_id not in self.story_data:
            return "End of story.", None, None

        self.user_sessions[user_id] = next_node_id
        return self._render_node(next_node_id)

    def _render_node(self, node_id: str):
        node = self.story_data.get(node_id)
        
        if not node:
            return "Error: Node not found.", None, None

        text = node.get("text", "No text provided.")
        image = node.get("media", None)
        options = node.get("options", [])

        keyboard = []
        for option in options:
            btn_text = option.get("label", "Next")
            target_node = option.get("target", "start")
            callback = f"game_{target_node}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback)])

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        return text, reply_markup, image

    def get_current_state(self, user_id: int):
        node_id = self.user_sessions.get(user_id, "start")
        return self._render_node(node_id)
