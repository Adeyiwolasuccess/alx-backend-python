#!/usr/bin/env python3
"""Unit tests for utils.py covering nested map access, HTTP JSON fetch, and
memoization behavior with caching. Tests are parameterized, patched where
appropriate, and comply with pycodestyle 2.5 requirements.
"""
import unittest
from typing import Any, Dict, Mapping, Sequence, Tuple
from parameterized import parameterized
from unittest.mock import patch, Mock

from utils import access_nested_map, get_json, memoize


class TestAccessNestedMap(unittest.TestCase):
    """Tests for access_nested_map to validate correct traversal and errors."""

    @parameterized.expand([
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2),
    ])
    def test_access_nested_map(
        self,
        nested_map: Mapping[str, Any],
        path: Sequence[str],
        expected: Any
    ) -> None:
        """It should return the expected value along the provided key path."""
        self.assertEqual(access_nested_map(nested_map, path), expected)

    @parameterized.expand([
        ({}, ("a",), "'a'"),
        ({"a": 1}, ("a", "b"), "'b'"),
    ])
    def test_access_nested_map_exception(
        self,
        nested_map: Mapping[str, Any],
        path: Sequence[str],
        expected_msg: str
    ) -> None:
        """It should raise KeyError with the missing key as the message."""
        with self.assertRaises(KeyError) as cm:
            access_nested_map(nested_map, path)
        self.assertEqual(str(cm.exception), expected_msg)


class TestGetJson(unittest.TestCase):
    """Tests for get_json ensuring HTTP is mocked and payloads are returned."""

    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False}),
    ])
    def test_get_json(self, test_url: str, test_payload: Dict[str, Any]) -> None:
        """It should return the JSON payload and call requests.get exactly once."""
        with patch("utils.requests.get") as mock_get:
            mock_resp = Mock()
            mock_resp.json.return_value = test_payload
            mock_get.return_value = mock_resp

            result: Dict[str, Any] = get_json(test_url)

            mock_get.assert_called_once_with(test_url)
            self.assertEqual(result, test_payload)


class TestMemoize(unittest.TestCase):
    """Tests for memoize to assert that cached values avoid repeated calls."""

    def test_memoize(self) -> None:
        """It should call the underlying method once and cache the result."""
        class TestClass:
            """Helper class exposing a memoized property for testing."""

            def a_method(self) -> int:
                """Return a sentinel integer used to test memoization."""
                return 42

            @memoize
            def a_property(self) -> int:
                """Return the result of a_method but cache after first call."""
                return self.a_method()

        with patch.object(TestClass, "a_method", return_value=42) as mock_method:
            obj = TestClass()
            self.assertEqual(obj.a_property, 42)   # computes & caches
            self.assertEqual(obj.a_property, 42)   # returns cached value
            mock_method.assert_called_once()       # called only once


if __name__ == "__main__":
    unittest.main()
