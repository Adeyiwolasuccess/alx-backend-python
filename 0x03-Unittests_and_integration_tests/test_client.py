#!/usr/bin/env python3
"""Unit and integration tests for client.GithubOrgClient."""
import unittest
from typing import Any, Dict, List
from unittest.mock import patch, PropertyMock, Mock
from parameterized import parameterized, parameterized_class

from client import GithubOrgClient
from fixtures import (
    org_payload, repos_payload, expected_repos, apache2_repos,
)


class TestGithubOrgClient(unittest.TestCase):
    """Unit tests for GithubOrgClient behaviors."""

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

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False),
    ])
    def test_has_license(
        self,
        repo: Dict[str, Any],
        license_key: str,
        expected: bool,
    ) -> None:
        """Return True if repo has license_key; otherwise return False."""
        result = GithubOrgClient.has_license(repo, license_key)
        self.assertEqual(result, expected)


@parameterized_class([{
    "org_payload": org_payload,
    "repos_payload": repos_payload,
    "expected_repos": expected_repos,
    "apache2_repos": apache2_repos,
}])
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """Integration tests for GithubOrgClient.public_repos.
    Only external requests are mocked; internal logic is exercised.
    """
    org_payload: Dict[str, Any]
    repos_payload: List[Dict[str, Any]]
    expected_repos: List[str]
    apache2_repos: List[str]

    @classmethod
    def setUpClass(cls) -> None:
        """Start a patcher for requests.get with fixture-driven responses."""
        def _response_for(url: str) -> Mock:
            mock_resp = Mock()
            names: List[str] = []
            # Try common org identifiers from the fixture.
            for k in ("login", "name"):
                v = cls.org_payload.get(k)
                if isinstance(v, str) and v not in names:
                    names.append(v)

            org_urls = [
                GithubOrgClient.ORG_URL.format(org=n) for n in names
            ]
            if url in org_urls:
                mock_resp.json.return_value = cls.org_payload
            elif url == cls.org_payload.get("repos_url"):
                mock_resp.json.return_value = cls.repos_payload
            else:
                mock_resp.json.return_value = {}
            return mock_resp

        cls.get_patcher = patch("requests.get", side_effect=_response_for)
        cls.get_patcher.start()

    @classmethod
    def tearDownClass(cls) -> None:
        """Stop the requests.get patcher."""
        cls.get_patcher.stop()

    def _org_name(self) -> str:
        """Best-effort extraction of org name used by the fixture."""
        for k in ("login", "name"):
            v = self.org_payload.get(k)
            if isinstance(v, str):
                return v
        return "org"

    def test_public_repos(self) -> None:
        """It should return all repo names from the repos fixture."""
        client = GithubOrgClient(self._org_name())
        self.assertEqual(client.public_repos(), self.expected_repos)

    def test_public_repos_with_license(self) -> None:
        """It should filter repos by the apache-2.0 license key."""
        client = GithubOrgClient(self._org_name())
        self.assertEqual(
            client.public_repos(license="apache-2.0"),
            self.apache2_repos,
        )


if __name__ == "__main__":
    unittest.main()
