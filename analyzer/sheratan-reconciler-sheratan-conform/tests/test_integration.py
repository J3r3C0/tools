"""Integration tests for Sheratan Version Reconciler."""

import pytest
from pathlib import Path
from src.app import SheratanReconciler


class TestIntegration:
    """Integration tests for full workflow."""
    
    def test_reconciler_initialization(self):
        """Test that reconciler initializes correctly."""
        reconciler = SheratanReconciler()
        
        assert reconciler.file_ops is not None
        assert reconciler.file_analyzer is not None
        assert reconciler.code_analyzer is not None
        assert reconciler.config_analyzer is not None
        assert reconciler.merger is not None
        assert reconciler.reporter is not None
    
    def test_config_loading(self, tmp_path):
        """Test configuration loading."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
merge_strategy: manual
backup_originals: false
""")
        
        reconciler = SheratanReconciler(config_file)
        
        assert reconciler.config['merge_strategy'] == 'manual'
        assert reconciler.config['backup_originals'] is False
    
    def test_scan_with_empty_directories(self):
        """Test scanning with no valid directories."""
        reconciler = SheratanReconciler()
        
        directories = {
            'v1': Path('/nonexistent/path1'),
            'v2': Path('/nonexistent/path2')
        }
        
        results = reconciler.scan(directories)
        
        assert 'error' in results


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
