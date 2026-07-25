import sys
import os

from scanner import scan_project
from architecture_builder import build_architecture
from report_builder import build_report

from utils import (read_json, write_json)





personal_ignore_file = "personal_ignores.json"
if( not (os.path.exists(personal_ignore_file) and os.path.isfile(personal_ignore_file))):
    write_json(personal_ignore_file,{"IGNORE_FOLDERS":[],"IGNORE_FILES":[]})



RECOMMENDED_IGNORE = read_json("recommended_ignores.json")
PERSONAL_IGNORE = read_json(personal_ignore_file)
IGNORE = {
    "IGNORE_FOLDERS":list(set(RECOMMENDED_IGNORE.get("IGNORE_FOLDERS",[])) | set(PERSONAL_IGNORE.get("IGNORE_FOLDERS",[]))),
          
    "IGNORE_FILES":list(set(RECOMMENDED_IGNORE.get("IGNORE_FILES",[])) | set(PERSONAL_IGNORE.get("IGNORE_FILES",[])))
    }





def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <project_path>")
        return

    raw_project_path = (sys.argv[1]) if (((sys.argv[1])[0]) == "/") else ("/" + (sys.argv[1]))
   
    project_path = os.path.abspath(raw_project_path)
    project_realpath = os.path.realpath(project_path)
    project_name = os.path.basename(project_realpath)

    print("Current working directory:")
    print(f"  {os.getcwd()}")

    print("\nRequested project path:")
    print(f"  {raw_project_path}")

    print("\nAbsolute project path:")
    print(f"  {project_path}")

    print("\nResolved project path:")
    print(f"  {project_realpath}")

    print("\nDetected project name:")
    print(f"  {project_name}")

    if not os.path.exists(project_realpath):
        print(f"\nError: project path does not exist: {project_realpath}")
        return

    if not os.path.isdir(project_realpath):
        print(f"\nError: project path is not a directory: {project_realpath}")
        return

    os.makedirs("reports", exist_ok=True)

    architecture_output = os.path.join("reports", f"{project_name}-architecture.md")
    report_output = os.path.join("reports", f"{project_name}-project-report.md")

    print("\nScanning project...")

    files = scan_project(project_realpath, IGNORE)

    print(f"Scanned files after ignores: {len(files)}")

    if len(files) == 0:
        print("Warning: no files were found. Check your path or ignore rules.")
        return

    print("\nFirst 10 scanned files:")
    for file in files[:10]:
        print(f"  - {file}")

    print("\nGenerating architecture...")

    architecture = build_architecture(project_realpath, IGNORE)

    with open(architecture_output, "w", encoding="utf-8") as f:
        f.write("# Project Architecture\n\n")
        f.write(architecture)

    print(f"Architecture written to: {architecture_output}")

    print("\nGenerating project report...")

    build_report(
        project_path=project_realpath,
        file_paths=files,
        ignore=IGNORE,
        output_path=report_output,
    )

    print(f"Project report written to: {report_output}")

    print("\nDone.")


if __name__ == "__main__":
    main()