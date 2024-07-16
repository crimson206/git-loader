import requests
from typing import List, Optional


def create_headers(token: Optional[str] = None):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def get_user_repositories(username: str, token: Optional[str] = None) -> List[str]:
    """
    Fetch all public repository names for a given GitHub user.

    Args:
    username (str): The GitHub username to fetch repositories for.
    token (Optional[str]): GitHub personal access token for authentication.

    Returns:
    List[str]: A list of repository names.
    """
    url = f"https://api.github.com/users/{username}/repos"
    headers = create_headers(token)
    repositories = []
    page = 1

    while True:
        response = requests.get(f"{url}?page={page}&per_page=100", headers=headers)
        response.raise_for_status()
        repos_page = response.json()

        if not repos_page:
            break

        repositories.extend([repo["name"] for repo in repos_page])
        page += 1

    return repositories
