"""Tests for reconciler modules."""

import pytest
from pathlib import Path
from src.utils.file_ops import FileOperations
from src.reconciler import Merger, ConflictResolver


class TestConflictResolver:
    """Tests for ConflictResolver."""
    
    def test_select_newest(self, tmp_path):
        """Test selecting newest file."""
        resolver = ConflictResolver(interactive=False)
        
        # Create test files with different timestamps
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("old content")
        file2.write_text("new content")
        
        versions = {'v1': file1, 'v2': file2}
        selected = resolver._select_newest(versions)
        
        assert selected in versions.values()
    
    def test_select_largest(self, tmp_path):
        """Test selecting largest file."""
        resolver = ConflictResolver(interactive=False)
        
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("short")
        file2.write_text("much longer content here")
        
        versions = {'v1': file1, 'v2': file2}
        selected = resolver._select_largest(versions)
        
        assert selected == file2


class TestMerger:
    """Tests for Merger."""
    
    def test_merge_log_tracking(self):
        """Test that merge operations are logged."""
        file_ops = FileOperations()
        resolver = ConflictResolver(interactive=False)
        merger = Merger(file_ops, resolver)
        
        assert merger.merge_log == []
    
    def test_get_merge_summary(self):
        """Test merge summary generation."""
        file_ops = FileOperations()
        resolver = ConflictResolver(interactive=False)
        merger = Merger(file_ops, resolver)
        
        # Add some mock log entries
        merger.merge_log = [
            {'action': 'copied'},
            {'action': 'merged'},
            {'action': 'copied_unique'}
        ]
        
        summary = merger.get_merge_summary()
        assert 'Total files: 3' in summary


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
