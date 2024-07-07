import requests
from typing import Dict, Any, Optional


def get_folder_structure(
    owner: str, repo: str, path: str, token: Optional[str] = None
) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    if token:
        headers["Authorization"] = f"token {token}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    structure = {}
    for item in response.json():
        if item["type"] == "file":
            structure[item["name"]] = "file"
        elif item["type"] == "dir":
            structure[item["name"]] = get_folder_structure(
                owner, repo, item["path"], token
            )

    return structure


def _print_folder_structure(structure: Dict[str, Any], indent: str = "") -> None:
    for name, content in structure.items():
        if content == "file":
            print(f"{indent}├── {name}")
        else:
            print(f"{indent}├── {name}/")
            _print_folder_structure(content, indent + "│   ")
