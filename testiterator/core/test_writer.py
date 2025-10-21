"""
AI-powered test generation using Gemini API.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class TestWriter:
    """
    Generates comprehensive unittest.TestCase classes with AI assistance.
    """
    
    def __init__(self, model: str = "gemini-2.5-flash", timeout: int = 30):
        """
        Initialize TestWriter.
        
        Args:
            model: AI model to use (currently supports gemini-2.5-flash)
            timeout: Timeout for API requests in seconds
        """
        self.model = model
        self.timeout = timeout
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
    
    def check_llm_availability(self) -> bool:
        """
        Check if Gemini API is available and accessible.
        
        Returns:
            True if API is available, False otherwise
        """
        if not self.api_key:
            logger.warning("No API key configured")
            return False
        
        try:
            # Try a simple request to check connectivity
            url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{
                    "parts": [{"text": "test"}]
                }]
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=5
            )
            
            return response.status_code == 200
            
        except requests.exceptions.Timeout:
            logger.warning("API request timed out")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning("Could not connect to API")
            return False
        except Exception as e:
            logger.warning(f"Error checking API availability: {e}")
            return False
    
    def generate_tests(
        self,
        analysis: Dict[str, Any],
        parameter_name: str,
        parameter_values: List[Any],
        mock_dependencies: bool = True
    ) -> Optional[str]:
        """
        Generate comprehensive unittest tests using AI.
        
        Args:
            analysis: Code analysis dictionary from CodeAnalyzer
            parameter_name: Parameter name for parameterized tests
            parameter_values: List of parameter values
            mock_dependencies: Whether to generate mocks for dependencies
        
        Returns:
            Generated test code as string, or None if generation fails
        """
        if not self.api_key:
            logger.error("Cannot generate tests: No API key configured")
            return None
        
        try:
            prompt = self._create_prompt(
                analysis, parameter_name, parameter_values, mock_dependencies
            )
            
            logger.info(f"Generating tests using {self.model}...")
            
            url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 8192,
                }
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "candidates" in result and len(result["candidates"]) > 0:
                    generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # Extract Python code from markdown if present
                    tests_code = self._extract_code(generated_text)
                    
                    # Validate the generated code
                    if self._validate_test_code(tests_code):
                        logger.info("Successfully generated tests")
                        return tests_code
                    else:
                        logger.warning("Generated code failed validation")
                        return None
                else:
                    logger.error("No candidates in API response")
                    return None
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("API request timed out")
            return None
        except Exception as e:
            logger.error(f"Error generating tests: {e}")
            return None
    
    def generate_template_tests(
        self,
        analysis: Dict[str, Any],
        parameter_name: str,
        parameter_values: List[Any]
    ) -> str:
        """
        Generate template-based tests as fallback when AI is unavailable.
        
        Args:
            analysis: Code analysis dictionary
            parameter_name: Parameter name
            parameter_values: Parameter values
        
        Returns:
            Template test code as string
        """
        function_name = analysis.get("function_name", "unknown")
        params = analysis.get("parameters", [])
        
        # Create parameter list for function call
        param_names = [p["name"] for p in params]
        
        template = f'''"""
Generated tests for {function_name}
Auto-generated by testiterator (template mode)
"""

import unittest
from unittest.mock import Mock, patch, MagicMock


class Test{function_name.title().replace("_", "")}(unittest.TestCase):
    """Test cases for {function_name} function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_values = {parameter_values}
    
    def test_{function_name}_with_different_parameters(self):
        """Test {function_name} with different parameter values."""
        for value in self.test_values:
            with self.subTest({parameter_name}=value):
                # TODO: Add assertions based on expected behavior
                # result = {function_name}({parameter_name}=value)
                # self.assertIsNotNone(result)
                pass
    
    def test_{function_name}_type_validation(self):
        """Test type validation for {function_name}."""
        # TODO: Add type validation tests
        pass
    
    def test_{function_name}_edge_cases(self):
        """Test edge cases for {function_name}."""
        # TODO: Add edge case tests
        pass


if __name__ == "__main__":
    unittest.main()
'''
        return template
    
    def _create_prompt(
        self,
        analysis: Dict[str, Any],
        parameter_name: str,
        parameter_values: List[Any],
        mock_dependencies: bool
    ) -> str:
        """Create structured prompt for AI test generation."""
        
        function_name = analysis.get("function_name", "unknown")
        signature = analysis.get("signature", "")
        docstring = analysis.get("docstring", "")
        dependencies = analysis.get("direct_dependencies", [])
        imports = analysis.get("imports", [])
        
        prompt = f"""You are an expert Python test engineer. Generate comprehensive unittest.TestCase tests for the following function.

FUNCTION TO TEST:
```python
{signature}
'''
{docstring}
'''
```

FUNCTION ANALYSIS:
- Parameter to test: {parameter_name}
- Test values: {parameter_values}
- Dependencies: {dependencies}
- Required imports: {[imp['statement'] for imp in imports]}

REQUIREMENTS:
1. Create a complete unittest.TestCase class
2. Include parameterized tests for all values in {parameter_values}
3. {"Mock all external dependencies using unittest.mock" if mock_dependencies else "Do not mock dependencies"}
4. Test edge cases, error conditions, and normal operations
5. Use descriptive test method names
6. Include docstrings for all test methods
7. Add setUp and tearDown methods if needed
8. Use self.subTest() for parameterized iterations

OUTPUT FORMAT:
Provide ONLY valid Python code (no explanations). Include all necessary imports.
Start with imports, then the test class, then if __name__ == "__main__": unittest.main()

Generate the complete test code now:
"""
        return prompt
    
    def _extract_code(self, text: str) -> str:
        """Extract Python code from markdown-formatted text."""
        # Try to find code within markdown code blocks
        code_block_pattern = r'```python\n(.*?)\n```'
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        
        if matches:
            return matches[0]
        
        # If no markdown blocks, try to find code without markers
        code_block_pattern = r'```(.*?)```'
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        
        if matches:
            return matches[0]
        
        # Return as-is if no code blocks found
        return text
    
    def _validate_test_code(self, code: str) -> bool:
        """Validate that generated code is syntactically correct."""
        try:
            compile(code, '<string>', 'exec')
            
            # Check for basic test requirements
            required_elements = [
                'import unittest',
                'class Test',
                'unittest.TestCase',
                'def test_'
            ]
            
            for element in required_elements:
                if element not in code:
                    logger.warning(f"Generated code missing required element: {element}")
                    return False
            
            return True
            
        except SyntaxError as e:
            logger.error(f"Generated code has syntax error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating code: {e}")
            return False
    
    def save_tests(
        self,
        function_name: str,
        tests_code: str,
        original_code: str,
        output_dir: Optional[str] = None
    ) -> Path:
        """
        Save generated tests to a timestamped file.
        
        Args:
            function_name: Name of the tested function
            tests_code: Generated test code
            original_code: Original source code
            output_dir: Directory to save file (default: current directory)
        
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{function_name}_with_comprehensive_tests_{timestamp}.py"
        
        if output_dir:
            output_path = Path(output_dir) / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path = Path(filename)
        
        # Create complete file with header, original code comment, and tests
        complete_code = f'''"""
Comprehensive tests for {function_name}
Generated by testiterator on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This file contains:
1. Generated unittest tests
2. Original source code (commented at bottom)
"""

{tests_code}


"""
ORIGINAL SOURCE CODE:
{'='*80}

{original_code}

{'='*80}
"""
'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(complete_code)
        
        logger.info(f"Saved tests to {output_path}")
        return output_path