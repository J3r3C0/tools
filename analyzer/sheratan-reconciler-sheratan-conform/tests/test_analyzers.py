"""Tests for analyzer modules."""

import pytest
from pathlib import Path
from src.utils.file_ops import FileOperations
from src.analyzers import FileStructureAnalyzer, CodeDiffAnalyzer, ConfigDriftAnalyzer


class TestFileStructureAnalyzer:
    """Tests for FileStructureAnalyzer."""
    
    def test_find_common_files(self):
        """Test finding common files across versions."""
        file_ops = FileOperations()
        analyzer = FileStructureAnalyzer(file_ops)
        
        file_trees = {
            'v1': {'file1.py', 'file2.py', 'file3.py'},
            'v2': {'file1.py', 'file2.py', 'file4.py'}
        }
        
        common = analyzer._find_common_files(file_trees)
        assert common == {'file1.py', 'file2.py'}
    
    def test_find_unique_files(self):
        """Test finding unique files per version."""
        file_ops = FileOperations()
        analyzer = FileStructureAnalyzer(file_ops)
        
        file_trees = {
            'v1': {'file1.py', 'file2.py', 'unique1.py'},
            'v2': {'file1.py', 'file2.py', 'unique2.py'}
        }
        
        unique = analyzer._find_unique_files(file_trees)
        assert unique['v1'] == {'unique1.py'}
        assert unique['v2'] == {'unique2.py'}
    
    def test_similarity_calculation(self):
        """Test similarity score calculation."""
        file_ops = FileOperations()
        analyzer = FileStructureAnalyzer(file_ops)
        
        file_trees = {
            'v1': {'file1.py', 'file2.py'},
            'v2': {'file1.py', 'file2.py'}
        }
        
        similarity = analyzer._calculate_similarity_matrix(file_trees)
        assert similarity[('v1', 'v2')] == 1.0
        assert similarity[('v2', 'v1')] == 1.0


class TestCodeDiffAnalyzer:
    """Tests for CodeDiffAnalyzer."""
    
    def test_extract_functions(self):
        """Test extracting function names from AST."""
        import ast
        
        code = """
def func1():
    pass

def func2():
    pass
"""
        
        file_ops = FileOperations()
        analyzer = CodeDiffAnalyzer(file_ops)
        
        tree = ast.parse(code)
        functions = analyzer._extract_functions(tree)
        
        assert 'func1' in functions
        assert 'func2' in functions
    
    def test_extract_classes(self):
        """Test extracting class names from AST."""
        import ast
        
        code = """
class MyClass:
    pass

class AnotherClass:
    pass
"""
        
        file_ops = FileOperations()
        analyzer = CodeDiffAnalyzer(file_ops)
        
        tree = ast.parse(code)
        classes = analyzer._extract_classes(tree)
        
        assert 'MyClass' in classes
        assert 'AnotherClass' in classes
    
    def test_change_type_classification(self):
        """Test change type classification."""
        file_ops = FileOperations()
        analyzer = CodeDiffAnalyzer(file_ops)
        
        # Identical content
        contents = {
            'v1': 'def foo():\n    pass',
            'v2': 'def foo():\n    pass'
        }
        
        change_type = analyzer._classify_change_type(contents)
        assert change_type == 'minor'  # High similarity


class TestConfigDriftAnalyzer:
    """Tests for ConfigDriftAnalyzer."""
    
    def test_is_config_file(self):
        """Test config file detection."""
        file_ops = FileOperations()
        analyzer = ConfigDriftAnalyzer(file_ops)
        
        assert analyzer._is_config_file('config.yaml')
        assert analyzer._is_config_file('settings.json')
        assert analyzer._is_config_file('.env')
        assert not analyzer._is_config_file('main.py')
    
    def test_flatten_dict(self):
        """Test dictionary flattening."""
        file_ops = FileOperations()
        analyzer = ConfigDriftAnalyzer(file_ops)
        
        nested = {
            'a': {
                'b': {
                    'c': 'value'
                }
            },
            'd': 'value2'
        }
        
        flat = analyzer._flatten_dict(nested)
        assert flat['a.b.c'] == 'value'
        assert flat['d'] == 'value2'
    
    def test_find_config_conflicts(self):
        """Test finding configuration conflicts."""
        file_ops = FileOperations()
        analyzer = ConfigDriftAnalyzer(file_ops)
        
        configs = {
            'v1': {'key1': 'value1', 'key2': 'same'},
            'v2': {'key1': 'value2', 'key2': 'same'}
        }
        
        conflicts = analyzer._find_config_conflicts(configs)
        
        # Should find conflict for key1 but not key2
        conflict_keys = [c['key'] for c in conflicts]
        assert 'key1' in conflict_keys
        assert 'key2' not in conflict_keys


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
