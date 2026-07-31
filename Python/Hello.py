import json

data = {
    "name": "Alice",
    "age": 25,
    "active": True
}

with open("data.json", "w") as f:
    json.dump(data, f, indent=4)
