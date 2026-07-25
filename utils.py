import json


def read_json(file_path):
    """
    Reads and returns JSON data from a file.
    """

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(file_path, data):
    """
    Writes updated data to a JSON file.
    """

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)