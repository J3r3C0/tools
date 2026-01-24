"""Conflict resolution logic for Sheratan Version Reconciler."""

from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm


class ConflictResolver:
    """Handles conflict resolution during merge operations."""
    
    def __init__(self, interactive: bool = True):
        """Initialize conflict resolver.
        
        Args:
            interactive: Whether to prompt user for conflict resolution
        """
        self.interactive = interactive
        self.console = Console()
        self.resolution_log = []
    
    def resolve_file_conflict(self, file_path: str, versions: Dict[str, Path], 
                             strategy: str = 'newest') -> Optional[Path]:
        """Resolve conflict for a file present in multiple versions.
        
        Args:
            file_path: Relative path to conflicting file
            versions: Dictionary mapping version name to full file path
            strategy: Resolution strategy (newest, manual, largest, etc.)
            
        Returns:
            Path to selected version or None
        """
        if not versions:
            return None
        
        if len(versions) == 1:
            return list(versions.values())[0]
        
        if strategy == 'newest':
            return self._select_newest(versions)
        elif strategy == 'largest':
            return self._select_largest(versions)
        elif strategy == 'manual' and self.interactive:
            return self._prompt_user_selection(file_path, versions)
        else:
            # Default to newest
            return self._select_newest(versions)
    
    def _select_newest(self, versions: Dict[str, Path]) -> Path:
        """Select the newest version based on modification time.
        
        Args:
            versions: Dictionary mapping version name to file path
            
        Returns:
            Path to newest file
        """
        newest = None
        newest_time = 0
        
        for version_name, file_path in versions.items():
            if file_path.exists():
                mtime = file_path.stat().st_mtime
                if mtime > newest_time:
                    newest_time = mtime
                    newest = file_path
        
        return newest or list(versions.values())[0]
    
    def _select_largest(self, versions: Dict[str, Path]) -> Path:
        """Select the largest version based on file size.
        
        Args:
            versions: Dictionary mapping version name to file path
            
        Returns:
            Path to largest file
        """
        largest = None
        largest_size = 0
        
        for version_name, file_path in versions.items():
            if file_path.exists():
                size = file_path.stat().st_size
                if size > largest_size:
                    largest_size = size
                    largest = file_path
        
        return largest or list(versions.values())[0]
    
    def _prompt_user_selection(self, file_path: str, versions: Dict[str, Path]) -> Optional[Path]:
        """Prompt user to select which version to use.
        
        Args:
            file_path: Relative path to file
            versions: Dictionary mapping version name to file path
            
        Returns:
            Selected file path or None
        """
        self.console.print(f"\n[yellow]Conflict detected for:[/yellow] {file_path}")
        self.console.print("[cyan]Available versions:[/cyan]")
        
        version_list = list(versions.items())
        for i, (version_name, full_path) in enumerate(version_list, 1):
            if full_path.exists():
                size = full_path.stat().st_size
                mtime = full_path.stat().st_mtime
                self.console.print(f"  {i}. {version_name} (size: {size} bytes, modified: {mtime})")
            else:
                self.console.print(f"  {i}. {version_name} (not found)")
        
        choice = Prompt.ask(
            "Select version",
            choices=[str(i) for i in range(1, len(version_list) + 1)],
            default="1"
        )
        
        selected_version, selected_path = version_list[int(choice) - 1]
        self.resolution_log.append({
            'file': file_path,
            'selected_version': selected_version,
            'available_versions': list(versions.keys())
        })
        
        return selected_path
    
    def resolve_config_conflict(self, key: str, values: Dict[str, Any], 
                               strategy: str = 'prompt') -> Any:
        """Resolve configuration value conflict.
        
        Args:
            key: Configuration key
            values: Dictionary mapping version to value
            strategy: Resolution strategy
            
        Returns:
            Selected value
        """
        if len(values) == 1:
            return list(values.values())[0]
        
        if strategy == 'prompt' and self.interactive:
            return self._prompt_config_selection(key, values)
        elif strategy == 'newest':
            # Return first value (would need timestamp info for true newest)
            return list(values.values())[0]
        else:
            return list(values.values())[0]
    
    def _prompt_config_selection(self, key: str, values: Dict[str, Any]) -> Any:
        """Prompt user to select configuration value.
        
        Args:
            key: Configuration key
            values: Dictionary mapping version to value
            
        Returns:
            Selected value
        """
        self.console.print(f"\n[yellow]Config conflict for key:[/yellow] {key}")
        self.console.print("[cyan]Available values:[/cyan]")
        
        value_list = list(values.items())
        for i, (version, value) in enumerate(value_list, 1):
            self.console.print(f"  {i}. {version}: {value}")
        
        choice = Prompt.ask(
            "Select value",
            choices=[str(i) for i in range(1, len(value_list) + 1)],
            default="1"
        )
        
        selected_version, selected_value = value_list[int(choice) - 1]
        self.resolution_log.append({
            'type': 'config',
            'key': key,
            'selected_version': selected_version,
            'selected_value': selected_value
        })
        
        return selected_value
    
    def get_resolution_summary(self) -> str:
        """Get summary of all conflict resolutions.
        
        Returns:
            Summary string
        """
        if not self.resolution_log:
            return "No conflicts resolved"
        
        summary = [f"Resolved {len(self.resolution_log)} conflicts:"]
        for entry in self.resolution_log:
            if entry.get('type') == 'config':
                summary.append(f"  - Config '{entry['key']}': selected from {entry['selected_version']}")
            else:
                summary.append(f"  - File '{entry['file']}': selected from {entry['selected_version']}")
        
        return "\n".join(summary)
