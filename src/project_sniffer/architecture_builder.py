import os


def build_architecture(root_path, ignore=None):
    """
    Build a readable folder/file tree for a project.

    Uses the same ignore config as scanner.py so generated architecture.md
    does not include virtual environments, Git data, cache folders, etc.
    """

    ignore = ignore or {}

    ignore_folders = set(ignore.get("IGNORE_FOLDERS", []))
    ignore_files = set(ignore.get("IGNORE_FILES", []))

    root_path = os.path.abspath(root_path)

    lines = []

    for root, dirs, files in os.walk(root_path):
        dirs[:] = sorted([d for d in dirs if d not in ignore_folders])
        files = sorted([f for f in files if f not in ignore_files])

        relative_root = os.path.relpath(root, root_path)

        if relative_root == ".":
            level = 0
            folder_name = os.path.basename(root_path)
        else:
            level = relative_root.count(os.sep) + 1
            folder_name = os.path.basename(root)

        indent = "│   " * level
        lines.append(f"{indent}{folder_name}/")

        subindent = "│   " * (level + 1)

        for file in files:
            lines.append(f"{subindent}{file}")

    return "\n".join(lines)