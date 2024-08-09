import requests
import os
from typing import Optional, List, Dict, Any
from crimson.file_loader.utils import filter_paths
from .reader import get_user_repositories


def create_headers(token: Optional[str] = None) -> Dict[str, str]:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def download_file(
    owner: str,
    repo: str,
    file_path: str,
    save_as: Optional[str] = None,
    token: Optional[str] = None,
) -> None:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{file_path}"
    headers = create_headers(token)
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    if save_as is None:
        save_as = os.path.join(".", os.path.basename(file_path))

    dir_name = os.path.dirname(save_as)
    if dir_name == "":
        dir_name = "."
    os.makedirs(dir_name, exist_ok=True)
    with open(save_as, "wb") as f:
        f.write(response.content)

    print(f"{file_path} has been downloaded and saved as {save_as}")


def get_tree_contents(
    owner: str, repo: str, tree_sha: str, token: Optional[str] = None
) -> List[Dict[str, Any]]:
    url = (
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1"
    )
    headers = create_headers(token)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["tree"]


def download_folder(
    owner: str,
    repo: str,
    folder_path: str,
    local_dir: str,
    token: Optional[str] = None,
    includes: List[str] = [],
    excludes: List[str] = [],
) -> None:
    # First, get the default branch (usually 'main' or 'master')
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = create_headers(token)
    response = requests.get(repo_url, headers=headers)
    response.raise_for_status()
    default_branch = response.json()["default_branch"]

    # Get the tree contents
    tree_contents = get_tree_contents(owner, repo, default_branch, token)
    path_filter = _generate_path_filter(tree_contents, includes, excludes)

    # Filter and download files
    for item in tree_contents:
        if item["type"] == "blob" and item["path"].startswith(folder_path):
            file_path = item["path"]
            if file_path in path_filter:
                save_as = os.path.join(
                    local_dir, os.path.relpath(file_path, folder_path)
                )
                download_file(owner, repo, file_path, save_as, token)


def download_all_shared_path(
    username: str, shared_path: str, token: Optional[str] = None
) -> List[str]:
    repositories = get_user_repositories(username, token)
    downloaded_repos = []

    for repo in repositories:
        save_as = "/".join(["tomls", repo, shared_path])

        try:
            if download_file(username, repo, shared_path, save_as):
                downloaded_repos.append(repo)
        except Exception as e:
            print("Repository,", repo, ", caused an error:", e)

    return downloaded_repos


def _generate_path_filter(
    tree_contents: List[Dict[str, Any]], includes: List[str], excludes: List[str]
) -> List[str]:
    paths = [tree_content["path"] for tree_content in tree_contents]
    paths_filter = filter_paths(paths, includes, excludes)

    return paths_filter
