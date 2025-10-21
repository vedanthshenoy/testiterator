"""
Test runner for parameterized test execution with mocking support.
"""

import json
import logging
import time
import traceback
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import Mock, patch, MagicMock

logger = logging.getLogger(__name__)


class TestRunner:
    """
    Executes parameterized tests with mocking support and detailed reporting.
    """
    
    def __init__(self, mock_dependencies: bool = True):
        """
        Initialize TestRunner.
        
        Args:
            mock_dependencies: Whether to mock external dependencies
        """
        self.mock_dependencies = mock_dependencies
        self.results = []
    
    def run_parameterized_tests(
        self,
        func: Callable,
        parameter_name: str,
        parameter_values: List[Any],
        analysis: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run parameterized tests for a function.
        
        Args:
            func: Function to test
            parameter_name: Name of parameter to vary
            parameter_values: List of values to test
            analysis: Code analysis from CodeAnalyzer
            config: Optional configuration dictionary
        
        Returns:
            Dictionary with test results and summary
        """
        logger.info(f"Running parameterized tests for {func.__name__}")
        
        self.results = []
        start_time = time.time()
        
        # Get dependencies to mock
        dependencies = analysis.get("direct_dependencies", [])
        
        for idx, value in enumerate(parameter_values):
            result = self._run_single_test(
                func=func,
                parameter_name=parameter_name,
                parameter_value=value,
                test_index=idx,
                dependencies=dependencies,
                config=config
            )
            self.results.append(result)
        
        end_time = time.time()
        
        # Generate summary
        summary = self._generate_summary(start_time, end_time)
        
        return {
            "function_name": func.__name__,
            "parameter_name": parameter_name,
            "parameter_values": parameter_values,
            "results": self.results,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
    
    def _run_single_test(
        self,
        func: Callable,
        parameter_name: str,
        parameter_value: Any,
        test_index: int,
        dependencies: List[str],
        config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run a single parameterized test."""
        test_result = {
            "test_index": test_index,
            "parameter_value": parameter_value,
            "status": "pending",
            "error": None,
            "output": None,
            "execution_time": 0,
            "mocked_dependencies": []
        }
        
        start_time = time.time()
        
        try:
            # Create mocks if enabled
            mocks = {}
            if self.mock_dependencies and dependencies:
                mocks = self._create_mocks(dependencies)
                test_result["mocked_dependencies"] = list(mocks.keys())
            
            # Execute function with parameter
            kwargs = {parameter_name: parameter_value}
            
            if mocks:
                # Use patch context for mocks
                with patch.multiple(func.__module__, **mocks):
                    output = func(**kwargs)
            else:
                output = func(**kwargs)
            
            test_result["output"] = str(output)
            test_result["status"] = "passed"
            
            logger.info(f"Test {test_index} passed: {parameter_name}={parameter_value}")
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            test_result["traceback"] = traceback.format_exc()
            
            logger.error(f"Test {test_index} failed: {parameter_name}={parameter_value} - {e}")
        
        finally:
            test_result["execution_time"] = time.time() - start_time
        
        return test_result
    
    def _create_mocks(self, dependencies: List[str]) -> Dict[str, Mock]:
        """Create mock objects for dependencies."""
        mocks = {}
        for dep in dependencies:
            mocks[dep] = MagicMock(name=f"Mock_{dep}")
        return mocks
    
    def _generate_summary(self, start_time: float, end_time: float) -> Dict[str, Any]:
        """Generate test execution summary."""
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(1 for r in self.results if r["status"] == "failed")
        
        return {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
            "total_execution_time": end_time - start_time,
            "average_execution_time": (end_time - start_time) / total_tests if total_tests > 0 else 0
        }
    
    def save_results(
        self,
        results: Dict[str, Any],
        function_name: str,
        output_dir: Optional[str] = None,
        format: str = "json"
    ) -> Path:
        """
        Save test results to file.
        
        Args:
            results: Test results dictionary
            function_name: Name of tested function
            output_dir: Output directory
            format: Output format ('json' or 'yaml')
        
        Returns:
            Path to saved results file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{function_name}_test_results_{timestamp}.{format}"
        
        if output_dir:
            output_path = Path(output_dir) / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path = Path(filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if format == "json":
                json.dump(results, f, indent=2, default=str)
            elif format == "yaml":
                yaml.dump(results, f, default_flow_style=False)
        
        logger.info(f"Saved test results to {output_path}")
        return output_path
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load test configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
        
        Returns:
            Configuration dictionary
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Loaded configuration from {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """
        Generate human-readable test report.
        
        Args:
            results: Test results dictionary
        
        Returns:
            Formatted report string
        """
        summary = results["summary"]
        
        report = f"""
{'='*80}
TEST EXECUTION REPORT
{'='*80}

Function: {results['function_name']}
Parameter: {results['parameter_name']}
Timestamp: {results['timestamp']}

SUMMARY:
--------
Total Tests: {summary['total_tests']}
Passed: {summary['passed']} ({summary['success_rate']:.1f}%)
Failed: {summary['failed']}
Total Time: {summary['total_execution_time']:.3f}s
Average Time: {summary['average_execution_time']:.3f}s

DETAILED RESULTS:
-----------------
"""
        
        for result in results["results"]:
            status_icon = "✓" if result["status"] == "passed" else "✗"
            report += f"\n{status_icon} Test {result['test_index']}: "
            report += f"{results['parameter_name']}={result['parameter_value']}\n"
            report += f"  Status: {result['status'].upper()}\n"
            report += f"  Time: {result['execution_time']:.3f}s\n"
            
            if result["mocked_dependencies"]:
                report += f"  Mocks: {', '.join(result['mocked_dependencies'])}\n"
            
            if result["status"] == "passed":
                report += f"  Output: {result['output']}\n"
            else:
                report += f"  Error: {result['error']}\n"
        
        report += f"\n{'='*80}\n"
        
        return report