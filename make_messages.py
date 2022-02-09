import json

with open("messages.json", "rt", encoding="utf-8") as file:
    all_texts = json.load(file)

start = """
import json

with open("messages.json", "rt", encoding="utf-8") as file:
    all_texts = json.load(file)


"""

with open('messages.py', 'w', encoding='utf-8') as msg_file:
    msg_file.write(start)
    msg_file.writelines([f'{key} = all_texts[\'{key}\']\n' for key in all_texts.keys()])
