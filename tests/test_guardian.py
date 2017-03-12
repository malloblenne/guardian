#!/bin/python3
# Example unit test https://docs.python.org/3.6/library/unittest.html
# http://doc.pytest.org/en/latest/getting-started.html
import pytest

# content of test_sample.py
def func(x):
    return x + 1

def test_answer():
    assert func(4) == 5