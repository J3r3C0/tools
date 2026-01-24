"""File operation utilities for Sheratan Version Reconciler."""

import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Set, Optional
from datetime import datetime
import pathspec


class FileOperations:
    """Handles file operations with safety checks and backup capabilities."""
    
    def __init__(self, ignore_patterns: List[str] = None):
        """Initialize file operations handler.
        
        Args:
            ignore_patterns: List of gitignore-style patterns to ignore
        """
        self.ignore_patterns = ignore_patterns or []
        self.spec = pathspec.PathSpec.from_lines('gitwildmatch', self.ignore_patterns)
    
    def should_ignore(self, path: Path, base_path: Path) -> bool:
        """Check if a path should be ignored based on patterns.
        
        Args:
            path: Path to check
            base_path: Base directory for relative path calculation
            
        Returns:
            True if path should be ignored
        """
        try:
            rel_path = path.relative_to(base_path)
            return self.spec.match_file(str(rel_path))
        except ValueError:
            return False
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex digest of file hash
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def get_file_info(self, file_path: Path) -> dict:
        """Get detailed information about a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file metadata
        """
        try:
            stat = file_path.stat()
            return {
                'path': str(file_path),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'hash': self.get_file_hash(file_path) if file_path.is_file() else None,
                'is_file': file_path.is_file(),
                'is_dir': file_path.is_dir()
            }
        except Exception as e:
            return {'path': str(file_path), 'error': str(e)}
    
    def walk_directory(self, directory: Path, include_dirs: bool = False) -> List[Path]:
        """Walk directory and return all files, respecting ignore patterns.
        
        Args:
            directory: Directory to walk
            include_dirs: Whether to include directories in results
            
        Returns:
            List of Path objects
        """
        results = []
        
        if not directory.exists():
            return results
        
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
            
            # Filter directories
            dirs[:] = [d for d in dirs if not self.should_ignore(root_path / d, directory)]
            
            # Add directories if requested
            if include_dirs:
                for dir_name in dirs:
                    dir_path = root_path / dir_name
                    if not self.should_ignore(dir_path, directory):
                        results.append(dir_path)
            
            # Add files
            for file_name in files:
                file_path = root_path / file_name
                if not self.should_ignore(file_path, directory):
                    results.append(file_path)
        
        return results
    
    def get_relative_paths(self, files: List[Path], base_path: Path) -> Set[str]:
        """Convert absolute paths to relative paths.
        
        Args:
            files: List of absolute paths
            base_path: Base directory for relative calculation
            
        Returns:
            Set of relative path strings
        """
        return {str(f.relative_to(base_path)) for f in files}
    
    def copy_file_safe(self, src: Path, dst: Path, backup: bool = True) -> bool:
        """Safely copy a file with optional backup.
        
        Args:
            src: Source file path
            dst: Destination file path
            backup: Whether to backup existing destination
            
        Returns:
            True if successful
        """
        try:
            # Create destination directory if needed
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # Backup existing file if requested
            if backup and dst.exists():
                backup_path = dst.with_suffix(dst.suffix + '.backup')
                shutil.copy2(dst, backup_path)
            
            # Copy file
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            print(f"Error copying {src} to {dst}: {e}")
            return False
    
    def create_backup(self, directory: Path, backup_suffix: str = None) -> Optional[Path]:
        """Create a backup of an entire directory.
        
        Args:
            directory: Directory to backup
            backup_suffix: Optional suffix for backup name
            
        Returns:
            Path to backup directory or None if failed
        """
        if not directory.exists():
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = backup_suffix or timestamp
            backup_path = directory.parent / f"{directory.name}_backup_{suffix}"
            
            shutil.copytree(directory, backup_path, ignore=shutil.ignore_patterns(*self.ignore_patterns))
            return backup_path
        except Exception as e:
            print(f"Error creating backup of {directory}: {e}")
            return None
    
    def read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content as text.
        
        Args:
            file_path: Path to file
            
        Returns:
            File content or None if error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception:
                return None
        except Exception:
            return None
