"""Core application logic for Sheratan Version Reconciler."""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from .analyzers import FileStructureAnalyzer, CodeDiffAnalyzer, ConfigDriftAnalyzer
from .reconciler import Merger, ConflictResolver
from .utils import FileOperations, Reporter


class SheratanReconciler:
    """Main application class for reconciling Sheratan versions."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize reconciler.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.file_ops = FileOperations(self.config.get('ignore_patterns', []))
        self.file_analyzer = FileStructureAnalyzer(self.file_ops)
        self.code_analyzer = CodeDiffAnalyzer(self.file_ops)
        self.config_analyzer = ConfigDriftAnalyzer(self.file_ops)
        self.conflict_resolver = ConflictResolver(interactive=True)
        self.merger = Merger(self.file_ops, self.conflict_resolver)
        self.reporter = Reporter(self.config.get('reporting', {}).get('format', 'markdown'))
    
    def _load_config(self, config_path: Optional[Path]) -> Dict:
        """Load configuration from file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            Configuration dictionary
        """
        if config_path and config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        
        # Default configuration
        return {
            'merge_strategy': 'newest',
            'backup_originals': True,
            'output_directory': './sheratan-unified',
            'ignore_patterns': [
                '*.pyc', '__pycache__', '.git', '*.log', 'venv/', '.env'
            ],
            'reporting': {
                'format': 'markdown',
                'include_diffs': True
            }
        }
    
    def scan(self, directories: Dict[str, Path]) -> Dict:
        """Scan and analyze multiple Sheratan directories.
        
        Args:
            directories: Dictionary mapping version names to directory paths
            
        Returns:
            Analysis results dictionary
        """
        print(f"Scanning {len(directories)} Sheratan versions...")
        
        # Validate directories
        valid_dirs = {}
        for version, directory in directories.items():
            if directory.exists():
                valid_dirs[version] = directory
                print(f"  ✓ {version}: {directory}")
            else:
                print(f"  ✗ {version}: {directory} (not found)")
        
        if not valid_dirs:
            return {'error': 'No valid directories found'}
        
        # Analyze file structure
        print("\nAnalyzing file structures...")
        file_structure = self.file_analyzer.analyze(valid_dirs)
        
        # Analyze code differences
        print("Analyzing code differences...")
        common_files = file_structure.get('common_files', set())
        code_diff = self.code_analyzer.analyze(common_files, valid_dirs)
        
        # Analyze configuration drift
        print("Analyzing configuration drift...")
        config_drift = self.config_analyzer.analyze(common_files, valid_dirs)
        
        # Generate summary
        summary = {
            'version_count': len(valid_dirs),
            'total_files': len(file_structure.get('all_files', set())),
            'common_files': len(common_files),
            'different_files': code_diff.get('modified_count', 0),
            'unique_files': sum(len(files) for files in file_structure.get('unique_files', {}).values()),
            'conflicts': config_drift.get('conflict_count', 0)
        }
        
        results = {
            'summary': summary,
            'file_structure': file_structure,
            'code_diff': code_diff,
            'config_drift': config_drift,
            'directories': {k: str(v) for k, v in valid_dirs.items()}
        }
        
        print("\n" + self.reporter.generate_summary(results))
        
        return results
    
    def compare(self, directories: Dict[str, Path], output_path: Optional[Path] = None) -> str:
        """Generate detailed comparison report.
        
        Args:
            directories: Dictionary mapping version names to directory paths
            output_path: Optional path to save report
            
        Returns:
            Report content
        """
        print("Generating comparison report...")
        
        # Perform analysis
        results = self.scan(directories)
        
        # Generate report
        if output_path is None:
            output_path = Path('sheratan_comparison_report.md')
        
        report = self.reporter.generate_comparison_report(results, output_path)
        
        print(f"\nReport saved to: {output_path}")
        
        return report
    
    def merge(self, directories: Dict[str, Path], output_dir: Optional[Path] = None,
             dry_run: bool = False) -> Dict:
        """Merge multiple Sheratan versions into unified installation.
        
        Args:
            directories: Dictionary mapping version names to directory paths
            output_dir: Output directory for merged version
            dry_run: If True, don't actually perform merge
            
        Returns:
            Merge results dictionary
        """
        if output_dir is None:
            output_dir = Path(self.config.get('output_directory', './sheratan-unified'))
        
        print(f"Merging {len(directories)} Sheratan versions...")
        print(f"Output directory: {output_dir}")
        
        if dry_run:
            print("\n[DRY RUN MODE - No files will be modified]")
        
        # Perform analysis first
        analysis_results = self.scan(directories)
        
        if 'error' in analysis_results:
            return analysis_results
        
        # Show summary and ask for confirmation
        print("\n" + "="*60)
        print("MERGE SUMMARY")
        print("="*60)
        print(f"Total files to merge: {analysis_results['summary']['total_files']}")
        print(f"Files with conflicts: {analysis_results['summary']['different_files']}")
        print(f"Configuration conflicts: {analysis_results['summary']['conflicts']}")
        
        if not dry_run:
            response = input("\nProceed with merge? [y/N]: ")
            if response.lower() != 'y':
                print("Merge cancelled.")
                return {'cancelled': True}
        
        # Perform merge
        if not dry_run:
            print("\nMerging files...")
            merge_results = self.merger.merge(
                directories,
                output_dir,
                analysis_results,
                backup=self.config.get('backup_originals', True)
            )
            
            # Merge requirements.txt
            print("Merging requirements.txt...")
            self.merger.merge_requirements(directories, output_dir)
            
            print("\n" + self.merger.get_merge_summary())
            print("\n" + self.conflict_resolver.get_resolution_summary())
            
            print(f"\n✓ Merge complete! Unified version created at: {output_dir}")
            
            return merge_results
        else:
            print("\nDry run complete. No files were modified.")
            return {'dry_run': True, 'analysis': analysis_results}
    
    def report(self, analysis_results: Dict, output_path: Path, format: str = 'markdown') -> bool:
        """Export analysis results to file.
        
        Args:
            analysis_results: Analysis results dictionary
            output_path: Output file path
            format: Output format (markdown, json, html)
            
        Returns:
            True if successful
        """
        original_format = self.reporter.output_format
        self.reporter.output_format = format
        
        try:
            self.reporter.generate_comparison_report(analysis_results, output_path)
            print(f"Report exported to: {output_path}")
            return True
        except Exception as e:
            print(f"Error exporting report: {e}")
            return False
        finally:
            self.reporter.output_format = original_format
