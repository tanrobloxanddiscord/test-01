import json
import os

MEMORY_FILE = "bot_memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def update_user_memory(user_id, info_text):
    memory = load_memory()
    str_user_id = str(user_id)
    if str_user_id not in memory:
        memory[str_user_id] = []
    if info_text not in memory[str_user_id]:
        memory[str_user_id].append(info_text)
        save_memory(memory)
        return True
    return False

def get_user_memory(user_id):
    memory = load_memory()
    str_user_id = str(user_id)
    if str_user_id in memory and memory[str_user_id]:
        return "\n- " + "\n- ".join(memory[str_user_id])
    return ""

def clear_user_memory(user_id):
    memory = load_memory()
    str_user_id = str(user_id)
    if str_user_id in memory:
        del memory[str_user_id]
        save_memory(memory)
        return True
    return False
