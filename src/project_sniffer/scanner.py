import os


def scan_project(root_path, ignore=None):
    """
    Walk through a project and collect file paths.

    The ignore config prevents heavy/unwanted folders like:
    - .git
    - node_modules
    - virtual-env
    - __pycache__

    from being scanned.
    """

    ignore = ignore or {}

    ignore_folders = set(ignore.get("IGNORE_FOLDERS", []))
    ignore_files = set(ignore.get("IGNORE_FILES", []))

    file_paths = []

    for root, dirs, files in os.walk(root_path):
        # Modify dirs in-place so os.walk does not enter ignored folders
        dirs[:] = [d for d in dirs if d not in ignore_folders]

        for file in files:
            if file in ignore_files:
                continue

            location = os.path.join(root, file)
            file_paths.append(location)

    return file_paths