#!/usr/bin/env python3
"""Unit tests for client.GithubOrgClient.org using patch and
parameterization without performing real HTTP calls.
"""
import unittest
from typing import Any, Dict
from unittest.mock import patch
from parameterized import parameterized

from client import GithubOrgClient


class TestGithubOrgClient(unittest.TestCase):
    """Tests for GithubOrgClient behaviors against the GitHub API."""

    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch("client.get_json")
    def test_org(self, org: str, mock_get_json) -> None:
        """It should call get_json once with the org URL and return payload."""
        payload: Dict[str, Any] = {"login": org, "id": 1}
        mock_get_json.return_value = payload

        client = GithubOrgClient(org)
        result = client.org

        expected_url = GithubOrgClient.ORG_URL.format(org=org)
        mock_get_json.assert_called_once_with(expected_url)
        self.assertEqual(result, payload)


if __name__ == "__main__":
    unittest.main()
