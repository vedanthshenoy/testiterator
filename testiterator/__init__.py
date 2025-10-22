"""
testiterator - AI-Powered Testing Framework with Decorator-Based Parameterized Testing

A comprehensive testing library that uses AI to generate tests and supports
parameterized testing through decorators.
"""

__version__ = "1.0.0"
__author__ = "TestIterator Contributors"
__license__ = "MIT"

from .decorator import testiterator
from .core import CodeAnalyzer, TestWriter, TestRunner

__all__ = [
    "testiterator",
    "CodeAnalyzer",
    "TestWriter",
    "TestRunner",
    "__version__",
]