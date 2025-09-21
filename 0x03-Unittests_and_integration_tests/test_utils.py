#!/usr/bin/env python3
"""Unit tests for utils.py: nested map access, HTTP JSON fetch,
and memoization behavior. Tests are parameterized and patched
where appropriate, and comply with pycodestyle 2.5.
"""
import unittest
from typing import Any, Dict, Mapping, Sequence
from parameterized import parameterized
from unittest.mock import patch, Mock

from utils import access_nested_map, get_json, memoize


class TestAccessNestedMap(unittest.TestCase):
    """Validate traversal and error behavior for access_nested_map."""

    @parameterized.expand([
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2),
    ])
    def test_access_nested_map(
        self,
        nested_map: Mapping[str, Any],
        path: Sequence[str],
        expected: Any,
    ) -> None:
        """Return the expected value along the provided key path."""
        self.assertEqual(access_nested_map(nested_map, path), expected)

    @parameterized.expand([
        ({}, ("a",), "'a'"),
        ({"a": 1}, ("a", "b"), "'b'"),
    ])
    def test_access_nested_map_exception(
        self,
        nested_map: Mapping[str, Any],
        path: Sequence[str],
        expected_msg: str,
    ) -> None:
        """Raise KeyError with the missing key as the message."""
        with self.assertRaises(KeyError) as cm:
            access_nested_map(nested_map, path)
        self.assertEqual(str(cm.exception), expected_msg)


class TestGetJson(unittest.TestCase):
    """Ensure get_json returns payload and does one HTTP call."""

    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False}),
    ])
    def test_get_json(
        self,
        test_url: str,
        test_payload: Dict[str, Any],
    ) -> None:
        """Return the payload and call requests.get exactly once."""
        with patch("utils.requests.get") as mock_get:
            mock_resp = Mock()
            mock_resp.json.return_value = test_payload
            mock_get.return_value = mock_resp

            result: Dict[str, Any] = get_json(test_url)

            mock_get.assert_called_once_with(test_url)
            self.assertEqual(result, test_payload)


class TestMemoize(unittest.TestCase):
    """Verify memoize caches values to avoid repeated calls."""

    def test_memoize(self) -> None:
        """Call the underlying method once and cache the result."""
        class TestClass:
            """Expose a memoized property for testing."""

            def a_method(self) -> int:
                """Return a sentinel integer to test memoization."""
                return 42

            @memoize
            def a_property(self) -> int:
                """Return self.a_method() and cache after the first call."""
                return self.a_method()

        with patch.object(
            TestClass, "a_method", return_value=42
        ) as mock_method:
            obj = TestClass()
            # First access computes and caches the value.
            self.assertEqual(obj.a_property, 42)
            # Second access returns the cached value.
            self.assertEqual(obj.a_property, 42)
            mock_method.assert_called_once()


if __name__ == "__main__":
    unittest.main()
