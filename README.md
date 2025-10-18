# Test Iterator

Test Iterator is a simple Python project that provides tools for running, analyzing, and managing tests. It includes modules for test iteration, decorators for test functions, and a command-line interface (CLI) to streamline testing workflows.

## Project Structure

- **core/**: Contains the core functionalities for analyzing and running tests.
- **testiterator/**: Houses the CLI, decorators, and build/upload scripts for handling tests.

## Features

- Command-line interface for executing tests
- Test decorators to simplify test invocation
- Modular design separating core functionalities from CLI operations

## Getting Started

1. Install the package using setup.py or pip.
2. Run the CLI (see documentation for usage details).
3. Explore and extend the core modules as needed.

## Contributing

Contributions are welcome! Please see the contributing guidelines for more details.

## License

This project is licensed under the terms specified in the LICENSE file.

# testiterator

[![PyPI version](https://badge.fury.io/py/testiterator.svg)](https://badge.fury.io/py/testiterator)
[![Python](https://img.shields.io/pypi/pyversions/testiterator.svg)](https://pypi.org/project/testiterator/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/testiterator)](https://pepy.tech/project/testiterator)

**testiterator** is an AI-powered testing framework that simplifies parameterized testing through elegant decorators. It automatically analyzes your code, generates comprehensive tests using AI, and executes parameterized tests with intelligent mocking.

## ✨ Features

- 🎯 **Decorator-Based Testing** - Simple `@testiterator` decorator for instant parameterized testing
- 🤖 **AI-Powered Test Generation** - Uses Google Gemini to generate comprehensive unittest suites
- 🔍 **Smart Code Analysis** - AST-based analysis to understand your code structure
- 🎭 **Automatic Mocking** - Intelligent mocking of external dependencies
- 📊 **Detailed Reports** - Comprehensive test execution reports with timing and results
- 🛠️ **CLI Interface** - Powerful command-line tools for analysis, generation, and execution
- 📝 **YAML Configuration** - Support for configuration files for complex test scenarios
- 🔄 **Template Fallback** - Works without AI when API is unavailable

## 📦 Installation
```bash
pip install testiterator
```

## 🚀 Quick Start

### 1. Get Your API Key

Get your free Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### 2. Set Environment Variable
```bash
export GEMINI_API_KEY='your_api_key_here'
```

**To make it permanent, add to your shell profile:**
```bash
# For bash (~/.bashrc or ~/.bash_profile)
echo "export GEMINI_API_KEY='your_api_key_here'" >> ~/.bashrc
source ~/.bashrc

# For zsh (~/.zshrc)
echo "export GEMINI_API_KEY='your_api_key_here'" >> ~/.zshrc
source ~/.zshrc
```

### 3. Use the Decorator
```python
from testiterator import testiterator

@testiterator('greeting', ["Hello", "Hi", "Hey"])
def greet(greeting, name="World"):
    return f"{greeting}, {name}!"

# The decorator automatically:
# ✓ Analyzes the function
# ✓ Generates AI-powered tests
# ✓ Runs parameterized tests with ["Hello", "Hi", "Hey"]
# ✓ Saves test file with timestamp
```

That's it! 🎉

## 📖 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
  - [Basic Parameterized Testing](#basic-parameterized-testing)
  - [Testing Functions with Dependencies](#testing-functions-with-dependencies)
  - [Advanced Configuration](#advanced-configuration)
  - [Testing with File Operations](#testing-with-file-operations)
- [CLI Usage](#-cli-usage)
- [API Reference](#-api-reference)
- [Generated Files](#-generated-files)
- [Configuration](#-configuration)
- [Advanced Use Cases](#-advanced-use-cases)
- [Contributing](#-contributing)
- [License](#-license)

## 💡 Usage Examples

### Basic Parameterized Testing
```python
from testiterator import testiterator

@testiterator('operation', ['add', 'subtract', 'multiply'])
def calculate(operation, a=10, b=5):
    """Perform calculation based on operation."""
    if operation == 'add':
        return a + b
    elif operation == 'subtract':
        return a - b
    elif operation == 'multiply':
        return a * b
    else:
        raise ValueError(f"Unknown operation: {operation}")
```

### Testing Functions with Dependencies
```python
from testiterator import testiterator

def add(a, b):
    """Helper function - will be tracked as dependency."""
    return a + b

@testiterator('n', [5, 7, 10])
def factorial(n):
    """Calculate factorial using the add function."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result = result * i
    return result

# testiterator will:
# ✓ Detect 'add' as a dependency
# ✓ Generate tests with proper mocking
# ✓ Test with values [5, 7, 10]
```

### Advanced Configuration
```python
@testiterator(
    'user_type',
    ['admin', 'user', 'guest'],
    generate_tests=True,      # Generate AI tests (default: True)
    save_results=True,        # Save results to file (default: True)
    mock_dependencies=True,   # Mock external calls (default: True)
    output_dir='./tests',     # Custom output directory
    model='gemini-2.5-flash'  # AI model to use
)
def process_user(user_type):
    return f"Processing {user_type}"
```

### Testing with File Operations

When you need to test functions that read from files (e.g., YAML configs):
```python
import yaml
from unittest.mock import patch, mock_open
from testiterator import testiterator

def load_config():
    """Load configuration from YAML file."""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def process_data(user_input):
    """Process data using config from file."""
    config = load_config()
    system_prompt = config['system_prompt']
    return f"[{system_prompt}] Processing: {user_input}"

# Test with different config values by mocking file reads
@testiterator('system_prompt', [
    "You are a helpful assistant.",
    "You are a technical expert.",
    "You are a creative writer."
])
def test_different_prompts(system_prompt):
    """Test with different system prompts by mocking YAML."""
    mock_yaml = f"system_prompt: {system_prompt}\ntemperature: 0.7"
    
    with patch('builtins.open', mock_open(read_data=mock_yaml)):
        result = process_data("What is Python?")
    
    return result
```

## 🖥️ CLI Usage

testiterator provides powerful CLI commands for code analysis and test generation.

### Analyze Code Structure
```bash
# Analyze entire file
testiterator analyze mycode.py

# Analyze specific function
testiterator analyze mycode.py --function my_function

# Save analysis to file
testiterator analyze mycode.py --function my_function --output analysis.json
```

**Example output:**
```json
{
  "function_name": "calculate",
  "parameters": [
    {"name": "operation", "annotation": null},
    {"name": "a", "annotation": null},
    {"name": "b", "annotation": null}
  ],
  "dependencies": ["add", "subtract"],
  "imports": [
    {"type": "import", "module": "math"}
  ]
}
```

### Generate AI Tests
```bash
# Basic generation
testiterator generate mycode.py --function calculate --params "1,2,3"

# With custom parameter name
testiterator generate mycode.py \
  --function calculate \
  --parameter value \
  --params "10,20,30"

# Specify output directory
testiterator generate mycode.py \
  --function process_data \
  --params "data1,data2,data3" \
  --output-dir ./tests
```

### Run Parameterized Tests
```bash
# Basic test run
testiterator run mycode.py \
  --function calculate \
  --parameter value \
  --params "1,2,3"

# With result saving
testiterator run mycode.py \
  --function fetch_data \
  --parameter url \
  --params "http://api1.com,http://api2.com" \
  --save-results \
  --format json

# Without mocking
testiterator run mycode.py \
  --function my_function \
  --parameter x \
  --params "1,2,3" \
  --no-mock
```

## 📚 API Reference

### Main Decorator
```python
@testiterator(
    parameter_name: str,
    parameter_values: List[Any],
    generate_tests: bool = True,
    save_results: bool = True,
    mock_dependencies: bool = True,
    output_dir: Optional[str] = None,
    model: str = "gemini-2.5-flash"
)
```

**Parameters:**
- `parameter_name` - Name of the parameter to iterate over
- `parameter_values` - List of values to test with
- `generate_tests` - Whether to generate AI-powered tests
- `save_results` - Whether to save test results to file
- `mock_dependencies` - Whether to mock external dependencies
- `output_dir` - Directory to save generated tests (default: current dir)
- `model` - AI model to use for test generation

### Core Classes

#### CodeAnalyzer

Analyzes Python code using AST:
```python
from testiterator import CodeAnalyzer

analyzer = CodeAnalyzer()
analysis = analyzer.analyze_code(code_content, target_function="my_func")
```

**Returns:**
```python
{
  "function_name": "my_func",
  "parameters": [...],
  "dependencies": [...],
  "imports": [...],
  "docstring": "...",
  "signature": "my_func(x: int) -> str"
}
```

#### TestWriter

Generates AI-powered tests:
```python
from testiterator import TestWriter

writer = TestWriter(model="gemini-2.5-flash", timeout=30)

# Check AI availability
if writer.check_llm_availability():
    tests = writer.generate_tests(
        analysis=analysis,
        parameter_name="value",
        parameter_values=[1, 2, 3],
        mock_dependencies=True
    )
    
    # Save tests
    output_path = writer.save_tests(
        function_name="my_func",
        tests_code=tests,
        original_code=source_code
    )
```

#### TestRunner

Executes parameterized tests:
```python
from testiterator import TestRunner

runner = TestRunner(mock_dependencies=True)

results = runner.run_parameterized_tests(
    func=my_function,
    parameter_name="value",
    parameter_values=[1, 2, 3],
    analysis=analysis
)

# Generate human-readable report
report = runner.generate_report(results)
print(report)
```

## 📁 Generated Files

testiterator generates comprehensive test files with timestamps:

### 1. Test File: `{function_name}_with_comprehensive_tests_{timestamp}.py`
```python
"""
Comprehensive tests for calculate
Generated by testiterator on 2024-10-16 14:30:00
"""

import unittest
from unittest.mock import Mock, patch, MagicMock


class TestCalculate(unittest.TestCase):
    """Test cases for calculate function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.operations = ['add', 'subtract', 'multiply']
    
    def test_calculate_with_different_operations(self):
        """Test calculate with different operation values."""
        test_cases = [
            ('add', 10, 5, 15),
            ('subtract', 10, 5, 5),
            ('multiply', 10, 5, 50),
        ]
        
        for operation, a, b, expected in test_cases:
            with self.subTest(operation=operation):
                result = calculate(operation, a, b)
                self.assertEqual(result, expected)
    
    def test_calculate_invalid_operation(self):
        """Test calculate with invalid operation."""
        with self.assertRaises(ValueError):
            calculate('divide', 10, 5)


if __name__ == "__main__":
    unittest.main()
```

### 2. Results File: `{function_name}_test_results_{timestamp}.json`
```json
{
  "function_name": "calculate",
  "parameter_name": "operation",
  "parameter_values": ["add", "subtract", "multiply"],
  "results": [
    {
      "test_index": 0,
      "parameter_value": "add",
      "status": "passed",
      "output": "15",
      "execution_time": 0.001,
      "mocked_dependencies": []
    }
  ],
  "summary": {
    "total_tests": 3,
    "passed": 3,
    "failed": 0,
    "success_rate": 100.0,
    "total_execution_time": 0.045,
    "average_execution_time": 0.015
  },
  "timestamp": "2024-10-16T14:30:00"
}
```

### 3. Execution Report (Console)
```
================================================================================
TEST EXECUTION REPORT
================================================================================

Function: calculate
Parameter: operation
Timestamp: 2024-10-16T14:30:00

SUMMARY:
--------
Total Tests: 3
Passed: 3 (100.0%)
Failed: 0
Total Time: 0.045s
Average Time: 0.015s

DETAILED RESULTS:
-----------------

✓ Test 0: operation=add
  Status: PASSED
  Time: 0.012s
  Output: 15

✓ Test 1: operation=subtract
  Status: PASSED
  Time: 0.015s
  Output: 5

✓ Test 2: operation=multiply
  Status: PASSED
  Time: 0.018s
  Output: 50

================================================================================
```

## ⚙️ Configuration

### YAML Configuration File

Create `testiterator.yaml` for complex test scenarios:
```yaml
# testiterator.yaml
parameters:
  user_type:
    values:
      - admin
      - user
      - guest
    mock_dependencies: true

  data_format:
    values:
      - json
      - csv
      - xml
    mock_dependencies: false

output:
  directory: ./test_results
  format: json
  save_results: true

ai:
  model: gemini-2.5-flash
  timeout: 30
```

Use with CLI:
```bash
testiterator run mycode.py \
  --function process_user \
  --parameter user_type \
  --params "admin,user,guest" \
  --config testiterator.yaml
```

### Environment Variables
```bash
# Required: Gemini API Key
export GEMINI_API_KEY='your_api_key_here'

# Optional: Default model
export TESTITERATOR_MODEL='gemini-2.5-flash'

# Optional: Default timeout
export TESTITERATOR_TIMEOUT=30
```

## 🎯 Advanced Use Cases

### 1. Testing API Endpoints
```python
import requests
from testiterator import testiterator

@testiterator(
    'endpoint',
    ['/users', '/posts', '/comments'],
    mock_dependencies=True  # Mocks requests.get
)
def fetch_api_data(endpoint):
    """Fetch data from API endpoint."""
    response = requests.get(f"https://api.example.com{endpoint}")
    return response.json()
```

### 2. Testing Data Processing Pipelines
```python
@testiterator(
    'data_format',
    ['json', 'csv', 'xml', 'parquet'],
    save_results=True,
    output_dir='./pipeline_tests'
)
def process_data(data_format, data_content="sample"):
    """Process data based on format."""
    parsers = {
        'json': parse_json,
        'csv': parse_csv,
        'xml': parse_xml,
        'parquet': parse_parquet
    }
    
    if data_format not in parsers:
        raise ValueError(f"Unsupported format: {data_format}")
    
    return parsers[data_format](data_content)
```

### 3. Testing LLM System Prompts
```python
from unittest.mock import patch, mock_open

def load_system_prompt():
    """Load system prompt from config."""
    with open('llm_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    return config['system_prompt']

@testiterator('system_prompt', [
    "You are a helpful assistant.",
    "You are a technical expert.",
    "You are a creative writer.",
    "You are a code reviewer."
])
def test_llm_prompts(system_prompt):
    """Test LLM with different system prompts."""
    mock_yaml = f"system_prompt: {system_prompt}\ntemperature: 0.7"
    
    with patch('builtins.open', mock_open(read_data=mock_yaml)):
        prompt = load_system_prompt()
        result = call_llm(prompt, "Explain recursion")
    
    return result
```

### 4. Testing with Edge Cases
```python
@testiterator(
    'value',
    [
        0,              # Zero
        -1,             # Negative
        999999999,      # Large number
        None,           # None value
        "",             # Empty string
        "invalid"       # Invalid type
    ],
    generate_tests=True
)
def validate_input(value):
    """Validate and process input with comprehensive edge case testing."""
    if value is None:
        raise ValueError("Value cannot be None")
    
    if not isinstance(value, (int, float)):
        raise TypeError(f"Expected number, got {type(value)}")
    
    if value < 0:
        raise ValueError("Value must be non-negative")
    
    return value * 2
```

### 5. Testing Async Functions
```python
import asyncio
from testiterator import testiterator

@testiterator('delay', [0.1, 0.5, 1.0])
async def async_operation(delay):
    """Test async function with different delays."""
    await asyncio.sleep(delay)
    return f"Completed after {delay}s"

# Run async tests
if __name__ == "__main__":
    asyncio.run(async_operation(0.1))
```

## 🔧 Development

### Setting Up Development Environment
```bash
# Clone repository
git clone https://github.com/yourusername/testiterator.git
cd testiterator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=testiterator --cov-report=html

# Run specific test file
pytest tests/test_decorator.py -v
```

### Code Quality
```bash
# Format code with black
black testiterator/

# Lint with flake8
flake8 testiterator/

# Type checking with mypy
mypy testiterator/

# Sort imports
isort testiterator/
```

### Building and Testing Package
```bash
# Validate package structure
python check_package.py

# Build package
python build_and_upload.py --check-only

# Test on TestPyPI
python build_and_upload.py --test

# Upload to PyPI
python build_and_upload.py
```

## 📊 Architecture
```
┌──────────────────────────────────────────────────────────┐
│                    @testiterator                         │
│                     (Decorator)                          │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
      ┌──────────────────────┐
      │   Code Analyzer      │ ──► AST Analysis
      │  (analyzer.py)       │     Extract metadata
      └──────────┬───────────┘     Find dependencies
                 │
                 ▼
      ┌──────────────────────┐
      │   Test Writer        │ ──► Generate tests with AI
      │  (test_writer.py)    │     Create mocks
      └──────────┬───────────┘     Save to file
                 │
                 ▼
      ┌──────────────────────┐
      │   Test Runner        │ ──► Execute tests
      │   (runner.py)        │     Apply mocks
      └──────────────────────┘     Generate reports
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Run tests** (`pytest tests/`)
5. **Commit your changes** (`git commit -m 'Add amazing feature'`)
6. **Push to the branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Contribution Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Keep commits atomic and well-described
- Ensure all tests pass before submitting PR

## 🗺️ Roadmap

- [ ] Support for more AI models (Claude, GPT-4, Ollama)
- [ ] pytest plugin integration
- [ ] Visual test coverage dashboard
- [ ] Database query mocking
- [ ] Performance benchmarking tools
- [ ] Web UI for test management
- [ ] CI/CD pipeline integration templates
- [ ] Multi-language support
- [ ] Integration with popular IDEs

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed version history.

## ❓ FAQ

**Q: Do I need an API key to use testiterator?**  
A: The AI-powered test generation requires a Gemini API key (free). However, testiterator will fall back to template-based generation if no API key is provided.

**Q: Can I use testiterator with pytest?**  
A: Yes! The generated tests are standard unittest tests that work with pytest. We're also working on native pytest plugin support.

**Q: How does dependency mocking work?**  
A: testiterator uses AST analysis to detect function dependencies and automatically creates mocks using `unittest.mock`. You can control this with the `mock_dependencies` parameter.

**Q: Can I customize the AI model?**  
A: Currently, testiterator supports Gemini 2.5 Flash. Support for more models (Claude, GPT-4, Ollama) is planned.

**Q: Is my code sent to external servers?**  
A: Only function signatures and metadata are sent to Gemini for test generation. Your actual implementation code stays local unless you explicitly include it.

**Q: How do I test functions that read from files?**  
A: Use `unittest.mock.patch` to mock file operations. See the [Testing with File Operations](#testing-with-file-operations) section.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Google Gemini](https://deepmind.google/technologies/gemini/)
- Inspired by pytest and unittest frameworks
- Thanks to all contributors and users

## 📞 Support

- 📧 Email: support@example.com
- 💬 Discord: [Join our community](https://discord.gg/testiterator)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/testiterator/issues)
- 📖 Documentation: [Full Documentation](https://testiterator.readthedocs.io)
- ⭐ Star us on [GitHub](https://github.com/yourusername/testiterator)

## 🌟 Show Your Support

If you find testiterator helpful, please consider:

- ⭐ Starring the repository
- 🐦 Sharing on social media
- 📝 Writing a blog post about your experience
- 💡 Contributing new features or fixes

---

**Made with ❤️ by the testiterator team**