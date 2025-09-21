# 0x03 - Unittests and Integration Tests

This directory contains Python unittests and integration tests for the **utils** module.  
The focus is on practicing **test-driven development (TDD)**, parameterized testing, mocking, and integration testing.

---

## 📂 Project Structure

0x03-Unittests_and_integration_tests/
│
├── utils.py # Module with utility functions
├── test_utils.py # Unit tests for utils.py
└── README.md # Project documentation (this file)

yaml
Copy code

---

## 🛠️ Functions Under Test

### 1. `access_nested_map(nested_map, path)`
- Safely traverses a nested mapping (dictionary-like) using a sequence of keys.
- Raises `KeyError` if a key is missing or if traversal fails.

Example:
```python
nested_map = {"a": {"b": {"c": 1}}}
result = access_nested_map(nested_map, ["a", "b", "c"])
# result = 1
2. get_json(url)
Performs an HTTP GET request on a given URL.

Returns the JSON response as a Python dictionary.

3. memoize(fn)
A decorator that memoizes method results in class instances.

Prevents repeated expensive calls by caching results.

🧪 Unit Tests
All tests are written with the unittest framework and make use of the parameterized library for efficiency.

Implemented Tests
test_access_nested_map

Ensures correct traversal of nested dictionaries.

Uses @parameterized.expand to cover multiple input cases in one test.

Example from test_utils.py:

python
Copy code
@parameterized.expand([
    ({"a": 1}, ("a",), 1),
    ({"a": {"b": 2}}, ("a",), {"b": 2}),
    ({"a": {"b": 2}}, ("a", "b"), 2),
])
def test_access_nested_map(self, nested_map, path, expected):
    self.assertEqual(access_nested_map(nested_map, path), expected)
⚙️ Setup Instructions
Clone the repo (if not already):

bash
Copy code
git clone https://github.com/<your-username>/alx-backend-python.git
cd alx-backend-python/0x03-Unittests_and_integration_tests
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Minimum requirements: requests, parameterized

▶️ Running Tests
From inside the directory:

bash
Copy code
python -m unittest -v test_utils.py
Expected output:

diff
Copy code
test_access_nested_map_0 ... ok
test_access_nested_map_1 ... ok
test_access_nested_map_2 ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.002s
OK