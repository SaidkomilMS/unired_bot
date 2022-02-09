import json

with open("messages.json", "rt", encoding="utf-8") as file:
    all_texts = json.load(file)

for key, value in all_texts.items():
    exec(f"{key} = {value}")
