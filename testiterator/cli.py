"""
Command-line interface for testiterator.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from .core.analyzer import CodeAnalyzer
from .core.test_writer import TestWriter
from .core.runner import TestRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_command(args):
    """Handle 'analyze' command."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        analyzer = CodeAnalyzer()
        
        if args.function:
            analysis = analyzer.analyze_code(code_content, args.function)
            logger.info(f"Analysis for function: {args.function}")
        else:
            analysis = analyzer.analyze_code(code_content)
            logger.info(f"Full file analysis: {file_path}")
        
        # Pretty print analysis
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, default=str)
            logger.info(f"Analysis saved to: {output_path}")
        else:
            print("\n" + "="*80)
            print("CODE ANALYSIS RESULTS")
            print("="*80)
            print(json.dumps(analysis, indent=2, default=str))
            print("="*80)
        
    except Exception as e:
        logger.error(f"Error analyzing code: {e}")
        sys.exit(1)


def generate_command(args):
    """Handle 'generate' command."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        # Analyze code first
        analyzer = CodeAnalyzer()
        
        if args.function:
            analysis = analyzer.analyze_code(code_content, args.function)
        else:
            logger.error("--function parameter is required for generate command")
            sys.exit(1)
        
        # Generate tests
        test_writer = TestWriter(model=args.model, timeout=args.timeout)
        
        # Parse parameter values
        param_values = args.params.split(',') if args.params else []
        
        # Check AI availability
        if test_writer.check_llm_availability():
            logger.info("Generating AI-powered tests...")
            tests_code = test_writer.generate_tests(
                analysis=analysis,
                parameter_name=args.parameter or "value",
                parameter_values=param_values,
                mock_dependencies=args.mock
            )
        else:
            logger.warning("AI unavailable, using template generation...")
            tests_code = test_writer.generate_template_tests(
                analysis=analysis,
                parameter_name=args.parameter or "value",
                parameter_values=param_values
            )
        
        if tests_code:
            output_path = test_writer.save_tests(
                function_name=args.function,
                tests_code=tests_code,
                original_code=code_content,
                output_dir=args.output_dir
            )
            print(f"\n✓ Tests generated successfully: {output_path}")
        else:
            logger.error("Failed to generate tests")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error generating tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_command(args):
    """Handle 'run' command."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    try:
        # Import the module dynamically
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the function
        if not hasattr(module, args.function):
            logger.error(f"Function '{args.function}' not found in {file_path}")
            sys.exit(1)
        
        func = getattr(module, args.function)
        
        # Parse parameter values
        param_values = args.params.split(',') if args.params else []
        
        # Parse values based on type
        parsed_values = []
        for val in param_values:
            val = val.strip()
            # Try to evaluate as Python literal
            try:
                parsed_values.append(eval(val))
            except:
                # Keep as string if can't evaluate
                parsed_values.append(val)
        
        # Analyze code
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        analyzer = CodeAnalyzer()
        analysis = analyzer.analyze_code(code_content, args.function)
        
        # Run tests
        runner = TestRunner(mock_dependencies=args.mock)
        
        # Load config if provided
        config = None
        if args.config:
            config = runner.load_config(args.config)
        
        results = runner.run_parameterized_tests(
            func=func,
            parameter_name=args.parameter or "value",
            parameter_values=parsed_values,
            analysis=analysis,
            config=config
        )
        
        # Display report
        report = runner.generate_report(results)
        print(report)
        
        # Save results if requested
        if args.save_results:
            output_path = runner.save_results(
                results=results,
                function_name=args.function,
                output_dir=args.output_dir,
                format=args.format
            )
            print(f"Results saved to: {output_path}")
        
        # Exit with error code if tests failed
        if results["summary"]["failed"] > 0:
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="testiterator - AI-Powered Testing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze code structure
  testiterator analyze mycode.py --function my_function
  
  # Generate AI tests
  testiterator generate mycode.py --function my_function --params "1,2,3"
  
  # Run parameterized tests
  testiterator run mycode.py --function my_function --parameter value --params "a,b,c"
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='testiterator 1.0.0'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze code structure and dependencies'
    )
    analyze_parser.add_argument('file', help='Python file to analyze')
    analyze_parser.add_argument(
        '--function',
        '-f',
        help='Specific function to analyze'
    )
    analyze_parser.add_argument(
        '--output',
        '-o',
        help='Output file for analysis results (JSON)'
    )
    
    # Generate command
    generate_parser = subparsers.add_parser(
        'generate',
        help='Generate AI-powered tests'
    )
    generate_parser.add_argument('file', help='Python file containing function')
    generate_parser.add_argument(
        '--function',
        '-f',
        required=True,
        help='Function name to generate tests for'
    )
    generate_parser.add_argument(
        '--model',
        '-m',
        default='gemini-2.5-flash',
        help='AI model to use (default: gemini-2.5-flash)'
    )
    generate_parser.add_argument(
        '--parameter',
        '-p',
        help='Parameter name for parameterized tests'
    )
    generate_parser.add_argument(
        '--params',
        help='Comma-separated parameter values (e.g., "1,2,3")'
    )
    generate_parser.add_argument(
        '--mock',
        action='store_true',
        default=True,
        help='Mock external dependencies (default: True)'
    )
    generate_parser.add_argument(
        '--no-mock',
        dest='mock',
        action='store_false',
        help='Do not mock dependencies'
    )
    generate_parser.add_argument(
        '--output-dir',
        '-d',
        help='Output directory for generated tests'
    )
    generate_parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='API timeout in seconds (default: 30)'
    )
    
    # Run command
    run_parser = subparsers.add_parser(
        'run',
        help='Run parameterized tests'
    )
    run_parser.add_argument('file', help='Python file containing function')
    run_parser.add_argument(
        '--function',
        '-f',
        required=True,
        help='Function name to test'
    )
    run_parser.add_argument(
        '--parameter',
        '-p',
        required=True,
        help='Parameter name to vary'
    )
    run_parser.add_argument(
        '--params',
        required=True,
        help='Comma-separated parameter values'
    )
    run_parser.add_argument(
        '--mock',
        action='store_true',
        default=True,
        help='Mock external dependencies (default: True)'
    )
    run_parser.add_argument(
        '--no-mock',
        dest='mock',
        action='store_false',
        help='Do not mock dependencies'
    )
    run_parser.add_argument(
        '--config',
        '-c',
        help='YAML configuration file'
    )
    run_parser.add_argument(
        '--save-results',
        '-s',
        action='store_true',
        help='Save test results to file'
    )
    run_parser.add_argument(
        '--output-dir',
        '-d',
        help='Output directory for results'
    )
    run_parser.add_argument(
        '--format',
        choices=['json', 'yaml'],
        default='json',
        help='Output format for results (default: json)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == 'analyze':
        analyze_command(args)
    elif args.command == 'generate':
        generate_command(args)
    elif args.command == 'run':
        run_command(args)


if __name__ == '__main__':
    main()