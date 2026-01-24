"""Code diff analyzer for comparing Python files across Sheratan versions."""

import ast
import difflib
from pathlib import Path
from typing import Dict, List, Set, Optional
from ..utils.file_ops import FileOperations


class CodeDiffAnalyzer:
    """Analyzes code-level differences in Python files."""
    
    def __init__(self, file_ops: FileOperations):
        """Initialize analyzer.
        
        Args:
            file_ops: FileOperations instance for file handling
        """
        self.file_ops = file_ops
    
    def analyze(self, common_files: Set[str], directories: Dict[str, Path]) -> Dict:
        """Analyze code differences in common Python files.
        
        Args:
            common_files: Set of files present in all versions
            directories: Dictionary mapping version names to directory paths
            
        Returns:
            Dictionary containing code diff analysis
        """
        python_files = {f for f in common_files if f.endswith('.py')}
        
        modified_files = []
        identical_files = []
        
        for file_path in python_files:
            diff_result = self._compare_file(file_path, directories)
            
            if diff_result['has_differences']:
                modified_files.append(diff_result)
            else:
                identical_files.append(file_path)
        
        return {
            'modified_files': modified_files,
            'identical_files': identical_files,
            'total_python_files': len(python_files),
            'modified_count': len(modified_files),
            'identical_count': len(identical_files)
        }
    
    def _compare_file(self, file_path: str, directories: Dict[str, Path]) -> Dict:
        """Compare a single file across all versions.
        
        Args:
            file_path: Relative path to file
            directories: Dictionary mapping version names to directory paths
            
        Returns:
            Dictionary with comparison results
        """
        contents = {}
        hashes = {}
        
        # Read file contents from all versions
        for version, directory in directories.items():
            full_path = directory / file_path
            if full_path.exists():
                content = self.file_ops.read_file_content(full_path)
                contents[version] = content
                hashes[version] = self.file_ops.get_file_hash(full_path)
        
        # Check if all hashes are identical
        unique_hashes = set(hashes.values())
        has_differences = len(unique_hashes) > 1
        
        result = {
            'file': file_path,
            'has_differences': has_differences,
            'versions': list(directories.keys())
        }
        
        if has_differences:
            # Perform detailed analysis
            result['change_type'] = self._classify_change_type(contents)
            result['severity'] = self._assess_severity(file_path, contents)
            result['ast_differences'] = self._compare_ast(contents)
            result['line_diff'] = self._generate_line_diff(contents)
            result['description'] = self._generate_description(result)
        
        return result
    
    def _classify_change_type(self, contents: Dict[str, str]) -> str:
        """Classify the type of change.
        
        Args:
            contents: Dictionary mapping version to file content
            
        Returns:
            Change type classification
        """
        # Simple classification based on content analysis
        versions = list(contents.keys())
        if len(versions) < 2:
            return 'unknown'
        
        content1 = contents[versions[0]]
        content2 = contents[versions[1]]
        
        if content1 is None or content2 is None:
            return 'error'
        
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        
        # Calculate similarity
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        ratio = matcher.ratio()
        
        if ratio > 0.95:
            return 'minor'
        elif ratio > 0.7:
            return 'moderate'
        else:
            return 'major'
    
    def _assess_severity(self, file_path: str, contents: Dict[str, str]) -> str:
        """Assess severity of changes.
        
        Args:
            file_path: Path to file
            contents: Dictionary mapping version to file content
            
        Returns:
            Severity level (low, medium, high, critical)
        """
        # Critical files
        critical_files = ['core.py', 'orchestrator.py', 'config.py', 'main.py']
        if any(cf in file_path for cf in critical_files):
            return 'high'
        
        # Check for breaking changes in AST
        ast_diff = self._compare_ast(contents)
        if ast_diff.get('function_removals') or ast_diff.get('class_removals'):
            return 'high'
        
        if ast_diff.get('function_additions') or ast_diff.get('class_additions'):
            return 'medium'
        
        return 'low'
    
    def _compare_ast(self, contents: Dict[str, str]) -> Dict:
        """Compare AST structures of Python files.
        
        Args:
            contents: Dictionary mapping version to file content
            
        Returns:
            Dictionary with AST comparison results
        """
        ast_data = {}
        
        # Parse AST for each version
        for version, content in contents.items():
            if content is None:
                continue
            
            try:
                tree = ast.parse(content)
                ast_data[version] = {
                    'functions': self._extract_functions(tree),
                    'classes': self._extract_classes(tree),
                    'imports': self._extract_imports(tree)
                }
            except SyntaxError:
                ast_data[version] = {'error': 'syntax_error'}
        
        if len(ast_data) < 2:
            return {}
        
        # Compare AST structures
        versions = list(ast_data.keys())
        v1_data = ast_data[versions[0]]
        v2_data = ast_data[versions[1]]
        
        if 'error' in v1_data or 'error' in v2_data:
            return {'error': 'parse_error'}
        
        return {
            'function_additions': list(set(v2_data['functions']) - set(v1_data['functions'])),
            'function_removals': list(set(v1_data['functions']) - set(v2_data['functions'])),
            'class_additions': list(set(v2_data['classes']) - set(v1_data['classes'])),
            'class_removals': list(set(v1_data['classes']) - set(v2_data['classes'])),
            'import_changes': list(set(v1_data['imports']) ^ set(v2_data['imports']))
        }
    
    def _extract_functions(self, tree: ast.AST) -> List[str]:
        """Extract function names from AST.
        
        Args:
            tree: AST tree
            
        Returns:
            List of function names
        """
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        return functions
    
    def _extract_classes(self, tree: ast.AST) -> List[str]:
        """Extract class names from AST.
        
        Args:
            tree: AST tree
            
        Returns:
            List of class names
        """
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        return classes
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST.
        
        Args:
            tree: AST tree
            
        Returns:
            List of import statements
        """
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return imports
    
    def _generate_line_diff(self, contents: Dict[str, str], max_lines: int = 50) -> Optional[str]:
        """Generate line-by-line diff.
        
        Args:
            contents: Dictionary mapping version to file content
            max_lines: Maximum number of diff lines to include
            
        Returns:
            Diff string or None
        """
        if len(contents) < 2:
            return None
        
        versions = list(contents.keys())
        content1 = contents[versions[0]]
        content2 = contents[versions[1]]
        
        if content1 is None or content2 is None:
            return None
        
        lines1 = content1.splitlines(keepends=True)
        lines2 = content2.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            lines1, lines2,
            fromfile=f"{versions[0]}",
            tofile=f"{versions[1]}",
            lineterm=''
        )
        
        diff_lines = list(diff)[:max_lines]
        return ''.join(diff_lines) if diff_lines else None
    
    def _generate_description(self, result: Dict) -> str:
        """Generate human-readable description of changes.
        
        Args:
            result: Comparison result dictionary
            
        Returns:
            Description string
        """
        descriptions = []
        
        ast_diff = result.get('ast_differences', {})
        
        if ast_diff.get('function_additions'):
            descriptions.append(f"Added functions: {', '.join(ast_diff['function_additions'][:3])}")
        
        if ast_diff.get('function_removals'):
            descriptions.append(f"Removed functions: {', '.join(ast_diff['function_removals'][:3])}")
        
        if ast_diff.get('class_additions'):
            descriptions.append(f"Added classes: {', '.join(ast_diff['class_additions'][:3])}")
        
        if ast_diff.get('class_removals'):
            descriptions.append(f"Removed classes: {', '.join(ast_diff['class_removals'][:3])}")
        
        change_type = result.get('change_type', 'unknown')
        if not descriptions:
            descriptions.append(f"{change_type.capitalize()} code changes detected")
        
        return "; ".join(descriptions)
