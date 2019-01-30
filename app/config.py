import json
from os import path
from constant import PROJECT_ROOT

# loading config files
with open(path.join(PROJECT_ROOT, "config.json"), "r") as reader:
    config = json.loads(reader.read())
