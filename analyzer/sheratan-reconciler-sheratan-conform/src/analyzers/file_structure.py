"""File structure analyzer for comparing directory trees across Sheratan versions."""

from pathlib import Path
from typing import Dict, List, Set, Tuple
from ..utils.file_ops import FileOperations


class FileStructureAnalyzer:
    """Analyzes and compares file structures across multiple Sheratan installations."""
    
    def __init__(self, file_ops: FileOperations):
        """Initialize analyzer.
        
        Args:
            file_ops: FileOperations instance for file handling
        """
        self.file_ops = file_ops
    
    def analyze(self, directories: Dict[str, Path]) -> Dict:
        """Analyze file structures across multiple directories.
        
        Args:
            directories: Dictionary mapping version names to directory paths
            
        Returns:
            Dictionary containing analysis results
        """
        # Build file trees for each version
        file_trees = {}
        for version, directory in directories.items():
            if directory.exists():
                files = self.file_ops.walk_directory(directory)
                file_trees[version] = self.file_ops.get_relative_paths(files, directory)
            else:
                file_trees[version] = set()
        
        # Find common and unique files
        all_files = set()
        for files in file_trees.values():
            all_files.update(files)
        
        # Analyze differences
        results = {
            'file_trees': file_trees,
            'all_files': all_files,
            'common_files': self._find_common_files(file_trees),
            'unique_files': self._find_unique_files(file_trees),
            'missing_files': self._find_missing_files(file_trees),
            'extra_files': self._find_extra_files(file_trees),
            'similarity_matrix': self._calculate_similarity_matrix(file_trees),
            'statistics': self._calculate_statistics(file_trees)
        }
        
        return results
    
    def _find_common_files(self, file_trees: Dict[str, Set[str]]) -> Set[str]:
        """Find files present in all versions.
        
        Args:
            file_trees: Dictionary of version -> file set
            
        Returns:
            Set of common file paths
        """
        if not file_trees:
            return set()
        
        common = set(next(iter(file_trees.values())))
        for files in file_trees.values():
            common &= files
        
        return common
    
    def _find_unique_files(self, file_trees: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        """Find files unique to each version.
        
        Args:
            file_trees: Dictionary of version -> file set
            
        Returns:
            Dictionary mapping version to unique files
        """
        unique = {}
        
        for version, files in file_trees.items():
            other_files = set()
            for other_version, other_version_files in file_trees.items():
                if other_version != version:
                    other_files.update(other_version_files)
            
            unique[version] = files - other_files
        
        return unique
    
    def _find_missing_files(self, file_trees: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        """Find files missing from each version (present in others).
        
        Args:
            file_trees: Dictionary of version -> file set
            
        Returns:
            Dictionary mapping version to missing files
        """
        missing = {}
        all_files = set()
        
        for files in file_trees.values():
            all_files.update(files)
        
        for version, files in file_trees.items():
            missing[version] = all_files - files
        
        return missing
    
    def _find_extra_files(self, file_trees: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        """Find extra files in each version (not in others).
        
        Args:
            file_trees: Dictionary of version -> file set
            
        Returns:
            Dictionary mapping version to extra files
        """
        return self._find_unique_files(file_trees)
    
    def _calculate_similarity_matrix(self, file_trees: Dict[str, Set[str]]) -> Dict[Tuple[str, str], float]:
        """Calculate similarity scores between all version pairs.
        
        Args:
            file_trees: Dictionary of version -> file set
            
        Returns:
            Dictionary mapping (version1, version2) to similarity score (0-1)
        """
        similarity = {}
        versions = list(file_trees.keys())
        
        for i, v1 in enumerate(versions):
            for v2 in versions[i:]:
                if v1 == v2:
                    similarity[(v1, v2)] = 1.0
                else:
                    files1 = file_trees[v1]
                    files2 = file_trees[v2]
                    
                    if not files1 and not files2:
                        score = 1.0
                    elif not files1 or not files2:
                        score = 0.0
                    else:
                        intersection = len(files1 & files2)
                        union = len(files1 | files2)
                        score = intersection / union if union > 0 else 0.0
                    
                    similarity[(v1, v2)] = score
                    similarity[(v2, v1)] = score
        
        return similarity
    
    def _calculate_statistics(self, file_trees: Dict[str, Set[str]]) -> Dict:
        """Calculate statistics about file structures.
        
        Args:
            file_trees: Dictionary of version -> file set
            
        Returns:
            Dictionary with statistics
        """
        all_files = set()
        for files in file_trees.values():
            all_files.update(files)
        
        common_files = self._find_common_files(file_trees)
        
        stats = {
            'version_count': len(file_trees),
            'total_unique_files': len(all_files),
            'common_file_count': len(common_files),
            'per_version': {}
        }
        
        for version, files in file_trees.items():
            stats['per_version'][version] = {
                'file_count': len(files),
                'unique_files': len(self._find_unique_files({version: files, 'others': all_files - files})[version])
            }
        
        return stats
    
    def get_file_comparison(self, file_path: str, directories: Dict[str, Path]) -> Dict:
        """Get detailed comparison of a specific file across versions.
        
        Args:
            file_path: Relative path to file
            directories: Dictionary mapping version names to directory paths
            
        Returns:
            Dictionary with file comparison data
        """
        comparison = {
            'file': file_path,
            'versions': {}
        }
        
        for version, directory in directories.items():
            full_path = directory / file_path
            if full_path.exists():
                info = self.file_ops.get_file_info(full_path)
                comparison['versions'][version] = info
            else:
                comparison['versions'][version] = {'exists': False}
        
        return comparison
