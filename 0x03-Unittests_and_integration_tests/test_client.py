#!/usr/bin/env python3
"""Unit tests for client.GithubOrgClient."""
import unittest
from typing import Any, Dict
from unittest.mock import patch, PropertyMock
from parameterized import parameterized

from client import GithubOrgClient


class TestGithubOrgClient(unittest.TestCase):
    """Tests for GithubOrgClient behaviors."""

    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch("client.get_json")
    def test_org(self, org: str, mock_get_json) -> None:
        """Call get_json once with org URL and return payload."""
        payload: Dict[str, Any] = {"login": org, "id": 1}
        mock_get_json.return_value = payload

        client = GithubOrgClient(org)
        result = client.org

        expected_url = GithubOrgClient.ORG_URL.format(org=org)
        mock_get_json.assert_called_once_with(expected_url)
        self.assertEqual(result, payload)

    def test_public_repos_url(self) -> None:
        """Return repos_url derived from the mocked org property."""
        repos_url = "https://api.github.com/orgs/test/repos"
        payload: Dict[str, Any] = {"repos_url": repos_url}
        with patch(
            "client.GithubOrgClient.org",
            new_callable=PropertyMock,
            return_value=payload,
        ):
            client = GithubOrgClient("test")
            self.assertEqual(client._public_repos_url, repos_url)


if __name__ == "__main__":
    unittest.main()
