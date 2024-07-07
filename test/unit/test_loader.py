# test_loader.py
import pytest
from unittest.mock import patch, MagicMock, Mock
from typing import Generator
from crimson.git_loader.loader import (
    create_headers,
    download_file,
    get_tree_contents,
    download_folder,
    _generate_path_filter,
)
from crimson.file_loader.utils import filter_paths


@pytest.fixture
def mock_requests_get() -> Generator[Mock, None, None]:
    with patch("crimson.git_loader.loader.requests.get") as mock_get:
        yield mock_get


def test_create_headers():
    # Test without token
    headers = create_headers()
    assert headers == {"Accept": "application/vnd.github.v3+json"}

    # Test with token
    headers = create_headers("test_token")
    assert headers == {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": "token test_token",
    }


@patch("crimson.git_loader.loader.requests.get")
@patch("builtins.open", new_callable=MagicMock)
@patch("os.makedirs")
def test_download_file(mock_makedirs: Mock, mock_open: MagicMock, mock_get: Mock):
    mock_response = MagicMock()
    mock_response.content = b"File content"
    mock_get.return_value = mock_response

    download_file("owner", "repo", "file.txt", "local_file.txt", "token")

    mock_get.assert_called_with(
        "https://raw.githubusercontent.com/owner/repo/main/file.txt",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "token token",
        },
    )
    mock_makedirs.assert_called_once_with(".", exist_ok=True)
    mock_open.assert_called_with("local_file.txt", "wb")


def test_get_tree_contents(mock_requests_get: Mock):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "tree": [{"path": "file1.txt"}, {"path": "folder/file2.txt"}]
    }
    mock_requests_get.return_value = mock_response

    result = get_tree_contents("owner", "repo", "main", "token")

    mock_requests_get.assert_called_with(
        "https://api.github.com/repos/owner/repo/git/trees/main?recursive=1",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "token token",
        },
    )
    assert result == [{"path": "file1.txt"}, {"path": "folder/file2.txt"}]


@patch("crimson.git_loader.loader.requests.get")
@patch("crimson.git_loader.loader.get_tree_contents")
@patch("crimson.git_loader.loader.download_file")
@patch("crimson.git_loader.loader._generate_path_filter")
def test_download_folder(
    mock_generate_path_filter: Mock,
    mock_download_file: Mock,
    mock_get_tree_contents: Mock,
    mock_get: Mock,
):
    mock_repo_response = MagicMock()
    mock_repo_response.json.return_value = {"default_branch": "main"}
    mock_get.return_value = mock_repo_response

    mock_get_tree_contents.return_value = [
        {"type": "blob", "path": "folder/file1.txt"},
        {"type": "blob", "path": "folder/file2.txt"},
        {"type": "tree", "path": "folder/subfolder"},
    ]

    mock_generate_path_filter.return_value = {
        "folder/file1.txt": True,
        "folder/file2.txt": False,
        "folder/subfolder": True,
    }

    download_folder(
        "owner", "repo", "folder", "local_dir", "token", ["*.txt"], ["file2.txt"]
    )

    mock_get.assert_called_with(
        "https://api.github.com/repos/owner/repo",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "token token",
        },
    )
    mock_get_tree_contents.assert_called_with("owner", "repo", "main", "token")
    mock_generate_path_filter.assert_called_with(
        mock_get_tree_contents.return_value, ["*.txt"], ["file2.txt"]
    )


def test_generate_path_filter():
    tree_contents = [
        {"path": "folder/file1.txt"},
        {"path": "folder/file2.py"},
        {"path": "folder/subfolder/file3.txt"},
    ]
    includes = [".*.txt"]
    excludes = ["subfolder/*"]

    result = _generate_path_filter(tree_contents, includes, excludes)

    assert result == [
        "folder/file1.txt",
    ]
