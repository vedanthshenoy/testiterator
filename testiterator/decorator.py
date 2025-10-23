"""
Core decorator functionality for testiterator.
"""

import functools
import inspect
import logging
from typing import Any, Callable, List, Optional, Dict
from pathlib import Path

from .core.analyzer import CodeAnalyzer
from .core.test_writer import TestWriter
from .core.runner import TestRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def testiterator(
    parameter_name: str,
    parameter_values: List[Any],
    generate_tests: bool = True,
    save_results: bool = True,
    mock_dependencies: bool = True,
    output_dir: Optional[str] = None,
    model: str = "gemini-2.5-flash",
    **options
) -> Callable:
    """
    Decorator for AI-powered parameterized testing.
    
    Args:
        parameter_name: Name of the parameter to iterate over
        parameter_values: List of values to test with
        generate_tests: Whether to generate AI-powered tests
        save_results: Whether to save test results to file
        mock_dependencies: Whether to mock external dependencies
        output_dir: Directory to save generated tests (default: current dir)
        model: AI model to use for test generation
        **options: Additional options for customization
    
    Usage:
        @testiterator('greeting', ["Hello", "Hi", "Hey"])
        def greet(greeting, name):
            return f"{greeting}, {name}!"
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Call the original function normally
            return func(*args, **kwargs)
        
        # Perform test generation and execution
        try:
            _process_function(
                func=func,
                parameter_name=parameter_name,
                parameter_values=parameter_values,
                generate_tests=generate_tests,
                save_results=save_results,
                mock_dependencies=mock_dependencies,
                output_dir=output_dir,
                model=model,
                options=options
            )
        except Exception as e:
            logger.error(f"Error processing function {func.__name__}: {e}")
            # Don't break the decorator - return original function
        
        return wrapper
    
    return decorator


def _process_function(
    func: Callable,
    parameter_name: str,
    parameter_values: List[Any],
    generate_tests: bool,
    save_results: bool,
    mock_dependencies: bool,
    output_dir: Optional[str],
    model: str,
    options: Dict[str, Any]
) -> None:
    """
    Process function through analyzer -> test_writer -> runner workflow.
    
    Args:
        func: Function to process
        parameter_name: Parameter name for parameterized testing
        parameter_values: List of parameter values
        generate_tests: Whether to generate tests
        save_results: Whether to save results
        mock_dependencies: Whether to mock dependencies
        output_dir: Output directory for generated files
        model: AI model name
        options: Additional options
    """
    logger.info(f"Processing function: {func.__name__}")
    
    # Step 1: Analyze the function
    try:
        source_code = inspect.getsource(func)
        source_file = inspect.getfile(func)
        
        # Read the entire file for better context
        with open(source_file, 'r') as f:
            file_content = f.read()
        
        analyzer = CodeAnalyzer()
        analysis = analyzer.analyze_code(file_content, func.__name__)
        
        logger.info(f"Code analysis completed for {func.__name__}")
        logger.debug(f"Analysis: {analysis}")
        
    except Exception as e:
        logger.error(f"Failed to analyze function: {e}")
        analysis = {
            "function_name": func.__name__,
            "source_code": str(func),
            "dependencies": [],
            "imports": []
        }
    
    # Step 2: Generate AI-powered tests
    if generate_tests:
        try:
            test_writer = TestWriter(model=model)
            
            # Check if AI is available
            if test_writer.check_llm_availability():
                logger.info("AI service available, generating tests...")
                generated_tests = test_writer.generate_tests(
                    analysis=analysis,
                    parameter_name=parameter_name,
                    parameter_values=parameter_values,
                    mock_dependencies=mock_dependencies
                )
                
                if save_results and generated_tests:
                    output_path = test_writer.save_tests(
                        function_name=func.__name__,
                        tests_code=generated_tests,
                        original_code=file_content,
                        output_dir=output_dir
                    )
                    logger.info(f"Tests saved to: {output_path}")
            else:
                logger.warning("AI service unavailable, using template-based generation")
                generated_tests = test_writer.generate_template_tests(
                    analysis=analysis,
                    parameter_name=parameter_name,
                    parameter_values=parameter_values
                )
                
                if save_results and generated_tests:
                    output_path = test_writer.save_tests(
                        function_name=func.__name__,
                        tests_code=generated_tests,
                        original_code=file_content,
                        output_dir=output_dir
                    )
                    logger.info(f"Template tests saved to: {output_path}")
                    
        except Exception as e:
            logger.error(f"Failed to generate tests: {e}")
    
    # Step 3: Run parameterized tests
    try:
        runner = TestRunner(mock_dependencies=mock_dependencies)
        results = runner.run_parameterized_tests(
            func=func,
            parameter_name=parameter_name,
            parameter_values=parameter_values,
            analysis=analysis
        )
        
        logger.info(f"Test execution completed: {results['summary']}")
        
        if save_results:
            runner.save_results(
                results=results,
                function_name=func.__name__,
                output_dir=output_dir
            )
            
    except Exception as e:
        logger.error(f"Failed to run tests: {e}")