"""Merger logic for combining multiple Sheratan versions."""

import shutil
from pathlib import Path
from typing import Dict, List, Set, Optional
from ..utils.file_ops import FileOperations
from .conflict_resolver import ConflictResolver


class Merger:
    """Handles merging of multiple Sheratan versions into unified installation."""
    
    def __init__(self, file_ops: FileOperations, conflict_resolver: ConflictResolver):
        """Initialize merger.
        
        Args:
            file_ops: FileOperations instance
            conflict_resolver: ConflictResolver instance
        """
        self.file_ops = file_ops
        self.conflict_resolver = conflict_resolver
        self.merge_log = []
    
    def merge(self, directories: Dict[str, Path], output_dir: Path, 
             analysis_results: Dict, backup: bool = True) -> Dict:
        """Merge multiple Sheratan versions into unified installation.
        
        Args:
            directories: Dictionary mapping version names to directory paths
            output_dir: Output directory for merged version
            analysis_results: Results from analyzers
            backup: Whether to backup original directories
            
        Returns:
            Dictionary with merge results
        """
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup originals if requested
        backups = {}
        if backup:
            for version, directory in directories.items():
                backup_path = self.file_ops.create_backup(directory, version)
                if backup_path:
                    backups[version] = backup_path
        
        # Get file lists
        file_structure = analysis_results.get('file_structure', {})
        all_files = file_structure.get('all_files', set())
        common_files = file_structure.get('common_files', set())
        unique_files = file_structure.get('unique_files', {})
        
        # Merge files
        merged_count = 0
        conflict_count = 0
        
        # Process common files (may have conflicts)
        for file_path in common_files:
            result = self._merge_file(file_path, directories, output_dir)
            if result['merged']:
                merged_count += 1
            if result['had_conflict']:
                conflict_count += 1
        
        # Process unique files (no conflicts)
        for version, files in unique_files.items():
            for file_path in files:
                source_dir = directories[version]
                source_file = source_dir / file_path
                dest_file = output_dir / file_path
                
                if self.file_ops.copy_file_safe(source_file, dest_file, backup=False):
                    merged_count += 1
                    self.merge_log.append({
                        'file': file_path,
                        'source_version': version,
                        'action': 'copied_unique'
                    })
        
        return {
            'success': True,
            'output_directory': str(output_dir),
            'backups': {k: str(v) for k, v in backups.items()},
            'merged_file_count': merged_count,
            'conflict_count': conflict_count,
            'merge_log': self.merge_log
        }
    
    def _merge_file(self, file_path: str, directories: Dict[str, Path], 
                   output_dir: Path) -> Dict:
        """Merge a single file from multiple versions.
        
        Args:
            file_path: Relative path to file
            directories: Dictionary mapping version names to directory paths
            output_dir: Output directory
            
        Returns:
            Dictionary with merge result
        """
        # Collect all versions of this file
        file_versions = {}
        file_hashes = {}
        
        for version, directory in directories.items():
            full_path = directory / file_path
            if full_path.exists():
                file_versions[version] = full_path
                file_hashes[version] = self.file_ops.get_file_hash(full_path)
        
        # Check if all versions are identical
        unique_hashes = set(file_hashes.values())
        had_conflict = len(unique_hashes) > 1
        
        # Select source file
        if had_conflict:
            source_file = self.conflict_resolver.resolve_file_conflict(
                file_path, file_versions, strategy='newest'
            )
            selected_version = next(v for v, p in file_versions.items() if p == source_file)
        else:
            # All identical, pick first
            selected_version = list(file_versions.keys())[0]
            source_file = file_versions[selected_version]
        
        # Copy to output
        dest_file = output_dir / file_path
        success = self.file_ops.copy_file_safe(source_file, dest_file, backup=False)
        
        if success:
            self.merge_log.append({
                'file': file_path,
                'source_version': selected_version,
                'had_conflict': had_conflict,
                'action': 'merged' if had_conflict else 'copied'
            })
        
        return {
            'merged': success,
            'had_conflict': had_conflict,
            'selected_version': selected_version
        }
    
    def merge_requirements(self, directories: Dict[str, Path], output_dir: Path) -> bool:
        """Merge requirements.txt files from all versions (union).
        
        Args:
            directories: Dictionary mapping version names to directory paths
            output_dir: Output directory
            
        Returns:
            True if successful
        """
        all_requirements = set()
        
        for version, directory in directories.items():
            req_file = directory / 'requirements.txt'
            if req_file.exists():
                content = self.file_ops.read_file_content(req_file)
                if content:
                    lines = content.splitlines()
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            all_requirements.add(line)
        
        if all_requirements:
            output_file = output_dir / 'requirements.txt'
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(sorted(all_requirements)))
                f.write('\n')
            
            self.merge_log.append({
                'file': 'requirements.txt',
                'action': 'merged_union',
                'total_requirements': len(all_requirements)
            })
            
            return True
        
        return False
    
    def get_merge_summary(self) -> str:
        """Get summary of merge operations.
        
        Returns:
            Summary string
        """
        if not self.merge_log:
            return "No files merged"
        
        copied = sum(1 for e in self.merge_log if e.get('action') == 'copied')
        merged = sum(1 for e in self.merge_log if e.get('action') == 'merged')
        unique = sum(1 for e in self.merge_log if e.get('action') == 'copied_unique')
        
        summary = [
            f"Merge Summary:",
            f"  - Total files: {len(self.merge_log)}",
            f"  - Identical files copied: {copied}",
            f"  - Conflicting files merged: {merged}",
            f"  - Unique files copied: {unique}"
        ]
        
        return "\n".join(summary)
