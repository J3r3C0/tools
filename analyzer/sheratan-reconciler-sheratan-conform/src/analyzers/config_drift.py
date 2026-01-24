"""Configuration drift analyzer for comparing config files across Sheratan versions."""

import json
import yaml
import configparser
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from ..utils.file_ops import FileOperations


class ConfigDriftAnalyzer:
    """Analyzes configuration drift across multiple Sheratan installations."""
    
    def __init__(self, file_ops: FileOperations):
        """Initialize analyzer.
        
        Args:
            file_ops: FileOperations instance for file handling
        """
        self.file_ops = file_ops
        self.config_extensions = {'.yaml', '.yml', '.json', '.ini', '.toml', '.env'}
    
    def analyze(self, common_files: Set[str], directories: Dict[str, Path]) -> Dict:
        """Analyze configuration drift in common config files.
        
        Args:
            common_files: Set of files present in all versions
            directories: Dictionary mapping version names to directory paths
            
        Returns:
            Dictionary containing config drift analysis
        """
        config_files = {f for f in common_files if self._is_config_file(f)}
        
        conflicts = []
        identical_configs = []
        
        for file_path in config_files:
            drift_result = self._compare_config(file_path, directories)
            
            if drift_result['has_conflicts']:
                conflicts.append(drift_result)
            else:
                identical_configs.append(file_path)
        
        return {
            'conflicts': conflicts,
            'identical_configs': identical_configs,
            'total_config_files': len(config_files),
            'conflict_count': len(conflicts),
            'identical_count': len(identical_configs)
        }
    
    def _is_config_file(self, file_path: str) -> bool:
        """Check if file is a configuration file.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is a config file
        """
        path = Path(file_path)
        return path.suffix in self.config_extensions or path.name.startswith('.env')
    
    def _compare_config(self, file_path: str, directories: Dict[str, Path]) -> Dict:
        """Compare a configuration file across all versions.
        
        Args:
            file_path: Relative path to config file
            directories: Dictionary mapping version names to directory paths
            
        Returns:
            Dictionary with comparison results
        """
        configs = {}
        
        # Parse config files from all versions
        for version, directory in directories.items():
            full_path = directory / file_path
            if full_path.exists():
                parsed = self._parse_config_file(full_path)
                configs[version] = parsed
        
        result = {
            'file': file_path,
            'has_conflicts': False,
            'versions': list(directories.keys())
        }
        
        if len(configs) < 2:
            return result
        
        # Find conflicts
        conflicts = self._find_config_conflicts(configs)
        
        if conflicts:
            result['has_conflicts'] = True
            result['conflicts'] = conflicts
            result['severity'] = self._assess_config_severity(file_path, conflicts)
            result['description'] = self._generate_config_description(conflicts)
        
        return result
    
    def _parse_config_file(self, file_path: Path) -> Optional[Dict]:
        """Parse a configuration file based on its extension.
        
        Args:
            file_path: Path to config file
            
        Returns:
            Parsed configuration as dictionary or None if error
        """
        try:
            if file_path.suffix in {'.yaml', '.yml'}:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            
            elif file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            elif file_path.suffix == '.ini':
                config = configparser.ConfigParser()
                config.read(file_path)
                return {section: dict(config[section]) for section in config.sections()}
            
            elif file_path.name.startswith('.env') or file_path.suffix == '.env':
                return self._parse_env_file(file_path)
            
            else:
                # Try to parse as key=value format
                return self._parse_env_file(file_path)
        
        except Exception as e:
            return {'_parse_error': str(e)}
    
    def _parse_env_file(self, file_path: Path) -> Dict:
        """Parse .env style configuration file.
        
        Args:
            file_path: Path to .env file
            
        Returns:
            Dictionary of key-value pairs
        """
        config = {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        
        return config
    
    def _find_config_conflicts(self, configs: Dict[str, Dict]) -> List[Dict]:
        """Find conflicting configuration values.
        
        Args:
            configs: Dictionary mapping version to parsed config
            
        Returns:
            List of conflict dictionaries
        """
        conflicts = []
        
        # Get all keys across all versions
        all_keys = set()
        for config in configs.values():
            if isinstance(config, dict):
                all_keys.update(self._flatten_dict(config).keys())
        
        # Check each key for conflicts
        for key in all_keys:
            values = {}
            for version, config in configs.items():
                if isinstance(config, dict):
                    flat_config = self._flatten_dict(config)
                    if key in flat_config:
                        values[version] = flat_config[key]
            
            # Check if values differ
            unique_values = set(str(v) for v in values.values())
            if len(unique_values) > 1:
                conflicts.append({
                    'key': key,
                    'values': values,
                    'unique_value_count': len(unique_values)
                })
        
        return conflicts
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """Flatten nested dictionary.
        
        Args:
            d: Dictionary to flatten
            parent_key: Parent key for recursion
            sep: Separator for nested keys
            
        Returns:
            Flattened dictionary
        """
        items = []
        
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    def _assess_config_severity(self, file_path: str, conflicts: List[Dict]) -> str:
        """Assess severity of configuration conflicts.
        
        Args:
            file_path: Path to config file
            conflicts: List of conflicts
            
        Returns:
            Severity level (low, medium, high, critical)
        """
        # Critical config files
        critical_files = ['.env', 'config.yaml', 'config.yml', 'settings.json']
        if any(cf in file_path for cf in critical_files):
            return 'high'
        
        # Check for security-sensitive keys
        sensitive_keys = ['password', 'secret', 'token', 'key', 'api_key', 'auth']
        for conflict in conflicts:
            key = conflict['key'].lower()
            if any(sk in key for sk in sensitive_keys):
                return 'critical'
        
        # Based on number of conflicts
        if len(conflicts) > 10:
            return 'high'
        elif len(conflicts) > 5:
            return 'medium'
        else:
            return 'low'
    
    def _generate_config_description(self, conflicts: List[Dict]) -> str:
        """Generate description of configuration conflicts.
        
        Args:
            conflicts: List of conflicts
            
        Returns:
            Description string
        """
        if not conflicts:
            return "No conflicts"
        
        conflict_count = len(conflicts)
        sample_keys = [c['key'] for c in conflicts[:3]]
        
        desc = f"{conflict_count} configuration conflict(s) detected"
        if sample_keys:
            desc += f": {', '.join(sample_keys)}"
            if conflict_count > 3:
                desc += f", and {conflict_count - 3} more"
        
        return desc
