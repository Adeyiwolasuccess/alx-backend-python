#!/usr/bin/env python3
"""Unit tests for client.GithubOrgClient."""
import unittest
from typing import Any, Dict, List
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
        ) as mock_org:
            client = GithubOrgClient("test")
            self.assertEqual(client._public_repos_url, repos_url)
            mock_org.assert_called_once()

    @patch("client.get_json")
    def test_public_repos(self, mock_get_json) -> None:
        """Return repo names from payload; assert single calls to mocks."""
        repos_url = "https://api.github.com/orgs/test/repos"
        payload: List[Dict[str, Any]] = [
            {"name": "alpha"},
            {"name": "beta", "license": {"key": "mit"}},
            {"name": "gamma", "license": {"key": "apache-2.0"}},
        ]
        mock_get_json.return_value = payload

        with patch(
            "client.GithubOrgClient._public_repos_url",
            new_callable=PropertyMock,
            return_value=repos_url,
        ) as mock_prop:
            client = GithubOrgClient("test")
            result = client.public_repos()

            self.assertEqual(result, ["alpha", "beta", "gamma"])
            mock_prop.assert_called_once()
            mock_get_json.assert_called_once_with(repos_url)


if __name__ == "__main__":
    unittest.main()
