"""
AST-based code analysis for extracting function dependencies and metadata.
"""

import ast
import inspect
import logging
from typing import Dict, List, Any, Optional, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """
    Analyzes Python code using AST to extract dependencies, imports, and metadata.
    """
    
    def __init__(self):
        self.imports = []
        self.functions = {}
        self.classes = {}
        self.dependencies = {}
    
    def analyze_code(self, code_content: str, target_function: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze Python code and extract comprehensive information.
        
        Args:
            code_content: Python source code as string
            target_function: Specific function to analyze (optional)
        
        Returns:
            Dictionary containing analysis results
        """
        try:
            tree = ast.parse(code_content)
            
            # Extract imports
            self.imports = self._extract_imports(tree)
            
            # Extract all functions and classes
            self._extract_definitions(tree)
            
            # Analyze dependencies
            self._analyze_dependencies(tree)
            
            # If target function specified, focus on it
            if target_function and target_function in self.functions:
                return self._create_function_analysis(target_function, code_content)
            
            # Otherwise return general analysis
            return self._create_general_analysis(code_content)
            
        except SyntaxError as e:
            logger.error(f"Syntax error in code: {e}")
            return self._create_error_analysis(code_content, str(e))
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return self._create_error_analysis(code_content, str(e))
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract all import statements from AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "type": "import",
                        "module": alias.name,
                        "alias": alias.asname,
                        "statement": f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append({
                        "type": "from_import",
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "statement": f"from {module} import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")
                    })
        
        return imports
    
    def _extract_definitions(self, tree: ast.AST) -> None:
        """Extract function and class definitions."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = self._analyze_function(node)
                self.functions[node.name] = func_info
            elif isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node)
                self.classes[node.name] = class_info
    
    def _analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze a function definition node."""
        # Extract parameters
        params = []
        for arg in node.args.args:
            param_info = {
                "name": arg.arg,
                "annotation": ast.unparse(arg.annotation) if arg.annotation else None
            }
            params.append(param_info)
        
        # Extract return type
        return_type = ast.unparse(node.returns) if node.returns else None
        
        # Extract docstring
        docstring = ast.get_docstring(node)
        
        # Extract decorators
        decorators = [ast.unparse(dec) for dec in node.decorator_list]
        
        # Find function calls within this function
        calls = self._extract_function_calls(node)
        
        return {
            "name": node.name,
            "parameters": params,
            "return_type": return_type,
            "docstring": docstring,
            "decorators": decorators,
            "calls": calls,
            "lineno": node.lineno,
            "is_async": isinstance(node, ast.AsyncFunctionDef)
        }
    
    def _analyze_class(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Analyze a class definition node."""
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
        
        return {
            "name": node.name,
            "bases": [ast.unparse(base) for base in node.bases],
            "methods": methods,
            "docstring": ast.get_docstring(node),
            "lineno": node.lineno
        }
    
    def _extract_function_calls(self, node: ast.AST) -> List[str]:
        """Extract all function calls within a node."""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(ast.unparse(child.func))
        return list(set(calls))  # Remove duplicates
    
    def _analyze_dependencies(self, tree: ast.AST) -> None:
        """Analyze inter-function dependencies."""
        for func_name, func_info in self.functions.items():
            deps = set()
            for call in func_info["calls"]:
                # Check if call is to another function in the same file
                call_base = call.split('.')[0]
                if call_base in self.functions:
                    deps.add(call_base)
            self.dependencies[func_name] = list(deps)
    
    def _create_function_analysis(self, function_name: str, code_content: str) -> Dict[str, Any]:
        """Create detailed analysis for a specific function."""
        func_info = self.functions[function_name]
        
        # Find dependencies (both direct and transitive)
        all_deps = self._find_all_dependencies(function_name)
        
        return {
            "function_name": function_name,
            "signature": self._create_signature(func_info),
            "parameters": func_info["parameters"],
            "return_type": func_info["return_type"],
            "docstring": func_info["docstring"],
            "decorators": func_info["decorators"],
            "direct_dependencies": self.dependencies.get(function_name, []),
            "all_dependencies": all_deps,
            "imports": self.imports,
            "source_code": code_content,
            "is_async": func_info["is_async"],
            "related_functions": {name: info for name, info in self.functions.items() if name in all_deps},
            "related_classes": self.classes
        }
    
    def _create_general_analysis(self, code_content: str) -> Dict[str, Any]:
        """Create general code analysis."""
        return {
            "imports": self.imports,
            "functions": self.functions,
            "classes": self.classes,
            "dependencies": self.dependencies,
            "source_code": code_content
        }
    
    def _create_error_analysis(self, code_content: str, error: str) -> Dict[str, Any]:
        """Create minimal analysis when parsing fails."""
        return {
            "error": error,
            "source_code": code_content,
            "imports": [],
            "functions": {},
            "classes": {},
            "dependencies": {}
        }
    
    def _find_all_dependencies(self, function_name: str, visited: Optional[Set[str]] = None) -> List[str]:
        """Find all dependencies recursively."""
        if visited is None:
            visited = set()
        
        if function_name in visited:
            return []
        
        visited.add(function_name)
        deps = []
        
        for dep in self.dependencies.get(function_name, []):
            deps.append(dep)
            deps.extend(self._find_all_dependencies(dep, visited))
        
        return list(set(deps))
    
    def _create_signature(self, func_info: Dict[str, Any]) -> str:
        """Create function signature string."""
        params = []
        for param in func_info["parameters"]:
            param_str = param["name"]
            if param["annotation"]:
                param_str += f": {param['annotation']}"
            params.append(param_str)
        
        signature = f"{func_info['name']}({', '.join(params)})"
        if func_info["return_type"]:
            signature += f" -> {func_info['return_type']}"
        
        return signature